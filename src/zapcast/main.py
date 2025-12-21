import logging
import sys
from json import load

from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from zapcast.settings import load_settings, setup_logging

logger = logging.getLogger(__name__)


class EmojiPicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.search_bar: QLineEdit | None = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("zapcast")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search emojis...")
        layout.addWidget(self.search_bar)

        # Emoji grid
        emoji_widget = QWidget()
        self.emoji_layout = QGridLayout(emoji_widget)
        layout.addWidget(emoji_widget)

        self.load_emojis()

    def load_emojis(self):
        emojis = [
            "😀",
            "😃",
            "😄",
            "😁",
            "😅",
            "😂",
            "🤣",
            "😊",
            "😇",
            "🙂",
            "🙃",
            "😉",
            "😌",
            "😍",
            "🥰",
            "😘",
            "👍",
            "👎",
            "👋",
            "🤝",
            "🙏",
            "✌️",
            "🤞",
            "🤘",
        ]

        row, col = 0, 0
        for emoji in emojis:
            btn = QPushButton(emoji)
            btn.setFixedSize(50, 50)
            btn.setStyleSheet("font-size: 24px;")
            btn.clicked.connect(lambda checked, e=emoji: self.copy_emoji(e))
            self.emoji_layout.addWidget(btn, row, col)

            col += 1
            if col > 7:  # 8 columns
                col = 0
                row += 1

    def copy_emoji(self, emoji: str) -> None:
        logger.debug(f"Copying emoji to clipboard: {emoji}")
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(emoji)
        # self.close()


def main() -> None:
    load_settings()

    app = QApplication(sys.argv)
    window = EmojiPicker()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
