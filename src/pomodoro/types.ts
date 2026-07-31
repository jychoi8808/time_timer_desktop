export interface PomodoroSegment {
  id: string;
  label: string;
  minutes: number;
  color: string;
}

export interface PomodoroConfig {
  enabled: boolean;
  autoAdvance: boolean; // 구간 종료 시 자동으로 다음 구간 시작
  loop: boolean; // 리스트 끝나면 처음부터 반복
  segments: PomodoroSegment[];
}

export const SEGMENT_COLORS = [
  "#f05650", // red
  "#4a9d7f", // green
  "#4a8cf0", // blue
  "#f0a350", // orange
  "#9d6ef0", // purple
  "#50b8c9", // teal
];

export const DEFAULT_POMODORO: PomodoroConfig = {
  enabled: false,
  autoAdvance: true,
  loop: true,
  segments: [
    { id: "seg-focus", label: "집중", minutes: 25, color: "#f05650" },
    { id: "seg-break", label: "휴식", minutes: 5, color: "#4a9d7f" },
  ],
};

export function newSegmentId(): string {
  return `seg-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}
