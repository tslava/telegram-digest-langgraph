from __future__ import annotations

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    message_id: int | None = None
    author: str | None = None
    ts: str | None = None


class DigestItem(BaseModel):
    title: str
    details: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class TodoItem(BaseModel):
    task: str
    owner: str | None = None
    due: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class LinkItem(BaseModel):
    url: str
    title: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class EventItem(BaseModel):
    name: str
    when: str | None = None
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
