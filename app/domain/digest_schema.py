from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    message_id: Optional[int] = None
    author: Optional[str] = None
    ts: Optional[str] = None


class DigestItem(BaseModel):
    title: str
    details: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)


class TodoItem(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)


class LinkItem(BaseModel):
    url: str
    title: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)


class EventItem(BaseModel):
    name: str
    when: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)


class Metrics(BaseModel):
    messages: int
    participants: int
    window_start: str
    window_end: str


class DigestPayload(BaseModel):
    highlights: list[DigestItem] = Field(default_factory=list)
    decisions: list[DigestItem] = Field(default_factory=list)
    todos: list[TodoItem] = Field(default_factory=list)
    open_questions: list[DigestItem] = Field(default_factory=list)
    links: list[LinkItem] = Field(default_factory=list)
    events: list[EventItem] = Field(default_factory=list)
    risks: list[DigestItem] = Field(default_factory=list)
    metrics: Metrics
