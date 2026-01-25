from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
)
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel, Chat, User
from telethon.utils import get_display_name

from app.config import Settings


class ChatResolutionError(Exception):
    """Raised when a chat identifier cannot be resolved."""


@dataclass
class ResolvedChat:
    """Result of resolving a chat identifier."""

    chat_id: int
    title: str
    about: str | None = None


def _require_telethon_settings(settings: Settings) -> None:
    if not settings.tg_api_id or not settings.tg_api_hash:
        raise ChatResolutionError("TG_API_ID and TG_API_HASH are required for Telethon.")


def _parse_identifier(identifier: str) -> str | int:
    """Parse identifier and return normalized form for get_entity().

    Returns:
        int: If identifier is a numeric ID
        str: If identifier is a username or invite link
    """
    identifier = identifier.strip()

    # Try to parse as numeric ID
    try:
        return int(identifier)
    except ValueError:
        pass

    # Handle t.me links
    # Formats: t.me/username, t.me/+invite_hash, t.me/joinchat/invite_hash
    tme_patterns = [
        r"(?:https?://)?t\.me/\+([a-zA-Z0-9_-]+)",  # t.me/+hash
        r"(?:https?://)?t\.me/joinchat/([a-zA-Z0-9_-]+)",  # t.me/joinchat/hash
        r"(?:https?://)?t\.me/([a-zA-Z][a-zA-Z0-9_]{3,})",  # t.me/username
    ]

    for pattern in tme_patterns:
        match = re.match(pattern, identifier)
        if match:
            extracted = match.group(1)
            # If it's an invite hash (from +hash or joinchat/hash patterns)
            if pattern in tme_patterns[:2]:
                return f"https://t.me/+{extracted}"
            # It's a username
            return f"@{extracted}"

    # Handle @username format (already has @)
    if identifier.startswith("@"):
        return identifier

    # Assume it's a username without @
    if re.match(r"^[a-zA-Z][a-zA-Z0-9_]{3,}$", identifier):
        return f"@{identifier}"

    # Return as-is, let Telethon handle it
    return identifier


def _get_entity_id(entity: Channel | Chat | User) -> int:
    """Extract the proper chat_id from a Telegram entity.

    For channels and supergroups, returns the negative ID format.
    """
    if isinstance(entity, Channel):
        # Channels/supergroups use -100 prefix
        return -1000000000000 - entity.id
    elif isinstance(entity, Chat):
        # Regular groups use negative ID
        return -entity.id
    else:
        # Users use positive ID
        return entity.id


def resolve_chat_identifier(settings: Settings, identifier: str) -> ResolvedChat:
    """Resolve a chat identifier (username, link, or numeric ID) to chat_id and title.

    Args:
        settings: App settings with Telegram credentials
        identifier: Chat identifier in one of these formats:
            - Numeric ID: "123456" or "-1001234567890"
            - Username: "@username" or "username"
            - Invite link: "https://t.me/+hash" or "t.me/joinchat/hash"
            - Public link: "https://t.me/username"

    Returns:
        ResolvedChat with numeric chat_id and title

    Raises:
        ChatResolutionError: If identifier cannot be resolved
    """
    _require_telethon_settings(settings)

    parsed = _parse_identifier(identifier)

    async def _resolve() -> ResolvedChat:
        async with TelegramClient(
            str(settings.telethon_session), settings.tg_api_id, settings.tg_api_hash
        ) as client:
            try:
                entity = await client.get_entity(parsed)
                chat_id = _get_entity_id(entity)
                title = get_display_name(entity)

                # Fetch channel description if available
                about: str | None = None
                if isinstance(entity, Channel):
                    try:
                        full_channel = await client(GetFullChannelRequest(entity))
                        about = full_channel.full_chat.about or None
                    except Exception:
                        pass  # Silently ignore if we can't fetch full info

                return ResolvedChat(chat_id=chat_id, title=title, about=about)
            except UsernameNotOccupiedError:
                raise ChatResolutionError(f"Username not found: {identifier}") from None
            except UsernameInvalidError:
                raise ChatResolutionError(f"Invalid username format: {identifier}") from None
            except InviteHashInvalidError:
                raise ChatResolutionError(f"Invalid invite link: {identifier}") from None
            except InviteHashExpiredError:
                raise ChatResolutionError(f"Invite link has expired: {identifier}") from None
            except ChannelPrivateError:
                raise ChatResolutionError(
                    f"Cannot access private channel: {identifier}. "
                    "Make sure you have joined this channel first."
                ) from None
            except ValueError as e:
                raise ChatResolutionError(f"Could not resolve '{identifier}': {e}") from e

    try:
        return asyncio.run(_resolve())
    except ChatResolutionError:
        raise
    except Exception as e:
        raise ChatResolutionError(f"Failed to resolve '{identifier}': {e}") from e
