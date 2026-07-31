import { useEffect } from "react";
import { getCurrentWindow, PhysicalPosition, PhysicalSize } from "@tauri-apps/api/window";
import { LazyStore } from "@tauri-apps/plugin-store";

interface WinState {
  x: number;
  y: number;
  w: number;
  h: number;
}

const store = new LazyStore("window.json");

/**
 * 창의 위치·크기를 저장하고 앱 시작 시 복원한다.
 * 이동/리사이즈 시 400ms 디바운스로 저장.
 */
export function useWindowPersistence() {
  useEffect(() => {
    const win = getCurrentWindow();
    const unlisteners: Array<() => void> = [];
    let saveTimer: number | undefined;
    let cancelled = false;

    (async () => {
      const st = await store.get<WinState>("state").catch(() => undefined);
      if (!cancelled && st && st.w > 0 && st.h > 0) {
        try {
          await win.setSize(new PhysicalSize(st.w, st.h));
          await win.setPosition(new PhysicalPosition(st.x, st.y));
        } catch {
          /* 모니터 구성 변경 등으로 실패 시 무시 */
        }
      }

      const save = async () => {
        try {
          const pos = await win.outerPosition();
          const size = await win.outerSize();
          await store.set("state", { x: pos.x, y: pos.y, w: size.width, h: size.height });
          await store.save();
        } catch {
          /* ignore */
        }
      };
      const schedule = () => {
        if (saveTimer) window.clearTimeout(saveTimer);
        saveTimer = window.setTimeout(save, 400);
      };

      unlisteners.push(await win.onResized(schedule));
      unlisteners.push(await win.onMoved(schedule));
    })();

    return () => {
      cancelled = true;
      unlisteners.forEach((u) => u());
      if (saveTimer) window.clearTimeout(saveTimer);
    };
  }, []);
}
