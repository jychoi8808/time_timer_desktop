import { Toggle } from "./Toggle";
import { SOUND_NAMES } from "../audio/sounds";
import type { Settings } from "../settings/useSettings";
import type { OcclusionMode } from "../hooks/useOcclusion";
import "./SettingsPage.css";

interface Props {
  settings: Settings;
  update: (patch: Partial<Settings>) => void;
  onBack: () => void;
  onPreview: () => void;
  onOpenPomodoro: () => void;
}

const OCCLUSION_LABELS: { value: OcclusionMode; label: string }[] = [
  { value: "manual", label: "수동" },
  { value: "semi-transparent", label: "반투명" },
  { value: "click-through", label: "클릭통과" },
];

export function SettingsPage({ settings, update, onBack, onPreview, onOpenPomodoro }: Props) {
  const s = settings;
  return (
    <div className="settings">
      <div className="settings-header">
        <button className="back-btn" onClick={onBack}>
          ← 뒤로
        </button>
        <div className="settings-title">설정</div>
        <div style={{ width: 56 }} />
      </div>

      <div className="settings-scroll">
        {/* 알림음 */}
        <div className="group-label">알림음</div>
        <Row title="알림음 사용" desc="타이머 종료 시 소리 재생">
          <Toggle checked={s.soundEnabled} onChange={(v) => update({ soundEnabled: v })} />
        </Row>
        <Row title="무음 모드" desc="종료 시 소리 대신 화면 깜빡임">
          <Toggle checked={s.silentFlash} onChange={(v) => update({ silentFlash: v })} />
        </Row>
        <Row title="OS 알림" desc="종료 시 시스템 알림 표시">
          <Toggle checked={s.osNotification} onChange={(v) => update({ osNotification: v })} />
        </Row>
        <div className="col-row">
          <div className="row-title">알림음 종류</div>
          <div className="sound-picker">
            <select
              className="select"
              value={s.soundName}
              onChange={(e) => update({ soundName: e.target.value })}
            >
              {SOUND_NAMES.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
            <button className="back-btn preview-btn" onClick={onPreview}>
              ▶ 미리듣기
            </button>
          </div>
          <div className="col-row" style={{ paddingTop: 8 }}>
            <div className="row-desc">음량 {Math.round(s.volume * 100)}%</div>
            <input
              className="slider"
              type="range"
              min={0}
              max={100}
              value={Math.round(s.volume * 100)}
              onChange={(e) => update({ volume: Number(e.target.value) / 100 })}
            />
          </div>
        </div>

        <div className="sep" />

        {/* 타이머 */}
        <div className="group-label">타이머</div>
        <Row title="120분 모드" desc="다이얼 최대 시간을 120분으로 설정">
          <Toggle checked={s.mode120} onChange={(v) => update({ mode120: v })} />
        </Row>
        <div className="setting-row">
          <div className="row-text">
            <div className="row-title">뽀모도로</div>
            <div className="row-desc">
              {s.pomodoro.enabled ? `사용 중 · 구간 ${s.pomodoro.segments.length}개` : "꺼짐"}
            </div>
          </div>
          <button className="back-btn" onClick={onOpenPomodoro}>
            편집 →
          </button>
        </div>

        <div className="sep" />

        {/* 화면 / 가림 방지 */}
        <div className="group-label">화면 · 가림 방지</div>
        <div className="col-row">
          <div className="row-title">가림 방지 모드</div>
          <div className="row-desc">
            {s.occlusionMode === "manual" && "투명도만 수동 조절 (자동 반응 없음)"}
            {s.occlusionMode === "semi-transparent" && "커서를 올리면 반투명해집니다"}
            {s.occlusionMode === "click-through" && "커서를 올리면 뒤 작업을 클릭할 수 있습니다"}
          </div>
          <div className="segmented">
            {OCCLUSION_LABELS.map((o) => (
              <button
                key={o.value}
                className={`seg ${s.occlusionMode === o.value ? "active" : ""}`}
                onClick={() => update({ occlusionMode: o.value })}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>

        <div className="col-row">
          <div className="row-desc">창 투명도 {Math.round(s.baseOpacity * 100)}%</div>
          <input
            className="slider"
            type="range"
            min={20}
            max={100}
            value={Math.round(s.baseOpacity * 100)}
            onChange={(e) => update({ baseOpacity: Number(e.target.value) / 100 })}
          />
        </div>

        <div className="col-row">
          <div className="row-desc">
            커서 올렸을 때 투명도 {Math.round(s.hoverOpacity * 100)}%
            {s.occlusionMode === "manual" && " (수동 모드에서는 미적용)"}
          </div>
          <input
            className="slider"
            type="range"
            min={5}
            max={90}
            value={Math.round(s.hoverOpacity * 100)}
            disabled={s.occlusionMode === "manual"}
            onChange={(e) => update({ hoverOpacity: Number(e.target.value) / 100 })}
          />
        </div>

        <div className="sep" />

        {/* 전역 단축키 (안내) */}
        <div className="group-label">전역 단축키</div>
        <div className="hotkey-row">
          <span>시작 / 정지</span>
          <kbd>{fmtKey(s.hotkeys.startPause)}</kbd>
        </div>
        <div className="hotkey-row">
          <span>리셋</span>
          <kbd>{fmtKey(s.hotkeys.reset)}</kbd>
        </div>
        <div className="hotkey-row">
          <span>창 표시 / 숨김</span>
          <kbd>{fmtKey(s.hotkeys.toggleWindow)}</kbd>
        </div>
        <div className="hotkey-row">
          <span>가림 방지 모드 전환</span>
          <kbd>{fmtKey(s.hotkeys.cycleOcclusion)}</kbd>
        </div>
      </div>
    </div>
  );
}

function fmtKey(accel: string | undefined): string {
  if (!accel) return "—";
  return accel.replace("CommandOrControl", "Ctrl").replace(/\+/g, " + ");
}

function Row({ title, desc, children }: { title: string; desc?: string; children: React.ReactNode }) {
  return (
    <div className="setting-row">
      <div className="row-text">
        <div className="row-title">{title}</div>
        {desc && <div className="row-desc">{desc}</div>}
      </div>
      {children}
    </div>
  );
}
