from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.config import get_settings
from app.db.migrate import migrate
from app.db.repositories import insert_digest, upsert_chat_state
from app.db.sqlite import get_connection
from app.domain.digest_schema import DigestPayload
from app.domain.models import ChatState, DigestRecord, NormalizedMessage, Window
from app.formatters.telegram_render import format_digest
from app.llm.extract import extract_chunk
from app.llm.reduce import fix_to_schema, reduce_digests
from app.tools.telegram_fetch import fetch_messages
from app.tools.telegram_post import post_message

CHUNK_SIZE = 20


def fetch_messages_node(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    config = state["config"]
    window: Window = state["window"]
    fixture_messages = state.get("fixture_messages")
    if fixture_messages is not None:
        messages = fixture_messages
    else:
        last_message_id = state.get("last_message_id")
        messages = fetch_messages(
            settings=settings,
            chat_id=config.chat_id,
            window_start=window.start,
            window_end=window.end,
            after_message_id=last_message_id,
        )
    return {"raw_messages": messages, "is_empty": len(messages) == 0}


def route_empty(state: dict[str, Any]) -> str:
    return "empty" if state.get("is_empty") else "non_empty"


def preprocess_node(state: dict[str, Any]) -> dict[str, Any]:
    messages: list[NormalizedMessage] = [
        msg for msg in state.get("raw_messages", []) if msg.text.strip()
    ]
    chunks: list[list[NormalizedMessage]] = []
    for i in range(0, len(messages), CHUNK_SIZE):
        chunks.append(messages[i : i + CHUNK_SIZE])
    participants = {m.author for m in messages if m.author}
    metrics = {
        "messages": len(messages),
        "participants": len(participants),
        "window_start": state["window"].start.isoformat(),
        "window_end": state["window"].end.isoformat(),
    }
    return {"chunks": chunks, "metrics": metrics}


def extract_map_node(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    config = state["config"]
    window = state["window"]
    chunk_extracts = []
    for chunk in state.get("chunks", []):
        chunk_extracts.append(
            extract_chunk(
                messages=chunk,
                window=window,
                settings=settings,
                language=config.language,
                profile=config.profile,
            )
        )
    return {"chunk_extracts": chunk_extracts}


def reduce_dedupe_node(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    config = state["config"]
    window = state["window"]
    digest = reduce_digests(
        chunks=state.get("chunk_extracts", []),
        window=window,
        config=config,
        settings=settings,
    )
    return {"digest_structured": digest}


def _empty_digest(state: dict[str, Any]) -> dict[str, Any]:
    window = state["window"]
    metrics = {
        "messages": 0,
        "participants": 0,
        "window_start": window.start.isoformat(),
        "window_end": window.end.isoformat(),
    }
    return {
        "highlights": [],
        "decisions": [],
        "todos": [],
        "open_questions": [],
        "links": [],
        "events": [],
        "risks": [],
        "metrics": metrics,
    }


def empty_digest_node(state: dict[str, Any]) -> dict[str, Any]:
    return {"digest_structured": _empty_digest(state), "status": "empty"}


def _apply_limits(payload: dict[str, Any], config) -> dict[str, Any]:
    payload["highlights"] = payload.get("highlights", [])[: config.max_highlights]
    payload["todos"] = payload.get("todos", [])[: config.max_todos]
    payload["open_questions"] = payload.get("open_questions", [])[: config.max_questions]
    return payload


def validate_node(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    config = state["config"]
    digest = state.get("digest_structured") or {}
    if not digest.get("metrics") and state.get("metrics"):
        digest["metrics"] = state["metrics"]
    digest = _apply_limits(digest, config)
    try:
        payload = DigestPayload.model_validate(digest)
        return {"digest_structured": payload.model_dump(), "status": state.get("status", "ok")}
    except ValidationError as exc:
        try:
            fixed = fix_to_schema(digest, str(exc), settings)
            fixed = _apply_limits(fixed, config)
            payload = DigestPayload.model_validate(fixed)
            return {"digest_structured": payload.model_dump(), "status": state.get("status", "ok")}
        except ValidationError as exc2:
            return {"status": "error", "error": str(exc2)}


def format_node(state: dict[str, Any]) -> dict[str, Any]:
    config = state["config"]
    if state.get("status") == "error":
        return {"final_text": f"Digest failed for chat {config.chat_id}."}
    digest = state.get("digest_structured") or _empty_digest(state)
    final_text = format_digest(digest, config, state.get("is_empty", False))
    return {"final_text": final_text}


def compute_hash_node(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("status") == "error":
        return {"digest_hash": None}
    digest = state.get("digest_structured") or {}
    payload = json.dumps(digest, sort_keys=True, ensure_ascii=False)
    digest_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return {"digest_hash": digest_hash}


def publish_node(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("status") == "error":
        return {"posted_message_id": None}

    settings = get_settings()
    last_digest_hash = state.get("last_digest_hash")
    if last_digest_hash and last_digest_hash == state.get("digest_hash"):
        return {"posted_message_id": None}

    posted_message_id = post_message(
        settings=settings,
        text=state.get("final_text", ""),
        channel_id=state["config"].target_channel_id,
    )
    return {"posted_message_id": posted_message_id}


def persist_node(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    config = state["config"]
    window = state["window"]
    raw_messages: list[NormalizedMessage] = state.get("raw_messages", [])
    messages_count = len(raw_messages)
    latest_message_id = max([m.message_id for m in raw_messages], default=state.get("last_message_id"))

    digest_structured = state.get("digest_structured") or _empty_digest(state)
    final_text = state.get("final_text", "")
    digest_json = json.dumps(digest_structured, ensure_ascii=False)

    now = datetime.now(timezone.utc).isoformat()
    record = DigestRecord(
        chat_id=config.chat_id,
        window_start=window.start.isoformat(),
        window_end=window.end.isoformat(),
        messages_count=messages_count,
        payload_json=digest_json,
        final_text=final_text,
        posted_channel_id=config.target_channel_id,
        posted_message_id=state.get("posted_message_id"),
        created_at=now,
    )

    status = state.get("status", "ok")
    error = state.get("error")
    if status == "error":
        latest_message_id = state.get("last_message_id")

    migrate(settings.db_path)
    conn = get_connection(settings.db_path)
    with conn:
        insert_digest(conn, record)
        upsert_chat_state(
            conn,
            ChatState(
                chat_id=config.chat_id,
                last_message_id=latest_message_id,
                last_run_at=now,
                last_status=status,
                last_error=error,
                last_digest_hash=state.get("digest_hash"),
            ),
        )
    conn.close()
    return {"status": status}
