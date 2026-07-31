import { getCurrentWindow } from "@tauri-apps/api/window";
import "./ResizeHandles.css";

// 프레임리스 창의 커스텀 리사이즈 핸들 (Windows는 기본 가장자리 리사이즈 미지원)
type Dir = "North" | "South" | "East" | "West" | "NorthEast" | "NorthWest" | "SouthEast" | "SouthWest";

const HANDLES: { cls: string; dir: Dir }[] = [
  { cls: "rh-n", dir: "North" },
  { cls: "rh-s", dir: "South" },
  { cls: "rh-e", dir: "East" },
  { cls: "rh-w", dir: "West" },
  { cls: "rh-ne", dir: "NorthEast" },
  { cls: "rh-nw", dir: "NorthWest" },
  { cls: "rh-se", dir: "SouthEast" },
  { cls: "rh-sw", dir: "SouthWest" },
];

export function ResizeHandles() {
  return (
    <>
      {HANDLES.map((h) => (
        <div
          key={h.cls}
          className={`resize-handle ${h.cls}`}
          onPointerDown={(e) => {
            if (e.button !== 0) return;
            e.preventDefault();
            void getCurrentWindow().startResizeDragging(h.dir);
          }}
        />
      ))}
    </>
  );
}
