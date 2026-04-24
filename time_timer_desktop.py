"""
Time Timer (Desktop) — v3
- 120분 모드 ON/OFF 토글
- 시스템 라이트/다크 테마 자동 감지 및 동적 반영
- 창 리사이즈에 반응하는 반응형 원형 타이머
- 8종 내장 알림음 (파형 합성, 외부 파일 불필요)
"""

import sys
import math
import struct
import wave
import os
import tempfile

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QComboBox, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, QSize, QUrl
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QRadialGradient, QCursor, QPalette
)
from PyQt5.QtMultimedia import QSoundEffect


# ======================================================================
# 테마 토큰 — 라이트 / 다크
# ======================================================================
class Theme:
    """모든 색상/스타일을 한 곳에서 관리한다."""

    # 공통
    RED_BRIGHT  = QColor(239, 68,  68)
    RED_DARK    = QColor(185, 28,  28)
    RED_HOVER   = QColor(220, 38,  38, 55)
    RED_ACCENT  = QColor(220, 38,  38)

    def __init__(self, dark: bool):
        self.dark = dark
        if dark:
            # ── 다크 팔레트 ──
            self.win_bg            = QColor(28,  28,  30)   # 창 배경
            self.container_bg      = QColor(36,  36,  38)   # 컨테이너
            self.container_border  = QColor(60,  60,  65)
            self.shadow_color      = QColor(0,   0,   0, 120)

            self.dial_bg_inner     = QColor(52,  52,  56)
            self.dial_bg_outer     = QColor(42,  42,  46)
            self.dial_border       = QColor(90,  90,  95)
            self.dial_outer_shadow = QColor(0,   0,   0, 60)

            self.tick_major        = QColor(200, 200, 205)
            self.tick_minor        = QColor(120, 120, 128)
            self.number_color      = QColor(210, 210, 215)

            self.center_bg_inner   = QColor(48,  48,  52, 240)
            self.center_bg_outer   = QColor(44,  44,  48, 200)
            self.center_border     = QColor(255, 255, 255, 20)
            self.center_time_color = QColor(235, 235, 240)
            self.center_dot        = QColor(180, 180, 185)

            self.status_running    = QColor(248, 113, 113)
            self.status_dragging   = QColor(160, 160, 165)
            self.status_ready      = QColor(130, 130, 135)
            self.status_idle       = QColor(100, 100, 108)

            self.title_color       = "#d0d0d5"
            self.label_color       = "#909096"
        else:
            # ── 라이트 팔레트 ──
            self.win_bg            = QColor(240, 240, 242)
            self.container_bg      = QColor(250, 250, 250)
            self.container_border  = QColor(217, 217, 217)
            self.shadow_color      = QColor(0,   0,   0, 80)

            self.dial_bg_inner     = QColor(255, 255, 255)
            self.dial_bg_outer     = QColor(243, 243, 243)
            self.dial_border       = QColor(40,  40,  40)
            self.dial_outer_shadow = QColor(0,   0,   0, 25)

            self.tick_major        = QColor(30,  30,  30)
            self.tick_minor        = QColor(70,  70,  70)
            self.number_color      = QColor(30,  30,  30)

            self.center_bg_inner   = QColor(255, 255, 255, 245)
            self.center_bg_outer   = QColor(255, 255, 255, 200)
            self.center_border     = QColor(0,   0,   0, 30)
            self.center_time_color = QColor(20,  20,  20)
            self.center_dot        = QColor(40,  40,  40)

            self.status_running    = QColor(220, 38,  38)
            self.status_dragging   = QColor(80,  80,  80)
            self.status_ready      = QColor(120, 120, 120)
            self.status_idle       = QColor(150, 150, 150)

            self.title_color       = "#333333"
            self.label_color       = "#555555"

    # ─── QSS 스타일시트 생성 ────────────────────────────────────────────
    def stylesheet(self) -> str:
        if self.dark:
            c = dict(
                container_bg      = "#242426",
                container_border  = "#3c3c41",
                title_color       = "#d0d0d5",
                label_color       = "#909096",
                btn_bg            = "#2e2e32",
                btn_border        = "#48484e",
                btn_color         = "#d8d8dd",
                btn_hover_bg      = "#383840",
                btn_press_bg      = "#22222a",
                start_bg          = "#dc2626",
                start_hover       = "#ef4444",
                start_press       = "#b91c1c",
                reset_bg          = "#2e2e32",
                reset_color       = "#c0c0c8",
                preset_bg         = "#26262a",
                preset_border     = "#3a3a40",
                preset_hover_bg   = "#3d1212",
                preset_hover_bd   = "#dc2626",
                preset_hover_cl   = "#ef4444",
                pin_bg            = "#3d1212",
                pin_border        = "#7f1d1d",
                pin_color         = "#f87171",
                pin_chk_bg        = "#dc2626",
                pin_chk_brd       = "#dc2626",
                pin_hover         = "#4d1515",
                pin_chk_hover     = "#ef4444",
                win_btn_color     = "#888890",
                close_hover_bg    = "#dc2626",
                winbtn_hover_bg   = "#3a3a40",
                preview_bg        = "#1e2a3a",
                preview_border    = "#1d3a5e",
                preview_color     = "#60a5fa",
                preview_hover     = "#1e3a5e",
                combo_bg          = "#2a2a2e",
                combo_border      = "#48484e",
                combo_hover_bd    = "#666670",
                combo_arrow       = "#aaaaaa",
                combo_view_bg     = "#2a2a2e",
                combo_sel_bg      = "#3d1212",
                combo_sel_color   = "#ef4444",
                mode_bg           = "#1e2e1e",
                mode_border       = "#2d5a2d",
                mode_color        = "#4ade80",
                mode_chk_bg       = "#166534",
                mode_chk_bd       = "#16a34a",
                mode_chk_cl       = "#bbf7d0",
                mode_hover        = "#24382a",
            )
        else:
            c = dict(
                container_bg      = "#fafafa",
                container_border  = "#d9d9d9",
                title_color       = "#333333",
                label_color       = "#555555",
                btn_bg            = "#ffffff",
                btn_border        = "#d0d0d0",
                btn_color         = "#222222",
                btn_hover_bg      = "#f4f4f4",
                btn_press_bg      = "#e8e8e8",
                start_bg          = "#dc2626",
                start_hover       = "#ef4444",
                start_press       = "#b91c1c",
                reset_bg          = "#ffffff",
                reset_color       = "#333333",
                preset_bg         = "#f3f4f6",
                preset_border     = "#e2e4e8",
                preset_hover_bg   = "#fee2e2",
                preset_hover_bd   = "#dc2626",
                preset_hover_cl   = "#dc2626",
                pin_bg            = "#fef2f2",
                pin_border        = "#fecaca",
                pin_color         = "#dc2626",
                pin_chk_bg        = "#dc2626",
                pin_chk_brd       = "#dc2626",
                pin_hover         = "#fee2e2",
                pin_chk_hover     = "#ef4444",
                win_btn_color     = "#666666",
                close_hover_bg    = "#dc2626",
                winbtn_hover_bg   = "#e5e5e5",
                preview_bg        = "#eff6ff",
                preview_border    = "#bfdbfe",
                preview_color     = "#1d4ed8",
                preview_hover     = "#dbeafe",
                combo_bg          = "#ffffff",
                combo_border      = "#d0d0d0",
                combo_hover_bd    = "#999999",
                combo_arrow       = "#666666",
                combo_view_bg     = "#ffffff",
                combo_sel_bg      = "#fee2e2",
                combo_sel_color   = "#dc2626",
                mode_bg           = "#f0fdf4",
                mode_border       = "#bbf7d0",
                mode_color        = "#166534",
                mode_chk_bg       = "#16a34a",
                mode_chk_bd       = "#15803d",
                mode_chk_cl       = "#ffffff",
                mode_hover        = "#dcfce7",
            )

        return f"""
            QFrame#container {{
                background-color: {c['container_bg']};
                border: 1px solid {c['container_border']};
                border-radius: 18px;
            }}
            QLabel#titleLabel {{
                color: {c['title_color']};
                font-size: 13px;
                font-weight: bold;
                padding-left: 4px;
            }}
            QLabel#soundLabel, QLabel#modeLabel {{
                color: {c['label_color']};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {c['btn_bg']};
                border: 1px solid {c['btn_border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                color: {c['btn_color']};
            }}
            QPushButton:hover {{
                background-color: {c['btn_hover_bg']};
                border-color: {c['combo_hover_bd']};
            }}
            QPushButton:pressed {{
                background-color: {c['btn_press_bg']};
            }}
            QPushButton#startBtn {{
                background-color: {c['start_bg']};
                color: white;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton#startBtn:hover {{ background-color: {c['start_hover']}; }}
            QPushButton#startBtn:pressed {{ background-color: {c['start_press']}; }}
            QPushButton#resetBtn {{
                background-color: {c['reset_bg']};
                color: {c['reset_color']};
                font-size: 13px;
            }}
            QPushButton#presetBtn {{
                background-color: {c['preset_bg']};
                border: 1px solid {c['preset_border']};
                padding: 6px 4px;
                font-size: 12px;
            }}
            QPushButton#presetBtn:hover {{
                background-color: {c['preset_hover_bg']};
                border-color: {c['preset_hover_bd']};
                color: {c['preset_hover_cl']};
            }}
            QPushButton#pinBtn {{
                background-color: {c['pin_bg']};
                border: 1px solid {c['pin_border']};
                color: {c['pin_color']};
                font-size: 14px;
                padding: 0;
            }}
            QPushButton#pinBtn:checked {{
                background-color: {c['pin_chk_bg']};
                color: white;
                border: 1px solid {c['pin_chk_brd']};
            }}
            QPushButton#pinBtn:hover {{ background-color: {c['pin_hover']}; }}
            QPushButton#pinBtn:checked:hover {{ background-color: {c['pin_chk_hover']}; }}
            QPushButton#closeBtn, QPushButton#winBtn {{
                background-color: transparent;
                border: none;
                color: {c['win_btn_color']};
                font-size: 14px;
                padding: 0;
            }}
            QPushButton#closeBtn:hover {{
                background-color: {c['close_hover_bg']};
                color: white;
                border-radius: 6px;
            }}
            QPushButton#winBtn:hover {{
                background-color: {c['winbtn_hover_bg']};
                border-radius: 6px;
            }}
            QPushButton#previewBtn {{
                background-color: {c['preview_bg']};
                border: 1px solid {c['preview_border']};
                color: {c['preview_color']};
                font-size: 11px;
                padding: 4px 10px;
            }}
            QPushButton#previewBtn:hover {{ background-color: {c['preview_hover']}; }}
            QPushButton#modeBtn {{
                background-color: {c['mode_bg']};
                border: 1px solid {c['mode_border']};
                color: {c['mode_color']};
                font-size: 11px;
                padding: 4px 10px;
                font-weight: bold;
            }}
            QPushButton#modeBtn:checked {{
                background-color: {c['mode_chk_bg']};
                border: 1px solid {c['mode_chk_bd']};
                color: {c['mode_chk_cl']};
            }}
            QPushButton#modeBtn:hover {{ background-color: {c['mode_hover']}; }}
            QComboBox#soundCombo {{
                background-color: {c['combo_bg']};
                border: 1px solid {c['combo_border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                color: {c['btn_color']};
                min-height: 22px;
            }}
            QComboBox#soundCombo:hover {{ border-color: {c['combo_hover_bd']}; }}
            QComboBox#soundCombo::drop-down {{ border: none; width: 18px; }}
            QComboBox#soundCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {c['combo_arrow']};
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['combo_view_bg']};
                border: 1px solid {c['combo_border']};
                color: {c['btn_color']};
                selection-background-color: {c['combo_sel_bg']};
                selection-color: {c['combo_sel_color']};
                outline: none;
                padding: 4px;
            }}
        """


# ======================================================================
# 다크 모드 감지 유틸
# ======================================================================
def is_system_dark() -> bool:
    """QApplication 팔레트의 윈도우 배경 밝기로 다크 여부 판단."""
    app = QApplication.instance()
    if app is None:
        return False
    bg = app.palette().color(QPalette.Window)
    # 밝기(perceived luminance) < 128 이면 다크 모드로 간주
    luminance = 0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()
    return luminance < 128


# ======================================================================
# 알림음 합성 라이브러리
# ======================================================================
class SoundLibrary:
    SAMPLE_RATE = 44100

    def __init__(self):
        self.cache_dir = tempfile.mkdtemp(prefix="timetimer_sounds_")
        self.sounds: dict[str, str] = {}
        self._generate_all()

    def _write_wav(self, samples, name):
        path = os.path.join(self.cache_dir, f"{name}.wav")
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            data = b"".join(
                struct.pack("<h", max(-32767, min(32767, int(s * 32767))))
                for s in samples
            )
            wf.writeframes(data)
        return path

    def _envelope(self, n, attack=0.01, release=0.1):
        a = max(1, int(n * attack))
        r = max(1, int(n * release))
        env = [1.0] * n
        for i in range(min(a, n)):
            env[i] = i / a
        for i in range(min(r, n)):
            idx = n - 1 - i
            if idx >= 0:
                env[idx] = min(env[idx], i / r)
        return env

    def _tone(self, freq, dur, wtype="sine", vol=0.5, atk=0.01, rel=0.15):
        n = int(self.SAMPLE_RATE * dur)
        env = self._envelope(n, atk, rel)
        out = []
        for i in range(n):
            t = i / self.SAMPLE_RATE
            if wtype == "sine":
                s = math.sin(2 * math.pi * freq * t)
            elif wtype == "triangle":
                ph = (freq * t) % 1.0
                s = 4 * abs(ph - 0.5) - 1
            elif wtype == "square":
                s = (1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0) * 0.6
            else:
                s = math.sin(2 * math.pi * freq * t)
            out.append(s * env[i] * vol)
        return out

    def _sil(self, dur):
        return [0.0] * int(self.SAMPLE_RATE * dur)

    def _cat(self, *parts):
        o = []
        for p in parts:
            o.extend(p)
        return o

    def _mix(self, a, b):
        n = min(len(a), len(b))
        return [a[i] + b[i] for i in range(n)]

    def _make_chime(self):
        return self._cat(self._tone(659.25, .4, "sine", .5, .005, .6),
                         self._sil(.05),
                         self._tone(1046.5, .6, "sine", .45, .005, .7))

    def _make_bell(self):
        b  = self._tone(523.25, 1.2, "sine", .40, .002, .95)
        h1 = self._tone(1046.5, 1.2, "sine", .15, .002, .95)
        h2 = self._tone(1568.0, 1.2, "sine", .08, .002, .95)
        return self._mix(self._mix(b, h1), h2)

    def _make_beep(self):
        b = self._tone(880, .12, "square", .4, .002, .05)
        return self._cat(b, self._sil(.08), b, self._sil(.08), b)

    def _make_soft_ding(self):
        return self._cat(self._tone(880,    .35, "sine", .5,  .005, .6),
                         self._tone(698.46, .5,  "sine", .45, .005, .7))

    def _make_alarm(self):
        o = []
        for _ in range(3):
            o += self._tone(1000, .15, "square", .35, .002, .02)
            o += self._sil(.06)
            o += self._tone(800,  .15, "square", .35, .002, .02)
            o += self._sil(.12)
        return o

    def _make_wave(self):
        n = int(self.SAMPLE_RATE * 1.2)
        o = []
        for i in range(n):
            t = i / self.SAMPLE_RATE
            f = 500 + 300 * math.sin(math.pi * t / 1.2)
            s = math.sin(2 * math.pi * f * t)
            o.append(s * math.sin(math.pi * t / 1.2) * 0.45)
        return o

    def _make_triple(self):
        return self._cat(self._tone(523.25, .28, "sine", .45, .005, .5),
                         self._tone(659.25, .28, "sine", .45, .005, .5),
                         self._tone(783.99, .7,  "sine", .5,  .005, .7))

    def _generate_all(self):
        for name, fn in [
            ("부드러운 차임", self._make_chime),
            ("도미솔 상승",   self._make_triple),
            ("종소리",        self._make_bell),
            ("디지털 비프",   self._make_beep),
            ("딩동",          self._make_soft_ding),
            ("알람 시계",     self._make_alarm),
            ("파도 음",       self._make_wave),
            ("무음",          lambda: self._sil(.1)),
        ]:
            try:
                self.sounds[name] = self._write_wav(fn(), name.replace(" ", "_"))
            except Exception as e:
                print(f"[sound] {name}: {e}", file=sys.stderr)

    def names(self):
        return list(self.sounds.keys())

    def path(self, name):
        return self.sounds.get(name)


# ======================================================================
# 타이머 다이얼
# ======================================================================
class TimerDial(QWidget):
    def __init__(self, parent_window=None):
        super().__init__(parent_window)
        self._pw = parent_window            # parent window 참조
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(180, 180)

        # 타이머 상태
        self.max_minutes      = 60          # 60 or 120
        self.total_seconds    = 0
        self.remaining_seconds = 0
        self.is_running       = False
        self.is_dragging      = False
        self.hover_angle      = None
        self._display_seconds = 0.0

        # 테마
        self.theme = Theme(dark=False)

        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(1000)
        self.tick_timer.timeout.connect(self._on_tick)

        self.smooth_timer = QTimer(self)
        self.smooth_timer.setInterval(50)
        self.smooth_timer.timeout.connect(self._smooth_update)
        self.smooth_timer.start()

        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        return QSize(320, 320)

    # ── public API ──────────────────────────────────────────────────────
    def set_theme(self, theme: Theme):
        self.theme = theme
        self.update()

    def set_max_minutes(self, minutes: int):
        """60 또는 120. 현재 남은 시간이 범위 초과하면 클램프."""
        self.max_minutes = minutes
        cap = minutes * 60
        if self.remaining_seconds > cap:
            self.remaining_seconds = cap
            self.total_seconds = cap
            self._display_seconds = float(cap)
        self.update()

    def start(self):
        if self.remaining_seconds <= 0:
            return False
        self.is_running = True
        self.tick_timer.start()
        return True

    def pause(self):
        self.is_running = False
        self.tick_timer.stop()

    def reset(self):
        self.is_running = False
        self.tick_timer.stop()
        self.total_seconds = self.remaining_seconds = 0
        self._display_seconds = 0.0
        self.update()
        if self._pw:
            self._pw.on_timer_state_changed()

    # ── 내부 슬롯 ───────────────────────────────────────────────────────
    def _on_tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.remaining_seconds <= 0:
                self.remaining_seconds = 0
                self.is_running = False
                self.tick_timer.stop()
                if self._pw and hasattr(self._pw, "on_timer_finished"):
                    self._pw.on_timer_finished()
        if self._pw:
            self._pw.on_timer_state_changed()

    def _smooth_update(self):
        target = float(self.remaining_seconds)
        if self.is_running:
            if abs(target - self._display_seconds) < 0.001:
                self._display_seconds = target
            else:
                self._display_seconds = max(target, self._display_seconds - 0.05)
        else:
            self._display_seconds = target
        self.update()

    # ── 마우스 ──────────────────────────────────────────────────────────
    def _angle_from_pos(self, pos):
        cx, cy = self.width() / 2, self.height() / 2
        angle = math.degrees(math.atan2(pos.y() - cy, pos.x() - cx))
        return (angle + 90) % 360

    def _secs_from_angle(self, angle):
        return int(round((angle / 360.0) * self.max_minutes * 60))

    def _inside_dial(self, pos):
        cx, cy = self.width() / 2, self.height() / 2
        r = min(self.width(), self.height()) / 2 - 10
        return (pos.x() - cx) ** 2 + (pos.y() - cy) ** 2 <= r * r

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.is_running:
            if self._inside_dial(event.pos()):
                self.is_dragging = True
                self._set_time_from_pos(event.pos())

    def mouseMoveEvent(self, event):
        if self.is_dragging and not self.is_running:
            self._set_time_from_pos(event.pos())
        elif not self.is_running and self._inside_dial(event.pos()):
            self.hover_angle = self._angle_from_pos(event.pos())
            self.update()
        elif self.hover_angle is not None:
            self.hover_angle = None
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def leaveEvent(self, event):
        self.hover_angle = None
        self.update()

    def _set_time_from_pos(self, pos):
        angle = self._angle_from_pos(pos)
        secs = (self._secs_from_angle(angle) // 5) * 5
        secs = max(0, secs)
        self.total_seconds = self.remaining_seconds = secs
        self._display_seconds = float(secs)
        self.update()
        if self._pw:
            self._pw.on_timer_state_changed()

    # ── 렌더링 ──────────────────────────────────────────────────────────
    def paintEvent(self, event):
        t = self.theme
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        side = min(w, h)
        cx, cy = w / 2, h / 2
        margin = side * 0.04
        radius = side / 2 - margin

        # 비율 기반 수치
        rw   = max(2, side * 0.012)         # ring width
        tll  = side * 0.045                 # tick long length
        tsl  = side * 0.025                 # tick short length
        tlw  = max(2, side * 0.008)         # tick long width
        tsw  = max(1, side * 0.003)         # tick short width
        li   = side * 0.11                  # label inset
        nfx  = max(10, int(side * 0.048))   # number font px
        cfx  = max(14, int(side * 0.10))    # center font px
        cbr  = radius * 0.30                # center bg radius

        # ─ 외곽 후광 ─
        og = QRadialGradient(cx, cy, radius + margin)
        og.setColorAt(0.95, QColor(0, 0, 0, 0))
        og.setColorAt(1.0,  t.dial_outer_shadow)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(og))
        p.drawEllipse(QPointF(cx, cy), radius + margin, radius + margin)

        # ─ 다이얼 배경 ─
        bg = QRadialGradient(cx, cy - radius * 0.3, radius * 1.2)
        bg.setColorAt(0.0, t.dial_bg_inner)
        bg.setColorAt(1.0, t.dial_bg_outer)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bg))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        pie_rect = QRectF(cx - radius + rw, cy - radius + rw,
                          (radius - rw) * 2, (radius - rw) * 2)

        # ─ 호버 미리보기 ─
        if self.hover_angle is not None and not self.is_running and not self.is_dragging:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(Theme.RED_HOVER))
            p.drawPie(pie_rect, 90 * 16, int(-self.hover_angle * 16))

        # ─ 빨간 파이 섹터 ─
        if self._display_seconds > 0:
            fraction = self._display_seconds / (self.max_minutes * 60)
            span_deg = fraction * 360.0
            rg = QRadialGradient(cx, cy, radius)
            rg.setColorAt(0.0, Theme.RED_BRIGHT)
            rg.setColorAt(1.0, Theme.RED_DARK)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(rg))
            p.drawPie(pie_rect, int(90 * 16), int(-span_deg * 16))

        # ─ 테두리 링 ─
        p.setPen(QPen(t.dial_border, rw))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        # ─ 눈금 ─
        # 120분 모드: 눈금 수 = 120 (1분 단위), 5분마다 긴 눈금
        # 60분 모드: 눈금 수 = 60 (1분 단위), 5분마다 긴 눈금
        num_ticks = self.max_minutes
        p.save()
        p.translate(cx, cy)
        for i in range(num_ticks):
            angle_deg = i * (360 / num_ticks)
            p.save()
            p.rotate(angle_deg)
            if i % 5 == 0:
                p.setPen(QPen(t.tick_major, tlw))
                p.drawLine(0, int(-radius + rw), 0, int(-radius + rw + tll))
            else:
                p.setPen(QPen(t.tick_minor, tsw))
                p.drawLine(0, int(-radius + rw), 0, int(-radius + rw + tsl))
            p.restore()
        p.restore()

        # ─ 숫자 라벨 ─
        # 60분: 0 5 10 ... 55  (12개, 30°간격)
        # 120분: 0 10 20 ... 110  (12개, 30°간격)
        step = self.max_minutes // 12  # 5 or 10
        p.save()
        font = QFont("Arial", nfx, QFont.Bold)
        p.setFont(font)
        p.setPen(t.number_color)
        lr = radius - li - tll  # label radius
        for i in range(12):
            minute = i * step
            rad = math.radians(i * 30 - 90)
            lx = cx + lr * math.cos(rad)
            ly = cy + lr * math.sin(rad)
            text = str(minute)
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            p.drawText(int(lx - tw / 2), int(ly + th / 4), text)
        p.restore()

        # ─ 중앙 시간 표시 ─
        p.save()
        shown = int(math.ceil(self._display_seconds)) if self.is_running else self.remaining_seconds
        mins, secs = divmod(shown, 60)

        # 중앙 배경 원
        cg2 = QRadialGradient(cx, cy, cbr)
        cg2.setColorAt(0.0, t.center_bg_inner)
        cg2.setColorAt(1.0, t.center_bg_outer)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(cg2))
        p.drawEllipse(QPointF(cx, cy), cbr, cbr)
        p.setPen(QPen(t.center_border, 1))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), cbr, cbr)

        # 시간 텍스트
        time_text = f"{mins:02d}:{secs:02d}"
        p.setFont(QFont("Arial", cfx, QFont.Bold))
        p.setPen(t.center_time_color)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(time_text)
        th = fm.height()
        p.drawText(int(cx - tw / 2), int(cy + th / 4 - th * 0.05), time_text)

        # 상태 힌트
        if self.is_running:
            status, sc = "실행 중", t.status_running
        elif self.is_dragging:
            status, sc = "설정 중...", t.status_dragging
        elif self.remaining_seconds > 0:
            status, sc = "준비", t.status_ready
        else:
            status, sc = "시간을 설정하세요", t.status_idle

        p.setFont(QFont("Arial", max(8, int(cfx * 0.32))))
        p.setPen(sc)
        fm2 = p.fontMetrics()
        tw2 = fm2.horizontalAdvance(status)
        p.drawText(int(cx - tw2 / 2), int(cy + th * 0.75), status)
        p.restore()

        # ─ 중앙 점 ─
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(t.center_dot))
        p.drawEllipse(QPointF(cx, cy), max(2, side * 0.008), max(2, side * 0.008))


# ======================================================================
# 1:1 비율 유지 래퍼
# ======================================================================
class AspectRatioWidget(QWidget):
    def __init__(self, child, parent=None):
        super().__init__(parent)
        self._child = child
        self._child.setParent(self)
        self.setMinimumSize(180, 180)

    def resizeEvent(self, event):
        side = min(self.width(), self.height())
        x = (self.width()  - side) // 2
        y = (self.height() - side) // 2
        self._child.setGeometry(x, y, side, side)


# ======================================================================
# 메인 윈도우
# ======================================================================
class TimeTimerWindow(QWidget):
    RESIZE_MARGIN = 8

    def __init__(self):
        super().__init__()
        self.always_on_top  = True
        self._drag_pos      = None
        self._resize_edge   = None
        self._resize_start_geo  = None
        self._resize_start_pos  = None

        # 사운드
        self.sound_lib = SoundLibrary()
        self.sound_effect = QSoundEffect()
        self.selected_sound = "부드러운 차임"

        # 테마 (초기 감지)
        self._dark = is_system_dark()
        self.theme = Theme(self._dark)

        self._init_ui()
        self._apply_always_on_top()
        self.resize(400, 600)
        self.setMinimumSize(300, 490)
        self.setWindowTitle("Time Timer")

        # 시스템 테마 폴링 (2초)
        self._theme_poll = QTimer(self)
        self._theme_poll.setInterval(2000)
        self._theme_poll.timeout.connect(self._check_theme)
        self._theme_poll.start()

    # ── UI 구성 ─────────────────────────────────────────────────────────
    def _init_ui(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.container = QFrame(self)
        self.container.setObjectName("container")

        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(24)
        self.shadow_effect.setOffset(0, 4)
        self.container.setGraphicsEffect(self.shadow_effect)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(self.container)

        root = QVBoxLayout(self.container)
        root.setContentsMargins(14, 10, 14, 14)
        root.setSpacing(10)

        # 상단 바
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)
        self.title_label = QLabel("⏱  Time Timer")
        self.title_label.setObjectName("titleLabel")

        self.pin_btn = QPushButton("📌")
        self.pin_btn.setObjectName("pinBtn")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True)
        self.pin_btn.setToolTip("항상 위 고정")
        self.pin_btn.setFixedSize(32, 28)
        self.pin_btn.clicked.connect(self._toggle_always_on_top)
        self.pin_btn.setCursor(Qt.PointingHandCursor)

        min_btn = QPushButton("—")
        min_btn.setObjectName("winBtn")
        min_btn.setFixedSize(28, 28)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setCursor(Qt.PointingHandCursor)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.PointingHandCursor)

        top_bar.addWidget(self.title_label)
        top_bar.addStretch()
        top_bar.addWidget(self.pin_btn)
        top_bar.addWidget(min_btn)
        top_bar.addWidget(close_btn)
        root.addLayout(top_bar)

        # 다이얼
        self.dial = TimerDial(self)
        self.dial_wrapper = AspectRatioWidget(self.dial)
        self.dial_wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.dial_wrapper, 1)

        # 컨트롤
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.start_btn = QPushButton("▶  시작")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self._on_start_pause)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setMinimumHeight(38)

        self.reset_btn = QPushButton("⟲  리셋")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.clicked.connect(self.dial.reset)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setMinimumHeight(38)

        btn_row.addWidget(self.start_btn, 2)
        btn_row.addWidget(self.reset_btn, 1)
        root.addLayout(btn_row)

        # 프리셋
        preset_row = QHBoxLayout()
        preset_row.setSpacing(4)
        for m in [5, 10, 15, 25, 45]:
            b = QPushButton(f"{m}분")
            b.setObjectName("presetBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, v=m: self._set_preset(v))
            preset_row.addWidget(b)
        root.addLayout(preset_row)

        # ─ 120분 모드 토글 ─────────────────────────────────────────────
        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        mode_label = QLabel("⏳ 최대 시간")
        mode_label.setObjectName("modeLabel")

        self.mode_btn = QPushButton("120분 모드  OFF")
        self.mode_btn.setObjectName("modeBtn")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(False)
        self.mode_btn.setCursor(Qt.PointingHandCursor)
        self.mode_btn.clicked.connect(self._toggle_120_mode)

        self.mode_info = QLabel("현재: 최대 60분")
        self.mode_info.setObjectName("soundLabel")

        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.mode_btn)
        mode_row.addStretch()
        mode_row.addWidget(self.mode_info)
        root.addLayout(mode_row)

        # 사운드
        sound_row = QHBoxLayout()
        sound_row.setSpacing(6)
        sound_label = QLabel("🔔 알림음")
        sound_label.setObjectName("soundLabel")
        self.sound_combo = QComboBox()
        self.sound_combo.setObjectName("soundCombo")
        self.sound_combo.addItems(self.sound_lib.names())
        self.sound_combo.setCurrentText(self.selected_sound)
        self.sound_combo.currentTextChanged.connect(lambda n: setattr(self, "selected_sound", n))
        self.sound_combo.setCursor(Qt.PointingHandCursor)

        self.preview_btn = QPushButton("▶ 미리듣기")
        self.preview_btn.setObjectName("previewBtn")
        self.preview_btn.clicked.connect(self._preview_sound)
        self.preview_btn.setCursor(Qt.PointingHandCursor)

        sound_row.addWidget(sound_label)
        sound_row.addWidget(self.sound_combo, 1)
        sound_row.addWidget(self.preview_btn)
        root.addLayout(sound_row)

        # 최초 테마 적용
        self._apply_theme()

    # ── 테마 ────────────────────────────────────────────────────────────
    def _check_theme(self):
        """2초마다 시스템 다크 여부를 확인해서 변경 시 테마를 갱신한다."""
        dark = is_system_dark()
        if dark != self._dark:
            self._dark = dark
            self.theme = Theme(dark)
            self._apply_theme()

    def _apply_theme(self):
        t = self.theme
        # 창 배경 투명 + 그림자 색상
        self.shadow_effect.setColor(t.shadow_color)
        # 컨테이너 QSS
        self.container.setStyleSheet(t.stylesheet())
        # 다이얼에 테마 전달
        self.dial.set_theme(t)

    # ── 120분 모드 ───────────────────────────────────────────────────────
    def _toggle_120_mode(self):
        on = self.mode_btn.isChecked()
        if on:
            self.mode_btn.setText("120분 모드  ON")
            self.mode_info.setText("현재: 최대 120분")
            self.dial.set_max_minutes(120)
        else:
            self.mode_btn.setText("120분 모드  OFF")
            self.mode_info.setText("현재: 최대 60분")
            self.dial.set_max_minutes(60)

    # ── 동작 ────────────────────────────────────────────────────────────
    def _apply_always_on_top(self):
        flags = self.windowFlags()
        if self.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _toggle_always_on_top(self):
        self.always_on_top = self.pin_btn.isChecked()
        self._apply_always_on_top()

    def _on_start_pause(self):
        if self.dial.is_running:
            self.dial.pause()
        else:
            self.dial.start()
        self.on_timer_state_changed()

    def _set_preset(self, minutes):
        if self.dial.is_running:
            return
        cap = self.dial.max_minutes * 60
        secs = min(minutes * 60, cap)
        self.dial.total_seconds = self.dial.remaining_seconds = secs
        self.dial._display_seconds = float(secs)
        self.dial.update()
        self.on_timer_state_changed()

    def _play_sound(self, name):
        path = self.sound_lib.path(name)
        if not path or not os.path.exists(path) or name == "무음":
            return
        self.sound_effect.stop()
        self.sound_effect.setSource(QUrl.fromLocalFile(path))
        self.sound_effect.setVolume(0.8)
        self.sound_effect.play()

    def _preview_sound(self):
        self._play_sound(self.selected_sound)

    def on_timer_state_changed(self):
        self.start_btn.setText("⏸  일시정지" if self.dial.is_running else "▶  시작")

    def on_timer_finished(self):
        self._play_sound(self.selected_sound)
        self.start_btn.setText("▶  시작")

    # ── 프레임리스 이동 + 리사이즈 ──────────────────────────────────────
    def _edge_at(self, pos):
        x, y, w, h, m = pos.x(), pos.y(), self.width(), self.height(), self.RESIZE_MARGIN
        l, r = x <= m, x >= w - m
        t, b = y <= m, y >= h - m
        if r and b: return "br"
        if r and t: return "tr"
        if l and b: return "bl"
        if l and t: return "tl"
        if r: return "r"
        if l: return "l"
        if b: return "b"
        if t: return "t"
        return None

    def _cursor_for_edge(self, edge):
        return {
            "l": Qt.SizeHorCursor,  "r": Qt.SizeHorCursor,
            "t": Qt.SizeVerCursor,  "b": Qt.SizeVerCursor,
            "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
            "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
        }.get(edge, Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        edge = self._edge_at(event.pos())
        if edge:
            self._resize_edge = edge
            self._resize_start_geo = self.geometry()
            self._resize_start_pos = event.globalPos()
            return
        if event.pos().y() < 50:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.NoButton:
            edge = self._edge_at(event.pos())
            self.setCursor(QCursor(self._cursor_for_edge(edge) if edge else Qt.ArrowCursor))
            return
        if self._resize_edge and self._resize_start_geo and self._resize_start_pos:
            d = event.globalPos() - self._resize_start_pos
            g = self._resize_start_geo
            nx, ny, nw, nh = g.x(), g.y(), g.width(), g.height()
            mw, mh = self.minimumWidth(), self.minimumHeight()
            e = self._resize_edge
            if "r" in e:
                nw = max(mw, g.width()  + d.x())
            if "b" in e:
                nh = max(mh, g.height() + d.y())
            if "l" in e:
                nw = max(mw, g.width()  - d.x())
                nx = g.x() + g.width()  - nw
            if "t" in e:
                nh = max(mh, g.height() - d.y())
                ny = g.y() + g.height() - nh
            self.setGeometry(nx, ny, nw, nh)
            return
        if event.buttons() & Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = self._resize_edge = self._resize_start_geo = self._resize_start_pos = None


# ======================================================================
# 진입점
# ======================================================================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Time Timer")
    try:
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    window = TimeTimerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()