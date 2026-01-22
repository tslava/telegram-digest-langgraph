from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import FixturePayload, NormalizedMessage


def save_fixture(path: Path, payload: FixturePayload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_fixture(path: Path) -> FixturePayload:
    data = json.loads(path.read_text(encoding="utf-8"))
    messages = [NormalizedMessage(**msg) for msg in data.get("messages", [])]
    return FixturePayload(
        chat_id=data.get("chat_id"),
        window_start=data.get("window_start"),
        window_end=data.get("window_end"),
        messages=messages,
    )
