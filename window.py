import os
import sys

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
    QStackedWidget, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer, QEvent, QUrl
from PyQt5.QtGui import QCursor
from PyQt5.QtMultimedia import QSoundEffect

from theme import ACCENT, Theme, is_dark
from sound import SoundLibrary
from widgets import TimerDial, AspectBox, SettingsPage


class TimeTimerWindow(QWidget):
    _CUR = {
        "l":  Qt.SizeHorCursor,  "r":  Qt.SizeHorCursor,
        "t":  Qt.SizeVerCursor,  "b":  Qt.SizeVerCursor,
        "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
        "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
    }

    def __init__(self):
        super().__init__()
        self.always_on_top = True
        self._drag_pos = self._resize_edge = None
        self._resize_start_geo = self._resize_start_pos = self._mouse_press_pos = None

        self.sound_lib     = SoundLibrary()
        self.sound_fx      = QSoundEffect()
        self.sound_enabled = True
        self.silent_mode   = False
        self.selected_snd  = "부드러운 차임"
        self.mode_120      = False
        self._alerted      = False  # 알림 지속 중 여부

        self._dark  = is_dark()
        self.theme  = Theme(self._dark)

        self.NORMAL_MIN_WIDTH  = 200
        self.NORMAL_MIN_HEIGHT = 250
        self._is_minimal_ui    = False

        self._build_ui()
        self._apply_theme()
        self._apply_aot()

        self.setMinimumSize(100, 100)
        self.resize(420, 620)
        self.setWindowTitle("Time Timer")
        self._opacity = 1.0
        self._update_btn_sizes()

        self._poll = QTimer(self)
        self._poll.setInterval(2000)
        self._poll.timeout.connect(self._check_theme)
        self._poll.start()

    def _build_ui(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.surface = QFrame(self)
        self.surface.setObjectName("surface")
        self.shadow  = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(28)
        self.shadow.setOffset(0, 5)
        self.surface.setGraphicsEffect(self.shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.addWidget(self.surface)

        self.stack = QStackedWidget()
        sf_lay = QVBoxLayout(self.surface)
        sf_lay.setContentsMargins(0, 0, 0, 0)
        sf_lay.setSpacing(0)
        sf_lay.addWidget(self.stack)

        self.main_page = QWidget()
        mp = QVBoxLayout(self.main_page)
        mp.setContentsMargins(18, 14, 18, 16)
        mp.setSpacing(0)

        self.top_widget = QWidget()
        top = QHBoxLayout(self.top_widget)
        top.setContentsMargins(0, 0, 0, 10)
        top.setSpacing(8)

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
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self._open_settings)

        min_btn = QPushButton("—")
        min_btn.setObjectName("iconBtn")
        min_btn.setFixedSize(28, 28)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setCursor(Qt.PointingHandCursor)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.PointingHandCursor)

        top.addWidget(self.settings_btn)
        top.addWidget(min_btn)
        top.addWidget(close_btn)
        mp.addWidget(self.top_widget)

        self.dial = TimerDial(self)
        self.dial_box = AspectBox(self.dial)
        self.dial_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mp.addWidget(self.dial_box, 1)

        self.bottom_widget = QWidget()
        btn_row = QHBoxLayout(self.bottom_widget)
        btn_row.setContentsMargins(0, 16, 0, 8)
        btn_row.setSpacing(14)
        btn_row.addStretch()

        self.reset_icon = QPushButton("🔄")
        self.reset_icon.setObjectName("emojiBtn")
        self.reset_icon.setCursor(Qt.PointingHandCursor)
        self.reset_icon.clicked.connect(self._on_reset)

        self.start_icon = QPushButton("▶️")
        self.start_icon.setObjectName("emojiBtn")
        self.start_icon.setCursor(Qt.PointingHandCursor)
        self.start_icon.clicked.connect(self._on_start_pause)

        btn_row.addWidget(self.reset_icon)
        btn_row.addSpacing(4)
        btn_row.addWidget(self.start_icon)
        btn_row.addStretch()
        mp.addWidget(self.bottom_widget)
        self.stack.addWidget(self.main_page)

        self.mini_pin_btn = QPushButton("📌", self.surface)
        self.mini_pin_btn.setObjectName("pinBtn")
        self.mini_pin_btn.setCheckable(True)
        self.mini_pin_btn.setChecked(True)
        self.mini_pin_btn.setFixedSize(26, 26)
        self.mini_pin_btn.setCursor(Qt.PointingHandCursor)
        self.mini_pin_btn.move(14, 14)
        self.mini_pin_btn.hide()
        self.mini_pin_btn.clicked.connect(self._toggle_aot)

        self.settings_page = QWidget()
        sp_outer = QVBoxLayout(self.settings_page)
        sp_outer.setContentsMargins(0, 0, 0, 0)
        sp_outer.setSpacing(0)

        hdr = QHBoxLayout()
        hdr.setContentsMargins(18, 14, 18, 12)
        hdr.setSpacing(8)
        back_btn = QPushButton("← 뒤로")
        back_btn.setObjectName("backBtn")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._close_settings)
        title_lbl = QLabel("설정")
        title_lbl.setObjectName("title")
        hdr.addWidget(back_btn)
        hdr.addStretch()
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        sp_outer.addLayout(hdr)

        sep_frame = QFrame()
        sep_frame.setObjectName("separator")
        sep_frame.setFixedHeight(1)
        sp_outer.addWidget(sep_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_inner = SettingsPage()
        scroll.setWidget(self.settings_inner)
        sp_outer.addWidget(scroll, 1)
        self.stack.addWidget(self.settings_page)

        self.surface.installEventFilter(self)
        self.stack.installEventFilter(self)
        self.main_page.installEventFilter(self)
        self.setMouseTracking(True)
        self.surface.setMouseTracking(True)
        self.stack.setMouseTracking(True)
        self.main_page.setMouseTracking(True)
        self.settings_page.setMouseTracking(True)

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
            if lpos.y() < 50 or getattr(self, "_is_minimal_ui", False):
                self._drag_pos = gpos - self.frameGeometry().topLeft()
                self._mouse_press_pos = gpos
                return True

        elif event.type() == QEvent.MouseMove:
            gpos = event.globalPos()
            lpos = self.mapFromGlobal(gpos)
            if event.buttons() == Qt.NoButton:
                edge = self._edge(lpos)
                if edge:
                    self.setCursor(QCursor(self._CUR.get(edge, Qt.ArrowCursor)))
                else:
                    self.unsetCursor()
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
            if getattr(self, "_is_minimal_ui", False) and getattr(self, "_mouse_press_pos", None):
                dist = (event.globalPos() - self._mouse_press_pos).manhattanLength()
                if dist < 15:
                    if self._alerted:
                        self._dismiss_alert()
                    else:
                        self._on_start_pause()
            self._drag_pos = self._resize_edge = None
            self._resize_start_geo = self._resize_start_pos = self._mouse_press_pos = None

        return super().eventFilter(obj, event)

    def _check_theme(self):
        d = is_dark()
        if d != self._dark:
            self._dark = d
            self.theme = Theme(d)
            self._apply_theme()

    def _apply_theme(self):
        t = self.theme
        self.shadow.setColor(t.shadow)
        self.surface.setStyleSheet(t.qss())
        self.dial.set_theme(t)
        for sw in (
            getattr(self.settings_inner, "sound_toggle", None),
            getattr(self.settings_inner, "silent_toggle", None),
            getattr(self.settings_inner, "mode_toggle", None),
        ):
            if sw:
                sw.update()

    def _open_settings(self):
        self.settings_inner.build(
            self.sound_lib, self.theme,
            self.sound_enabled, self.silent_mode,
            self.selected_snd, self.mode_120,
            self._opacity,
        )
        self.surface.setStyleSheet(self.theme.qss())
        self.settings_inner.preview_btn.clicked.connect(self._preview)
        self.settings_inner.sound_toggle.toggled  = self._on_sound_toggle
        self.settings_inner.silent_toggle.toggled = self._on_silent_toggle
        self.settings_inner.mode_toggle.toggled   = self._on_mode_toggle
        self.settings_inner.sound_combo.currentTextChanged.connect(
            lambda n: setattr(self, "selected_snd", n)
        )
        self.settings_inner.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.stack.setCurrentIndex(1)

    def _on_opacity_changed(self, value):
        self._opacity = value / 100.0
        self.setWindowOpacity(self._opacity)
        lbl = getattr(self.settings_inner, "opacity_label", None)
        if lbl:
            lbl.setText(f"현재: {value}%")

    def _close_settings(self):
        self.stack.setCurrentIndex(0)

    def _on_sound_toggle(self, v):
        self.sound_enabled = v

    def _on_silent_toggle(self, v):
        self.silent_mode = v

    def _on_mode_toggle(self, v):
        self.mode_120 = v
        self.dial.set_max_minutes(120 if v else 60)

    def _play(self, name, loop: bool = False):
        """단발(preview) 또는 반복(알림) 재생."""
        if not self.sound_enabled:
            return
        path = self.sound_lib.path(name)
        if not path or not os.path.exists(path):
            return
        self.sound_fx.stop()
        self.sound_fx.setSource(QUrl.fromLocalFile(path))
        self.sound_fx.setVolume(0.85)
        self.sound_fx.setLoopCount(QSoundEffect.Infinite if loop else 1)
        self.sound_fx.play()

    def _preview(self):
        name = self.settings_inner.sound_combo.currentText()
        if self.silent_mode:
            self._flash_window(loop=False)
        else:
            self._play(name)

    def on_state_changed(self):
        self.start_icon.setText("⏸️" if self.dial.is_running else "▶️")

    def on_finished(self):
        self._alerted = True
        if self.silent_mode:
            self._flash_window(loop=True)
        else:
            self._play(self.selected_snd, loop=True)
        self.start_icon.setText("▶️")

    def _flash_window(self, loop: bool = False):
        self._flash_count = 0
        self._flash_loop  = loop
        if not hasattr(self, "_flash_tmr"):
            self._flash_tmr = QTimer(self)
            self._flash_tmr.timeout.connect(self._do_flash)
        self._flash_tmr.start(300)

    def _do_flash(self):
        self._flash_count += 1
        # loop=False(미리보기)는 3회 깜빡임 후 종료, loop=True(알림)는 클릭 전까지 지속
        if not self._flash_loop and self._flash_count > 6:
            self._flash_tmr.stop()
            self.surface.setStyleSheet(self.theme.qss())
            return
        if self._flash_count % 2 == 1:
            qss = self.theme.qss() + f"\nQFrame#surface {{ background: {ACCENT}; }}"
            self.surface.setStyleSheet(qss)
        else:
            self.surface.setStyleSheet(self.theme.qss())

    def _dismiss_alert(self):
        """알림(소리/깜빡임)을 중단하고 alerted 상태를 해제한다."""
        if not self._alerted:
            return
        self._alerted = False
        self.sound_fx.stop()
        if hasattr(self, "_flash_tmr") and self._flash_tmr.isActive():
            self._flash_loop = False
            self._flash_tmr.stop()
        self.surface.setStyleSheet(self.theme.qss())

    def _on_reset(self):
        self._dismiss_alert()
        self.dial.reset()

    def _on_start_pause(self):
        if self._alerted:
            self._dismiss_alert()
            return
        if self.dial.is_running:
            self.dial.pause()
        else:
            self.dial.start()
        self.on_state_changed()

    def _apply_aot(self):
        flags = self.windowFlags()
        if self.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _toggle_aot(self):
        sender = self.sender()
        if sender:
            self.always_on_top = sender.isChecked()
            self.pin_btn.setChecked(self.always_on_top)
            self.mini_pin_btn.setChecked(self.always_on_top)
        self._apply_aot()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        should_be_minimal = (w < self.NORMAL_MIN_WIDTH) or (h < self.NORMAL_MIN_HEIGHT)

        if should_be_minimal and not self._is_minimal_ui:
            self._is_minimal_ui = True
            self.top_widget.hide()
            self.bottom_widget.hide()
            self.dial.set_minimal(True)
            self.main_page.layout().setContentsMargins(4, 4, 4, 4)
            self.mini_pin_btn.show()

        elif not should_be_minimal and self._is_minimal_ui:
            self._is_minimal_ui = False
            self.top_widget.show()
            self.bottom_widget.show()
            self.dial.set_minimal(False)
            self.main_page.layout().setContentsMargins(18, 14, 18, 16)
            self.mini_pin_btn.hide()

        self._update_btn_sizes()

    def _update_btn_sizes(self):
        w = self.width()
        btn_sz  = max(36, min(72, int(w * 0.10)))
        font_sz = max(16, min(32, int(btn_sz * 0.50)))
        for btn in (self.reset_icon, self.start_icon):
            btn.setFixedSize(btn_sz, btn_sz)
            f = btn.font()
            f.setPixelSize(font_sz)
            btn.setFont(f)
            btn.setStyleSheet(f"border-radius:{btn_sz // 2}px; font-size:{font_sz}px;")

    def _edge(self, pos):
        m     = 6  if getattr(self, "_is_minimal_ui", False) else 18
        c_len = 24 if getattr(self, "_is_minimal_ui", False) else 44
        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        l, r, t, b = x <= m, x >= w - m, y <= m, y >= h - m
        if (l and y <= c_len) or (t and x <= c_len):         return "tl"
        if (r and y <= c_len) or (t and x >= w - c_len):     return "tr"
        if (l and y >= h - c_len) or (b and x <= c_len):     return "bl"
        if (r and y >= h - c_len) or (b and x >= w - c_len): return "br"
        if r: return "r"
        if l: return "l"
        if b: return "b"
        if t: return "t"
        return None

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        edge = self._edge(e.pos())
        if edge:
            self._resize_edge = edge
            self._resize_start_geo = self.geometry()
            self._resize_start_pos = e.globalPos()
        elif self._is_minimal_ui or e.pos().y() < 50:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            self._mouse_press_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.NoButton:
            edge = self._edge(e.pos())
            if edge:
                self.setCursor(QCursor(self._CUR.get(edge, Qt.ArrowCursor)))
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
            if "l" in ed: nw = max(mw, g.width() - d.x()); nx = g.x() + g.width() - nw
            if "t" in ed: nh = max(mh, g.height() - d.y()); ny = g.y() + g.height() - nh
            self.setGeometry(nx, ny, nw, nh)
        elif self._drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        if getattr(self, "_is_minimal_ui", False) and getattr(self, "_mouse_press_pos", None):
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
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    w = TimeTimerWindow()
    w.show()
    sys.exit(app.exec_())
