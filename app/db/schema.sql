CREATE TABLE IF NOT EXISTS chat_configs (
    chat_id INTEGER PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1,
    title TEXT NULL,
    profile TEXT NOT NULL DEFAULT 'work',
    language TEXT NOT NULL DEFAULT 'ru',
    window_mode TEXT NOT NULL DEFAULT 'calendar_day',
    lookback_hours INTEGER NOT NULL DEFAULT 24,
    timezone TEXT NOT NULL DEFAULT 'Europe/Warsaw',
    max_highlights INTEGER NOT NULL DEFAULT 7,
    max_todos INTEGER NOT NULL DEFAULT 7,
    max_questions INTEGER NOT NULL DEFAULT 7,
    include_quotes INTEGER NOT NULL DEFAULT 1,
    target_channel_id INTEGER NOT NULL,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS chat_state (
    chat_id INTEGER PRIMARY KEY,
    last_message_id INTEGER NULL,
    last_run_at TEXT NULL,
    last_status TEXT NULL,
    last_error TEXT NULL,
    last_digest_hash TEXT NULL
);

CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    messages_count INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    final_text TEXT NOT NULL,
    posted_channel_id INTEGER NULL,
    posted_message_id INTEGER NULL,
    created_at TEXT NOT NULL
);
