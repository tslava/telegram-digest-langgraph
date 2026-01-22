from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.db.migrate import migrate
from app.db.repositories import insert_digest, list_enabled_chats, upsert_chat_state
from app.db.sqlite import get_connection
from app.domain.models import ChatState, DigestRecord, Window
from app.graph.build import build_graph

logger = logging.getLogger(__name__)


def _compute_window(config) -> Window:
    tz = ZoneInfo(config.timezone)
    now = datetime.now(tz)
    if config.window_mode == "calendar_day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        start = now - timedelta(hours=config.lookback_hours)
        end = now
    return Window(start=start, end=end)


def _persist_failure(chat_id: int, error: str) -> None:
    settings = get_settings()
    migrate(settings.db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(settings.db_path)
    existing = conn.execute(
        "SELECT last_message_id, last_digest_hash FROM chat_state WHERE chat_id = ?",
        (chat_id,),
    ).fetchone()
    last_message_id = existing["last_message_id"] if existing else None
    last_digest_hash = existing["last_digest_hash"] if existing else None
    with conn:
        upsert_chat_state(
            conn,
            ChatState(
                chat_id=chat_id,
                last_message_id=last_message_id,
                last_run_at=now,
                last_status="error",
                last_error=error,
                last_digest_hash=last_digest_hash,
            ),
        )
        insert_digest(
            conn,
            DigestRecord(
                chat_id=chat_id,
                window_start=now,
                window_end=now,
                messages_count=0,
                payload_json="{}",
                final_text=f"Digest failed for chat {chat_id}: {error}",
                posted_channel_id=None,
                posted_message_id=None,
                created_at=now,
            ),
        )
    conn.close()


def run_all() -> None:
    settings = get_settings()
    migrate(settings.db_path)
    conn = get_connection(settings.db_path)
    graph = build_graph()

    with conn:
        chats = list_enabled_chats(conn)

    for config in chats:
        window = _compute_window(config)
        with conn:
            state = conn.execute(
                "SELECT * FROM chat_state WHERE chat_id = ?", (config.chat_id,)
            ).fetchone()
        last_message_id = state["last_message_id"] if state else None
        last_digest_hash = state["last_digest_hash"] if state else None

        try:
            result = graph.invoke(
                {
                    "config": config,
                    "window": window,
                    "last_message_id": last_message_id,
                    "last_digest_hash": last_digest_hash,
                    "dry_run": settings.dry_run,
                    "post_to_telegram": settings.post_to_telegram,
                }
            )
            if settings.dry_run:
                print(result.get("final_text", ""))
        except Exception as exc:
            logger.exception("Failed to process chat %s", config.chat_id)
            _persist_failure(config.chat_id, str(exc))

    conn.close()
