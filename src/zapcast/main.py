import logging
import sys

from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from zapcast.emoji_picker import EmojiStore
from zapcast.settings import load_settings

logger = logging.getLogger(__name__)


class ToastWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "background-color: rgba(50, 50, 50, 200); color: white; "
            "padding: 8px 16px; border-radius: 8px; font-size: 14px;"
        )
        self.hide()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

        self._fade_in = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_in.setDuration(150)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)

        self._fade_out = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_out.setDuration(300)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.finished.connect(self.hide)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out.start)

    def show_message(self, message: str, duration: int = 1000):
        self.setText(message)
        self.adjustSize()
        if self.parentWidget():
            parent_rect = self.parentWidget().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - 20
            self.move(x, y)
        self._fade_out.stop()
        self._timer.stop()
        self.show()
        self._fade_in.start()
        self._timer.start(duration)


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing
        self._items: list = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def spacing(self):
        return self._spacing if self._spacing >= 0 else 5

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._items:
            item_size = item.sizeHint()
            next_x = x + item_size.width() + spacing

            if next_x - spacing > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + spacing
                next_x = x + item_size.width() + spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x = next_x
            line_height = max(line_height, item_size.height())

        return y + line_height - rect.y()


class EmojiButton(QPushButton):
    def __init__(self, emoji: str, name: str = "", parent=None):
        super().__init__(emoji, parent)
        self.emoji = emoji
        self.setFixedSize(50, 50)
        self.setStyleSheet(
            "QPushButton { font-size: 24px; border: none; background: transparent; }"
            "QPushButton:hover { background: palette(midlight); border-radius: 5px; }"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if name:
            self.setToolTip(name)


class CategorySection(QWidget):
    def __init__(self, category_name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(5)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        label = QLabel(category_name)
        label.setStyleSheet("font-weight: bold; font-size: 11px; color: palette(text);")

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        header_layout.addWidget(label)
        header_layout.addWidget(line)
        layout.addLayout(header_layout)

        self.emoji_container = QWidget()
        self.flow_layout = FlowLayout(self.emoji_container, margin=0, spacing=2)
        layout.addWidget(self.emoji_container)

    def add_emoji(self, emoji: str, name: str, callback):
        btn = EmojiButton(emoji, name)
        btn.clicked.connect(lambda: callback(emoji))
        self.flow_layout.addWidget(btn)


class EmojiPicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.emoji_store = EmojiStore()
        self.search_bar: QLineEdit | None = None
        self.scroll_area: QScrollArea | None = None
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._pending_query: str = ""
        self._all_emojis_widget: QWidget | None = None
        self._search_results_widget: QWidget | None = None
        self._showing_all = True
        self._toast: ToastWidget | None = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("zapcast")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search emojis...")
        self.search_bar.textChanged.connect(self.filter_emojis)
        self.search_bar.setClearButtonEnabled(True)
        layout.addWidget(self.search_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        layout.addWidget(self.scroll_area)

        self._toast = ToastWidget(central_widget)

        QTimer.singleShot(0, self.load_emojis)

    def load_emojis(self):
        self.emoji_store.load()
        self._build_all_emojis_widget()
        self.scroll_area.setWidget(self._all_emojis_widget)

    def _build_all_emojis_widget(self):
        self._all_emojis_widget = QWidget()
        layout = QVBoxLayout(self._all_emojis_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        grouped = self.emoji_store.get_grouped_emojis()
        current_section: CategorySection | None = None
        for item in grouped:
            if item.is_category_header:
                current_section = CategorySection(item.category_name)
                layout.addWidget(current_section)
            elif current_section:
                current_section.add_emoji(item.char, item.name, self.copy_emoji)

        layout.addStretch()

    def _show_all_emojis(self):
        if self._showing_all:
            return
        old = self.scroll_area.takeWidget()
        if old and old is not self._all_emojis_widget:
            old.deleteLater()
        self.scroll_area.setWidget(self._all_emojis_widget)
        self._showing_all = True

    def _show_search_results(self, query: str):
        old = self.scroll_area.takeWidget()
        if old and old is not self._all_emojis_widget:
            old.deleteLater()
        import time

        logger.debug(f"Search term: {query}")
        start = time.perf_counter()
        grouped = self.emoji_store.search_grouped(query, limit=1000)
        end = time.perf_counter()
        duration = (end - start) * 1000
        logger.debug(f"Duration {duration} ms")

        self._search_results_widget = QWidget()
        layout = QVBoxLayout(self._search_results_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        current_section: CategorySection | None = None
        for item in grouped:
            if item.is_category_header:
                current_section = CategorySection(item.category_name)
                layout.addWidget(current_section)
            elif current_section:
                current_section.add_emoji(item.char, item.name, self.copy_emoji)

        layout.addStretch()
        self.scroll_area.setWidget(self._search_results_widget)
        self._showing_all = False

    def filter_emojis(self, query: str) -> None:
        self._pending_query = query
        self._search_timer.start(75)

    def _do_search(self) -> None:
        if self._pending_query:
            self._show_search_results(self._pending_query)
        else:
            self._show_all_emojis()

    def copy_emoji(self, emoji: str) -> None:
        logger.debug(f"Copying emoji to clipboard: {emoji}")
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(emoji)
        if self._toast:
            self._toast.show_message(f"{emoji} copied!")


def main() -> None:
    load_settings()

    app = QApplication(sys.argv)
    window = EmojiPicker()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
