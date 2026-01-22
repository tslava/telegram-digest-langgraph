from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.utils import get_display_name

from app.config import Settings
from app.domain.models import NormalizedMessage


def _normalize_message(message: Message, chat_id: int) -> Optional[NormalizedMessage]:
    text = message.message or ""
    if not text.strip():
        return None

    author = None
    if message.sender:
        author = get_display_name(message.sender)
    ts = message.date.isoformat()

    reply_to_id = message.reply_to_msg_id
    reactions_count = 0
    if message.reactions and message.reactions.results:
        reactions_count = sum(r.count for r in message.reactions.results)

    has_link = "http://" in text or "https://" in text

    return NormalizedMessage(
        message_id=message.id,
        ts=ts,
        author=author,
        text=text,
        reply_to_id=reply_to_id,
        reactions_count=reactions_count,
        has_link=has_link,
        chat_id=chat_id,
    )


def _require_telethon_settings(settings: Settings) -> None:
    if not settings.tg_api_id or not settings.tg_api_hash:
        raise ValueError("TG_API_ID and TG_API_HASH are required for Telethon.")


def telethon_login(settings: Settings) -> None:
    _require_telethon_settings(settings)

    async def _login() -> None:
        async with TelegramClient(str(settings.telethon_session), settings.tg_api_id, settings.tg_api_hash) as client:
            await client.start()

    asyncio.run(_login())


def fetch_messages(
    settings: Settings,
    chat_id: int,
    window_start: datetime,
    window_end: datetime,
    after_message_id: Optional[int] = None,
) -> list[NormalizedMessage]:
    _require_telethon_settings(settings)

    async def _fetch() -> list[NormalizedMessage]:
        messages: list[NormalizedMessage] = []
        async with TelegramClient(str(settings.telethon_session), settings.tg_api_id, settings.tg_api_hash) as client:
            async for msg in client.iter_messages(chat_id, offset_date=window_end):
                if msg.date > window_end:
                    continue
                if msg.date < window_start:
                    break
                if after_message_id and msg.id <= after_message_id:
                    continue
                if msg.action:
                    continue
                normalized = _normalize_message(msg, chat_id)
                if normalized:
                    messages.append(normalized)
        messages.sort(key=lambda m: m.message_id)
        return messages

    return asyncio.run(_fetch())
