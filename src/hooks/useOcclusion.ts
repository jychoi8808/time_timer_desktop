import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

export type OcclusionMode = "manual" | "semi-transparent" | "click-through";

interface Options {
  mode: OcclusionMode;
  baseOpacity: number; // 평상시 투명도 (수동 슬라이더 값) 0.2~1
  hoverOpacity: number; // 커서가 올라왔을 때 투명도
  active?: boolean; // false면 가림방지 일시 중지 (설정 화면 등에서 조작 보장)
}

/**
 * 가림 방지 로직.
 * - manual: 항상 baseOpacity 적용 (자동 반응 없음)
 * - semi-transparent: 커서가 창 위에 오면 hoverOpacity로 반투명, 벗어나면 복귀
 * - click-through: Rust 전역 커서 폴링으로 커서가 창 위일 때 클릭을 통과시키고
 *   동시에 hoverOpacity로 반투명. (occlusion-cursor 이벤트 수신)
 *
 * active가 false면 (예: 설정 화면 오픈) 강제로 manual처럼 동작해
 * 클릭 통과가 풀리고 창을 항상 조작할 수 있게 한다.
 *
 * @returns surface에 적용할 유효 투명도
 */
export function useOcclusion({ mode, baseOpacity, hoverOpacity, active = true }: Options): number {
  const [hovering, setHovering] = useState(false);
  const effMode: OcclusionMode = active ? mode : "manual";

  // 반투명 모드: DOM 포인터 enter/leave로 감지
  useEffect(() => {
    if (effMode !== "semi-transparent") return;
    const el = document.documentElement;
    const enter = () => setHovering(true);
    const leave = () => setHovering(false);
    el.addEventListener("pointerenter", enter);
    el.addEventListener("pointerleave", leave);
    return () => {
      el.removeEventListener("pointerenter", enter);
      el.removeEventListener("pointerleave", leave);
      setHovering(false);
    };
  }, [effMode]);

  // 클릭 통과 모드: Rust 폴링 활성화 + 이벤트 수신
  useEffect(() => {
    if (effMode !== "click-through") {
      setHovering(false);
      return;
    }
    let unlisten: (() => void) | undefined;
    void invoke("set_click_through", { enable: true });
    void listen<boolean>("occlusion-cursor", (e) => setHovering(e.payload)).then((f) => {
      unlisten = f;
    });
    return () => {
      void invoke("set_click_through", { enable: false });
      unlisten?.();
      setHovering(false);
    };
  }, [effMode]);

  return effMode !== "manual" && hovering ? hoverOpacity : baseOpacity;
}
