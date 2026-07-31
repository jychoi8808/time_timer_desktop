/**
 * 알림음 합성 — 기존 PyQt 버전의 SoundLibrary 파형 레시피를 Web Audio API로 포팅.
 * 외부 파일 의존 없이 AudioBuffer를 즉석 합성해 재생한다.
 */

const SR = 44100;
type Wave = "sine" | "tri" | "square";

function env(n: number, atk = 0.01, rel = 0.12): Float32Array {
  const a = Math.max(1, Math.floor(n * atk));
  const r = Math.max(1, Math.floor(n * rel));
  const e = new Float32Array(n).fill(1);
  for (let i = 0; i < Math.min(a, n); i++) e[i] = i / a;
  for (let i = 0; i < Math.min(r, n); i++) {
    const idx = n - 1 - i;
    if (idx >= 0) e[idx] = Math.min(e[idx], i / r);
  }
  return e;
}

function tone(
  f: number,
  d: number,
  wt: Wave = "sine",
  v = 0.5,
  a = 0.01,
  r = 0.15,
): number[] {
  const n = Math.floor(SR * d);
  const e = env(n, a, r);
  const out = new Array<number>(n);
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    let s: number;
    if (wt === "tri") {
      const ph = (f * t) % 1;
      s = 4 * Math.abs(ph - 0.5) - 1;
    } else if (wt === "square") {
      s = (Math.sin(2 * Math.PI * f * t) >= 0 ? 1 : -1) * 0.6;
    } else {
      s = Math.sin(2 * Math.PI * f * t);
    }
    out[i] = s * e[i] * v;
  }
  return out;
}

const sil = (d: number): number[] => new Array<number>(Math.floor(SR * d)).fill(0);
const cat = (...parts: number[][]): number[] => ([] as number[]).concat(...parts);
function mix(a: number[], b: number[]): number[] {
  const n = Math.min(a.length, b.length);
  const o = new Array<number>(n);
  for (let i = 0; i < n; i++) o[i] = a[i] + b[i];
  return o;
}

// ── 레시피 (Python 버전과 동일 파라미터) ──────────────
const recipes: Record<string, () => number[]> = {
  "부드러운 차임": () =>
    cat(tone(659.25, 0.4, "sine", 0.5, 0.005, 0.6), sil(0.05), tone(1046.5, 0.6, "sine", 0.45, 0.005, 0.7)),
  "도미솔 상승": () =>
    cat(
      tone(523.25, 0.28, "sine", 0.45, 0.005, 0.5),
      tone(659.25, 0.28, "sine", 0.45, 0.005, 0.5),
      tone(783.99, 0.7, "sine", 0.5, 0.005, 0.7),
    ),
  종소리: () => {
    const b = tone(523.25, 1.2, "sine", 0.4, 0.002, 0.95);
    return mix(mix(b, tone(1046.5, 1.2, "sine", 0.15, 0.002, 0.95)), tone(1568, 1.2, "sine", 0.08, 0.002, 0.95));
  },
  "디지털 비프": () => {
    const b = tone(880, 0.12, "square", 0.4, 0.002, 0.05);
    const s = sil(0.08);
    return cat(b, s, b, s, b);
  },
  딩동: () => cat(tone(880, 0.35, "sine", 0.5, 0.005, 0.6), tone(698.46, 0.5, "sine", 0.45, 0.005, 0.7)),
  "알람 시계": () => {
    let o: number[] = [];
    for (let i = 0; i < 3; i++) {
      o = cat(
        o,
        tone(1000, 0.15, "square", 0.35, 0.002, 0.02),
        sil(0.06),
        tone(800, 0.15, "square", 0.35, 0.002, 0.02),
        sil(0.12),
      );
    }
    return o;
  },
  "파도 음": () => {
    const n = Math.floor(SR * 1.2);
    const o = new Array<number>(n);
    for (let i = 0; i < n; i++) {
      const t = i / SR;
      const f = 500 + 300 * Math.sin((Math.PI * t) / 1.2);
      o[i] = Math.sin(2 * Math.PI * f * t) * Math.sin((Math.PI * t) / 1.2) * 0.45;
    }
    return o;
  },
};

export const SOUND_NAMES = Object.keys(recipes);

let ctx: AudioContext | null = null;
const bufferCache = new Map<string, AudioBuffer>();

function getCtx(): AudioContext {
  if (!ctx) ctx = new AudioContext();
  return ctx;
}

function getBuffer(name: string): AudioBuffer | null {
  const recipe = recipes[name];
  if (!recipe) return null;
  let buf = bufferCache.get(name);
  if (!buf) {
    const samples = recipe();
    const c = getCtx();
    buf = c.createBuffer(1, samples.length, SR);
    const ch = buf.getChannelData(0);
    for (let i = 0; i < samples.length; i++) ch[i] = Math.max(-1, Math.min(1, samples[i]));
    bufferCache.set(name, buf);
  }
  return buf;
}

/** 지정한 알림음을 재생한다. volume: 0~1 */
export function playSound(name: string, volume = 0.85): void {
  const c = getCtx();
  if (c.state === "suspended") void c.resume();
  const buf = getBuffer(name);
  if (!buf) return;
  const src = c.createBufferSource();
  src.buffer = buf;
  const gain = c.createGain();
  gain.gain.value = volume;
  src.connect(gain).connect(c.destination);
  src.start();
}
