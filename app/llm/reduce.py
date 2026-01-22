from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.domain.models import ChatConfig, Window
from app.llm.prompts import FIX_SYSTEM, FIX_USER_TEMPLATE, REDUCE_SYSTEM, REDUCE_USER_TEMPLATE


def _dedupe(items: list[dict[str, Any]], key: str = "title") -> list[dict[str, Any]]:
    seen = set()
    output = []
    for item in items:
        value = item.get(key) or ""
        norm = value.strip().lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        output.append(item)
    return output


def _trim(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return items[:limit]


def _stub_reduce(
    chunks: list[dict[str, Any]], window: Window, config: ChatConfig
) -> dict[str, Any]:
    highlights = []
    decisions = []
    todos = []
    questions = []
    links = []
    events = []
    risks = []
    messages = 0
    participants = 0

    for chunk in chunks:
        highlights.extend(chunk.get("highlights", []))
        decisions.extend(chunk.get("decisions", []))
        todos.extend(chunk.get("todos", []))
        questions.extend(chunk.get("open_questions", []))
        links.extend(chunk.get("links", []))
        events.extend(chunk.get("events", []))
        risks.extend(chunk.get("risks", []))
        metrics = chunk.get("metrics") or {}
        messages += metrics.get("messages", 0)
        participants = max(participants, metrics.get("participants", 0))

    return {
        "highlights": _trim(_dedupe(highlights), config.max_highlights),
        "decisions": _dedupe(decisions),
        "todos": _trim(_dedupe(todos, key="task"), config.max_todos),
        "open_questions": _trim(_dedupe(questions), config.max_questions),
        "links": _dedupe(links, key="url"),
        "events": _dedupe(events, key="name"),
        "risks": _dedupe(risks),
        "metrics": {
            "messages": messages,
            "participants": participants,
            "window_start": window.start.isoformat(),
            "window_end": window.end.isoformat(),
        },
    }


def reduce_digests(
    chunks: list[dict[str, Any]],
    window: Window,
    config: ChatConfig,
    settings: Settings,
) -> dict[str, Any]:
    if settings.llm_mode == "stub":
        return _stub_reduce(chunks, window, config)

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for LLM mode.")

    client = OpenAI(api_key=settings.openai_api_key)
    user_prompt = REDUCE_USER_TEMPLATE.format(
        language=config.language,
        profile=config.profile,
        window_start=window.start.isoformat(),
        window_end=window.end.isoformat(),
        max_highlights=config.max_highlights,
        max_todos=config.max_todos,
        max_questions=config.max_questions,
        chunk_digests=json.dumps(chunks, ensure_ascii=False),
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": REDUCE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def fix_to_schema(payload: dict[str, Any], error: str, settings: Settings) -> dict[str, Any]:
    if settings.llm_mode == "stub":
        return payload

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for LLM mode.")

    client = OpenAI(api_key=settings.openai_api_key)
    user_prompt = FIX_USER_TEMPLATE.format(payload=json.dumps(payload, ensure_ascii=False), error=error)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": FIX_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
