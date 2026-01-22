from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatConfig(BaseModel):
    chat_id: int
    enabled: bool = True
    title: Optional[str] = None
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
    last_message_id: Optional[int] = None
    last_run_at: Optional[str] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    last_digest_hash: Optional[str] = None


class DigestRecord(BaseModel):
    chat_id: int
    window_start: str
    window_end: str
    messages_count: int
    payload_json: str
    final_text: str
    posted_channel_id: Optional[int]
    posted_message_id: Optional[int]
    created_at: str


class Window(BaseModel):
    start: datetime
    end: datetime


class NormalizedMessage(BaseModel):
    message_id: int
    ts: str
    author: Optional[str] = None
    text: str
    reply_to_id: Optional[int] = None
    reactions_count: int = 0
    has_link: bool = False
    chat_id: Optional[int] = None


class FixturePayload(BaseModel):
    chat_id: Optional[int] = None
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    messages: list[NormalizedMessage] = Field(default_factory=list)
