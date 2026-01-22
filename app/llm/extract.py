from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.domain.models import NormalizedMessage, Window
from app.llm.prompts import EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE


def _format_messages(messages: list[NormalizedMessage]) -> str:
    lines = []
    for msg in messages:
        author = msg.author or "unknown"
        lines.append(f"[{msg.message_id}] {msg.ts} {author}: {msg.text}")
    return "\n".join(lines)


def _stub_extract(messages: list[NormalizedMessage], window: Window) -> dict[str, Any]:
    highlights = []
    decisions = []
    todos = []
    questions = []
    links = []

    participants = {m.author for m in messages if m.author}
    for msg in messages:
        text_lower = msg.text.lower()
        evidence = [{"message_id": msg.message_id, "author": msg.author, "ts": msg.ts}]
        if "http://" in msg.text or "https://" in msg.text:
            links.append({"url": _extract_first_link(msg.text), "title": None, "evidence": evidence})
        if "?" in msg.text:
            questions.append({"title": msg.text[:120], "details": None, "evidence": evidence})
        if "todo" in text_lower:
            todos.append({"task": msg.text[:120], "owner": None, "due": None, "evidence": evidence})
        if "decided" in text_lower or "we will" in text_lower:
            decisions.append({"title": msg.text[:120], "details": None, "evidence": evidence})
        if "!" in msg.text:
            highlights.append({"title": msg.text[:120], "details": None, "evidence": evidence})

    return {
        "highlights": highlights,
        "decisions": decisions,
        "todos": todos,
        "open_questions": questions,
        "links": links,
        "events": [],
        "risks": [],
        "metrics": {
            "messages": len(messages),
            "participants": len(participants),
            "window_start": window.start.isoformat(),
            "window_end": window.end.isoformat(),
        },
    }


def _extract_first_link(text: str) -> str:
    for token in text.split():
        if token.startswith("http://") or token.startswith("https://"):
            return token
    return ""


def extract_chunk(
    messages: list[NormalizedMessage],
    window: Window,
    settings: Settings,
    language: str,
    profile: str,
) -> dict[str, Any]:
    if settings.llm_mode == "stub":
        return _stub_extract(messages, window)

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for LLM mode.")

    client = OpenAI(api_key=settings.openai_api_key)
    user_prompt = EXTRACT_USER_TEMPLATE.format(
        language=language,
        profile=profile,
        window_start=window.start.isoformat(),
        window_end=window.end.isoformat(),
        messages=_format_messages(messages),
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
