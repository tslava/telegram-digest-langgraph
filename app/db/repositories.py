from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.domain.models import ChatConfig, ChatState, DigestRecord


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_chat_config(row) -> ChatConfig:
    return ChatConfig(
        chat_id=row["chat_id"],
        enabled=bool(row["enabled"]),
        title=row["title"],
        profile=row["profile"],
        language=row["language"],
        window_mode=row["window_mode"],
        lookback_hours=row["lookback_hours"],
        timezone=row["timezone"],
        max_highlights=row["max_highlights"],
        max_todos=row["max_todos"],
        max_questions=row["max_questions"],
        include_quotes=bool(row["include_quotes"]),
        target_channel_id=row["target_channel_id"],
    )


def list_enabled_chats(conn) -> list[ChatConfig]:
    rows = conn.execute(
        "SELECT * FROM chat_configs WHERE enabled = 1 ORDER BY chat_id"
    ).fetchall()
    return [_row_to_chat_config(row) for row in rows]


def list_chats(conn) -> list[ChatConfig]:
    rows = conn.execute("SELECT * FROM chat_configs ORDER BY chat_id").fetchall()
    return [_row_to_chat_config(row) for row in rows]


def get_chat_config(conn, chat_id: int) -> Optional[ChatConfig]:
    row = conn.execute(
        "SELECT * FROM chat_configs WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    if not row:
        return None
    return _row_to_chat_config(row)


def upsert_chat_config(conn, config: ChatConfig) -> None:
    now = _utc_now()
    conn.execute(
        """
        INSERT INTO chat_configs (
            chat_id, enabled, title, profile, language, window_mode, lookback_hours,
            timezone, max_highlights, max_todos, max_questions, include_quotes,
            target_channel_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            enabled=excluded.enabled,
            title=excluded.title,
            profile=excluded.profile,
            language=excluded.language,
            window_mode=excluded.window_mode,
            lookback_hours=excluded.lookback_hours,
            timezone=excluded.timezone,
            max_highlights=excluded.max_highlights,
            max_todos=excluded.max_todos,
            max_questions=excluded.max_questions,
            include_quotes=excluded.include_quotes,
            target_channel_id=excluded.target_channel_id,
            updated_at=excluded.updated_at
        """,
        (
            config.chat_id,
            1 if config.enabled else 0,
            config.title,
            config.profile,
            config.language,
            config.window_mode,
            config.lookback_hours,
            config.timezone,
            config.max_highlights,
            config.max_todos,
            config.max_questions,
            1 if config.include_quotes else 0,
            config.target_channel_id,
            now,
            now,
        ),
    )


def set_chat_enabled(conn, chat_id: int, enabled: bool) -> None:
    now = _utc_now()
    conn.execute(
        "UPDATE chat_configs SET enabled = ?, updated_at = ? WHERE chat_id = ?",
        (1 if enabled else 0, now, chat_id),
    )


def get_chat_state(conn, chat_id: int) -> ChatState:
    row = conn.execute(
        "SELECT * FROM chat_state WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    if not row:
        return ChatState(chat_id=chat_id)
    return ChatState(
        chat_id=row["chat_id"],
        last_message_id=row["last_message_id"],
        last_run_at=row["last_run_at"],
        last_status=row["last_status"],
        last_error=row["last_error"],
        last_digest_hash=row["last_digest_hash"],
    )


def upsert_chat_state(conn, state: ChatState) -> None:
    conn.execute(
        """
        INSERT INTO chat_state (
            chat_id, last_message_id, last_run_at, last_status, last_error, last_digest_hash
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            last_message_id=excluded.last_message_id,
            last_run_at=excluded.last_run_at,
            last_status=excluded.last_status,
            last_error=excluded.last_error,
            last_digest_hash=excluded.last_digest_hash
        """,
        (
            state.chat_id,
            state.last_message_id,
            state.last_run_at,
            state.last_status,
            state.last_error,
            state.last_digest_hash,
        ),
    )


def insert_digest(conn, record: DigestRecord) -> None:
    conn.execute(
        """
        INSERT INTO digests (
            chat_id, window_start, window_end, messages_count, payload_json,
            final_text, posted_channel_id, posted_message_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.chat_id,
            record.window_start,
            record.window_end,
            record.messages_count,
            record.payload_json,
            record.final_text,
            record.posted_channel_id,
            record.posted_message_id,
            record.created_at,
        ),
    )
