# telegram-digest-langgraph

Daily Telegram chat digest generator using LangGraph and Telethon. It reads messages from configured chats, extracts structured highlights with an LLM workflow, and posts summaries to a private Telegram channel.

## Quick start (local)

1) Install deps

```bash
uv sync --dev
```

2) Configure env

```bash
cp .env_example .env
```

3) Init DB

```bash
uv run tg-digest init-db
```

4) Login to Telegram (Telethon user session)

```bash
uv run tg-digest telegram-login
```

5) Add a chat

```bash
uv run tg-digest add-chat --chat-id 123 --target-channel-id -100123
```

6) Run once

```bash
uv run tg-digest run-all --dry-run 1
```

## Fixture mode

Run the pipeline without Telethon (and without posting):

```bash
LLM_MODE=stub uv run tg-digest run-from-fixture --in fixtures/sample_messages.json --dry-run 1
```

Record a fixture from a real chat:

```bash
uv run tg-digest record-fixture --chat-id 123 --hours 24 --out fixtures/my_chat.json
```

## Scripts (local)

Convenience wrappers live in `scripts/`:

- `scripts/init_db.sh`
- `scripts/add_chat.sh`
- `scripts/disable_chat.sh`
- `scripts/list_chats.sh`
- `scripts/run_once.sh`

## Deployment

### Bootstrap server

```bash
sudo deploy/scripts/bootstrap_server.sh
```

### Install/update app

```bash
sudo deploy/scripts/install_app.sh --repo <git-url> --ref main
```

### Smoke test

```bash
sudo deploy/scripts/smoke_test.sh
```

### Manual deploy from local machine

```bash
deploy/scripts/deploy_local.sh root@88.198.77.251 main
```

## Environment variables

See `.env.example` for the full list. Required for production:

- `TG_API_ID`, `TG_API_HASH`: Telegram API credentials for a user account. Get them at `https://my.telegram.org` -> API Development Tools -> create an app.
- `TG_BOT_TOKEN`: Telegram Bot API token. Create a bot via `@BotFather` and copy the token.
- `TG_TARGET_CHANNEL_ID`: Private channel ID where digests are posted. Create a private channel, add the bot as admin, then get the ID by forwarding a message from that channel to `@userinfobot` or by calling the Bot API `getUpdates` after the bot posts once (it will look like `-1001234567890`).
- `OPENAI_API_KEY`: OpenAI API key from `https://platform.openai.com/api-keys`.

Optional/common:

- `OPENAI_MODEL`: LLM model name (default `gpt-4o-mini`).
- `DB_PATH`: SQLite file path (local default `./.local/app.db`).
- `TELETHON_SESSION`: Telethon session file path (local default `./.local/telethon.session`).
- `DRY_RUN`: `1` to skip posting to Telegram.
- `POST_TO_TELEGRAM`: `1` to allow posting, `0` to disable.
- `LOG_LEVEL`: e.g. `INFO`, `DEBUG`.

## GitHub Actions CI/CD setup and maintenance

Setup:
- Add secrets in repo Settings > Secrets and variables > Actions:
  - `SERVER_IP`, `SSH_PRIVATE_KEY`, `SSH_USER`
  - `TG_API_ID`, `TG_API_HASH`, `TG_BOT_TOKEN`, `TG_TARGET_CHANNEL_ID`
  - `OPENAI_API_KEY`
- Ensure the server accepts SSH from GitHub Actions (or via your network controls).
- If you add new required env vars, update `.env.example` and the env block in `.github/workflows/deploy.yml`.

Maintenance:
- Rotate the SSH key and Telegram/OpenAI secrets periodically; update both GitHub secrets and server `authorized_keys`.
- Keep action versions up to date in `.github/workflows/ci.yml` and `.github/workflows/deploy.yml`.
- Use `workflow_dispatch` to force a deploy, then check `systemctl status tg-digest.timer`.

## Notes

- Empty chats post a "No messages" digest for the window.
- `LLM_MODE=stub` runs a deterministic, non-LLM extractor for fixtures and tests.
