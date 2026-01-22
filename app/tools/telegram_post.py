from __future__ import annotations

from typing import Optional

import httpx

from app.config import Settings


class TelegramPostError(RuntimeError):
    pass


def post_message(settings: Settings, text: str, channel_id: Optional[int] = None) -> Optional[int]:
    if settings.dry_run or not settings.post_to_telegram:
        return None

    if not settings.tg_bot_token:
        raise ValueError("TG_BOT_TOKEN is required for posting.")

    target_channel = channel_id or settings.tg_target_channel_id
    if not target_channel:
        raise ValueError("TG_TARGET_CHANNEL_ID is required for posting.")

    url = f"https://api.telegram.org/bot{settings.tg_bot_token}/sendMessage"
    payload = {
        "chat_id": target_channel,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, data=payload)
        if response.status_code != 200:
            raise TelegramPostError(
                f"Telegram API error {response.status_code}: {response.text}"
            )
        data = response.json()
        if not data.get("ok"):
            raise TelegramPostError(f"Telegram API error: {data}")
        return data["result"]["message_id"]
