import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor, QFont, QFontDatabase
from PyQt5.QtGui import QPalette

ACCENT       = "#f05650"
ACCENT_HOVER = "#f37370"
ACCENT_PRESS = "#c94440"


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


def is_dark() -> bool:
    app = QApplication.instance()
    if not app:
        return False
    bg = app.palette().color(QPalette.Window)
    return (0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()) < 128


class Theme:
    RED       = QColor(0xf0, 0x56, 0x50)
    RED_LIGHT = QColor(0xf0, 0x56, 0x50, 45)
    RED_HAND  = QColor(0xf0, 0x56, 0x50)

    def __init__(self, dark: bool):
        self.dark = dark
        if dark:
            self.bg             = QColor(28, 28, 30)
            self.surface        = QColor(36, 36, 40)
            self.surface_border = QColor(55, 55, 60)
            self.shadow         = QColor(0, 0, 0, 130)

            self.dial_face      = QColor(44, 44, 48)
            self.dial_ring      = QColor(65, 65, 72)
            self.dial_track     = QColor(55, 55, 62)
            self.tick_major     = QColor(160, 160, 168)
            self.tick_minor     = QColor(80, 80, 90)
            self.number_col     = QColor(160, 160, 168)

            self.time_col       = QColor(0xD0, 0xD0, 0xD8)
            self.status_col     = QColor(110, 110, 120)
            self.hand_dot       = QColor(65, 65, 72)

            self.title_hex      = "#c8c8d0"
            self.subtitle_hex   = "#88888e"
            self.btn_bg         = "#2c2c32"
            self.btn_border     = "#46464e"
            self.btn_fg         = "#d0d0d8"
            self.btn_hover      = "#38383e"
            self.btn_press      = "#202026"
            self.input_bg       = "#26262c"
            self.input_border   = "#42424a"
            self.sep_col        = "#3a3a42"
            self.toggle_off_bg  = "#3a3a42"
            self.toggle_off_knob = "#888890"
        else:
            self.bg             = QColor(245, 245, 247)
            self.surface        = QColor(252, 252, 254)
            self.surface_border = QColor(218, 218, 224)
            self.shadow         = QColor(0, 0, 0, 70)

            self.dial_face      = QColor(255, 255, 255)
            self.dial_ring      = QColor(215, 215, 222)
            self.dial_track     = QColor(240, 240, 244)
            self.tick_major     = QColor(160, 160, 170)
            self.tick_minor     = QColor(200, 200, 208)
            self.number_col     = QColor(140, 140, 150)

            self.time_col       = QColor(0x20, 0x21, 0x23)
            self.status_col     = QColor(170, 170, 178)
            self.hand_dot       = QColor(215, 215, 222)

            self.title_hex      = "#202123"
            self.subtitle_hex   = "#888892"
            self.btn_bg         = "#ffffff"
            self.btn_border     = "#e0e0e6"
            self.btn_fg         = "#202123"
            self.btn_hover      = "#f4f4f8"
            self.btn_press      = "#e8e8ee"
            self.input_bg       = "#ffffff"
            self.input_border   = "#dcdce2"
            self.sep_col        = "#e8e8ee"
            self.toggle_off_bg  = "#d8d8de"
            self.toggle_off_knob = "#ffffff"

    def qss(self) -> str:
        d = self.dark
        surface    = "#242428" if d else "#fcfcfe"
        border     = "#363640" if d else "#dadae0"
        title      = self.title_hex
        sub        = self.subtitle_hex
        btn_bg     = self.btn_bg
        btn_bd     = self.btn_border
        btn_fg     = self.btn_fg
        btn_hv     = self.btn_hover
        btn_pr     = self.btn_press
        inp_bg     = self.input_bg
        inp_bd     = self.input_border
        sep        = self.sep_col
        arr_col    = "#aaaaaa" if d else "#888892"
        combo_vw   = "#26262c" if d else "#ffffff"
        combo_sel  = "#3a1010" if d else "#fde8e8"
        combo_selc = "#f87171" if d else ACCENT

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
