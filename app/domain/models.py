from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatConfig(BaseModel):
    chat_id: int
    enabled: bool = True
    title: str | None = None
    profile: str = "work"
    language: str = "ru"
    window_mode: str = "calendar_day"
    lookback_hours: int = 24
    timezone: str = "Europe/Warsaw"
    max_highlights: int = 7
    max_todos: int = 7
    max_questions: int = 7
    include_quotes: bool = True
    target_channel_id: int


class ChatState(BaseModel):
    chat_id: int
    last_message_id: int | None = None
    last_run_at: str | None = None
    last_status: str | None = None
    last_error: str | None = None
    last_digest_hash: str | None = None


class DigestRecord(BaseModel):
    chat_id: int
    window_start: str
    window_end: str
    messages_count: int
    payload_json: str
    final_text: str
    posted_channel_id: int | None
    posted_message_id: int | None
    created_at: str


class Window(BaseModel):
    start: datetime
    end: datetime


class NormalizedMessage(BaseModel):
    message_id: int
    ts: str
    author: str | None = None
    text: str
    reply_to_id: int | None = None
    reactions_count: int = 0
    has_link: bool = False
    chat_id: int | None = None


class FixturePayload(BaseModel):
    chat_id: int | None = None
    window_start: str | None = None
    window_end: str | None = None
    messages: list[NormalizedMessage] = Field(default_factory=list)
