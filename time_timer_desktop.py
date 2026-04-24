"""
Time Timer (Desktop) — v4
레퍼런스 이미지 기반 리디자인
- Pretendard 폰트
- 설정 페이지 (알림음 유무·종류, 120분 모드)
- 시스템 라이트/다크 테마 동적 반영
- 프리셋 제거, 항상 위 / 시작 버튼 #f05650
"""

import sys, math, struct, wave, os, tempfile

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QComboBox, QSizePolicy, QGraphicsDropShadowEffect,
    QStackedWidget, QScrollArea, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, QSize, QUrl
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontDatabase,
    QRadialGradient, QLinearGradient, QCursor, QPalette, QPainterPath
)
from PyQt5.QtMultimedia import QSoundEffect


# ══════════════════════════════════════════════════════════════════════
# 폰트 유틸
# ══════════════════════════════════════════════════════════════════════
def get_font(size: int, weight=QFont.Normal) -> QFont:
    """Pretendard → Apple SD Gothic Neo → Malgun Gothic → 시스템 기본 순으로 fallback.
    PyQt5 버전에 따라 QFontDatabase API가 다르므로 families() 방식으로 통일."""
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
    # 공통 액센트 (불변)
    RED         = QColor(0xf0, 0x56, 0x50)
    RED_LIGHT   = QColor(0xf0, 0x56, 0x50, 45)   # 호버 미리보기
    RED_HAND    = QColor(0xf0, 0x56, 0x50)        # 핸드

    def __init__(self, dark: bool):
        self.dark = dark
        if dark:
            self.bg                = QColor(28, 28, 30)
            self.surface           = QColor(36, 36, 40)
            self.surface_border    = QColor(55, 55, 60)
            self.shadow            = QColor(0, 0, 0, 130)

            # 다이얼
            self.dial_face         = QColor(44, 44, 48)        # 내부 원 배경
            self.dial_ring         = QColor(65, 65, 72)        # 테두리 링
            self.dial_track        = QColor(55, 55, 62)        # 눈금 트랙 배경
            self.tick_major        = QColor(160, 160, 168)
            self.tick_minor        = QColor(80, 80, 90)
            self.number_col        = QColor(160, 160, 168)

            # 중앙 텍스트 / 핸드
            self.time_col          = QColor(0xD0, 0xD0, 0xD8)   # Figma 다크: #D0D0D8
            self.status_col        = QColor(110, 110, 120)
            self.hand_dot          = QColor(65, 65, 72)

            # 버튼/텍스트
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
            self.status_col        = QColor(170, 170, 178)
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
        QLabel {{
            background:transparent;
        }}
        QLabel#title {{
            color:{title}; font-size:13px; font-weight:600;
        }}
        QLabel#subtitle {{
            color:{sub}; font-size:11px;
        }}
        QLabel#settingGroup {{
            color:{sub}; font-size:10px; font-weight:600;
            letter-spacing:0.5px;
        }}
        QLabel#settingLabel {{
            color:{btn_fg}; font-size:12px;
        }}
        QLabel#settingDesc {{
            color:{sub}; font-size:10px;
        }}
        QPushButton {{
            background:{btn_bg}; border:1px solid {btn_bd};
            border-radius:8px; padding:6px 14px;
            font-size:12px; color:{btn_fg};
        }}
        QPushButton:hover  {{ background:{btn_hv}; }}
        QPushButton:pressed {{ background:{btn_pr}; }}
        QPushButton#startBtn {{
            background:{ACCENT}; border:none;
            color:white; font-size:14px; font-weight:700;
            border-radius:10px;
        }}
        QPushButton#startBtn:hover  {{ background:{ACCENT_HOVER}; }}
        QPushButton#startBtn:pressed {{ background:{ACCENT_PRESS}; }}
        QPushButton#iconBtn {{
            background:transparent; border:none;
            color:{sub}; font-size:16px; padding:0;
        }}
        QPushButton#iconBtn:hover {{ color:{btn_fg}; }}
        QPushButton#pinBtn {{
            background:transparent; border:none;
            font-size:18px; padding:0;
            opacity: 0.4;
        }}
        QPushButton#pinBtn:checked {{
            opacity: 1.0;
        }}
        QPushButton#pinBtn:hover {{
            background: {btn_hv};
            border-radius: 8px;
        }}
        QPushButton#emojiBtn {{
            background:{btn_bg}; border:1px solid {btn_bd};
            border-radius:26px; padding:0;
            font-size:22px;
        }}
        QPushButton#emojiBtn:hover  {{ background:{btn_hv}; border-color:{btn_fg}; }}
        QPushButton#emojiBtn:pressed {{ background:{btn_pr}; }}
        QPushButton#settingsBtn {{
            background:transparent; border:none;
            font-size:18px; padding:0; color:{sub};
        }}
        QPushButton#settingsBtn:hover {{ color:{btn_fg}; }}
        QPushButton#backBtn {{
            background:{btn_bg}; border:1px solid {btn_bd};
            border-radius:8px; padding:5px 12px;
            font-size:12px; color:{btn_fg};
        }}
        QPushButton#backBtn:hover {{ background:{btn_hv}; }}
        QFrame#separator {{
            background:{sep}; border:none;
        }}
        QComboBox {{
            background:{inp_bg}; border:1px solid {inp_bd};
            border-radius:7px; padding:5px 10px;
            font-size:12px; color:{btn_fg}; min-height:26px;
        }}
        QComboBox:hover {{ border-color:{arr_col}; }}
        QComboBox::drop-down {{ border:none; width:20px; }}
        QComboBox::down-arrow {{
            image:none;
            border-left:4px solid transparent;
            border-right:4px solid transparent;
            border-top:5px solid {arr_col};
            margin-right:6px;
        }}
        QComboBox QAbstractItemView {{
            background:{combo_vw}; border:1px solid {inp_bd};
            color:{btn_fg};
            selection-background-color:{combo_sel};
            selection-color:{combo_selc};
            outline:none; padding:4px;
        }}
        QScrollArea {{ background:transparent; border:none; }}
        QScrollBar:vertical {{
            background:transparent; width:4px; margin:0;
        }}
        QScrollBar::handle:vertical {{
            background:{btn_bd}; border-radius:2px; min-height:20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height:0;
        }}
        QSlider#opacitySlider::groove:horizontal {{
            height:4px; background:{btn_bd}; border-radius:2px;
        }}
        QSlider#opacitySlider::handle:horizontal {{
            width:16px; height:16px; margin:-6px 0;
            background:{ACCENT}; border-radius:8px;
        }}
        QSlider#opacitySlider::sub-page:horizontal {{
            background:{ACCENT}; border-radius:2px;
        }}
        """


# ══════════════════════════════════════════════════════════════════════
# 시스템 다크 감지
# ══════════════════════════════════════════════════════════════════════
def is_dark() -> bool:
    app = QApplication.instance()
    if not app:
        return False
    bg = app.palette().color(QPalette.Window)
    return (0.299*bg.red() + 0.587*bg.green() + 0.114*bg.blue()) < 128


# ══════════════════════════════════════════════════════════════════════
# 알림음 합성 라이브러리
# ══════════════════════════════════════════════════════════════════════
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
            wf.writeframes(b"".join(
                struct.pack("<h", max(-32767, min(32767, int(s*32767))))
                for s in samples))
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

    def _chime(self):
        return self._cat(self._tone(659.25,.4,"sine",.5,.005,.6),
                         self._sil(.05),self._tone(1046.5,.6,"sine",.45,.005,.7))
    def _bell(self):
        b=self._tone(523.25,1.2,"sine",.4,.002,.95)
        return self._mix(self._mix(b,self._tone(1046.5,1.2,"sine",.15,.002,.95)),
                         self._tone(1568,1.2,"sine",.08,.002,.95))
    def _beep(self):
        b=self._tone(880,.12,"square",.4,.002,.05); s=self._sil(.08)
        return self._cat(b,s,b,s,b)
    def _ding(self):
        return self._cat(self._tone(880,.35,"sine",.5,.005,.6),
                         self._tone(698.46,.5,"sine",.45,.005,.7))
    def _alarm(self):
        o=[]
        for _ in range(3):
            o+=self._tone(1000,.15,"square",.35,.002,.02)+self._sil(.06)+\
               self._tone(800,.15,"square",.35,.002,.02)+self._sil(.12)
        return o
    def _wave(self):
        n=int(self.SR*1.2); o=[]
        for i in range(n):
            t=i/self.SR; f=500+300*math.sin(math.pi*t/1.2)
            o.append(math.sin(2*math.pi*f*t)*math.sin(math.pi*t/1.2)*0.45)
        return o
    def _triple(self):
        return self._cat(self._tone(523.25,.28,"sine",.45,.005,.5),
                         self._tone(659.25,.28,"sine",.45,.005,.5),
                         self._tone(783.99,.7,"sine",.5,.005,.7))

    def _build(self):
        for name,fn in [("부드러운 차임",self._chime),("도미솔 상승",self._triple),
                        ("종소리",self._bell),("디지털 비프",self._beep),
                        ("딩동",self._ding),("알람 시계",self._alarm),
                        ("파도 음",self._wave)]:
            try: self.sounds[name]=self._wav(fn(),name.replace(" ","_"))
            except Exception as e: print(f"[snd]{name}:{e}",file=sys.stderr)

    def names(self): return list(self.sounds.keys())
    def path(self, name): return self.sounds.get(name)


# ══════════════════════════════════════════════════════════════════════
# 아이콘 버튼 — 외부 이미지 없이 QPainter로 직접 그림
# ══════════════════════════════════════════════════════════════════════
class SvgIconButton(QWidget):
    """
    icon_type: 'play' | 'pause' | 'reset' | 'pin'
    checkable: True이면 checked 상태에 따라 색상 전환
    """
    clicked = None   # 외부에서 연결할 콜백

    def __init__(self, icon_type: str, size=48, checkable=False,
                 bg_fill=False, parent=None):
        super().__init__(parent)
        self._icon = icon_type
        self._sz = size
        self._checkable = checkable
        self._checked = False
        self._bg_fill = bg_fill          # True = 배경 원 채움 (시작버튼용)
        self._hovered = False
        self._pressed = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self._cb = None                  # clicked 콜백

    # 외부 연결
    def connect(self, fn): self._cb = fn

    def isChecked(self): return self._checked
    def setChecked(self, v: bool): self._checked = v; self.update()

    # 테마 색상 접근용 — 부모 체인에서 TimeTimerWindow 찾기
    def _theme(self):
        w = self.parent()
        while w:
            if hasattr(w, 'theme'): return w.theme
            w = w.parent()
        return Theme(False)

    # 이벤트
    def enterEvent(self, _): self._hovered = True;  self.update()
    def leaveEvent(self, _): self._hovered = False; self._pressed = False; self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._pressed = True; self.update()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            if self._checkable:
                self._checked = not self._checked
            self.update()
            if self._cb: self._cb()

    def paintEvent(self, _):
        t = self._theme()
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        sz = self._sz
        cx = cy = sz / 2

        if self._icon in ('play', 'pause'):
            # ── 배경 원 (시작/일시정지 버튼) ──
            if self._pressed:
                bg = QColor(ACCENT_PRESS)
            elif self._hovered:
                bg = QColor(ACCENT_HOVER)
            else:
                bg = QColor(ACCENT)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(bg))
            p.drawEllipse(QPointF(cx, cy), cx, cy)
            icon_col = QColor("#ffffff")
        elif self._icon == 'reset':
            # ── 리셋: 배경 없음, 보더 원 ──
            border_col = t.btn_border
            if self._hovered: border_col = t.btn_fg
            p.setPen(QPen(QColor(border_col), max(1, sz*0.04)))
            p.setBrush(QBrush(QColor(t.btn_bg)))
            p.drawEllipse(QPointF(cx, cy), cx - sz*0.05, cy - sz*0.05)
            icon_col = QColor(t.btn_fg)
        elif self._icon == 'pin':
            # ── 핀: 활성이면 액센트, 비활성이면 서브텍스트 색 ──
            p.setPen(Qt.NoPen); p.setBrush(Qt.NoBrush)
            icon_col = QColor(ACCENT) if self._checked else QColor(t.subtitle_hex)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(icon_col))

        if self._icon == 'play':
            # ▶ 삼각형
            s = sz * 0.28
            ox = cx + sz * 0.06   # 살짝 오른쪽 오프셋
            path = QPainterPath()
            path.moveTo(ox - s*0.5, cy - s)
            path.lineTo(ox + s,     cy)
            path.lineTo(ox - s*0.5, cy + s)
            path.closeSubpath()
            p.fillPath(path, QBrush(icon_col))

        elif self._icon == 'pause':
            # ⏸ 두 사각형
            bw = sz * 0.13; bh = sz * 0.36; gap = sz * 0.10
            lx = cx - gap/2 - bw; ty = cy - bh/2
            p.drawRoundedRect(QRectF(lx, ty, bw, bh), 2, 2)
            p.drawRoundedRect(QRectF(cx + gap/2, ty, bw, bh), 2, 2)

        elif self._icon == 'reset':
            # ⟲ 원호 + 화살표
            pen = QPen(icon_col, max(1.5, sz*0.07), Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen); p.setBrush(Qt.NoBrush)
            arc_r = sz * 0.22
            rect = QRectF(cx - arc_r, cy - arc_r, arc_r*2, arc_r*2)
            p.drawArc(rect, int(60*16), int(-(300)*16))   # 300도 호
            # 화살표 머리 (60도 위치에서)
            arrow_angle = math.radians(60)
            tip_x = cx + arc_r * math.cos(arrow_angle)
            tip_y = cy - arc_r * math.sin(arrow_angle)
            ah = sz * 0.14
            p.setPen(Qt.NoPen); p.setBrush(QBrush(icon_col))
            path = QPainterPath()
            path.moveTo(tip_x, tip_y)
            path.lineTo(tip_x - ah*math.sin(arrow_angle - 0.5),
                        tip_y - ah*math.cos(arrow_angle - 0.5))
            path.lineTo(tip_x - ah*math.sin(arrow_angle + 0.5),
                        tip_y - ah*math.cos(arrow_angle + 0.5))
            path.closeSubpath()
            p.fillPath(path, QBrush(icon_col))

        elif self._icon == 'pin':
            # 📌 핀 아이콘 — 단순 기하 도형으로 표현
            # 원형 헤드
            p.setBrush(QBrush(icon_col)); p.setPen(Qt.NoPen)
            head_r = sz * 0.18
            head_cx = cx
            head_cy = cy - sz * 0.08
            p.drawEllipse(QPointF(head_cx, head_cy), head_r, head_r)
            # 핀 몸통 (마름모 + 아래 선)
            body_w = sz * 0.12; body_h = sz * 0.22
            path = QPainterPath()
            path.moveTo(head_cx,              head_cy + head_r - 1)
            path.lineTo(head_cx - body_w,     head_cy + head_r + body_h * 0.4)
            path.lineTo(head_cx,              head_cy + head_r + body_h)
            path.lineTo(head_cx + body_w,     head_cy + head_r + body_h * 0.4)
            path.closeSubpath()
            p.fillPath(path, QBrush(icon_col))
            # 아래 꼬리 선
            pen2 = QPen(icon_col, max(1.5, sz*0.06), Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen2)
            tail_y0 = head_cy + head_r + body_h
            tail_y1 = cy + sz * 0.30
            p.drawLine(QPointF(head_cx, tail_y0), QPointF(head_cx, tail_y1))


# ══════════════════════════════════════════════════════════════════════
# 토글 스위치 위젯
# ══════════════════════════════════════════════════════════════════════
class ToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)
        self._anim = 0.0   # 0=off, 1=on (향후 애니메이션용)

    def isChecked(self): return self._checked
    def setChecked(self, v: bool):
        self._checked = v; self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.update()
            if hasattr(self, "toggled"):
                self.toggled(self._checked)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height()
        r = h/2
        # 트랙
        track_col = QColor(ACCENT) if self._checked else \
                    QColor(self.parent().theme.toggle_off_bg if self.parent() and hasattr(self.parent(),'theme')
                           else "#d8d8de")
        p.setPen(Qt.NoPen); p.setBrush(QBrush(track_col))
        p.drawRoundedRect(QRectF(0,0,w,h), r, r)
        # 놉
        margin = 3
        knob_x = (w - h + margin) if self._checked else margin
        knob_col = QColor("#ffffff")
        p.setBrush(QBrush(knob_col))
        p.drawEllipse(QPointF(knob_x + r - margin, r), r-margin, r-margin)


# ══════════════════════════════════════════════════════════════════════
# 원형 타이머 다이얼 — 레퍼런스 이미지 스타일
# ══════════════════════════════════════════════════════════════════════
class TimerDial(QWidget):
    def __init__(self, pw=None):
        super().__init__(pw)
        self._pw = pw
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200)

        self.max_minutes      = 60
        self.total_seconds    = 0
        self.remaining_seconds= 0
        self.is_running       = False
        self.is_dragging      = False
        self.hover_angle      = None
        self._disp            = 0.0     # display seconds (부드러운)
        self.theme            = Theme(False)

        self.tick_tmr = QTimer(self); self.tick_tmr.setInterval(1000)
        self.tick_tmr.timeout.connect(self._tick)
        self.smooth_tmr = QTimer(self); self.smooth_tmr.setInterval(40)
        self.smooth_tmr.timeout.connect(self._smooth); self.smooth_tmr.start()

        self.setMouseTracking(True); self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self): return QSize(340, 340)

    # API ──────────────────────────────────────────────────────────────
    def set_theme(self, t): self.theme = t; self.update()

    def set_max_minutes(self, m):
        self.max_minutes = m
        cap = m * 60
        if self.remaining_seconds > cap:
            self.remaining_seconds = self.total_seconds = cap
            self._disp = float(cap)
        self.update()

    def start(self):
        if self.remaining_seconds <= 0: return False
        self.is_running = True; self.tick_tmr.start(); return True

    def pause(self):
        self.is_running = False; self.tick_tmr.stop()

    def reset(self):
        self.is_running = False; self.tick_tmr.stop()
        self.total_seconds = self.remaining_seconds = 0; self._disp = 0.0
        self.update()
        if self._pw: self._pw.on_state_changed()

    # 내부 ─────────────────────────────────────────────────────────────
    def _tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.remaining_seconds == 0:
                self.is_running = False; self.tick_tmr.stop()
                if self._pw: self._pw.on_finished()
        if self._pw: self._pw.on_state_changed()

    def _smooth(self):
        target = float(self.remaining_seconds)
        if self.is_running:
            self._disp = max(target, self._disp - 1/25)   # 40ms × 25 ≈ 1s
        else:
            self._disp = target
        self.update()

    # 마우스 ───────────────────────────────────────────────────────────
    def _angle(self, pos):
        cx, cy = self.width()/2, self.height()/2
        a = math.degrees(math.atan2(pos.y()-cy, pos.x()-cx))
        return (a + 90) % 360

    def _secs(self, angle):
        return int(round(angle/360 * self.max_minutes * 60))

    def _in_dial(self, pos):
        cx, cy = self.width()/2, self.height()/2
        # Figma: face_r=142.8, total_r=170 → 비율 0.839
        r = min(self.width(), self.height()) / 2 * 0.839
        return (pos.x()-cx)**2 + (pos.y()-cy)**2 <= r*r

    def mousePressEvent(self, e):
        if e.button()==Qt.LeftButton and not self.is_running and self._in_dial(e.pos()):
            self.is_dragging = True; self._apply(e.pos())

    def mouseMoveEvent(self, e):
        if self.is_dragging and not self.is_running:
            self._apply(e.pos())
        elif not self.is_running and self._in_dial(e.pos()):
            self.hover_angle = self._angle(e.pos()); self.update()
        elif self.hover_angle is not None:
            self.hover_angle = None; self.update()

    def mouseReleaseEvent(self, e):
        if e.button()==Qt.LeftButton: self.is_dragging = False

    def leaveEvent(self, _):
        self.hover_angle = None; self.update()

    def _apply(self, pos):
        # 분 단위로만 스냅 (60초 단위)
        raw = self._secs(self._angle(pos))
        s = (raw // 60) * 60
        self.total_seconds = self.remaining_seconds = max(0, s)
        self._disp = float(self.remaining_seconds)
        self.update()
        if self._pw: self._pw.on_state_changed()

    # 렌더링 ── Figma Make 수치 기반 ────────────────────────────────────
    def paintEvent(self, _):
        t = self.theme
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()
        side = min(W, H)
        cx, cy = W/2, H/2

        # ── 수치 정의 ──────────────────────────────────────────────────
        nfx       = max(8, int(side * 0.038))    # 숫자 라벨 폰트
        cfx       = max(11, int(side * 0.082))   # 시간 표시 폰트

        label_margin = nfx * 1.4               # 위젯 경계 ↔ 숫자 중심 여유
        tick_gap     = nfx * 1.0               # 눈금 바깥 끝 ↔ 숫자 중심 여백 (신규)
        num_gap      = nfx * 2.2               # 숫자 중심 ↔ 링 사이 여백

        total_r   = side * 0.500 - label_margin # 숫자 라벨 중심 반지름
        num_r     = total_r                      # 숫자 라벨 중심
        face_r    = total_r - num_gap            # 파이/링 반지름
        ring_r    = face_r
        ring_w    = max(1.0, side * 0.004)

        # 눈금: ring 바깥에서 시작 → 숫자와 tick_gap 만큼 떨어진 곳에서 끝
        tick_outer = total_r - tick_gap          # 눈금 바깥 끝 (숫자와 gap 확보)
        tick_long  = max(2, side * 0.022)
        tick_short = max(1, side * 0.012)
        tick_lw    = max(1.0, side * 0.004)
        tick_sw    = max(0.5, side * 0.002)

        # 중앙 원
        center_r  = max(cfx * 1.4, side * 0.130)

        # ── Layer 0: 다이얼 페이스 배경 (전체) ──
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(t.dial_face))
        p.drawEllipse(QPointF(cx, cy), side * 0.500, side * 0.500)

        # ── Layer 1: 호버 미리보기 ──
        if self.hover_angle is not None and not self.is_running and not self.is_dragging:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(Theme.RED_LIGHT))
            rect = QRectF(cx-face_r, cy-face_r, face_r*2, face_r*2)
            p.drawPie(rect, int(90*16), int(-self.hover_angle*16))

        # ── Layer 2: 빨간 파이 섹터 ──
        if self._disp > 0:
            frac = self._disp / (self.max_minutes * 60)
            span = frac * 360.0
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(Theme.RED))
            rect = QRectF(cx-face_r, cy-face_r, face_r*2, face_r*2)
            p.drawPie(rect, int(90*16), int(-span*16))

        # ── Layer 3: 링 테두리 (stroke only) ──
        p.setPen(QPen(t.dial_ring, ring_w))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # ── Layer 4: 눈금 (링 바깥, tick_outer 이내) ──
        num_ticks = self.max_minutes
        p.save(); p.translate(cx, cy)
        for i in range(num_ticks):
            ang = i * 360.0 / num_ticks
            p.save(); p.rotate(ang)
            major = (i % 5 == 0)
            y_out = -tick_outer
            y_in  = -(tick_outer - (tick_long if major else tick_short))
            p.setPen(QPen(
                t.tick_major if major else t.tick_minor,
                tick_lw if major else tick_sw,
                Qt.SolidLine, Qt.RoundCap
            ))
            p.drawLine(QPointF(0, y_in), QPointF(0, y_out))
            p.restore()
        p.restore()

        # ── Layer 5: 숫자 라벨 ──
        step = self.max_minutes // 12
        p.save()
        p.setFont(get_font(nfx, QFont.DemiBold))
        p.setPen(t.number_col)
        fm = p.fontMetrics()
        for i in range(12):
            minute = i * step
            rad = math.radians(i * 30 - 90)
            lx = cx + num_r * math.cos(rad)
            ly = cy + num_r * math.sin(rad)
            text = str(minute)
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            p.drawText(int(lx - tw/2), int(ly + th/3), text)
        p.restore()

        # ── Layer 6: 핸드 라인 ──
        if self._disp > 0:
            frac = self._disp / (self.max_minutes * 60)
            hand_rad = math.radians(frac * 360 - 90)
            hx = cx + face_r * math.cos(hand_rad)
            hy = cy + face_r * math.sin(hand_rad)
            p.setPen(QPen(Theme.RED_HAND, max(1.5, side * 0.006),
                          Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(cx, cy), QPointF(hx, hy))

        # ── Layer 7: 중앙 원 (fill=dial_face, 테두리 없음) ──
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(t.dial_face))
        p.drawEllipse(QPointF(cx, cy), center_r, center_r)

        # ── Layer 8: 시간 텍스트만 표시 (상태 힌트 없음) ──
        p.save()
        shown = int(math.ceil(self._disp)) if self.is_running else self.remaining_seconds
        mins, secs = divmod(shown, 60)
        time_txt = f"{mins:02d}:00" if self.is_dragging else f"{mins:02d}:{secs:02d}"
        p.setFont(get_font(cfx, QFont.Bold))
        p.setPen(t.time_col)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(time_txt)
        th = fm.height()
        p.drawText(int(cx - tw/2), int(cy + th/3), time_txt)
        p.restore()
        # ── 중앙 점 없음 ──


# Theme에 helper 추가 (monkey-patch 대신 메서드로)
def _theme_status(self, running):
    if running: return QColor(ACCENT)
    return self.status_col
Theme.theme_status = _theme_status


# ══════════════════════════════════════════════════════════════════════
# 1:1 비율 래퍼
# ══════════════════════════════════════════════════════════════════════
class AspectBox(QWidget):
    def __init__(self, child, parent=None):
        super().__init__(parent)
        self._c = child; child.setParent(self)
        self.setMinimumSize(200,200)
    def resizeEvent(self, _):
        s = min(self.width(), self.height())
        self._c.setGeometry((self.width()-s)//2,(self.height()-s)//2,s,s)


# ══════════════════════════════════════════════════════════════════════
# 설정 페이지
# ══════════════════════════════════════════════════════════════════════
class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def build(self, sound_lib, theme, sound_enabled, sound_name, mode_120, opacity):
        """레이아웃 동적 구성 (테마 적용 후 호출)."""
        # 기존 레이아웃 제거
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            QWidget().setLayout(old)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(0)

        def sep():
            f = QFrame(); f.setObjectName("separator")
            f.setFixedHeight(1); return f

        def group_label(text):
            lb = QLabel(text.upper()); lb.setObjectName("settingGroup")
            return lb

        def row_label(title, desc=None):
            col = QVBoxLayout(); col.setSpacing(1)
            tl = QLabel(title); tl.setObjectName("settingLabel")
            col.addWidget(tl)
            if desc:
                dl = QLabel(desc); dl.setObjectName("settingDesc")
                col.addWidget(dl)
            return col

        # ─ 알림음 그룹 ─
        root.addWidget(group_label("알림음"))
        root.addSpacing(8)

        # 알림음 ON/OFF
        r1 = QHBoxLayout(); r1.setSpacing(10)
        r1.addLayout(row_label("알림음 사용", "타이머 종료 시 소리 재생"))
        r1.addStretch()
        self.sound_toggle = ToggleSwitch(self)
        self.sound_toggle.setChecked(sound_enabled)
        r1.addWidget(self.sound_toggle)
        root.addLayout(r1)
        root.addSpacing(12)
        root.addWidget(sep())
        root.addSpacing(12)

        # 알림음 종류
        r2 = QVBoxLayout(); r2.setSpacing(6)
        r2.addLayout(row_label("알림음 종류"))
        h2 = QHBoxLayout(); h2.setSpacing(8)
        self.sound_combo = QComboBox()
        self.sound_combo.setObjectName("soundCombo")
        self.sound_combo.addItems(sound_lib.names())
        if sound_name in sound_lib.names():
            self.sound_combo.setCurrentText(sound_name)
        h2.addWidget(self.sound_combo, 1)
        self.preview_btn = QPushButton("▶ 미리듣기")
        self.preview_btn.setObjectName("backBtn")
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.setFixedWidth(84)
        h2.addWidget(self.preview_btn)
        r2.addLayout(h2)
        root.addLayout(r2)
        root.addSpacing(20)

        # ─ 타이머 그룹 ─
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

        # ─ 화면 그룹 ─
        root.addWidget(group_label("화면"))
        root.addSpacing(8)

        # 투명도 슬라이더
        r4 = QVBoxLayout(); r4.setSpacing(6)
        opacity_pct = int(opacity * 100)
        r4.addLayout(row_label("창 투명도", f"현재: {opacity_pct}%"))
        from PyQt5.QtWidgets import QSlider
        self.opacity_label = None  # desc label 참조용
        # desc label 찾기
        for i in range(r4.count()):
            item = r4.itemAt(i)
            if item and item.layout():
                lay = item.layout()
                for j in range(lay.count()):
                    w = lay.itemAt(j).widget() if lay.itemAt(j) else None
                    if w and w.objectName() == "settingDesc":
                        self.opacity_label = w

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setObjectName("opacitySlider")
        self.opacity_slider.setRange(20, 100)   # 20%~100%
        self.opacity_slider.setValue(opacity_pct)
        self.opacity_slider.setFixedHeight(28)
        r4.addWidget(self.opacity_slider)
        root.addLayout(r4)

        root.addStretch()


# ══════════════════════════════════════════════════════════════════════
# 메인 윈도우
# ══════════════════════════════════════════════════════════════════════
class TimeTimerWindow(QWidget):
    RM = 20   # resize margin

    def __init__(self):
        super().__init__()
        self.always_on_top = True
        self._drag_pos = self._resize_edge = None
        self._resize_start_geo = self._resize_start_pos = None

        self.sound_lib     = SoundLibrary()
        self.sound_fx      = QSoundEffect()
        self.sound_enabled = True
        self.selected_snd  = "부드러운 차임"
        self.mode_120      = False

        self._dark  = is_dark()
        self.theme  = Theme(self._dark)

        self._build_ui()
        self._apply_theme()
        self._apply_aot()
        self.resize(420, 620)
        self.setMinimumSize(280, 380)
        self.setWindowTitle("Time Timer")
        self._opacity = 1.0          # 투명도 (1.0=불투명, 0.2=최소)
        self._update_btn_sizes()     # 초기 버튼 크기

        self._poll = QTimer(self); self._poll.setInterval(2000)
        self._poll.timeout.connect(self._check_theme); self._poll.start()

    # ── UI 구성 ────────────────────────────────────────────────────────
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

        # QStackedWidget (메인 / 설정)
        self.stack = QStackedWidget()
        sf_lay = QVBoxLayout(self.surface)
        sf_lay.setContentsMargins(0,0,0,0); sf_lay.setSpacing(0)
        sf_lay.addWidget(self.stack)

        # ── 메인 페이지 ──
        self.main_page = QWidget()
        mp = QVBoxLayout(self.main_page)
        mp.setContentsMargins(18,14,18,16); mp.setSpacing(0)

        # 상단 바
        top = QHBoxLayout(); top.setSpacing(8)

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

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedSize(32,32)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self._open_settings)

        min_btn = QPushButton("—"); min_btn.setObjectName("iconBtn")
        min_btn.setFixedSize(28,28); min_btn.clicked.connect(self.showMinimized)
        min_btn.setCursor(Qt.PointingHandCursor)

        close_btn = QPushButton("✕"); close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28,28); close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.PointingHandCursor)

        top.addWidget(self.settings_btn)
        top.addWidget(min_btn)
        top.addWidget(close_btn)
        mp.addLayout(top)
        mp.addSpacing(10)

        # 다이얼
        self.dial = TimerDial(self)
        self.dial_box = AspectBox(self.dial)
        self.dial_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mp.addWidget(self.dial_box, 1)
        mp.addSpacing(16)

        # 시작 / 리셋 버튼 (이모지, 동일 크기)
        btn_row = QHBoxLayout(); btn_row.setSpacing(14)
        btn_row.addStretch()

        self.reset_icon = QPushButton("🔄")
        self.reset_icon.setObjectName("emojiBtn")
        self.reset_icon.setCursor(Qt.PointingHandCursor)
        self.reset_icon.clicked.connect(self.dial.reset)

        self.start_icon = QPushButton("▶️")
        self.start_icon.setObjectName("emojiBtn")   # 동일 objectName → 동일 스타일
        self.start_icon.setCursor(Qt.PointingHandCursor)
        self.start_icon.clicked.connect(self._on_start_pause)

        btn_row.addWidget(self.reset_icon)
        btn_row.addSpacing(4)
        btn_row.addWidget(self.start_icon)
        btn_row.addStretch()
        mp.addLayout(btn_row)
        mp.addSpacing(8)

        self.stack.addWidget(self.main_page)   # index 0

        # ── 설정 페이지 ──
        self.settings_page = QWidget()
        sp_outer = QVBoxLayout(self.settings_page)
        sp_outer.setContentsMargins(0,0,0,0); sp_outer.setSpacing(0)

        # 설정 헤더
        hdr = QHBoxLayout(); hdr.setContentsMargins(18,14,18,12); hdr.setSpacing(8)
        back_btn = QPushButton("← 뒤로"); back_btn.setObjectName("backBtn")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._close_settings)
        title_lbl = QLabel("설정"); title_lbl.setObjectName("title")
        hdr.addWidget(back_btn)
        hdr.addStretch()
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        sp_outer.addLayout(hdr)

        # 구분선
        sep_frame = QFrame(); sep_frame.setObjectName("separator")
        sep_frame.setFixedHeight(1); sp_outer.addWidget(sep_frame)

        # 스크롤 영역
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_inner = SettingsPage()
        scroll.setWidget(self.settings_inner)
        sp_outer.addWidget(scroll, 1)
        
        # ✨ 이 부분을 추가해 주세요! (index 1로 설정 페이지 등록)
        self.stack.addWidget(self.settings_page)

        # 리사이즈/드래그를 위해 surface와 stack 위젯에 eventFilter 설치
        self.surface.installEventFilter(self)
        self.stack.installEventFilter(self)
        self.main_page.installEventFilter(self)
        
        # 마우스 트래킹 활성화 (클릭 없이도 마우스 위치 추적)
        self.setMouseTracking(True)
        self.surface.setMouseTracking(True)
        self.stack.setMouseTracking(True)
        self.main_page.setMouseTracking(True)
        self.settings_page.setMouseTracking(True)

    # ── 이벤트 필터 (리사이즈 & 드래그 이벤트 가로채기) ──────────────
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            gpos = event.globalPos()
            lpos = self.mapFromGlobal(gpos)
            edge = self._edge(lpos)
            if edge:
                self._resize_edge = edge
                self._resize_start_geo = self.geometry()
                self._resize_start_pos = gpos
                return True          # 이벤트 소비 → 자식에 전달 안 함
            if lpos.y() < 50:
                self._drag_pos = gpos - self.frameGeometry().topLeft()
                return True
        elif event.type() == QEvent.MouseMove:
            gpos = event.globalPos()
            lpos = self.mapFromGlobal(gpos)
            if event.buttons() == Qt.NoButton:
                edge = self._edge(lpos)
                
                # ✨ 수정된 부분: edge가 있으면 해당 커서로, 없으면 커서 강제 지정 해제
                if edge:
                    self.setCursor(QCursor(self._CUR[edge]))
                else:
                    self.unsetCursor()

                # 커서만 바꾸고 이벤트는 자식에 전달
                return False
            if self._resize_edge and self._resize_start_geo and self._resize_start_pos:
                d = gpos - self._resize_start_pos
                g = self._resize_start_geo
                nx, ny, nw, nh = g.x(), g.y(), g.width(), g.height()
                mw, mh = self.minimumWidth(), self.minimumHeight()
                ed = self._resize_edge
                if "r" in ed: nw = max(mw, g.width() + d.x())
                if "b" in ed: nh = max(mh, g.height() + d.y())
                if "l" in ed:
                    nw = max(mw, g.width() - d.x())
                    nx = g.x() + g.width() - nw
                if "t" in ed:
                    nh = max(mh, g.height() - d.y())
                    ny = g.y() + g.height() - nh
                self.setGeometry(nx, ny, nw, nh)
                return True
            if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
                self.move(gpos - self._drag_pos)
                return True
        elif event.type() == QEvent.MouseButtonRelease:
            self._drag_pos = self._resize_edge = None
            self._resize_start_geo = self._resize_start_pos = None
        return super().eventFilter(obj, event)

    # ── 테마 ───────────────────────────────────────────────────────────
    def _check_theme(self):
        d = is_dark()
        if d != self._dark:
            self._dark = d; self.theme = Theme(d); self._apply_theme()

    def _apply_theme(self):
        t = self.theme
        self.shadow.setColor(t.shadow)
        self.surface.setStyleSheet(t.qss())
        self.dial.set_theme(t)
        # 설정 페이지 토글 스위치 배경 반영
        for sw in (getattr(self.settings_inner,'sound_toggle',None),
                   getattr(self.settings_inner,'mode_toggle',None)):
            if sw: sw.update()

    # ── 설정 페이지 열기/닫기 ──────────────────────────────────────────
    def _open_settings(self):
        self.settings_inner.build(
            self.sound_lib, self.theme,
            self.sound_enabled, self.selected_snd, self.mode_120,
            self._opacity
        )
        self.surface.setStyleSheet(self.theme.qss())
        # 시그널 연결
        self.settings_inner.preview_btn.clicked.connect(self._preview)
        self.settings_inner.sound_toggle.toggled = self._on_sound_toggle
        self.settings_inner.mode_toggle.toggled  = self._on_mode_toggle
        self.settings_inner.sound_combo.currentTextChanged.connect(
            lambda n: setattr(self, 'selected_snd', n))
        self.settings_inner.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.stack.setCurrentIndex(1)

    def _on_opacity_changed(self, value):
        """슬라이더 값(20~100) → 창 투명도 적용."""
        self._opacity = value / 100.0
        self.setWindowOpacity(self._opacity)
        # 레이블 실시간 업데이트
        lbl = getattr(self.settings_inner, 'opacity_label', None)
        if lbl:
            lbl.setText(f"현재: {value}%")

    def _close_settings(self):
        # 설정값 저장 (이미 signal에서 실시간 반영됨)
        self.stack.setCurrentIndex(0)

    def _on_sound_toggle(self, v): self.sound_enabled = v
    def _on_mode_toggle(self, v):
        self.mode_120 = v
        self.dial.set_max_minutes(120 if v else 60)

    # ── 알림음 ─────────────────────────────────────────────────────────
    def _play(self, name):
        if not self.sound_enabled: return
        path = self.sound_lib.path(name)
        if not path or not os.path.exists(path): return
        self.sound_fx.stop()
        self.sound_fx.setSource(QUrl.fromLocalFile(path))
        self.sound_fx.setVolume(0.85); self.sound_fx.play()

    def _preview(self):
        name = self.settings_inner.sound_combo.currentText()
        self._play(name)

    # ── 타이머 콜백 ────────────────────────────────────────────────────
    def on_state_changed(self):
        self.start_icon.setText("⏸️" if self.dial.is_running else "▶️")

    def on_finished(self):
        self._play(self.selected_snd)
        self.start_icon.setText("▶️")

    def _on_start_pause(self):
        if self.dial.is_running: self.dial.pause()
        else:                    self.dial.start()
        self.on_state_changed()

    # ── Always on Top ──────────────────────────────────────────────────
    def _apply_aot(self):
        flags = self.windowFlags()
        if self.always_on_top: flags |= Qt.WindowStaysOnTopHint
        else:                  flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags); self.show()

    def _toggle_aot(self):
        self.always_on_top = self.pin_btn.isChecked()
        self._apply_aot()

    def resizeEvent(self, event):
        """창 크기 변경 시 버튼 크기를 창 너비에 비례해서 동적 조정."""
        super().resizeEvent(event)
        self._update_btn_sizes()

    def _update_btn_sizes(self):
        """버튼 크기 = 창 너비의 10%, 최소 36px ~ 최대 72px."""
        w = self.width()
        btn_sz = max(36, min(72, int(w * 0.10)))
        font_sz = max(16, min(32, int(btn_sz * 0.50)))
        for btn in (self.reset_icon, self.start_icon):
            btn.setFixedSize(btn_sz, btn_sz)
            f = btn.font()
            f.setPixelSize(font_sz)
            btn.setFont(f)
            # border-radius를 절반으로 유지 (원형)
            btn.setStyleSheet(
                f"border-radius:{btn_sz//2}px; font-size:{font_sz}px;"
            )

    # ── 프레임리스 이동 + 리사이즈 (eventFilter가 주 처리) ───────────
    def _edge(self, pos):
        x, y, w, h, m = pos.x(), pos.y(), self.width(), self.height(), self.RM
        l, r, t, b = x <= m, x >= w - m, y <= m, y >= h - m
        if r and b: return "br"
        if r and t: return "tr"
        if l and b: return "bl"
        if l and t: return "tl"
        if r: return "r"
        if l: return "l"
        if b: return "b"
        if t: return "t"
        return None

    _CUR = {"l": Qt.SizeHorCursor,  "r": Qt.SizeHorCursor,
            "t": Qt.SizeVerCursor,  "b": Qt.SizeVerCursor,
            "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
            "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor}

    def mousePressEvent(self, e):
        # 창 자체 영역(자식 없는 여백)에서 동작하는 fallback
        if e.button() != Qt.LeftButton: return
        edge = self._edge(e.pos())
        if edge:
            self._resize_edge = edge
            self._resize_start_geo = self.geometry()
            self._resize_start_pos = e.globalPos()
        elif e.pos().y() < 50:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.NoButton:
            edge = self._edge(e.pos())
            # ✨ 수정된 부분: 위와 동일하게 unsetCursor 적용
            if edge:
                self.setCursor(QCursor(self._CUR[edge]))
            else:
                self.unsetCursor()
            return
        
        if self._resize_edge and self._resize_start_geo and self._resize_start_pos:
            d = e.globalPos() - self._resize_start_pos
            g = self._resize_start_geo
            nx, ny, nw, nh = g.x(), g.y(), g.width(), g.height()
            mw, mh = self.minimumWidth(), self.minimumHeight()
            ed = self._resize_edge
            if "r" in ed: nw = max(mw, g.width() + d.x())
            if "b" in ed: nh = max(mh, g.height() + d.y())
            if "l" in ed:
                nw = max(mw, g.width() - d.x())
                nx = g.x() + g.width() - nw
            if "t" in ed:
                nh = max(mh, g.height() - d.y())
                ny = g.y() + g.height() - nh
            self.setGeometry(nx, ny, nw, nh)
        elif self._drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = self._resize_edge = None
        self._resize_start_geo = self._resize_start_pos = None


# ══════════════════════════════════════════════════════════════════════
# 진입점
# ══════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Time Timer")
    try:
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)
    except Exception:
        pass
    w = TimeTimerWindow(); w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()