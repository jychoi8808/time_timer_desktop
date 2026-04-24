"""
Time Timer (Desktop) — v5
- 미니모드 제어 개선 (클릭 정지/재생, 리사이즈 여백 조절, 일시정지 색상)
- 항상 위(핀) 버튼 미니모드 유지
- 무음 모드 (종료 시 화면 깜빡임)
"""

import sys, math, struct, wave, os, tempfile

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QComboBox, QSizePolicy, QGraphicsDropShadowEffect,
    QStackedWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, QSize, QUrl, QEvent
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontDatabase,
    QCursor, QPalette, QPainterPath
)
from PyQt5.QtMultimedia import QSoundEffect


# ══════════════════════════════════════════════════════════════════════
# 폰트 유틸
# ══════════════════════════════════════════════════════════════════════
def get_font(size: int, weight=QFont.Normal) -> QFont:
    try:
        installed = set(QFontDatabase().families())
    except Exception:
        try:
            installed = set(QFontDatabase.families())
        except Exception:
            installed = set()

    for family in ("Pretendard", "Apple SD Gothic Neo", "Malgun Gothic",
                   "Noto Sans KR", "Arial"):
        if family in installed:
            return QFont(family, size, weight)
    return QFont("Arial", size, weight)


# ══════════════════════════════════════════════════════════════════════
# 테마
# ══════════════════════════════════════════════════════════════════════
ACCENT          = "#f05650"
ACCENT_HOVER    = "#f37370"
ACCENT_PRESS    = "#c94440"

class Theme:
    RED         = QColor(0xf0, 0x56, 0x50)
    RED_LIGHT   = QColor(0xf0, 0x56, 0x50, 45)
    RED_HAND    = QColor(0xf0, 0x56, 0x50)

    def __init__(self, dark: bool):
        self.dark = dark
        if dark:
            self.bg                = QColor(28, 28, 30)
            self.surface           = QColor(36, 36, 40)
            self.surface_border    = QColor(55, 55, 60)
            self.shadow            = QColor(0, 0, 0, 130)

            self.dial_face         = QColor(44, 44, 48)
            self.dial_ring         = QColor(65, 65, 72)
            self.dial_track        = QColor(55, 55, 62)
            self.tick_major        = QColor(160, 160, 168)
            self.tick_minor        = QColor(80, 80, 90)
            self.number_col        = QColor(160, 160, 168)

            self.time_col          = QColor(0xD0, 0xD0, 0xD8)
            self.status_col        = QColor(110, 110, 120)  # 회색
            self.hand_dot          = QColor(65, 65, 72)

            self.title_hex         = "#c8c8d0"
            self.subtitle_hex      = "#88888e"
            self.btn_bg            = "#2c2c32"
            self.btn_border        = "#46464e"
            self.btn_fg            = "#d0d0d8"
            self.btn_hover         = "#38383e"
            self.btn_press         = "#202026"
            self.input_bg          = "#26262c"
            self.input_border      = "#42424a"
            self.sep_col           = "#3a3a42"
            self.toggle_off_bg     = "#3a3a42"
            self.toggle_off_knob   = "#888890"
        else:
            self.bg                = QColor(245, 245, 247)
            self.surface           = QColor(252, 252, 254)
            self.surface_border    = QColor(218, 218, 224)
            self.shadow            = QColor(0, 0, 0, 70)

            self.dial_face         = QColor(255, 255, 255)
            self.dial_ring         = QColor(215, 215, 222)
            self.dial_track        = QColor(240, 240, 244)
            self.tick_major        = QColor(160, 160, 170)
            self.tick_minor        = QColor(200, 200, 208)
            self.number_col        = QColor(140, 140, 150)

            self.time_col          = QColor(0x20, 0x21, 0x23)
            self.status_col        = QColor(170, 170, 178) # 회색
            self.hand_dot          = QColor(215, 215, 222)

            self.title_hex         = "#202123"
            self.subtitle_hex      = "#888892"
            self.btn_bg            = "#ffffff"
            self.btn_border        = "#e0e0e6"
            self.btn_fg            = "#202123"
            self.btn_hover         = "#f4f4f8"
            self.btn_press         = "#e8e8ee"
            self.input_bg          = "#ffffff"
            self.input_border      = "#dcdce2"
            self.sep_col           = "#e8e8ee"
            self.toggle_off_bg     = "#d8d8de"
            self.toggle_off_knob   = "#ffffff"

    def qss(self) -> str:
        d = self.dark
        surface     = "#242428" if d else "#fcfcfe"
        border      = "#363640" if d else "#dadae0"
        title       = self.title_hex
        sub         = self.subtitle_hex
        btn_bg      = self.btn_bg
        btn_bd      = self.btn_border
        btn_fg      = self.btn_fg
        btn_hv      = self.btn_hover
        btn_pr      = self.btn_press
        inp_bg      = self.input_bg
        inp_bd      = self.input_border
        sep         = self.sep_col
        arr_col     = "#aaaaaa" if d else "#888892"
        combo_vw    = "#26262c" if d else "#ffffff"
        combo_sel   = "#3a1010" if d else "#fde8e8"
        combo_selc  = "#f87171" if d else ACCENT

        return f"""
        QFrame#surface {{
            background:{surface}; border:1px solid {border};
            border-radius:20px;
        }}
        QLabel {{ background:transparent; }}
        QLabel#title {{ color:{title}; font-size:13px; font-weight:600; }}
        QLabel#subtitle {{ color:{sub}; font-size:11px; }}
        QLabel#settingGroup {{ color:{sub}; font-size:10px; font-weight:600; letter-spacing:0.5px; }}
        QLabel#settingLabel {{ color:{btn_fg}; font-size:12px; }}
        QLabel#settingDesc {{ color:{sub}; font-size:10px; }}
        QPushButton {{ background:{btn_bg}; border:1px solid {btn_bd}; border-radius:8px; padding:6px 14px; font-size:12px; color:{btn_fg}; }}
        QPushButton:hover  {{ background:{btn_hv}; }}
        QPushButton:pressed {{ background:{btn_pr}; }}
        QPushButton#startBtn {{ background:{ACCENT}; border:none; color:white; font-size:14px; font-weight:700; border-radius:10px; }}
        QPushButton#startBtn:hover  {{ background:{ACCENT_HOVER}; }}
        QPushButton#startBtn:pressed {{ background:{ACCENT_PRESS}; }}
        QPushButton#iconBtn {{ background:transparent; border:none; color:{sub}; font-size:16px; padding:0; }}
        QPushButton#iconBtn:hover {{ color:{btn_fg}; }}
        QPushButton#pinBtn {{ background:transparent; border:none; font-size:18px; padding:0; opacity: 0.4; }}
        QPushButton#pinBtn:checked {{ opacity: 1.0; }}
        QPushButton#pinBtn:hover {{ background: {btn_hv}; border-radius: 8px; }}
        QPushButton#emojiBtn {{ background:{btn_bg}; border:1px solid {btn_bd}; border-radius:26px; padding:0; font-size:22px; }}
        QPushButton#emojiBtn:hover  {{ background:{btn_hv}; border-color:{btn_fg}; }}
        QPushButton#emojiBtn:pressed {{ background:{btn_pr}; }}
        QPushButton#settingsBtn {{ background:transparent; border:none; font-size:18px; padding:0; color:{sub}; }}
        QPushButton#settingsBtn:hover {{ color:{btn_fg}; }}
        QPushButton#backBtn {{ background:{btn_bg}; border:1px solid {btn_bd}; border-radius:8px; padding:5px 12px; font-size:12px; color:{btn_fg}; }}
        QPushButton#backBtn:hover {{ background:{btn_hv}; }}
        QFrame#separator {{ background:{sep}; border:none; }}
        QComboBox {{ background:{inp_bg}; border:1px solid {inp_bd}; border-radius:7px; padding:5px 10px; font-size:12px; color:{btn_fg}; min-height:26px; }}
        QComboBox:hover {{ border-color:{arr_col}; }}
        QComboBox::drop-down {{ border:none; width:20px; }}
        QComboBox::down-arrow {{ image:none; border-left:4px solid transparent; border-right:4px solid transparent; border-top:5px solid {arr_col}; margin-right:6px; }}
        QComboBox QAbstractItemView {{ background:{combo_vw}; border:1px solid {inp_bd}; color:{btn_fg}; selection-background-color:{combo_sel}; selection-color:{combo_selc}; outline:none; padding:4px; }}
        QScrollArea {{ background:transparent; border:none; }}
        QScrollBar:vertical {{ background:transparent; width:4px; margin:0; }}
        QScrollBar::handle:vertical {{ background:{btn_bd}; border-radius:2px; min-height:20px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        QSlider#opacitySlider::groove:horizontal {{ height:4px; background:{btn_bd}; border-radius:2px; }}
        QSlider#opacitySlider::handle:horizontal {{ width:16px; height:16px; margin:-6px 0; background:{ACCENT}; border-radius:8px; }}
        QSlider#opacitySlider::sub-page:horizontal {{ background:{ACCENT}; border-radius:2px; }}
        """

def is_dark() -> bool:
    app = QApplication.instance()
    if not app: return False
    bg = app.palette().color(QPalette.Window)
    return (0.299*bg.red() + 0.587*bg.green() + 0.114*bg.blue()) < 128


class SoundLibrary:
    SR = 44100
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="timetimer_")
        self.sounds: dict[str, str] = {}
        self._build()
    def _wav(self, samples, name):
        path = os.path.join(self.dir, f"{name}.wav")
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(self.SR)
            wf.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(s*32767)))) for s in samples))
        return path
    def _env(self, n, atk=0.01, rel=0.12):
        a, r = max(1, int(n*atk)), max(1, int(n*rel))
        e = [1.0]*n
        for i in range(min(a,n)): e[i] = i/a
        for i in range(min(r,n)):
            idx = n-1-i
            if idx >= 0: e[idx] = min(e[idx], i/r)
        return e
    def _tone(self, f, d, wt="sine", v=0.5, a=0.01, r=0.15):
        n = int(self.SR*d); env = self._env(n,a,r); out=[]
        for i in range(n):
            t = i/self.SR
            if wt=="sine":     s = math.sin(2*math.pi*f*t)
            elif wt=="tri":    ph=(f*t)%1; s=4*abs(ph-0.5)-1
            elif wt=="square": s=(1.0 if math.sin(2*math.pi*f*t)>=0 else -1.0)*0.6
            else:              s = math.sin(2*math.pi*f*t)
            out.append(s*env[i]*v)
        return out
    def _sil(self, d): return [0.0]*int(self.SR*d)
    def _cat(self,*p):
        o=[]
        for x in p: o.extend(x)
        return o
    def _mix(self,a,b): n=min(len(a),len(b)); return [a[i]+b[i] for i in range(n)]

    def _chime(self): return self._cat(self._tone(659.25,.4,"sine",.5,.005,.6), self._sil(.05),self._tone(1046.5,.6,"sine",.45,.005,.7))
    def _bell(self):
        b=self._tone(523.25,1.2,"sine",.4,.002,.95)
        return self._mix(self._mix(b,self._tone(1046.5,1.2,"sine",.15,.002,.95)), self._tone(1568,1.2,"sine",.08,.002,.95))
    def _beep(self):
        b=self._tone(880,.12,"square",.4,.002,.05); s=self._sil(.08)
        return self._cat(b,s,b,s,b)
    def _ding(self): return self._cat(self._tone(880,.35,"sine",.5,.005,.6), self._tone(698.46,.5,"sine",.45,.005,.7))
    def _alarm(self):
        o=[]
        for _ in range(3): o+=self._tone(1000,.15,"square",.35,.002,.02)+self._sil(.06)+self._tone(800,.15,"square",.35,.002,.02)+self._sil(.12)
        return o
    def _wave(self):
        n=int(self.SR*1.2); o=[]
        for i in range(n):
            t=i/self.SR; f=500+300*math.sin(math.pi*t/1.2)
            o.append(math.sin(2*math.pi*f*t)*math.sin(math.pi*t/1.2)*0.45)
        return o
    def _triple(self): return self._cat(self._tone(523.25,.28,"sine",.45,.005,.5), self._tone(659.25,.28,"sine",.45,.005,.5), self._tone(783.99,.7,"sine",.5,.005,.7))
    def _build(self):
        for name,fn in [("부드러운 차임",self._chime),("도미솔 상승",self._triple), ("종소리",self._bell),("디지털 비프",self._beep),
                        ("딩동",self._ding),("알람 시계",self._alarm),("파도 음",self._wave)]:
            try: self.sounds[name]=self._wav(fn(),name.replace(" ","_"))
            except Exception as e: print(f"[snd]{name}:{e}",file=sys.stderr)
    def names(self): return list(self.sounds.keys())
    def path(self, name): return self.sounds.get(name)


class ToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)
    def isChecked(self): return self._checked
    def setChecked(self, v: bool):
        self._checked = v; self.update()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.update()
            if hasattr(self, "toggled"): self.toggled(self._checked)
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height(); r = h/2
        track_col = QColor(ACCENT) if self._checked else QColor(self.parent().theme.toggle_off_bg if self.parent() and hasattr(self.parent(),'theme') else "#d8d8de")
        p.setPen(Qt.NoPen); p.setBrush(QBrush(track_col))
        p.drawRoundedRect(QRectF(0,0,w,h), r, r)
        margin = 3; knob_x = (w - h + margin) if self._checked else margin
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(knob_x + r - margin, r), r-margin, r-margin)


class TimerDial(QWidget):
    def __init__(self, pw=None):
        super().__init__(pw)
        self._pw = pw
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(50, 50)
        self.max_minutes = 60
        self.total_seconds = 0
        self.remaining_seconds= 0
        self.is_running = False
        self.is_dragging = False
        self.hover_angle = None
        self._disp = 0.0
        self.theme = Theme(False)
        self.is_minimal = False

        self.tick_tmr = QTimer(self); self.tick_tmr.setInterval(1000)
        self.tick_tmr.timeout.connect(self._tick)
        self.smooth_tmr = QTimer(self); self.smooth_tmr.setInterval(40)
        self.smooth_tmr.timeout.connect(self._smooth); self.smooth_tmr.start()
        self.setMouseTracking(True); self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self): return QSize(340, 340)
    def set_theme(self, t): self.theme = t; self.update()
    def set_minimal(self, val):
        if self.is_minimal != val:
            self.is_minimal = val
            self.update()
    def set_max_minutes(self, m):
        self.max_minutes = m
        cap = m * 60
        if self.remaining_seconds > cap:
            self.remaining_seconds = self.total_seconds = cap
            self._disp = float(cap)
        self.update()
    def start(self):
        if self.remaining_seconds <= 0: return False
        self.is_running = True; self.tick_tmr.start(); self.update(); return True
    def pause(self):
        self.is_running = False; self.tick_tmr.stop(); self.update()
    def reset(self):
        self.is_running = False; self.tick_tmr.stop()
        self.total_seconds = self.remaining_seconds = 0; self._disp = 0.0
        self.update()
        if self._pw: self._pw.on_state_changed()

    def _tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.remaining_seconds == 0:
                self.is_running = False; self.tick_tmr.stop()
                if self._pw: self._pw.on_finished()
        if self._pw: self._pw.on_state_changed()

    def _smooth(self):
        target = float(self.remaining_seconds)
        if self.is_running: self._disp = max(target, self._disp - 1/25)
        else: self._disp = target
        self.update()

    def _angle(self, pos):
        cx, cy = self.width()/2, self.height()/2
        a = math.degrees(math.atan2(pos.y()-cy, pos.x()-cx))
        return (a + 90) % 360

    def _secs(self, angle): return int(round(angle/360 * self.max_minutes * 60))
    def _in_dial(self, pos):
        cx, cy = self.width()/2, self.height()/2
        r_sq = (pos.x()-cx)**2 + (pos.y()-cy)**2
        side = min(self.width(), self.height())
        
        if self.is_minimal:
            # ✨ 미니모드: 외부 반지름과 내부 반지름 사이(도넛 링)만 인식
            outer_r = side * 0.5
            inner_r = side * 0.28
            return (inner_r**2 <= r_sq <= outer_r**2)
        else:
            # 일반모드: 다이얼 전체 인식
            r = side / 2 * 0.839
            return r_sq <= r**2

    def mousePressEvent(self, e):
        # ✨ 기존의 if self.is_minimal: e.ignore() 부분을 삭제했습니다.
        # 이제 미니모드에서도 _in_dial(링 영역) 조건을 만족하면 시간 조절이 가능합니다.
        if e.button()==Qt.LeftButton and not self.is_running and self._in_dial(e.pos()):
            self.is_dragging = True
            self._apply(e.pos())
        else:
            e.ignore() # 도넛 중앙이나 바깥을 누르면 창 끄집기/일시정지로 양보

    def mouseMoveEvent(self, e):
        if self.is_dragging and not self.is_running: self._apply(e.pos())
        elif not self.is_running and self._in_dial(e.pos()): self.hover_angle = self._angle(e.pos()); self.update()
        elif self.hover_angle is not None: self.hover_angle = None; self.update()

    def mouseReleaseEvent(self, e):
        if e.button()==Qt.LeftButton: self.is_dragging = False

    def leaveEvent(self, _):
        self.hover_angle = None; self.update()

    def _apply(self, pos):
        raw = self._secs(self._angle(pos))
        s = (raw // 60) * 60
        self.total_seconds = self.remaining_seconds = max(0, s)
        self._disp = float(self.remaining_seconds)
        self.update()
        if self._pw: self._pw.on_state_changed()

    def paintEvent(self, _):
        t = self.theme
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()
        side = min(W, H)
        cx, cy = W/2, H/2

        nfx       = max(8, int(side * 0.038))
        cfx       = max(11, int(side * 0.082))
        label_margin = nfx * 1.4
        tick_gap     = nfx * 1.0
        num_gap      = nfx * 2.2

        total_r   = side * 0.500 - label_margin
        num_r     = total_r
        face_r    = total_r - num_gap
        ring_r    = face_r
        ring_w    = max(1.0, side * 0.004)

        tick_outer = total_r - tick_gap
        tick_long  = max(2, side * 0.022)
        tick_short = max(1, side * 0.012)
        tick_lw    = max(1.0, side * 0.004)
        tick_sw    = max(0.5, side * 0.002)

        center_r  = max(cfx * 1.4, side * 0.130)
        
        if self.is_minimal:
            face_r = side * 0.49
            center_r = side * 0.28

        # 0: 페이스 배경
        p.setPen(Qt.NoPen); p.setBrush(QBrush(t.dial_face))
        p.drawEllipse(QPointF(cx, cy), side * 0.500, side * 0.500)

        # 1: 호버
        if self.hover_angle is not None and not self.is_running and not self.is_dragging:
            p.setPen(Qt.NoPen); p.setBrush(QBrush(Theme.RED_LIGHT))
            rect = QRectF(cx-face_r, cy-face_r, face_r*2, face_r*2)
            p.drawPie(rect, int(90*16), int(-self.hover_angle*16))

        # 2: 빨간(또는 회색) 파이 섹터
        if self._disp > 0:
            frac = self._disp / (self.max_minutes * 60)
            span = frac * 360.0
            p.setPen(Qt.NoPen)
            # ✨ 미니모드이면서 정지상태일 때 회색으로 표시
            if self.is_minimal and not self.is_running:
                p.setBrush(QBrush(t.status_col))
            else:
                p.setBrush(QBrush(Theme.RED))
            rect = QRectF(cx-face_r, cy-face_r, face_r*2, face_r*2)
            p.drawPie(rect, int(90*16), int(-span*16))

        # 3, 4, 5, 6: 눈금, 테두리, 핸드 (미니모드에서는 생략)
        if not self.is_minimal:
            p.setPen(QPen(t.dial_ring, ring_w)); p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

            num_ticks = self.max_minutes
            p.save(); p.translate(cx, cy)
            for i in range(num_ticks):
                ang = i * 360.0 / num_ticks
                p.save(); p.rotate(ang)
                major = (i % 5 == 0)
                y_out = -tick_outer
                y_in  = -(tick_outer - (tick_long if major else tick_short))
                p.setPen(QPen(t.tick_major if major else t.tick_minor, tick_lw if major else tick_sw, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(0, y_in), QPointF(0, y_out))
                p.restore()
            p.restore()

            step = self.max_minutes // 12
            p.save(); p.setFont(get_font(nfx, QFont.DemiBold)); p.setPen(t.number_col)
            fm = p.fontMetrics()
            for i in range(12):
                minute = i * step
                rad = math.radians(i * 30 - 90)
                lx = cx + num_r * math.cos(rad); ly = cy + num_r * math.sin(rad)
                text = str(minute); tw = fm.horizontalAdvance(text); th = fm.height()
                p.drawText(int(lx - tw/2), int(ly + th/3), text)
            p.restore()

            if self._disp > 0:
                frac = self._disp / (self.max_minutes * 60)
                hand_rad = math.radians(frac * 360 - 90)
                hx = cx + face_r * math.cos(hand_rad); hy = cy + face_r * math.sin(hand_rad)
                p.setPen(QPen(Theme.RED_HAND, max(1.5, side * 0.006), Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(cx, cy), QPointF(hx, hy))

        # 7: 중앙 원
        p.setPen(Qt.NoPen); p.setBrush(QBrush(t.dial_face))
        p.drawEllipse(QPointF(cx, cy), center_r, center_r)

        # 8: 시간 텍스트 (미니모드에서도 렌더링, 크기 조절)
        p.save()
        shown = int(math.ceil(self._disp)) if self.is_running else self.remaining_seconds
        mins, secs = divmod(shown, 60)
        time_txt = f"{mins:02d}:00" if self.is_dragging else f"{mins:02d}:{secs:02d}"
        
        current_cfx = max(14, int(side * 0.13)) if self.is_minimal else cfx
        p.setFont(get_font(current_cfx, QFont.Bold))
        
        p.setPen(t.time_col)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(time_txt); th = fm.height()
        p.drawText(int(cx - tw/2), int(cy + th/3), time_txt)
        p.restore()


class AspectBox(QWidget):
    def __init__(self, child, parent=None):
        super().__init__(parent)
        self._c = child; child.setParent(self)
        self.setMinimumSize(50,50)
    def resizeEvent(self, _):
        s = min(self.width(), self.height())
        self._c.setGeometry((self.width()-s)//2,(self.height()-s)//2,s,s)


class SettingsPage(QWidget):
    def __init__(self, parent=None): super().__init__(parent)
    def build(self, sound_lib, theme, sound_enabled, silent_mode, sound_name, mode_120, opacity):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            QWidget().setLayout(old)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16); root.setSpacing(0)

        def sep(): f = QFrame(); f.setObjectName("separator"); f.setFixedHeight(1); return f
        def group_label(text): lb = QLabel(text.upper()); lb.setObjectName("settingGroup"); return lb
        def row_label(title, desc=None):
            col = QVBoxLayout(); col.setSpacing(1)
            tl = QLabel(title); tl.setObjectName("settingLabel"); col.addWidget(tl)
            if desc: dl = QLabel(desc); dl.setObjectName("settingDesc"); col.addWidget(dl)
            return col

        root.addWidget(group_label("알림음"))
        root.addSpacing(8)

        r1 = QHBoxLayout(); r1.setSpacing(10)
        r1.addLayout(row_label("알림음 사용", "타이머 종료 시 소리 재생"))
        r1.addStretch()
        self.sound_toggle = ToggleSwitch(self)
        self.sound_toggle.setChecked(sound_enabled)
        r1.addWidget(self.sound_toggle)
        root.addLayout(r1)
        root.addSpacing(12)

        # ✨ 무음 모드 (화면 깜빡임) 추가
        r_silent = QHBoxLayout(); r_silent.setSpacing(10)
        r_silent.addLayout(row_label("무음 모드", "종료 시 소리 대신 화면 깜빡임"))
        r_silent.addStretch()
        self.silent_toggle = ToggleSwitch(self)
        self.silent_toggle.setChecked(silent_mode)
        r_silent.addWidget(self.silent_toggle)
        root.addLayout(r_silent)
        root.addSpacing(12)
        root.addWidget(sep())
        root.addSpacing(12)

        r2 = QVBoxLayout(); r2.setSpacing(6)
        r2.addLayout(row_label("알림음 종류"))
        h2 = QHBoxLayout(); h2.setSpacing(8)
        self.sound_combo = QComboBox()
        self.sound_combo.setObjectName("soundCombo")
        self.sound_combo.addItems(sound_lib.names())
        if sound_name in sound_lib.names(): self.sound_combo.setCurrentText(sound_name)
        h2.addWidget(self.sound_combo, 1)
        self.preview_btn = QPushButton("▶ 미리듣기"); self.preview_btn.setObjectName("backBtn")
        self.preview_btn.setCursor(Qt.PointingHandCursor); self.preview_btn.setFixedWidth(84)
        h2.addWidget(self.preview_btn)
        r2.addLayout(h2)
        root.addLayout(r2)
        root.addSpacing(20)

        root.addWidget(group_label("타이머"))
        root.addSpacing(8)

        r3 = QHBoxLayout(); r3.setSpacing(10)
        r3.addLayout(row_label("120분 모드", "다이얼 최대 시간을 120분으로 설정"))
        r3.addStretch()
        self.mode_toggle = ToggleSwitch(self)
        self.mode_toggle.setChecked(mode_120)
        r3.addWidget(self.mode_toggle)
        root.addLayout(r3)
        root.addSpacing(20)

        root.addWidget(group_label("화면"))
        root.addSpacing(8)

        r4 = QVBoxLayout(); r4.setSpacing(6)
        opacity_pct = int(opacity * 100)
        r4.addLayout(row_label("창 투명도", f"현재: {opacity_pct}%"))
        from PyQt5.QtWidgets import QSlider
        self.opacity_label = None
        for i in range(r4.count()):
            item = r4.itemAt(i)
            if item and item.layout():
                lay = item.layout()
                for j in range(lay.count()):
                    w = lay.itemAt(j).widget() if lay.itemAt(j) else None
                    if w and w.objectName() == "settingDesc": self.opacity_label = w

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setObjectName("opacitySlider")
        self.opacity_slider.setRange(20, 100); self.opacity_slider.setValue(opacity_pct); self.opacity_slider.setFixedHeight(28)
        r4.addWidget(self.opacity_slider)
        root.addLayout(r4)
        root.addStretch()


class TimeTimerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.always_on_top = True
        self._drag_pos = self._resize_edge = None
        self._resize_start_geo = self._resize_start_pos = self._mouse_press_pos = None

        self.sound_lib     = SoundLibrary()
        self.sound_fx      = QSoundEffect()
        self.sound_enabled = True
        self.silent_mode   = False  # ✨ 무음 모드
        self.selected_snd  = "부드러운 차임"
        self.mode_120      = False

        self._dark  = is_dark()
        self.theme  = Theme(self._dark)

        self.NORMAL_MIN_WIDTH = 200
        self.NORMAL_MIN_HEIGHT = 250
        self._is_minimal_ui = False

        self._build_ui()
        self._apply_theme()
        self._apply_aot()
        
        self.setMinimumSize(100, 100)
        self.resize(420, 620)
        self.setWindowTitle("Time Timer")
        self._opacity = 1.0
        self._update_btn_sizes()

        self._poll = QTimer(self); self._poll.setInterval(2000)
        self._poll.timeout.connect(self._check_theme); self._poll.start()

    def _build_ui(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.surface = QFrame(self); self.surface.setObjectName("surface")
        self.shadow  = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(28); self.shadow.setOffset(0,5)
        self.surface.setGraphicsEffect(self.shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14,14,14,14)
        outer.addWidget(self.surface)

        self.stack = QStackedWidget()
        sf_lay = QVBoxLayout(self.surface)
        sf_lay.setContentsMargins(0,0,0,0); sf_lay.setSpacing(0)
        sf_lay.addWidget(self.stack)

        self.main_page = QWidget()
        mp = QVBoxLayout(self.main_page)
        mp.setContentsMargins(18,14,18,16); mp.setSpacing(0)

        self.top_widget = QWidget()
        top = QHBoxLayout(self.top_widget)
        top.setContentsMargins(0, 0, 0, 10); top.setSpacing(8)

        self.pin_btn = QPushButton("📌")
        self.pin_btn.setObjectName("pinBtn")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True)
        self.pin_btn.setFixedSize(32, 32)
        self.pin_btn.setToolTip("항상 위 고정")
        self.pin_btn.setCursor(Qt.PointingHandCursor)
        self.pin_btn.clicked.connect(self._toggle_aot)

        top.addWidget(self.pin_btn)
        top.addStretch()

        self.settings_btn = QPushButton("⚙"); self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedSize(32,32); self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self._open_settings)

        min_btn = QPushButton("—"); min_btn.setObjectName("iconBtn")
        min_btn.setFixedSize(28,28); min_btn.clicked.connect(self.showMinimized); min_btn.setCursor(Qt.PointingHandCursor)

        close_btn = QPushButton("✕"); close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28,28); close_btn.clicked.connect(self.close); close_btn.setCursor(Qt.PointingHandCursor)

        top.addWidget(self.settings_btn); top.addWidget(min_btn); top.addWidget(close_btn)
        mp.addWidget(self.top_widget)

        self.dial = TimerDial(self)
        self.dial_box = AspectBox(self.dial)
        self.dial_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mp.addWidget(self.dial_box, 1)

        self.bottom_widget = QWidget()
        btn_row = QHBoxLayout(self.bottom_widget)
        btn_row.setContentsMargins(0, 16, 0, 8); btn_row.setSpacing(14); btn_row.addStretch()

        self.reset_icon = QPushButton("🔄"); self.reset_icon.setObjectName("emojiBtn")
        self.reset_icon.setCursor(Qt.PointingHandCursor); self.reset_icon.clicked.connect(self.dial.reset)

        self.start_icon = QPushButton("▶️"); self.start_icon.setObjectName("emojiBtn")
        self.start_icon.setCursor(Qt.PointingHandCursor); self.start_icon.clicked.connect(self._on_start_pause)

        btn_row.addWidget(self.reset_icon); btn_row.addSpacing(4); btn_row.addWidget(self.start_icon); btn_row.addStretch()
        mp.addWidget(self.bottom_widget)
        self.stack.addWidget(self.main_page)

        # ✨ 미니모드용 핀(항상 위) 오버레이 버튼
        self.mini_pin_btn = QPushButton("📌", self.surface)
        self.mini_pin_btn.setObjectName("pinBtn")
        self.mini_pin_btn.setCheckable(True)
        self.mini_pin_btn.setChecked(True)
        self.mini_pin_btn.setFixedSize(26, 26)
        self.mini_pin_btn.setCursor(Qt.PointingHandCursor)
        self.mini_pin_btn.move(14, 14) # 좌측 상단 마진
        self.mini_pin_btn.hide()
        self.mini_pin_btn.clicked.connect(self._toggle_aot)

        self.settings_page = QWidget()
        sp_outer = QVBoxLayout(self.settings_page)
        sp_outer.setContentsMargins(0,0,0,0); sp_outer.setSpacing(0)

        hdr = QHBoxLayout(); hdr.setContentsMargins(18,14,18,12); hdr.setSpacing(8)
        back_btn = QPushButton("← 뒤로"); back_btn.setObjectName("backBtn")
        back_btn.setCursor(Qt.PointingHandCursor); back_btn.clicked.connect(self._close_settings)
        title_lbl = QLabel("설정"); title_lbl.setObjectName("title")
        hdr.addWidget(back_btn); hdr.addStretch(); hdr.addWidget(title_lbl); hdr.addStretch()
        sp_outer.addLayout(hdr)

        sep_frame = QFrame(); sep_frame.setObjectName("separator")
        sep_frame.setFixedHeight(1); sp_outer.addWidget(sep_frame)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_inner = SettingsPage()
        scroll.setWidget(self.settings_inner)
        sp_outer.addWidget(scroll, 1)
        self.stack.addWidget(self.settings_page)

        self.surface.installEventFilter(self); self.stack.installEventFilter(self); self.main_page.installEventFilter(self)
        self.setMouseTracking(True); self.surface.setMouseTracking(True); self.stack.setMouseTracking(True)
        self.main_page.setMouseTracking(True); self.settings_page.setMouseTracking(True)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            gpos = event.globalPos()
            lpos = self.mapFromGlobal(gpos)
            edge = self._edge(lpos)
            if edge:
                self._resize_edge = edge
                self._resize_start_geo = self.geometry()
                self._resize_start_pos = gpos
                return True
            if lpos.y() < 50 or getattr(self, '_is_minimal_ui', False):
                self._drag_pos = gpos - self.frameGeometry().topLeft()
                self._mouse_press_pos = gpos # ✨ 클릭 구분을 위해 위치 저장
                return True
                
        elif event.type() == QEvent.MouseMove:
            gpos = event.globalPos()
            lpos = self.mapFromGlobal(gpos)
            if event.buttons() == Qt.NoButton:
                edge = self._edge(lpos)
                if edge: self.setCursor(QCursor(self._CUR.get(edge, Qt.ArrowCursor)))
                else: self.unsetCursor()
                return False
            if self._resize_edge and self._resize_start_geo and self._resize_start_pos:
                d = gpos - self._resize_start_pos
                g = self._resize_start_geo
                nx, ny, nw, nh = g.x(), g.y(), g.width(), g.height()
                mw, mh = self.minimumWidth(), self.minimumHeight()
                ed = self._resize_edge
                if "r" in ed: nw = max(mw, g.width() + d.x())
                if "b" in ed: nh = max(mh, g.height() + d.y())
                if "l" in ed: nw = max(mw, g.width() - d.x()); nx = g.x() + g.width() - nw
                if "t" in ed: nh = max(mh, g.height() - d.y()); ny = g.y() + g.height() - nh
                self.setGeometry(nx, ny, nw, nh)
                return True
            if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
                self.move(gpos - self._drag_pos)
                return True
                
        elif event.type() == QEvent.MouseButtonRelease:
            # ✨ 미니모드에서 움직임이 거의 없었으면 클릭(일시정지/재생)으로 간주
            if getattr(self, '_is_minimal_ui', False) and getattr(self, '_mouse_press_pos', None):
                dist = (event.globalPos() - self._mouse_press_pos).manhattanLength()
                if dist < 5: 
                    self._on_start_pause()

            self._drag_pos = self._resize_edge = None
            self._resize_start_geo = self._resize_start_pos = self._mouse_press_pos = None
        return super().eventFilter(obj, event)

    def _check_theme(self):
        d = is_dark()
        if d != self._dark:
            self._dark = d; self.theme = Theme(d); self._apply_theme()

    def _apply_theme(self):
        t = self.theme
        self.shadow.setColor(t.shadow)
        self.surface.setStyleSheet(t.qss())
        self.dial.set_theme(t)
        for sw in (getattr(self.settings_inner,'sound_toggle',None),
                   getattr(self.settings_inner,'silent_toggle',None),
                   getattr(self.settings_inner,'mode_toggle',None)):
            if sw: sw.update()

    def _open_settings(self):
        self.settings_inner.build(
            self.sound_lib, self.theme,
            self.sound_enabled, self.silent_mode, self.selected_snd, self.mode_120,
            self._opacity
        )
        self.surface.setStyleSheet(self.theme.qss())
        self.settings_inner.preview_btn.clicked.connect(self._preview)
        self.settings_inner.sound_toggle.toggled = self._on_sound_toggle
        self.settings_inner.silent_toggle.toggled = self._on_silent_toggle
        self.settings_inner.mode_toggle.toggled  = self._on_mode_toggle
        self.settings_inner.sound_combo.currentTextChanged.connect(lambda n: setattr(self, 'selected_snd', n))
        self.settings_inner.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.stack.setCurrentIndex(1)

    def _on_opacity_changed(self, value):
        self._opacity = value / 100.0; self.setWindowOpacity(self._opacity)
        lbl = getattr(self.settings_inner, 'opacity_label', None)
        if lbl: lbl.setText(f"현재: {value}%")

    def _close_settings(self): self.stack.setCurrentIndex(0)
    def _on_sound_toggle(self, v): self.sound_enabled = v
    def _on_silent_toggle(self, v): self.silent_mode = v
    def _on_mode_toggle(self, v):
        self.mode_120 = v; self.dial.set_max_minutes(120 if v else 60)

    def _play(self, name):
        if not self.sound_enabled: return
        path = self.sound_lib.path(name)
        if not path or not os.path.exists(path): return
        self.sound_fx.stop(); self.sound_fx.setSource(QUrl.fromLocalFile(path))
        self.sound_fx.setVolume(0.85); self.sound_fx.play()

    def _preview(self):
        name = self.settings_inner.sound_combo.currentText()
        if self.silent_mode: self._flash_window() # 무음 모드 미리보기
        else: self._play(name)

    def on_state_changed(self):
        self.start_icon.setText("⏸️" if self.dial.is_running else "▶️")

    def on_finished(self):
        if self.silent_mode:
            self._flash_window() # ✨ 소리 대신 깜빡임
        else:
            self._play(self.selected_snd)
        self.start_icon.setText("▶️")

    # ✨ 화면 깜빡임 로직
    def _flash_window(self):
        self._flash_count = 0
        if not hasattr(self, '_flash_tmr'):
            self._flash_tmr = QTimer(self)
            self._flash_tmr.timeout.connect(self._do_flash)
        self._flash_tmr.start(300)

    def _do_flash(self):
        self._flash_count += 1
        if self._flash_count > 6: # 3번 깜빡임 (on/off 6번)
            self._flash_tmr.stop()
            self.surface.setStyleSheet(self.theme.qss()) # 원상복구
            return

        if self._flash_count % 2 == 1:
            # 배경을 빨간색으로 덮어씀
            qss = self.theme.qss() + f"\nQFrame#surface {{ background: {ACCENT}; }}"
            self.surface.setStyleSheet(qss)
        else:
            self.surface.setStyleSheet(self.theme.qss())

    def _on_start_pause(self):
        if self.dial.is_running: self.dial.pause()
        else:                    self.dial.start()
        self.on_state_changed()

    def _apply_aot(self):
        flags = self.windowFlags()
        if self.always_on_top: flags |= Qt.WindowStaysOnTopHint
        else:                  flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags); self.show()

    def _toggle_aot(self):
        sender = self.sender()
        if sender:
            self.always_on_top = sender.isChecked()
            # 두 버튼(메인, 미니) 상태 동기화
            self.pin_btn.setChecked(self.always_on_top)
            self.mini_pin_btn.setChecked(self.always_on_top)
        self._apply_aot()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        should_be_minimal = (w < self.NORMAL_MIN_WIDTH) or (h < self.NORMAL_MIN_HEIGHT)
        
        if should_be_minimal and not self._is_minimal_ui:
            self._is_minimal_ui = True
            self.top_widget.hide(); self.bottom_widget.hide()
            self.dial.set_minimal(True)
            self.main_page.layout().setContentsMargins(4, 4, 4, 4)
            self.mini_pin_btn.show() # ✨ 미니 핀 버튼 표시
            
        elif not should_be_minimal and self._is_minimal_ui:
            self._is_minimal_ui = False
            self.top_widget.show(); self.bottom_widget.show()
            self.dial.set_minimal(False)
            self.main_page.layout().setContentsMargins(18, 14, 18, 16)
            self.mini_pin_btn.hide() # ✨ 미니 핀 버튼 숨김

        self._update_btn_sizes()

    def _update_btn_sizes(self):
        w = self.width()
        btn_sz = max(36, min(72, int(w * 0.10)))
        font_sz = max(16, min(32, int(btn_sz * 0.50)))
        for btn in (self.reset_icon, self.start_icon):
            btn.setFixedSize(btn_sz, btn_sz)
            f = btn.font(); f.setPixelSize(font_sz); btn.setFont(f)
            btn.setStyleSheet(f"border-radius:{btn_sz//2}px; font-size:{font_sz}px;")

    def _edge(self, pos):
        # 테두리 두께 (리사이즈를 잡을 얇은 선)
        m = 6 if getattr(self, '_is_minimal_ui', False) else 18 
        # 모서리 판정 길이 (대각선 화살표가 뜨는 구간을 길게 확장)
        c_len = 24 if getattr(self, '_is_minimal_ui', False) else 44 

        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        
        # 일단 상하좌우 가장자리에 닿았는지 판정
        l, r, t, b = x <= m, x >= w - m, y <= m, y >= h - m
        
        # 대각선 판정: 가장자리에 닿아 있으면서, 코너 쪽(c_len)에 충분히 가까운가?
        if (l and y <= c_len) or (t and x <= c_len): return "tl"
        if (r and y <= c_len) or (t and x >= w - c_len): return "tr"
        if (l and y >= h - c_len) or (b and x <= c_len): return "bl"
        if (r and y >= h - c_len) or (b and x >= w - c_len): return "br"

        # 대각선이 아니라면 일반 상하좌우 판정
        if r: return "r"
        if l: return "l"
        if b: return "b"
        if t: return "t"
        return None

    _CUR = {"l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor, "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
            "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor, "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor}

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton: return
        edge = self._edge(e.pos())
        if edge:
            self._resize_edge = edge; self._resize_start_geo = self.geometry(); self._resize_start_pos = e.globalPos()
        elif self._is_minimal_ui or e.pos().y() < 50:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            self._mouse_press_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.NoButton:
            edge = self._edge(e.pos())
            if edge: self.setCursor(QCursor(self._CUR.get(edge, Qt.ArrowCursor)))
            else: self.unsetCursor()
            return
        if self._resize_edge and self._resize_start_geo and self._resize_start_pos:
            d = e.globalPos() - self._resize_start_pos
            g = self._resize_start_geo
            nx, ny, nw, nh = g.x(), g.y(), g.width(), g.height()
            mw, mh = self.minimumWidth(), self.minimumHeight()
            ed = self._resize_edge
            if "r" in ed: nw = max(mw, g.width() + d.x())
            if "b" in ed: nh = max(mh, g.height() + d.y())
            if "l" in ed: nw = max(mw, g.width() - d.x()); nx = g.x() + g.width() - nw
            if "t" in ed: nh = max(mh, g.height() - d.y()); ny = g.y() + g.height() - nh
            self.setGeometry(nx, ny, nw, nh)
        elif self._drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        if getattr(self, '_is_minimal_ui', False) and getattr(self, '_mouse_press_pos', None):
            # 클릭 시 손떨림/미끄러짐 허용 오차를 5에서 15로 대폭 증가
            dist = (e.globalPos() - self._mouse_press_pos).manhattanLength()
            if dist < 15: 
                self._on_start_pause()
                
        self._drag_pos = self._resize_edge = None
        self._resize_start_geo = self._resize_start_pos = self._mouse_press_pos = None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Time Timer")
    try:
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)
    except Exception: pass
    w = TimeTimerWindow(); w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()