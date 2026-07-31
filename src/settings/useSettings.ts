import { useCallback, useEffect, useState } from "react";
import { LazyStore } from "@tauri-apps/plugin-store";
import type { OcclusionMode } from "../hooks/useOcclusion";
import { DEFAULT_POMODORO, type PomodoroConfig } from "../pomodoro/types";

export interface Settings {
  soundEnabled: boolean;
  silentFlash: boolean; // 무음 모드: 소리 대신 화면 깜빡임
  soundName: string;
  volume: number; // 0~1
  mode120: boolean; // 다이얼 최대 120분
  occlusionMode: OcclusionMode;
  baseOpacity: number; // 평상시 창 투명도 0.2~1
  hoverOpacity: number; // 커서 올릴 때 투명도 0.05~0.9
  alwaysOnTop: boolean;
  osNotification: boolean; // 종료 시 OS 네이티브 알림
  hotkeys: Hotkeys;
  pomodoro: PomodoroConfig;
}

export interface Hotkeys {
  startPause: string;
  reset: string;
  toggleWindow: string;
  cycleOcclusion: string;
}

export const DEFAULT_HOTKEYS: Hotkeys = {
  startPause: "CommandOrControl+Shift+Space",
  reset: "CommandOrControl+Shift+R",
  toggleWindow: "CommandOrControl+Shift+T",
  cycleOcclusion: "CommandOrControl+Shift+O",
};

export const DEFAULT_SETTINGS: Settings = {
  soundEnabled: true,
  silentFlash: false,
  soundName: "부드러운 차임",
  volume: 0.85,
  mode120: false,
  occlusionMode: "manual",
  baseOpacity: 1,
  hoverOpacity: 0.25,
  alwaysOnTop: true,
  osNotification: true,
  hotkeys: DEFAULT_HOTKEYS,
  pomodoro: DEFAULT_POMODORO,
};

// 파일 기반 영속 저장소 (앱 데이터 폴더의 settings.json)
const store = new LazyStore("settings.json");

export interface SettingsApi {
  settings: Settings;
  update: (patch: Partial<Settings>) => void;
  loaded: boolean;
}

export function useSettings(): SettingsApi {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    store
      .get<Settings>("settings")
      .then((saved) => {
        if (cancelled) return;
        if (saved) {
          // 중첩 객체(hotkeys, pomodoro)까지 기본값과 병합해
          // 이후 추가된 키가 누락되지 않게 한다 (스키마 진화 대비).
          setSettings({
            ...DEFAULT_SETTINGS,
            ...saved,
            hotkeys: { ...DEFAULT_HOTKEYS, ...saved.hotkeys },
            pomodoro: { ...DEFAULT_POMODORO, ...saved.pomodoro },
          });
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const update = useCallback((patch: Partial<Settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      void store.set("settings", next).then(() => store.save());
      return next;
    });
  }, []);

  return { settings, update, loaded };
}
