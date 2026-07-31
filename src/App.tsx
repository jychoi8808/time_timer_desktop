import { useCallback, useEffect, useRef, useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { listen } from "@tauri-apps/api/event";
import "./App.css";
import { TimerDial } from "./components/TimerDial";
import { ResizeHandles } from "./components/ResizeHandles";
import { SettingsPage } from "./components/SettingsPage";
import { PomodoroEditor } from "./components/PomodoroEditor";
import { useTimer } from "./hooks/useTimer";
import { useOcclusion, type OcclusionMode } from "./hooks/useOcclusion";
import { useWindowPersistence } from "./hooks/useWindowPersistence";
import { useGlobalShortcuts } from "./hooks/useGlobalShortcuts";
import { useSettings } from "./settings/useSettings";
import { playSound } from "./audio/sounds";
import { notify } from "./notify";
import type { PomodoroConfig } from "./pomodoro/types";

const PRESETS = [5, 10, 15, 25, 45];
const MIN_W = 200;
const MIN_H = 250;

const appWindow = getCurrentWindow();

const OCCLUSION_ORDER: OcclusionMode[] = ["manual", "semi-transparent", "click-through"];
const OCCLUSION_LABEL: Record<OcclusionMode, string> = {
  manual: "가림 방지: 수동",
  "semi-transparent": "가림 방지: 반투명",
  "click-through": "가림 방지: 클릭통과",
};

type View = "main" | "settings" | "pomodoro";

function App() {
  const { settings, update, loaded } = useSettings();
  const [isMinimal, setIsMinimal] = useState(false);
  const [view, setView] = useState<View>("main");
  const [flash, setFlash] = useState(false);
  const [pomoIndex, setPomoIndex] = useState(0);
  const [toast, setToast] = useState<string | null>(null);
  const flashTimer = useRef<number | null>(null);
  const toastTimer = useRef<number | null>(null);

  useWindowPersistence();

  const pomo = settings.pomodoro;
  const maxMinutes = settings.mode120 ? 120 : 60;
  const currentSegment =
    pomo.enabled && pomo.segments.length ? pomo.segments[Math.min(pomoIndex, pomo.segments.length - 1)] : null;
  const accentColor = currentSegment ? currentSegment.color : "var(--red)";

  const surfaceOpacity = useOcclusion({
    mode: settings.occlusionMode,
    baseOpacity: settings.baseOpacity,
    hoverOpacity: settings.hoverOpacity,
    active: view === "main", // 설정/뽀모도로 화면에서는 가림방지 일시 중지
  });

  // 무음 모드: 화면을 붉게 3회 깜빡임 (기존 _flash_window 포팅)
  const doFlash = useCallback(() => {
    if (flashTimer.current) window.clearInterval(flashTimer.current);
    let n = 0;
    flashTimer.current = window.setInterval(() => {
      n += 1;
      setFlash(n % 2 === 1);
      if (n > 6) {
        if (flashTimer.current) window.clearInterval(flashTimer.current);
        flashTimer.current = null;
        setFlash(false);
      }
    }, 300);
  }, []);

  const settingsRef = useRef(settings);
  settingsRef.current = settings;
  const pomoIndexRef = useRef(pomoIndex);
  pomoIndexRef.current = pomoIndex;
  const runningRef = useRef(false);

  // 종료 처리: 알림 + (뽀모도로면) 다음 구간 진행
  const finishRef = useRef<() => void>(() => {});
  const timer = useTimer(() => finishRef.current());
  const { remainingSeconds, isRunning, setSeconds, start, startWith, pause, reset } = timer;
  runningRef.current = isRunning;

  finishRef.current = () => {
    const s = settingsRef.current;
    if (s.silentFlash) doFlash();
    else if (s.soundEnabled) playSound(s.soundName, s.volume);

    if (s.osNotification) {
      const body = currentSegment ? `${currentSegment.label} 종료` : "타이머 종료";
      void notify("Time Timer", body);
    }

    const p = s.pomodoro;
    if (!p.enabled || p.segments.length === 0) return;
    const cur = pomoIndexRef.current;
    let next = cur + 1;
    if (next >= p.segments.length) {
      if (!p.loop) {
        // 마지막 구간 종료 → 처음 구간 대기 상태로
        setPomoIndex(0);
        setSeconds(p.segments[0].minutes * 60);
        return;
      }
      next = 0;
    }
    setPomoIndex(next);
    const seg = p.segments[next];
    if (p.autoAdvance) startWith(seg.minutes * 60);
    else setSeconds(seg.minutes * 60);
  };

  const onStartPause = useCallback(() => {
    if (isRunning) pause();
    else start();
  }, [isRunning, pause, start]);

  const onReset = useCallback(() => {
    reset();
    const p = settingsRef.current.pomodoro;
    if (p.enabled && p.segments.length) {
      setPomoIndex(0);
      setSeconds(p.segments[0].minutes * 60);
    }
  }, [reset, setSeconds]);

  const onPreview = useCallback(() => {
    const s = settingsRef.current;
    if (s.silentFlash) doFlash();
    else playSound(s.soundName, s.volume);
  }, [doFlash]);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(null), 1400);
  }, []);

  const onCycleOcclusion = useCallback(() => {
    const cur = settingsRef.current.occlusionMode;
    const next = OCCLUSION_ORDER[(OCCLUSION_ORDER.indexOf(cur) + 1) % OCCLUSION_ORDER.length];
    update({ occlusionMode: next });
    showToast(OCCLUSION_LABEL[next]);
  }, [update, showToast]);

  const onToggleWindow = useCallback(async () => {
    const visible = await appWindow.isVisible();
    if (visible) {
      await appWindow.hide();
    } else {
      await appWindow.show();
      await appWindow.unminimize();
      await appWindow.setFocus();
    }
  }, []);

  // 트레이/단축키에서 최신 핸들러를 참조하기 위한 ref
  const handlersRef = useRef({ onStartPause, onReset, onOcclusionOff: () => {} });
  handlersRef.current = {
    onStartPause,
    onReset,
    onOcclusionOff: () => update({ occlusionMode: "manual" }),
  };

  // 시스템 트레이 메뉴 이벤트 수신
  useEffect(() => {
    const unlisteners: Array<() => void> = [];
    void listen("tray-startpause", () => handlersRef.current.onStartPause()).then((u) => unlisteners.push(u));
    void listen("tray-reset", () => handlersRef.current.onReset()).then((u) => unlisteners.push(u));
    void listen("tray-occlusion-off", () => handlersRef.current.onOcclusionOff()).then((u) => unlisteners.push(u));
    return () => unlisteners.forEach((u) => u());
  }, []);

  // 전역 단축키
  useGlobalShortcuts(settings.hotkeys, { onStartPause, onReset, onToggleWindow, onCycleOcclusion });

  // 뽀모도로 비활성화 시 타이머 초기화
  useEffect(() => {
    if (!pomo.enabled) reset();
  }, [pomo.enabled, reset]);

  // 뽀모도로 활성 & 정지 상태에서 현재 구간 길이를 다이얼에 반영 (구간 편집/전환 동기화)
  useEffect(() => {
    if (pomo.enabled && currentSegment && !runningRef.current) {
      setSeconds(currentSegment.minutes * 60);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSegment?.id, currentSegment?.minutes, pomo.enabled]);

  // 창 크기에 따라 미니모드 자동 전환
  useEffect(() => {
    const check = () => setIsMinimal(window.innerWidth < MIN_W || window.innerHeight < MIN_H);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // 항상 위 설정을 창에 동기화
  useEffect(() => {
    if (!loaded) return;
    void appWindow.setAlwaysOnTop(settings.alwaysOnTop);
  }, [settings.alwaysOnTop, loaded]);

  const togglePin = () => update({ alwaysOnTop: !settings.alwaysOnTop });
  const onChangePomo = (next: PomodoroConfig) => update({ pomodoro: next });

  const showOverlay = view !== "main" && !isMinimal;

  return (
    <>
      <ResizeHandles />
      <div
        className={`surface ${isMinimal ? "minimal" : ""} ${flash ? "flash" : ""}`}
        style={{ opacity: surfaceOpacity }}
      >
        {toast && <div className="toast">{toast}</div>}
        {showOverlay && view === "settings" && (
          <SettingsPage
            settings={settings}
            update={update}
            onBack={() => setView("main")}
            onPreview={onPreview}
            onOpenPomodoro={() => setView("pomodoro")}
          />
        )}
        {showOverlay && view === "pomodoro" && (
          <PomodoroEditor config={pomo} onChange={onChangePomo} onBack={() => setView("settings")} />
        )}

        {!showOverlay && (
          <>
            {!isMinimal && (
              <div className="titlebar">
                <button
                  className={`icon-btn pin ${settings.alwaysOnTop ? "active" : ""}`}
                  onClick={togglePin}
                  title="항상 위 고정"
                >
                  📌
                </button>
                <div className="drag-spacer" data-tauri-drag-region />
                <button className="icon-btn" onClick={() => setView("settings")} title="설정">
                  ⚙
                </button>
                <button className="icon-btn" onClick={() => appWindow.minimize()} title="최소화">
                  —
                </button>
                <button className="icon-btn" onClick={() => appWindow.close()} title="종료">
                  ✕
                </button>
              </div>
            )}

            <div className="content">
              <TimerDial
                maxMinutes={maxMinutes}
                remainingSeconds={remainingSeconds}
                isRunning={isRunning}
                onSetSeconds={setSeconds}
                minimal={isMinimal}
                onToggleRun={onStartPause}
                accentColor={accentColor}
                settable={!pomo.enabled}
              />
            </div>

            {!isMinimal && (
              <>
                {pomo.enabled && currentSegment ? (
                  <div className="pomo-status">
                    <span className="pomo-dot" style={{ background: currentSegment.color }} />
                    {currentSegment.label} · {pomoIndex + 1}/{pomo.segments.length}
                  </div>
                ) : (
                  <div className="presets">
                    {PRESETS.map((m) => (
                      <button
                        key={m}
                        className="preset-btn"
                        onClick={() => setSeconds(m * 60)}
                        disabled={isRunning || m > maxMinutes}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                )}

                <div className="controls">
                  <button className="ctrl-btn" onClick={onReset} title="리셋">
                    🔄
                  </button>
                  <button
                    className="ctrl-btn ctrl-primary"
                    onClick={onStartPause}
                    title={isRunning ? "일시정지" : "시작"}
                  >
                    {isRunning ? "⏸️" : "▶️"}
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </>
  );
}

export default App;
