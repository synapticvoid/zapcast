from __future__ import annotations

import logging

from PySide6.QtCore import QAbstractListModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QFont

from .store import EmojiItem, EmojiStore

logger = logging.getLogger(__name__)


class EmojiListModel(QAbstractListModel):
    IsCategoryHeaderRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, store: EmojiStore, parent=None):
        super().__init__(parent)
        self.store = store
        self.items: list[EmojiItem] = []
        self.show_all()

    def show_all(self):
        self.beginResetModel()
        self.items = self.store.get_grouped_emojis()
        self.endResetModel()

    def filter_emojis(self, query: str):
        if not query:
            self.show_all()
            return
        self.beginResetModel()
        results = self.store.search(query, limit=1000)
        self.items = [EmojiItem(char=e) for e in results]
        self.endResetModel()

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        if parent.isValid():
            return 0
        return len(self.items)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if not index.isValid() or index.row() >= len(self.items):
            return None

        item = self.items[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            if item.is_category_header:
                return item.category_name
            return item.char
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            if item.is_category_header:
                font.setPointSize(10)
                font.setBold(True)
            else:
                font.setPointSize(24)
            return font
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if item.is_category_header:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignCenter
        elif role == self.IsCategoryHeaderRole:
            return item.is_category_header

        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        item = self.items[index.row()]
        if item.is_category_header:
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
