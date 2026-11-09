from __future__ import annotations

from typing import Any, TypedDict

from app.domain.models import ChatConfig, NormalizedMessage, Window


class DigestState(TypedDict, total=False):
    config: ChatConfig
    window: Window
    last_message_id: int | None
    last_digest_hash: str | None
    raw_messages: list[NormalizedMessage]
    fixture_messages: list[NormalizedMessage]
    chunks: list[list[NormalizedMessage]]
    chunk_extracts: list[dict[str, Any]]
    digest_structured: dict[str, Any]
    final_text: str
    digest_hash: str
    posted_message_id: int | None
    status: str
    error: str | None
    metrics: dict[str, Any]
    dry_run: bool
    post_to_telegram: bool
    is_empty: bool
