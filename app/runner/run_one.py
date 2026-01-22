from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.db.migrate import migrate
from app.db.repositories import get_chat_config
from app.db.sqlite import get_connection
from app.domain.models import Window
from app.graph.build import build_graph

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


def run_one(chat_id: int) -> None:
    settings = get_settings()
    migrate(settings.db_path)
    conn = get_connection(settings.db_path)
    graph = build_graph()

    config = get_chat_config(conn, chat_id)
    if not config:
        raise ValueError(f"Chat {chat_id} not found in chat_configs")

    state = conn.execute(
        "SELECT * FROM chat_state WHERE chat_id = ?", (config.chat_id,)
    ).fetchone()
    last_message_id = state["last_message_id"] if state else None
    last_digest_hash = state["last_digest_hash"] if state else None

    window = _compute_window(config)

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
    conn.close()
