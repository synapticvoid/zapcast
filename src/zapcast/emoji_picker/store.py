from __future__ import annotations

import logging
from dataclasses import dataclass

from emoji import EMOJI_DATA  # ty:ignore[unresolved-import]
from rapidfuzz import fuzz, process

from zapcast.emoji_picker.emoji_categories import EMOJI_CATEGORIES

logger = logging.getLogger(__name__)

CATEGORY_ORDER = [
    "Smileys & Emotion",
    "People & Body",
    "Animals & Nature",
    "Food & Drink",
    "Travel & Places",
    "Activities",
    "Objects",
    "Symbols",
    "Flags",
]


@dataclass
class EmojiItem:
    char: str
    name: str = ""
    is_category_header: bool = False
    category_name: str = ""


class EmojiStore:
    def __init__(self):
        self.search_texts: list[str] = []
        self.emoji_chars: list[str] = []
        self.emoji_categories: dict[str, str] = {}
        self.emoji_names: dict[str, str] = {}

    def load(self) -> set[str]:
        logger.info("Loading emojis...")
        seen_emojis = set[str]()
        for emoji_char, data in EMOJI_DATA.items():
            primary_name = _clean_name(data["en"])
            self.search_texts.append(primary_name)
            self.emoji_chars.append(emoji_char)

            category = self._get_category(emoji_char)
            self.emoji_categories[emoji_char] = category
            self.emoji_names[emoji_char] = primary_name

            if "alias" in data:
                for alias in data["alias"]:
                    alias_name = _clean_name(alias)
                    self.search_texts.append(alias_name)
                    self.emoji_chars.append(emoji_char)

            if emoji_char not in seen_emojis:
                seen_emojis.add(emoji_char)

        logger.info("Loaded %d emojis", len(seen_emojis))
        return seen_emojis

    def _get_category(self, emoji_char: str) -> str:
        return EMOJI_CATEGORIES.get(emoji_char, "Other")

    def get_grouped_emojis(self) -> list[EmojiItem]:
        seen: set[str] = set()
        unique_emojis: list[str] = []
        for emoji_char in self.emoji_chars:
            if emoji_char not in seen:
                seen.add(emoji_char)
                unique_emojis.append(emoji_char)

        categorized: dict[str, list[str]] = {cat: [] for cat in CATEGORY_ORDER}
        categorized["Other"] = []

        for emoji_char in unique_emojis:
            category = self.emoji_categories.get(emoji_char, "Other")
            if category in categorized:
                categorized[category].append(emoji_char)
            else:
                categorized["Other"].append(emoji_char)

        items: list[EmojiItem] = []
        for category in CATEGORY_ORDER:
            emojis_list = categorized[category]
            if emojis_list:
                items.append(
                    EmojiItem(char="", is_category_header=True, category_name=category)
                )
                for emoji_char in emojis_list:
                    name = self.emoji_names.get(emoji_char, "")
                    items.append(EmojiItem(char=emoji_char, name=name))

        if categorized["Other"]:
            items.append(
                EmojiItem(char="", is_category_header=True, category_name="Other")
            )
            for emoji_char in categorized["Other"]:
                name = self.emoji_names.get(emoji_char, "")
                items.append(EmojiItem(char=emoji_char, name=name))

        return items

    def search(self, query: str, limit: int = 100) -> list[str]:
        if not query:
            return []

        query_lower = query.lower().strip()

        if len(query_lower) <= 2:
            matched_indices = [
                i
                for i, search_text in enumerate(self.search_texts)
                if query_lower in search_text
            ]
            seen: dict[str, None] = {}
            for idx in matched_indices:
                emoji_char = self.emoji_chars[idx]
                if emoji_char not in seen:
                    seen[emoji_char] = None
                    if len(seen) >= limit:
                        break
            return list(seen.keys())

        candidates: list[tuple[str, int]] = [
            (text, i)
            for i, text in enumerate(self.search_texts)
            if query_lower[0] in text or query_lower[:2] in text
        ]

        if not candidates:
            return []

        results = process.extract(
            query_lower,
            [c[0] for c in candidates],
            scorer=fuzz.WRatio,
            limit=limit * 2,
            score_cutoff=50,
        )

        seen_emojis: dict[str, None] = {}
        for _, _, idx in results:
            emoji_char = self.emoji_chars[candidates[idx][1]]
            if emoji_char not in seen_emojis:
                seen_emojis[emoji_char] = None
                if len(seen_emojis) >= limit:
                    break

        return list(seen_emojis.keys())

    def search_grouped(self, query: str, limit: int = 100) -> list[EmojiItem]:
        matching_emojis = self.search(query, limit)
        if not matching_emojis:
            return []

        categorized: dict[str, list[str]] = {cat: [] for cat in CATEGORY_ORDER}
        categorized["Other"] = []

        for emoji_char in matching_emojis:
            category = self.emoji_categories.get(emoji_char, "Other")
            if category in categorized:
                categorized[category].append(emoji_char)
            else:
                categorized["Other"].append(emoji_char)

        items: list[EmojiItem] = []
        for category in CATEGORY_ORDER:
            emojis_list = categorized[category]
            if emojis_list:
                items.append(
                    EmojiItem(char="", is_category_header=True, category_name=category)
                )
                for emoji_char in emojis_list:
                    name = self.emoji_names.get(emoji_char, "")
                    items.append(EmojiItem(char=emoji_char, name=name))

        if categorized["Other"]:
            items.append(
                EmojiItem(char="", is_category_header=True, category_name="Other")
            )
            for emoji_char in categorized["Other"]:
                name = self.emoji_names.get(emoji_char, "")
                items.append(EmojiItem(char=emoji_char, name=name))

        return items


def _clean_name(name: str) -> str:
    return name.strip(":").replace("_", " ").lower()
