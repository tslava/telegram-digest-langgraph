from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.domain.models import ChatConfig, Window
from app.graph.build import build_graph
from app.tools.storage import load_fixture


def test_fixture_pipeline(tmp_path: Path) -> None:
    os.environ["LLM_MODE"] = "stub"
    os.environ["DRY_RUN"] = "1"
    os.environ["POST_TO_TELEGRAM"] = "0"
    os.environ["DB_PATH"] = str(tmp_path / "test.db")

    get_settings.cache_clear()
    settings = get_settings()

    fixture = load_fixture(Path("fixtures/sample_messages.json"))
    window = Window(
        start=datetime.fromisoformat(fixture.window_start),
        end=datetime.fromisoformat(fixture.window_end),
    )

    config = ChatConfig(
        chat_id=fixture.chat_id or 0,
        enabled=True,
        title="Fixture Run",
        target_channel_id=0,
    )

    graph = build_graph()
    result = graph.invoke(
        {
            "config": config,
            "window": window,
            "fixture_messages": fixture.messages,
            "last_message_id": None,
            "last_digest_hash": None,
            "dry_run": settings.dry_run,
            "post_to_telegram": settings.post_to_telegram,
        }
    )

    assert "Daily digest" in result.get("final_text", "")
    assert (tmp_path / "test.db").exists()
