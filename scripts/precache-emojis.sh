#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="$PROJECT_ROOT/src/zapcast/emoji_picker/emoji_categories.py"

cd "$PROJECT_ROOT"

uv run python -c "
import emojis.db as emojis_db
from emoji import EMOJI_DATA

categories = {}
for emoji_char in EMOJI_DATA.keys():
    try:
        emoji_info = emojis_db.get_emoji_by_code(emoji_char)
        if emoji_info and emoji_info.category:
            categories[emoji_char] = emoji_info.category
        else:
            categories[emoji_char] = 'Other'
    except Exception:
        categories[emoji_char] = 'Other'

print('EMOJI_CATEGORIES: dict[str, str] = {')
for char, cat in categories.items():
    print(f'    {char!r}: {cat!r},')
print('}')
" > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE with $(grep -c ':' "$OUTPUT_FILE") entries"
