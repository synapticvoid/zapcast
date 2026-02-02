# AGENTS.md

## Environment
- Virtual environment: `.venv/` (managed by `uv`)
- Activate with: `source .venv/bin/activate`

## Commands
- **Format/Lint**: `make ruff`
- **Run app**: `uv run python -m zapcast.main`
- **Type check**: `ty check src/` (uses ty type checker)
- No tests exist yet

## Architecture
- **zapcast**: PySide6 (Qt) emoji picker desktop app
- `src/zapcast/main.py`: Qt GUI with EmojiPicker window, FlowLayout, EmojiButton
- `src/zapcast/emojis.py`: EmojiStore for loading/searching emojis using rapidfuzz
- `src/zapcast/settings.py`: Logging configuration

## Code Style
- Python 3.14+, uses `uv` for package management
- Imports: stdlib → third-party (PySide6, emoji, rapidfuzz) → local
- Type hints required (uses `ty` type checker with `ty:ignore` for untyped libs)
- Use dataclasses for data structures
- Logging via `logging.getLogger(__name__)`
- No trailing commas required; use ruff for formatting
