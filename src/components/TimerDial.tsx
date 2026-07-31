import { useCallback, useEffect, useRef, useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import "./TimerDial.css";

// ── 100 단위 좌표계 기하 상수 (기존 paintEvent 비율 포팅) ──
const CX = 50;
const CY = 50;
const R_NUM = 45; // 숫자 라벨 중심 반지름
const R_TICK_OUT = 41; // 눈금 바깥 반지름
const TICK_LONG = 2.4;
const TICK_SHORT = 1.3;
const R_FACE = 37; // 일반: 파이/링/핸드 반지름
const R_CENTER = 13; // 일반: 중앙 허브 반지름
const R_FACE_MIN = 49; // 미니: 파이 바깥 반지름
const R_CENTER_MIN = 28; // 미니: 중앙 허브(도넛 구멍) 반지름
const IN_DIAL_RATIO = 0.839; // 일반 클릭 인식 반경 (side/2 * 0.839)
const DRAG_THRESHOLD = 8; // 미니모드 클릭/드래그 판정 픽셀

interface Props {
  maxMinutes: number;
  remainingSeconds: number;
  isRunning: boolean;
  onSetSeconds: (s: number) => void;
  minimal?: boolean;
  onToggleRun?: () => void;
  accentColor?: string; // 파이/핸드 색 (뽀모도로 구간 색). 기본 빨강
  settable?: boolean; // false면 드래그로 시간 설정 불가 (뽀모도로 진행 중)
}

function pointOnCircle(r: number, deg: number): [number, number] {
  const rad = (deg * Math.PI) / 180;
  return [CX + r * Math.sin(rad), CY - r * Math.cos(rad)];
}

/** 12시 방향(0)에서 시계방향으로 sweepDeg만큼의 파이 섹터 path */
function piePath(r: number, sweepDeg: number): string {
  const s = Math.min(359.999, Math.max(0, sweepDeg));
  if (s <= 0) return "";
  const [x0, y0] = pointOnCircle(r, 0);
  const [x1, y1] = pointOnCircle(r, s);
  const large = s > 180 ? 1 : 0;
  return `M${CX} ${CY} L${x0} ${y0} A${r} ${r} 0 ${large} 1 ${x1} ${y1} Z`;
}

export function TimerDial({
  maxMinutes,
  remainingSeconds,
  isRunning,
  onSetSeconds,
  minimal = false,
  onToggleRun,
  accentColor = "var(--red)",
  settable = true,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [disp, setDisp] = useState(0); // 부드러운 표시용 (초, 소수)
  const [hoverAngle, setHoverAngle] = useState<number | null>(null);
  const [isDragging, setDragging] = useState(false);

  const dispRef = useRef(0);
  const runningRef = useRef(isRunning);
  runningRef.current = isRunning;
  const remainRef = useRef(remainingSeconds);
  remainRef.current = remainingSeconds;
  const pressRef = useRef<{ x: number; y: number } | null>(null);
  const draggingRef = useRef(false);
  draggingRef.current = isDragging;

  const rFace = minimal ? R_FACE_MIN : R_FACE;
  const rCenter = minimal ? R_CENTER_MIN : R_CENTER;

  // rAF로 disp를 remaining을 향해 부드럽게 이동 (기존 _smooth 로직)
  useEffect(() => {
    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      const target = remainRef.current;
      dispRef.current = runningRef.current ? Math.max(target, dispRef.current - dt) : target;
      setDisp(dispRef.current);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  // 좌표 → 12시 기준 시계방향 각도(0~360)
  const angleFromEvent = useCallback((clientX: number, clientY: number): number => {
    const svg = svgRef.current!;
    const rect = svg.getBoundingClientRect();
    const dx = clientX - (rect.left + rect.width / 2);
    const dy = clientY - (rect.top + rect.height / 2);
    const deg = (Math.atan2(dy, dx) * 180) / Math.PI + 90;
    return ((deg % 360) + 360) % 360;
  }, []);

  /** 클릭이 다이얼 조작 영역 안인지 판정 */
  const inDial = useCallback(
    (clientX: number, clientY: number): boolean => {
      const svg = svgRef.current;
      if (!svg) return false;
      const rect = svg.getBoundingClientRect();
      const dx = clientX - (rect.left + rect.width / 2);
      const dy = clientY - (rect.top + rect.height / 2);
      const distSq = dx * dx + dy * dy;
      const side = Math.min(rect.width, rect.height);
      if (minimal) {
        const inner = side * (R_CENTER_MIN / 100);
        const outer = side * (R_FACE_MIN / 100);
        return distSq >= inner * inner && distSq <= outer * outer;
      }
      const r = (side / 2) * IN_DIAL_RATIO;
      return distSq <= r * r;
    },
    [minimal],
  );

  const applyAngle = useCallback(
    (angle: number) => {
      const raw = Math.round((angle / 360) * maxMinutes * 60);
      const snapped = Math.floor(raw / 60) * 60; // 1분 단위 스냅
      onSetSeconds(Math.max(0, snapped));
    },
    [maxMinutes, onSetSeconds],
  );

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (e.button !== 0) return;
      const insideBand = inDial(e.clientX, e.clientY);
      if (minimal) {
        if (insideBand) {
          pressRef.current = { x: e.clientX, y: e.clientY };
          setDragging(false);
          (e.target as Element).setPointerCapture?.(e.pointerId);
        } else {
          // 밴드 밖 → 창 이동
          void getCurrentWindow().startDragging();
        }
        return;
      }
      // 일반 모드: 실행 중이 아니고 다이얼 안이면 시간 설정 시작
      if (!isRunning && settable && insideBand) {
        setDragging(true);
        applyAngle(angleFromEvent(e.clientX, e.clientY));
        (e.target as Element).setPointerCapture?.(e.pointerId);
      }
    },
    [minimal, isRunning, settable, inDial, applyAngle, angleFromEvent],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (minimal) {
        if (pressRef.current && (e.buttons & 1)) {
          if (!draggingRef.current) {
            const dx = e.clientX - pressRef.current.x;
            const dy = e.clientY - pressRef.current.y;
            if (Math.abs(dx) + Math.abs(dy) > DRAG_THRESHOLD) {
              setDragging(true);
              if (!isRunning && settable) applyAngle(angleFromEvent(e.clientX, e.clientY));
            }
          } else if (!isRunning && settable) {
            applyAngle(angleFromEvent(e.clientX, e.clientY));
          }
        } else if (!isRunning && settable && inDial(e.clientX, e.clientY)) {
          setHoverAngle(angleFromEvent(e.clientX, e.clientY));
        } else if (hoverAngle !== null) {
          setHoverAngle(null);
        }
        return;
      }
      // 일반 모드
      if (isRunning) return;
      if (isDragging) {
        applyAngle(angleFromEvent(e.clientX, e.clientY));
      } else if (settable && inDial(e.clientX, e.clientY)) {
        setHoverAngle(angleFromEvent(e.clientX, e.clientY));
      } else if (hoverAngle !== null) {
        setHoverAngle(null);
      }
    },
    [minimal, isRunning, settable, isDragging, inDial, applyAngle, angleFromEvent, hoverAngle],
  );

  const onPointerUp = useCallback(() => {
    if (minimal && pressRef.current && !draggingRef.current) {
      onToggleRun?.(); // 밴드에서 클릭(드래그 아님) → 시작/정지
    }
    pressRef.current = null;
    setDragging(false);
  }, [minimal, onToggleRun]);

  const onPointerLeave = useCallback(() => setHoverAngle(null), []);

  // ── 렌더 값 계산 ──
  const frac = disp / (maxMinutes * 60);
  const span = frac * 360;
  const handDeg = frac * 360;
  const [handX, handY] = pointOnCircle(R_FACE, handDeg);

  const shown = isRunning ? Math.ceil(disp) : remainingSeconds;
  const mins = Math.floor(shown / 60);
  const secs = shown % 60;
  const timeTxt = isDragging && !minimal
    ? `${String(mins).padStart(2, "0")}:00`
    : `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

  const pieFill = minimal && !isRunning ? "var(--status-col)" : accentColor;

  const step = Math.floor(maxMinutes / 12);
  const numbers = Array.from({ length: 12 }, (_, i) => {
    const [x, y] = pointOnCircle(R_NUM, i * 30);
    return { key: i, x, y, label: String(i * step) };
  });
  const ticks = Array.from({ length: maxMinutes }, (_, i) => {
    const deg = (i * 360) / maxMinutes;
    const major = i % 5 === 0;
    const [xo, yo] = pointOnCircle(R_TICK_OUT, deg);
    const [xi, yi] = pointOnCircle(R_TICK_OUT - (major ? TICK_LONG : TICK_SHORT), deg);
    return { key: i, xo, yo, xi, yi, major };
  });

  return (
    <div className="dial-wrap">
      <svg
        ref={svgRef}
        className="dial-svg"
        viewBox="0 0 100 100"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerLeave}
      >
        {/* 0: 페이스 배경 */}
        <circle cx={CX} cy={CY} r={50} fill="var(--dial-face)" />

        {/* 1: 호버 미리보기 */}
        {hoverAngle !== null && !isRunning && !isDragging && (
          <path d={piePath(rFace, hoverAngle)} fill="var(--red-light)" />
        )}

        {/* 2: 값 파이 섹터 */}
        {disp > 0 && <path d={piePath(rFace, span)} fill={pieFill} />}

        {/* 3~6: 눈금/링/숫자/핸드 (일반 모드만) */}
        {!minimal && (
          <>
            <circle cx={CX} cy={CY} r={R_FACE} fill="none" stroke="var(--dial-ring)" strokeWidth={0.5} />
            {ticks.map((t) => (
              <line
                key={t.key}
                x1={t.xi}
                y1={t.yi}
                x2={t.xo}
                y2={t.yo}
                stroke={t.major ? "var(--tick-major)" : "var(--tick-minor)"}
                strokeWidth={t.major ? 0.5 : 0.25}
                strokeLinecap="round"
              />
            ))}
            {numbers.map((n) => (
              <text
                key={n.key}
                x={n.x}
                y={n.y}
                fill="var(--number-col)"
                fontSize={4.4}
                fontWeight={600}
                textAnchor="middle"
                dominantBaseline="central"
              >
                {n.label}
              </text>
            ))}
            {disp > 0 && (
              <line x1={CX} y1={CY} x2={handX} y2={handY} stroke={accentColor} strokeWidth={0.7} strokeLinecap="round" />
            )}
          </>
        )}

        {/* 7: 중앙 허브 */}
        <circle cx={CX} cy={CY} r={rCenter} fill="var(--dial-face)" />

        {/* 8: 시간 텍스트 */}
        <text
          x={CX}
          y={CY}
          fill="var(--time-col)"
          fontSize={minimal ? 13 : 8.5}
          fontWeight={700}
          textAnchor="middle"
          dominantBaseline="central"
        >
          {timeTxt}
        </text>
      </svg>
    </div>
  );
}
