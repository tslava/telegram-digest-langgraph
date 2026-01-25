# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daily Telegram chat digest generator using LangGraph and Telethon. Reads messages from configured chats, extracts structured highlights (decisions, todos, questions, links, events, risks) via an LLM workflow, and posts summaries to a private Telegram channel. Deployed via systemd timer on Linux servers.

## Build & Development Commands

```bash
# Install dependencies (requires uv and Python 3.12+)
uv sync --dev

# Initialize database
uv run tg-digest init-db

# Telegram login (interactive, one-time per machine)
uv run tg-digest telegram-login

# Manage chats (--chat-id accepts numeric ID, @username, or t.me link)
uv run tg-digest add-chat --chat-id @channel_name --target-channel-id -100456
uv run tg-digest add-chat --chat-id "https://t.me/+inviteHash" --target-channel-id -100456
uv run tg-digest add-chat --chat-id -1001234567890 --target-channel-id -100456
uv run tg-digest list-chats
uv run tg-digest disable-chat --chat-id 123

# Run digests
uv run tg-digest run-all --dry-run 1
uv run tg-digest run-one --chat-id 123

# Fixture mode (no Telegram needed)
LLM_MODE=stub uv run tg-digest run-from-fixture --in fixtures/sample_messages.json --dry-run 1
uv run tg-digest record-fixture --chat-id 123 --hours 24 --out fixtures/my_chat.json

# Linting and testing
ruff check app/ tests/
ruff format app/ tests/
mypy app/
pytest
```

## Architecture

### LangGraph State Machine (app/graph/)

The digest pipeline is a 10-node LangGraph state machine defined in `app/graph/build.py`:

```
fetch_messages → [route_empty] → preprocess → extract_map → reduce_dedupe → validate → format → compute_hash → publish → persist
                      ↓
                 empty_digest ───────────────────────────────────────────────────────→ format
```

- **fetch_messages**: Reads from Telethon or fixture
- **route_empty**: Conditional branch for empty vs non-empty message sets
- **preprocess**: Filters and chunks messages (CHUNK_SIZE=20)
- **extract_map**: LLM call per chunk (or stub mode)
- **reduce_dedupe**: Merges and deduplicates across chunks
- **validate**: Pydantic schema validation with one retry
- **format**: HTML output for Telegram (includes clickable message links)
- **compute_hash**: SHA256 for deduplication
- **publish**: Posts to channel (skips if hash matches last run)
- **persist**: Saves digest record and updates cursor

### Key Components

- **app/cli.py**: Entry point (`tg-digest` command), all CLI subcommands
- **app/config.py**: Pydantic Settings, env var handling with `@lru_cache`
- **app/db/**: SQLite layer (schema.sql, repositories.py, migrate.py)
- **app/domain/models.py**: ChatConfig, ChatState, DigestRecord, Window, NormalizedMessage
- **app/domain/digest_schema.py**: Pydantic models for digest output (DigestPayload, DigestItem, Evidence)
- **app/llm/**: Prompts and LLM calls (extract.py, reduce.py, prompts.py, emoji.py)
- **app/tools/telegram_fetch.py**: Telethon client for reading messages
- **app/tools/telegram_resolve.py**: Resolves usernames/links to numeric chat IDs, fetches channel descriptions
- **app/tools/telegram_post.py**: Bot API for posting digests
- **app/runner/**: Orchestrates single chat (run_one.py) and all chats (run_all.py)

### Database (SQLite)

Three tables in `app/db/schema.sql`:
- **chat_configs**: Per-chat settings (window mode, limits, language, timezone)
- **chat_state**: Cursor tracking (last_message_id, last_digest_hash, status)
- **digests**: History with JSON payload and rendered text

### LLM Modes

- `LLM_MODE=openai`: Uses OpenAI API (default model: gpt-4o-mini)
- `LLM_MODE=stub`: Deterministic extractor for testing (no API calls)

## Environment Variables

Required:
- `TG_API_ID`, `TG_API_HASH`: Telegram user API credentials (my.telegram.org)
- `TG_BOT_TOKEN`: Bot token from @BotFather
- `TG_TARGET_CHANNEL_ID`: Private channel ID (format: -1001234567890)
- `OPENAI_API_KEY`: OpenAI API key

Optional:
- `OPENAI_MODEL`: Model name (default: gpt-4o-mini)
- `DB_PATH`: SQLite path (default: ./.local/app.db)
- `TELETHON_SESSION`: Session file path (default: ./.local/telethon.session)
- `DRY_RUN`: 1 to skip posting
- `LLM_MODE`: openai or stub

## Deployment

Server deployment uses systemd (see `deploy/`):
- **bootstrap_server.sh**: Creates user, installs Python/uv
- **install_app.sh**: Clones repo, installs deps, enables timer
- **smoke_test.sh**: Verifies app runs
- GitHub Actions auto-deploys on push to main

## Code Conventions

- Ruff linting: 100-char lines, rules E/F/I/UP/B/SIM/PIE
- Type hints required (mypy)
- LangGraph state uses TypedDict (not dataclasses)
- Async only for Telethon login; rest is sync

## Formatters (app/formatters/)

- **telegram_render.py**: Renders digest payload to HTML for Telegram
  - `_build_message_link(chat_id, message_id)`: Builds `https://t.me/c/{channel_id}/{message_id}` deep links for supergroups/channels (chat IDs with `-100` prefix); returns `None` for regular groups
  - Message IDs in evidence are rendered as clickable `<a href="...">` links when possible

## Emoji Selection (app/llm/emoji.py)

Auto-selects an emoji for chat titles when adding chats via `add-chat`:

- **`select_emoji(title, about, settings)`**: Main entry point
- **Stub mode** (`LLM_MODE=stub`): Keyword-based matching (80+ keywords mapped to emojis)
- **LLM mode**: Uses OpenAI to select contextually appropriate emoji
- **Fallback**: If LLM fails or no API key, falls back to stub mode
- **Edge cases**:
  - Returns empty string if title already starts with emoji
  - Skipped when user provides `--title` flag (user has full control)
  - Skipped for numeric chat IDs without resolution (no context)

The `ResolvedChat` dataclass includes an `about` field populated via Telethon's `GetFullChannelRequest` to provide additional context for emoji selection.
