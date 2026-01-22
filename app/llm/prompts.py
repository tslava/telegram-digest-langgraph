EXTRACT_SYSTEM = """
You are a careful assistant that extracts a structured digest from Telegram messages.
Return only JSON that matches the schema.
""".strip()

EXTRACT_USER_TEMPLATE = """
Chat context:
- Language: {language}
- Profile: {profile}
- Window: {window_start} to {window_end}

Messages (chronological):
{messages}

Schema (JSON):
{{
  "highlights": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "decisions": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "todos": [{{"task": "...", "owner": "...", "due": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "open_questions": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "links": [{{"url": "...", "title": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "events": [{{"name": "...", "when": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "risks": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "metrics": {{"messages": 0, "participants": 0, "window_start": "...", "window_end": "..."}}
}}

Rules:
- Use evidence from messages where possible.
- Keep each field short; do not invent authors.
- If unsure, leave lists empty but keep metrics.
""".strip()

REDUCE_SYSTEM = """
You merge chunk digests into one final digest.
Return only JSON that matches the schema.
""".strip()

REDUCE_USER_TEMPLATE = """
Chat context:
- Language: {language}
- Profile: {profile}
- Window: {window_start} to {window_end}
- Max highlights: {max_highlights}
- Max todos: {max_todos}
- Max questions: {max_questions}

Chunk digests (JSON list):
{chunk_digests}

Merge rules:
- Deduplicate similar items.
- Enforce max counts above.
- Keep evidence lists short (max 2 per item).
- Produce metrics for the full window.

Return only the final digest JSON.
""".strip()

FIX_SYSTEM = """
You fix JSON to match the required schema. Return only JSON.
""".strip()

FIX_USER_TEMPLATE = """
Schema must be:
{{
  "highlights": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "decisions": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "todos": [{{"task": "...", "owner": "...", "due": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "open_questions": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "links": [{{"url": "...", "title": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "events": [{{"name": "...", "when": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "risks": [{{"title": "...", "details": "...", "evidence": [{{"message_id": 1, "author": "name", "ts": "ISO"}}]}}],
  "metrics": {{"messages": 0, "participants": 0, "window_start": "...", "window_end": "..."}}
}}

Input JSON:
{payload}

Validation error:
{error}

Fix the JSON to conform to schema and keep semantics.
""".strip()
