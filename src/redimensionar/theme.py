from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class LightColors:
    PRIMARY = "#004B87"
    PRIMARY_HOVER = "#003B6A"
    SUCCESS = "#00A86B"
    WARNING = "#F5A623"
    DANGER = "#E17055"

    BG = "#F1F4FB"
    BG_CARD = "#FFFFFF"
    BG_INPUT = "#F8FAFC"
    BG_HOVER = "#EDEEF0"
    BORDER = "#94A3B8"
    BORDER_CARD = "#CBD5E1"
    BORDER_FOCUS = "#004B87"

    TEXT = "#1E293B"
    TEXT_SECONDARY = "#8A94A6"
    TEXT_DISABLED = "#B2BEC3"
    TEXT_LINK = "#004B87"

    STAGE_BG = "#181B1F"
    PROGRESS_TRACK = "#EAEAEA"


class DarkColors:
    PRIMARY = "#3B82F6"
    PRIMARY_HOVER = "#2563EB"
    SUCCESS = "#00A86B"
    WARNING = "#F5A623"
    DANGER = "#EF4444"

    BG = "#2D2F34"
    BG_CARD = "#383B40"
    BG_INPUT = "#404348"
    BG_HOVER = "#464950"
    BORDER = "#555860"
    BORDER_CARD = "#555860"
    BORDER_FOCUS = "#3B82F6"

    TEXT = "#E8E8EB"
    TEXT_SECONDARY = "#A1A5B0"
    TEXT_DISABLED = "#6B6E76"
    TEXT_LINK = "#60A5FA"

    STAGE_BG = "#1A1C20"
    PROGRESS_TRACK = "#404348"


def _build_qss(C):
    return f"""
        QMainWindow, QWidget {{
            background-color: {C.BG};
            color: {C.TEXT};
            font-family: "Segoe UI", "Segoe UI Variable Display", sans-serif;
            font-size: 10pt;
        }}

        QLabel {{
            color: {C.TEXT};
        }}
        QLabel#sectionTitle {{
            font-size: 9pt;
            font-weight: 700;
            text-transform: uppercase;
            color: {C.TEXT_SECONDARY};
        }}
        QLabel#statusLabel {{
            font-size: 9pt;
            color: {C.TEXT_SECONDARY};
        }}

        QFrame#stage {{
            background-color: {C.STAGE_BG};
            border-radius: 8px;
            border: none;
        }}
        QFrame#card {{
            background-color: {C.BG_CARD};
            border: 1px solid {C.BORDER_CARD};
            border-radius: 8px;
        }}

        QPushButton {{
            background: {C.BG_CARD};
            color: {C.TEXT};
            border: 1px solid {C.BORDER};
            border-radius: 4px;
            padding: 6px 14px;
            font-size: 10pt;
        }}
        QPushButton:hover {{
            background: {C.BG_HOVER};
            border-color: {C.BORDER_FOCUS};
        }}
        QPushButton:pressed {{
            background: {C.PRIMARY};
            color: white;
        }}
        QPushButton:disabled {{
            background: {C.BG};
            color: {C.TEXT_DISABLED};
            border-color: {C.BORDER};
        }}

        QPushButton#btnSelecionar {{
            background: transparent;
            color: {C.PRIMARY};
            border: 1px solid {C.PRIMARY};
            border-radius: 4px;
            padding: 6px 14px;
            font-size: 10pt;
        }}
        QPushButton#btnSelecionar:hover {{
            background: {C.PRIMARY};
            color: white;
        }}
        QPushButton#btnSelecionar:disabled {{
            background: transparent;
            color: {C.TEXT_DISABLED};
            border-color: {C.BORDER};
        }}

        QPushButton#btnProcessar {{
            background: {C.PRIMARY};
            color: white;
            font-weight: 700;
            font-size: 10pt;
            border: none;
            border-radius: 6px;
            padding: 0;
            min-height: 48px;
        }}
        QPushButton#btnProcessar:hover {{
            background: {C.PRIMARY_HOVER};
        }}
        QPushButton#btnProcessar:disabled {{
            background: {C.BORDER};
            color: {C.TEXT_DISABLED};
        }}

        QPushButton#btnNav {{
            background: transparent;
            border: 1px solid {C.BORDER};
            border-radius: 4px;
            padding: 4px 12px;
            font-size: 13px;
        }}
        QPushButton#btnNav:hover {{
            background: {C.BG_HOVER};
            border-color: {C.BORDER_FOCUS};
        }}

        QFrame#navFrame {{
            border: 1px solid {C.BORDER_CARD};
            border-radius: 4px;
            padding: 4px;
        }}

        QProgressBar {{
            border: none;
            border-radius: 4px;
            background: {C.PROGRESS_TRACK};
            min-height: 8px;
            max-height: 8px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {C.PRIMARY}, stop:1 {C.SUCCESS});
            border-radius: 4px;
        }}

        QRadioButton {{
            color: {C.TEXT};
            spacing: 8px;
            padding: 2px 0;
            font-size: 10pt;
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 2px solid {C.BORDER};
            background: {C.BG_INPUT};
        }}
        QRadioButton::indicator:checked {{
            background: {C.PRIMARY};
            border-color: {C.PRIMARY};
        }}
        QRadioButton::indicator:hover {{
            border-color: {C.BORDER_FOCUS};
        }}

        QCheckBox {{
            color: {C.TEXT};
            spacing: 8px;
            padding: 2px 0;
            font-size: 10pt;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 2px solid {C.BORDER};
            background: {C.BG_INPUT};
        }}
        QCheckBox::indicator:checked {{
            background: {C.PRIMARY};
            border-color: {C.PRIMARY};
        }}
        QCheckBox::indicator:hover {{
            border-color: {C.BORDER_FOCUS};
        }}

        QLineEdit {{
            background: {C.BG_INPUT};
            color: {C.TEXT};
            border: 1px solid {C.BORDER};
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 10pt;
            min-height: 28px;
            selection-background-color: {C.PRIMARY};
            selection-color: white;
        }}
        QLineEdit:focus {{
            border-color: {C.BORDER_FOCUS};
        }}
        QLineEdit:disabled {{
            background: {C.BG};
            color: {C.TEXT_DISABLED};
        }}

        QSlider::groove:horizontal {{
            background: {C.BORDER};
            height: 4px;
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {C.PRIMARY};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {C.PRIMARY_HOVER};
            width: 20px;
            height: 20px;
            margin: -8px 0;
        }}
        QSlider::sub-page:horizontal {{
            background: {C.PRIMARY};
            border-radius: 2px;
        }}

        QLabel#escalaVal {{
            font-weight: 700;
            color: {C.PRIMARY};
            font-size: 10pt;
        }}

        QMenuBar {{
            background: {C.BG_CARD};
            color: {C.TEXT};
            border-bottom: 1px solid {C.BORDER_CARD};
            font-size: 10pt;
            padding: 2px;
        }}
        QMenuBar::item {{
            padding: 4px 12px;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background: {C.BG_HOVER};
        }}

        QMenu {{
            background: {C.BG_CARD};
            color: {C.TEXT};
            border: 1px solid {C.BORDER};
            border-radius: 6px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 28px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background: {C.PRIMARY};
            color: white;
        }}
        QMenu::separator {{
            height: 1px;
            background: {C.BORDER};
            margin: 4px 10px;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {C.BORDER};
            min-height: 30px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {C.TEXT_SECONDARY};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar:horizontal {{
            background: transparent;
            height: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal {{
            background: {C.BORDER};
            min-width: 30px;
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {C.TEXT_SECONDARY};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        QToolTip {{
            background: {C.BG_CARD};
            color: {C.TEXT};
            border: 1px solid {C.PRIMARY};
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 10pt;
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}

        QFrame#separator {{
            border: none;
            background: {C.BORDER_CARD};
            min-height: 1px;
            max-height: 1px;
        }}
    """


_current_dark = False


def is_dark():
    return _current_dark


def aplicar_tema(app: QApplication, dark: bool = False):
    global _current_dark
    _current_dark = dark

    C = DarkColors if dark else LightColors

    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(C.BG))
    palette.setColor(QPalette.WindowText, QColor(C.TEXT))
    palette.setColor(QPalette.Base, QColor(C.BG_INPUT))
    palette.setColor(QPalette.AlternateBase, QColor(C.BG_CARD))
    palette.setColor(QPalette.ToolTipBase, QColor(C.BG_CARD))
    palette.setColor(QPalette.ToolTipText, QColor(C.TEXT))
    palette.setColor(QPalette.Text, QColor(C.TEXT))
    palette.setColor(QPalette.Button, QColor(C.BG_CARD))
    palette.setColor(QPalette.ButtonText, QColor(C.TEXT))
    palette.setColor(QPalette.BrightText, QColor("white"))
    palette.setColor(QPalette.Link, QColor(C.TEXT_LINK))
    palette.setColor(QPalette.Highlight, QColor(C.BORDER_FOCUS))
    palette.setColor(QPalette.HighlightedText, QColor("white"))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(C.TEXT_DISABLED))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(C.TEXT_DISABLED))
    app.setPalette(palette)

    app.setStyleSheet(_build_qss(C))
