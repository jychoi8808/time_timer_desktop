import { useCallback, useEffect, useRef, useState } from "react";

export interface TimerApi {
  totalSeconds: number;
  remainingSeconds: number;
  isRunning: boolean;
  setSeconds: (s: number) => void;
  start: () => boolean;
  startWith: (s: number) => boolean; // 시간 설정 + 즉시 시작 (동기)
  pause: () => void;
  reset: () => void;
}

/**
 * 카운트다운 상태 머신. 1초 간격으로 남은 시간을 감소시키고,
 * 0에 도달하면 onFinished를 호출한다. (기존 TimerDial의 타이머 로직 포팅)
 */
export function useTimer(onFinished?: () => void): TimerApi {
  const [totalSeconds, setTotal] = useState(0);
  const [remainingSeconds, setRemaining] = useState(0);
  const [isRunning, setRunning] = useState(false);

  const intervalRef = useRef<number | null>(null);
  const remainingRef = useRef(0);
  remainingRef.current = remainingSeconds;
  const finishedRef = useRef(onFinished);
  finishedRef.current = onFinished;

  const clear = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const pause = useCallback(() => {
    setRunning(false);
    clear();
  }, [clear]);

  const start = useCallback((): boolean => {
    if (remainingRef.current <= 0) return false;
    setRunning(true);
    return true;
  }, []);

  const reset = useCallback(() => {
    clear();
    setRunning(false);
    setTotal(0);
    setRemaining(0);
  }, [clear]);

  const setSeconds = useCallback((s: number) => {
    const v = Math.max(0, s);
    setTotal(v);
    setRemaining(v);
    remainingRef.current = v;
  }, []);

  const startWith = useCallback((s: number): boolean => {
    const v = Math.max(0, Math.floor(s));
    if (v <= 0) return false;
    setTotal(v);
    setRemaining(v);
    remainingRef.current = v;
    setRunning(true);
    return true;
  }, []);

  // 실행 상태에 따라 1초 인터벌을 관리
  useEffect(() => {
    if (!isRunning) {
      clear();
      return;
    }
    intervalRef.current = window.setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clear();
          setRunning(false);
          finishedRef.current?.();
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return clear;
  }, [isRunning, clear]);

  return { totalSeconds, remainingSeconds, isRunning, setSeconds, start, startWith, pause, reset };
}
