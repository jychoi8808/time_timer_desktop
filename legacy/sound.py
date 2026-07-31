import math
import os
import struct
import sys
import tempfile
import wave


class SoundLibrary:
    SR = 44100

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="timetimer_")
        self.sounds: dict[str, str] = {}
        self._build()

    def _wav(self, samples, name):
        path = os.path.join(self.dir, f"{name}.wav")
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.SR)
            wf.writeframes(
                b"".join(
                    struct.pack("<h", max(-32767, min(32767, int(s * 32767))))
                    for s in samples
                )
            )
        return path

    def _env(self, n, atk=0.01, rel=0.12):
        a, r = max(1, int(n * atk)), max(1, int(n * rel))
        e = [1.0] * n
        for i in range(min(a, n)):
            e[i] = i / a
        for i in range(min(r, n)):
            idx = n - 1 - i
            if idx >= 0:
                e[idx] = min(e[idx], i / r)
        return e

    def _tone(self, f, d, wt="sine", v=0.5, a=0.01, r=0.15):
        n = int(self.SR * d)
        env = self._env(n, a, r)
        out = []
        for i in range(n):
            t = i / self.SR
            if wt == "sine":
                s = math.sin(2 * math.pi * f * t)
            elif wt == "tri":
                ph = (f * t) % 1
                s = 4 * abs(ph - 0.5) - 1
            elif wt == "square":
                s = (1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0) * 0.6
            else:
                s = math.sin(2 * math.pi * f * t)
            out.append(s * env[i] * v)
        return out

    def _sil(self, d):
        return [0.0] * int(self.SR * d)

    def _cat(self, *p):
        o = []
        for x in p:
            o.extend(x)
        return o

    def _mix(self, a, b):
        n = min(len(a), len(b))
        return [a[i] + b[i] for i in range(n)]

    def _chime(self):
        return self._cat(
            self._tone(659.25, .4, "sine", .5, .005, .6),
            self._sil(.05),
            self._tone(1046.5, .6, "sine", .45, .005, .7),
        )

    def _bell(self):
        b = self._tone(523.25, 1.2, "sine", .4, .002, .95)
        return self._mix(
            self._mix(b, self._tone(1046.5, 1.2, "sine", .15, .002, .95)),
            self._tone(1568, 1.2, "sine", .08, .002, .95),
        )

    def _beep(self):
        b = self._tone(880, .12, "square", .4, .002, .05)
        s = self._sil(.08)
        return self._cat(b, s, b, s, b)

    def _ding(self):
        return self._cat(
            self._tone(880, .35, "sine", .5, .005, .6),
            self._tone(698.46, .5, "sine", .45, .005, .7),
        )

    def _alarm(self):
        o = []
        for _ in range(3):
            o += (
                self._tone(1000, .15, "square", .35, .002, .02)
                + self._sil(.06)
                + self._tone(800, .15, "square", .35, .002, .02)
                + self._sil(.12)
            )
        return o

    def _wave(self):
        n = int(self.SR * 1.2)
        o = []
        for i in range(n):
            t = i / self.SR
            f = 500 + 300 * math.sin(math.pi * t / 1.2)
            o.append(math.sin(2 * math.pi * f * t) * math.sin(math.pi * t / 1.2) * 0.45)
        return o

    def _triple(self):
        return self._cat(
            self._tone(523.25, .28, "sine", .45, .005, .5),
            self._tone(659.25, .28, "sine", .45, .005, .5),
            self._tone(783.99, .7,  "sine", .5,  .005, .7),
        )

    def _build(self):
        for name, fn in [
            ("부드러운 차임", self._chime),
            ("도미솔 상승",   self._triple),
            ("종소리",        self._bell),
            ("디지털 비프",   self._beep),
            ("딩동",          self._ding),
            ("알람 시계",     self._alarm),
            ("파도 음",       self._wave),
        ]:
            try:
                self.sounds[name] = self._wav(fn(), name.replace(" ", "_"))
            except Exception as e:
                print(f"[snd]{name}:{e}", file=sys.stderr)

    def names(self):
        return list(self.sounds.keys())

    def path(self, name):
        return self.sounds.get(name)
