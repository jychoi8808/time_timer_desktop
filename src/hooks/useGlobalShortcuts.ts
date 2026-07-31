import { useEffect, useRef } from "react";
import { register, unregister } from "@tauri-apps/plugin-global-shortcut";
import type { Hotkeys } from "../settings/useSettings";

export interface ShortcutHandlers {
  onStartPause: () => void;
  onReset: () => void;
  onToggleWindow: () => void;
  onCycleOcclusion: () => void;
}

/**
 * 전역 단축키 등록. 창 포커스와 무관하게 시작/정지·리셋·창토글을 수행한다.
 */
export function useGlobalShortcuts(hotkeys: Hotkeys, handlers: ShortcutHandlers) {
  const ref = useRef(handlers);
  ref.current = handlers;

  useEffect(() => {
    const entries: Array<[string, () => void]> = [
      [hotkeys.startPause, () => ref.current.onStartPause()],
      [hotkeys.reset, () => ref.current.onReset()],
      [hotkeys.toggleWindow, () => ref.current.onToggleWindow()],
      [hotkeys.cycleOcclusion, () => ref.current.onCycleOcclusion()],
    ];
    const registered: string[] = [];

    (async () => {
      for (const [accel, cb] of entries) {
        if (!accel) continue;
        try {
          await unregister(accel).catch(() => {});
          await register(accel, (e) => {
            if (e.state === "Pressed") cb();
          });
          registered.push(accel);
        } catch {
          /* 이미 다른 앱이 점유한 조합 등은 무시 */
        }
      }
    })();

    return () => {
      registered.forEach((a) => void unregister(a).catch(() => {}));
    };
  }, [hotkeys.startPause, hotkeys.reset, hotkeys.toggleWindow, hotkeys.cycleOcclusion]);
}
