from __future__ import annotations

from typing import Any, Optional, TypedDict

from app.domain.models import ChatConfig, NormalizedMessage, Window


class DigestState(TypedDict, total=False):
    config: ChatConfig
    window: Window
    last_message_id: Optional[int]
    last_digest_hash: Optional[str]
    raw_messages: list[NormalizedMessage]
    fixture_messages: list[NormalizedMessage]
    chunks: list[list[NormalizedMessage]]
    chunk_extracts: list[dict[str, Any]]
    digest_structured: dict[str, Any]
    final_text: str
    digest_hash: str
    posted_message_id: Optional[int]
    status: str
    error: Optional[str]
    metrics: dict[str, Any]
    dry_run: bool
    post_to_telegram: bool
    is_empty: bool
