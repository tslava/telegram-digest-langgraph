from __future__ import annotations

import html
from typing import Any

from app.domain.models import ChatConfig


def _esc(value: str) -> str:
    return html.escape(value, quote=False)


def _render_evidence(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return ""
    parts = []
    for ev in evidence[:2]:
        msg_id = ev.get("message_id")
        author = ev.get("author")
        if msg_id and author:
            parts.append(f"#{msg_id} {author}")
        elif msg_id:
            parts.append(f"#{msg_id}")
    if not parts:
        return ""
    return f" ({', '.join(parts)})"


def _render_items(items: list[dict[str, Any]], title_key: str, detail_key: str) -> list[str]:
    lines = []
    for item in items:
        title = _esc(str(item.get(title_key, "")))
        if not title:
            continue
        details = item.get(detail_key)
        suffix = f" - {_esc(str(details))}" if details else ""
        evidence = _render_evidence(item.get("evidence", []))
        lines.append(f"- {title}{suffix}{_esc(evidence)}")
    return lines


def format_digest(payload: dict[str, Any], config: ChatConfig, is_empty: bool) -> str:
    title = config.title or f"Chat {config.chat_id}"
    metrics = payload.get("metrics", {})
    window_start = metrics.get("window_start", "")
    window_end = metrics.get("window_end", "")

    lines = [f"<b>Daily digest: {_esc(title)}</b>"]
    if window_start and window_end:
        lines.append(f"<i>Window:</i> {_esc(window_start)} - {_esc(window_end)}")

    if is_empty:
        lines.append("No messages in this window.")
        return "\n".join(lines)

    sections = [
        ("Highlights", payload.get("highlights", []), "title", "details"),
        ("Decisions", payload.get("decisions", []), "title", "details"),
        ("Todos", payload.get("todos", []), "task", "owner"),
        ("Open Questions", payload.get("open_questions", []), "title", "details"),
        ("Links", payload.get("links", []), "url", "title"),
        ("Events", payload.get("events", []), "name", "when"),
        ("Risks", payload.get("risks", []), "title", "details"),
    ]

    for label, items, title_key, detail_key in sections:
        rendered = _render_items(items, title_key, detail_key)
        if not rendered:
            continue
        lines.append("")
        lines.append(f"<b>{_esc(label)}</b>")
        lines.extend(rendered)

    return "\n".join(lines)
