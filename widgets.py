import math

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QComboBox, QSizePolicy, QSlider,
)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, QSize, QElapsedTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

from theme import ACCENT, Theme, get_font


class ToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self):
        return self._checked

    def setChecked(self, v: bool):
        self._checked = v
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.update()
            if hasattr(self, "toggled"):
                self.toggled(self._checked)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2
        track_col = QColor(ACCENT) if self._checked else QColor(
            self.parent().theme.toggle_off_bg
            if self.parent() and hasattr(self.parent(), "theme")
            else "#d8d8de"
        )
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(track_col))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)
        margin = 3
        knob_x = (w - h + margin) if self._checked else margin
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(knob_x + r - margin, r), r - margin, r - margin)


class TimerDial(QWidget):
    def __init__(self, pw=None):
        super().__init__(pw)
        self._pw = pw
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(50, 50)
        self.max_minutes = 60
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.is_running = False
        self.is_dragging = False
        self.hover_angle = None
        self._disp = 0.0
        self.theme = Theme(False)
        self.is_minimal = False

        self.tick_tmr = QTimer(self)
        self.tick_tmr.setInterval(1000)
        self.tick_tmr.timeout.connect(self._tick)

        self.smooth_tmr = QTimer(self)
        self.smooth_tmr.setInterval(40)
        self.smooth_tmr.timeout.connect(self._smooth)
        self.smooth_tmr.start()

        self._smooth_elapsed = QElapsedTimer()
        self._smooth_elapsed.start()

        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        return QSize(340, 340)

    def set_theme(self, t):
        self.theme = t
        self.update()

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
        if self.remaining_seconds <= 0:
            return False
        self.is_running = True
        self.tick_tmr.start()
        self.update()
        return True

    def pause(self):
        self.is_running = False
        self.tick_tmr.stop()
        self.update()

    def reset(self):
        self.is_running = False
        self.tick_tmr.stop()
        self.total_seconds = self.remaining_seconds = 0
        self._disp = 0.0
        self.update()
        if self._pw:
            self._pw.on_state_changed()

    def _tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.remaining_seconds == 0:
                self.is_running = False
                self.tick_tmr.stop()
                if self._pw:
                    self._pw.on_finished()
        if self._pw:
            self._pw.on_state_changed()

    def _smooth(self):
        elapsed_ms = self._smooth_elapsed.restart()
        # Cap at 200 ms to prevent a large jump if the app was suspended
        dt = min(elapsed_ms / 1000.0, 0.2)

        target = float(self.remaining_seconds)
        if self.is_running or self._disp > target:
            self._disp = max(target, self._disp - dt)
        else:
            self._disp = target
        self.update()

    def _angle(self, pos):
        cx, cy = self.width() / 2, self.height() / 2
        a = math.degrees(math.atan2(pos.y() - cy, pos.x() - cx))
        return (a + 90) % 360

    def _secs(self, angle):
        return int(round(angle / 360 * self.max_minutes * 60))

    def _in_dial(self, pos):
        cx, cy = self.width() / 2, self.height() / 2
        r_sq = (pos.x() - cx) ** 2 + (pos.y() - cy) ** 2
        side = min(self.width(), self.height())
        if self.is_minimal:
            outer_r = side * 0.5
            inner_r = side * 0.28
            return inner_r ** 2 <= r_sq <= outer_r ** 2
        else:
            r = side / 2 * 0.839
            return r_sq <= r ** 2

    def mousePressEvent(self, e):
        # 링 영역(미니모드) 또는 다이얼 영역(일반모드) 안이면 시간 조절
        # 그 외(중앙 원, 링 바깥)는 윈도우에 양보 → pause/start
        if (e.button() == Qt.LeftButton
                and not self.is_running
                and self._in_dial(e.pos())):
            self.is_dragging = True
            self._apply(e.pos())
        else:
            e.ignore()

    def mouseMoveEvent(self, e):
        if self.is_dragging and not self.is_running:
            self._apply(e.pos())
        elif not self.is_running and self._in_dial(e.pos()):
            self.hover_angle = self._angle(e.pos())
            self.update()
        elif self.hover_angle is not None:
            self.hover_angle = None
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.is_dragging = False
            if self.is_minimal:
                # 릴리즈를 윈도우 eventFilter까지 전파 → 클릭 판정(pause/start)
                e.ignore()

    def leaveEvent(self, _):
        self.hover_angle = None
        self.update()

    def _apply(self, pos):
        raw = self._secs(self._angle(pos))
        s = (raw // 60) * 60
        self.total_seconds = self.remaining_seconds = max(0, s)
        self._disp = float(self.remaining_seconds)
        self.update()
        if self._pw:
            self._pw.on_state_changed()

    def paintEvent(self, _):
        t = self.theme
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()
        side = min(W, H)
        cx, cy = W / 2, H / 2

        nfx          = max(8, int(side * 0.038))
        cfx          = max(11, int(side * 0.082))
        label_margin = nfx * 1.4
        tick_gap     = nfx * 1.0
        num_gap      = nfx * 2.2

        total_r  = side * 0.500 - label_margin
        num_r    = total_r
        face_r   = total_r - num_gap
        ring_r   = face_r
        ring_w   = max(1.0, side * 0.004)

        tick_outer = total_r - tick_gap
        tick_long  = max(2, side * 0.022)
        tick_short = max(1, side * 0.012)
        tick_lw    = max(1.0, side * 0.004)
        tick_sw    = max(0.5, side * 0.002)

        center_r = max(cfx * 1.4, side * 0.130)

        if self.is_minimal:
            face_r   = side * 0.49
            center_r = side * 0.28

        # 페이스 배경
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(t.dial_face))
        p.drawEllipse(QPointF(cx, cy), side * 0.500, side * 0.500)

        # 호버
        if self.hover_angle is not None and not self.is_running and not self.is_dragging:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(Theme.RED_LIGHT))
            rect = QRectF(cx - face_r, cy - face_r, face_r * 2, face_r * 2)
            p.drawPie(rect, int(90 * 16), int(-self.hover_angle * 16))

        # 빨간(또는 회색) 파이 섹터
        if self._disp > 0:
            frac = self._disp / (self.max_minutes * 60)
            span = frac * 360.0
            p.setPen(Qt.NoPen)
            if self.is_minimal and not self.is_running:
                p.setBrush(QBrush(t.status_col))
            else:
                p.setBrush(QBrush(Theme.RED))
            rect = QRectF(cx - face_r, cy - face_r, face_r * 2, face_r * 2)
            p.drawPie(rect, int(90 * 16), int(-span * 16))

        # 눈금, 테두리, 핸드 (미니모드에서는 생략)
        if not self.is_minimal:
            p.setPen(QPen(t.dial_ring, ring_w))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

            num_ticks = self.max_minutes
            p.save()
            p.translate(cx, cy)
            for i in range(num_ticks):
                ang = i * 360.0 / num_ticks
                p.save()
                p.rotate(ang)
                major = (i % 5 == 0)
                y_out = -tick_outer
                y_in  = -(tick_outer - (tick_long if major else tick_short))
                p.setPen(QPen(
                    t.tick_major if major else t.tick_minor,
                    tick_lw if major else tick_sw,
                    Qt.SolidLine, Qt.RoundCap,
                ))
                p.drawLine(QPointF(0, y_in), QPointF(0, y_out))
                p.restore()
            p.restore()

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
                p.drawText(int(lx - tw / 2), int(ly + th / 3), text)
            p.restore()

            if self._disp > 0:
                frac = self._disp / (self.max_minutes * 60)
                hand_rad = math.radians(frac * 360 - 90)
                hx = cx + face_r * math.cos(hand_rad)
                hy = cy + face_r * math.sin(hand_rad)
                p.setPen(QPen(Theme.RED_HAND, max(1.5, side * 0.006), Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(cx, cy), QPointF(hx, hy))

        # 중앙 원
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(t.dial_face))
        p.drawEllipse(QPointF(cx, cy), center_r, center_r)

        # 시간 텍스트
        p.save()
        shown = int(math.ceil(self._disp)) if self.is_running else self.remaining_seconds
        mins, secs = divmod(shown, 60)
        time_txt = f"{mins:02d}:00" if self.is_dragging else f"{mins:02d}:{secs:02d}"
        current_cfx = max(14, int(side * 0.13)) if self.is_minimal else cfx
        p.setFont(get_font(current_cfx, QFont.Bold))
        p.setPen(t.time_col)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(time_txt)
        th = fm.height()
        p.drawText(int(cx - tw / 2), int(cy + th / 3), time_txt)
        p.restore()


class AspectBox(QWidget):
    def __init__(self, child, parent=None):
        super().__init__(parent)
        self._c = child
        child.setParent(self)
        self.setMinimumSize(50, 50)

    def resizeEvent(self, _):
        s = min(self.width(), self.height())
        self._c.setGeometry((self.width() - s) // 2, (self.height() - s) // 2, s, s)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def build(self, sound_lib, theme, sound_enabled, silent_mode, sound_name, mode_120, opacity):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(0)

        def sep():
            f = QFrame()
            f.setObjectName("separator")
            f.setFixedHeight(1)
            return f

        def group_label(text):
            lb = QLabel(text.upper())
            lb.setObjectName("settingGroup")
            return lb

        def row_label(title, desc=None):
            col = QVBoxLayout()
            col.setSpacing(1)
            tl = QLabel(title)
            tl.setObjectName("settingLabel")
            col.addWidget(tl)
            if desc:
                dl = QLabel(desc)
                dl.setObjectName("settingDesc")
                col.addWidget(dl)
            return col

        root.addWidget(group_label("알림음"))
        root.addSpacing(8)

        r1 = QHBoxLayout()
        r1.setSpacing(10)
        r1.addLayout(row_label("알림음 사용", "타이머 종료 시 소리 재생"))
        r1.addStretch()
        self.sound_toggle = ToggleSwitch(self)
        self.sound_toggle.setChecked(sound_enabled)
        r1.addWidget(self.sound_toggle)
        root.addLayout(r1)
        root.addSpacing(12)

        r_silent = QHBoxLayout()
        r_silent.setSpacing(10)
        r_silent.addLayout(row_label("무음 모드", "종료 시 소리 대신 화면 깜빡임"))
        r_silent.addStretch()
        self.silent_toggle = ToggleSwitch(self)
        self.silent_toggle.setChecked(silent_mode)
        r_silent.addWidget(self.silent_toggle)
        root.addLayout(r_silent)
        root.addSpacing(12)
        root.addWidget(sep())
        root.addSpacing(12)

        r2 = QVBoxLayout()
        r2.setSpacing(6)
        r2.addLayout(row_label("알림음 종류"))
        h2 = QHBoxLayout()
        h2.setSpacing(8)
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

        root.addWidget(group_label("타이머"))
        root.addSpacing(8)

        r3 = QHBoxLayout()
        r3.setSpacing(10)
        r3.addLayout(row_label("120분 모드", "다이얼 최대 시간을 120분으로 설정"))
        r3.addStretch()
        self.mode_toggle = ToggleSwitch(self)
        self.mode_toggle.setChecked(mode_120)
        r3.addWidget(self.mode_toggle)
        root.addLayout(r3)
        root.addSpacing(20)

        root.addWidget(group_label("화면"))
        root.addSpacing(8)

        r4 = QVBoxLayout()
        r4.setSpacing(6)
        opacity_pct = int(opacity * 100)
        r4.addLayout(row_label("창 투명도", f"현재: {opacity_pct}%"))

        self.opacity_label = None
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
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(opacity_pct)
        self.opacity_slider.setFixedHeight(28)
        r4.addWidget(self.opacity_slider)
        root.addLayout(r4)
        root.addStretch()
