import { Toggle } from "./Toggle";
import {
  SEGMENT_COLORS,
  newSegmentId,
  type PomodoroConfig,
  type PomodoroSegment,
} from "../pomodoro/types";
import "./PomodoroEditor.css";

interface Props {
  config: PomodoroConfig;
  onChange: (next: PomodoroConfig) => void;
  onBack: () => void;
}

export function PomodoroEditor({ config, onChange, onBack }: Props) {
  const segs = config.segments;

  const patch = (p: Partial<PomodoroConfig>) => onChange({ ...config, ...p });

  const updateSeg = (i: number, p: Partial<PomodoroSegment>) => {
    const next = segs.map((s, idx) => (idx === i ? { ...s, ...p } : s));
    patch({ segments: next });
  };

  const move = (i: number, dir: -1 | 1) => {
    const j = i + dir;
    if (j < 0 || j >= segs.length) return;
    const next = segs.slice();
    [next[i], next[j]] = [next[j], next[i]];
    patch({ segments: next });
  };

  const remove = (i: number) => {
    if (segs.length <= 1) return;
    patch({ segments: segs.filter((_, idx) => idx !== i) });
  };

  const add = () => {
    const color = SEGMENT_COLORS[segs.length % SEGMENT_COLORS.length];
    const seg: PomodoroSegment = { id: newSegmentId(), label: "새 구간", minutes: 10, color };
    patch({ segments: [...segs, seg] });
  };

  const cycleColor = (i: number) => {
    const cur = SEGMENT_COLORS.indexOf(segs[i].color);
    const next = SEGMENT_COLORS[(cur + 1) % SEGMENT_COLORS.length];
    updateSeg(i, { color: next });
  };

  const totalMin = segs.reduce((a, s) => a + s.minutes, 0);

  return (
    <div className="settings">
      <div className="settings-header">
        <button className="back-btn" onClick={onBack}>
          ← 뒤로
        </button>
        <div className="settings-title">뽀모도로</div>
        <div style={{ width: 56 }} />
      </div>

      <div className="settings-scroll">
        <div className="setting-row">
          <div className="row-text">
            <div className="row-title">뽀모도로 사용</div>
            <div className="row-desc">구간을 순서대로 진행</div>
          </div>
          <Toggle checked={config.enabled} onChange={(v) => patch({ enabled: v })} />
        </div>
        <div className="setting-row">
          <div className="row-text">
            <div className="row-title">자동 진행</div>
            <div className="row-desc">구간 종료 시 다음 구간 자동 시작</div>
          </div>
          <Toggle checked={config.autoAdvance} onChange={(v) => patch({ autoAdvance: v })} />
        </div>
        <div className="setting-row">
          <div className="row-text">
            <div className="row-title">반복</div>
            <div className="row-desc">마지막 구간 후 처음부터 다시</div>
          </div>
          <Toggle checked={config.loop} onChange={(v) => patch({ loop: v })} />
        </div>

        <div className="sep" />

        <div className="group-label">구간 · 총 {totalMin}분</div>

        <div className="seg-list">
          {segs.map((s, i) => (
            <div className="seg-item" key={s.id}>
              <button
                className="seg-color"
                style={{ background: s.color }}
                onClick={() => cycleColor(i)}
                title="색상 변경"
              />
              <input
                className="seg-label"
                value={s.label}
                maxLength={12}
                onChange={(e) => updateSeg(i, { label: e.target.value })}
              />
              <input
                className="seg-min"
                type="number"
                min={1}
                max={120}
                value={s.minutes}
                onChange={(e) => updateSeg(i, { minutes: clamp(Number(e.target.value), 1, 120) })}
              />
              <span className="seg-unit">분</span>
              <div className="seg-actions">
                <button onClick={() => move(i, -1)} disabled={i === 0} title="위로">
                  ▲
                </button>
                <button onClick={() => move(i, 1)} disabled={i === segs.length - 1} title="아래로">
                  ▼
                </button>
                <button onClick={() => remove(i)} disabled={segs.length <= 1} title="삭제">
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>

        <button className="add-seg-btn" onClick={add}>
          + 구간 추가
        </button>
      </div>
    </div>
  );
}

function clamp(v: number, lo: number, hi: number): number {
  if (Number.isNaN(v)) return lo;
  return Math.max(lo, Math.min(hi, v));
}
