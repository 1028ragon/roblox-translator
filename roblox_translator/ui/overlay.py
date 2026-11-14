"""게임 위에 표시하는 클릭 통과 자막 창."""

import html
import time

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..config import (
    BOTTOM_MARGIN_PX,
    FONT_SIZE_PX,
    LINE_TTL_SEC,
    MAX_LINES,
    SHOW_ORIGINAL,
)


class Bridge(QObject):
    # 원문, 번역문, 확정 여부
    text = Signal(str, str, bool)


class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput  # 클릭이 게임으로 통과
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        screen = QGuiApplication.primaryScreen().geometry()
        self._screen = screen
        self.setFixedWidth(int(screen.width() * 0.6))

        self.label = QLabel("")
        self.label.setTextFormat(Qt.RichText)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            f"color: white; font-size: {FONT_SIZE_PX}px; font-weight: bold;"
            "background-color: rgba(0, 0, 0, 160); padding: 10px 18px;"
            "border-radius: 10px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self.finals = []      # [(원문, 번역, 만료시각), ...]
        self.partial = None   # (원문, 번역)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._prune)
        self.timer.start(500)

    def on_text(self, original, translated, is_final):
        if is_final:
            self.finals.append((original, translated, time.time() + LINE_TTL_SEC))
            self.finals = self.finals[-MAX_LINES:]
            self.partial = None
        else:
            self.partial = (original, translated)
        self._render()

    def _prune(self):
        now = time.time()
        before = len(self.finals)
        self.finals = [f for f in self.finals if f[2] > now]
        if len(self.finals) != before:
            self._render()

    def _line_html(self, original, translated, dim=False):
        color = "#bbbbbb" if dim else "#ffffff"
        s = f'<span style="color:{color}">{html.escape(translated)}</span>'
        if SHOW_ORIGINAL and original:
            s += (
                f'<br><span style="font-size:{int(FONT_SIZE_PX * 0.6)}px;'
                f'color:#9aa0a6;font-weight:normal">{html.escape(original)}</span>'
            )
        return s

    def _render(self):
        parts = [self._line_html(o, t) for o, t, _ in self.finals]
        if self.partial:
            parts.append(self._line_html(self.partial[0], self.partial[1], dim=True))
        if not parts:
            self.hide()
            return
        self.label.setText("<br>".join(parts))
        self.adjustSize()
        x = self._screen.x() + (self._screen.width() - self.width()) // 2
        y = self._screen.y() + self._screen.height() - self.height() - BOTTOM_MARGIN_PX
        self.move(x, y)
        self.show()
