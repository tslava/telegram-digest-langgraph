from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import get_settings
from app.db.migrate import migrate
from app.db.repositories import list_chats, set_chat_enabled, upsert_chat_config
from app.db.sqlite import get_connection
from app.domain.models import ChatConfig, FixturePayload, Window
from app.logging_setup import setup_logging
from app.runner.run_all import run_all
from app.runner.run_one import run_one
from app.tools.storage import load_fixture, save_fixture
from app.tools.telegram_fetch import fetch_messages, telethon_login
from app.tools.telegram_resolve import ChatResolutionError, resolve_chat_identifier


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tg-digest")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Initialize the SQLite DB")

    add_chat = sub.add_parser("add-chat", help="Add or update a chat config")
    add_chat.add_argument(
        "--chat-id",
        type=str,
        required=True,
        help="Numeric ID, username (@name), or invite link",
    )
    add_chat.add_argument("--title", type=str, default=None)
    add_chat.add_argument("--profile", type=str, default="work")
    add_chat.add_argument("--language", type=str, default="ru")
    add_chat.add_argument("--window-mode", type=str, default="calendar_day")
    add_chat.add_argument("--lookback-hours", type=int, default=24)
    add_chat.add_argument("--timezone", type=str, default="Europe/Warsaw")
    add_chat.add_argument("--max-highlights", type=int, default=7)
    add_chat.add_argument("--max-todos", type=int, default=7)
    add_chat.add_argument("--max-questions", type=int, default=7)
    add_chat.add_argument("--include-quotes", type=int, default=1)
    add_chat.add_argument("--target-channel-id", type=int, default=None)
    add_chat.add_argument(
        "--no-emoji",
        action="store_true",
        help="Skip automatic emoji selection for title",
    )

    disable_chat = sub.add_parser("disable-chat", help="Disable a chat")
    disable_chat.add_argument("--chat-id", type=int, required=True)

    sub.add_parser("list-chats", help="List chats")

    run_all_cmd = sub.add_parser("run-all", help="Run digest for all enabled chats")
    run_all_cmd.add_argument("--dry-run", type=int, default=None)

    run_one_cmd = sub.add_parser("run-one", help="Run digest for a single chat")
    run_one_cmd.add_argument("--chat-id", type=int, required=True)
    run_one_cmd.add_argument("--dry-run", type=int, default=None)

    sub.add_parser("telegram-login", help="Run Telethon login flow")

    record_fixture = sub.add_parser("record-fixture", help="Record a fixture from a chat")
    record_fixture.add_argument("--chat-id", type=int, required=True)
    record_fixture.add_argument("--hours", type=int, default=24)
    record_fixture.add_argument("--out", type=str, required=True)
    record_fixture.add_argument("--after-message-id", type=int, default=None)

    run_fixture = sub.add_parser(
        "run-from-fixture", help="Run the pipeline from a JSON fixture"
    )
    run_fixture.add_argument("--in", dest="fixture_in", type=str, required=True)
    run_fixture.add_argument("--dry-run", type=int, default=1)

    return parser.parse_args()


def _apply_dry_run_override(value: int | None) -> None:
    if value is None:
        return
    settings = get_settings()
    settings.dry_run = bool(value)
    if settings.dry_run:
        settings.post_to_telegram = False


def _cmd_init_db() -> None:
    settings = get_settings()
    migrate(settings.db_path)


def _cmd_add_chat(args: argparse.Namespace) -> None:
    import sys

    from app.llm.emoji import select_emoji

    settings = get_settings()
    migrate(settings.db_path)
    target_channel_id = args.target_channel_id or settings.tg_target_channel_id
    if not target_channel_id:
        raise ValueError("target-channel-id or TG_TARGET_CHANNEL_ID is required")

    # Resolve chat identifier (username, link, or numeric ID)
    chat_id_input: str = args.chat_id
    should_add_emoji = not args.no_emoji and not args.title  # Skip if user provided title
    resolved_about: str | None = None

    try:
        # Try to parse as numeric ID first
        chat_id = int(chat_id_input)
        title = args.title  # Use provided title or None
        should_add_emoji = False  # No context for numeric IDs without resolution
        if title:
            print(f"Using numeric chat ID: {chat_id}")
        else:
            print(f"Using numeric chat ID: {chat_id} (no title provided)")
    except ValueError:
        # Not a numeric ID, need to resolve via Telegram
        print(f"Resolving '{chat_id_input}'...")
        try:
            resolved = resolve_chat_identifier(settings, chat_id_input)
            chat_id = resolved.chat_id
            title = args.title if args.title else resolved.title
            resolved_about = resolved.about
            print(f"Resolved to: {resolved.title} (ID: {chat_id})")
        except ChatResolutionError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Add emoji to title if applicable
    if should_add_emoji and title:
        emoji = select_emoji(title, resolved_about, settings)
        if emoji:
            title = f"{emoji} {title}"
            print(f"Added emoji: {title}")

    config = ChatConfig(
        chat_id=chat_id,
        enabled=True,
        title=title,
        profile=args.profile,
        language=args.language,
        window_mode=args.window_mode,
        lookback_hours=args.lookback_hours,
        timezone=args.timezone,
        max_highlights=args.max_highlights,
        max_todos=args.max_todos,
        max_questions=args.max_questions,
        include_quotes=bool(args.include_quotes),
        target_channel_id=target_channel_id,
    )

    conn = get_connection(settings.db_path)
    with conn:
        upsert_chat_config(conn, config)
    conn.close()
    print(f"Chat config saved: {config.chat_id} ({config.title or 'no title'})")


def _cmd_disable_chat(args: argparse.Namespace) -> None:
    settings = get_settings()
    conn = get_connection(settings.db_path)
    with conn:
        set_chat_enabled(conn, args.chat_id, False)
    conn.close()


def _cmd_list_chats() -> None:
    settings = get_settings()
    conn = get_connection(settings.db_path)
    with conn:
        chats = list_chats(conn)
    conn.close()
    for chat in chats:
        print(
            f"{chat.chat_id}\t{int(chat.enabled)}\t{chat.title or ''}\t{chat.window_mode}\t{chat.timezone}"
        )


def _cmd_telegram_login() -> None:
    settings = get_settings()
    telethon_login(settings)


def _cmd_record_fixture(args: argparse.Namespace) -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=args.hours)
    window_end = now

    messages = fetch_messages(
        settings=settings,
        chat_id=args.chat_id,
        window_start=window_start,
        window_end=window_end,
        after_message_id=args.after_message_id,
    )

    payload = FixturePayload(
        chat_id=args.chat_id,
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
        messages=messages,
    )
    save_fixture(Path(args.out), payload)


def _cmd_run_from_fixture(args: argparse.Namespace) -> None:
    settings = get_settings()
    settings.dry_run = bool(args.dry_run)
    if settings.dry_run:
        settings.post_to_telegram = False

    fixture = load_fixture(Path(args.fixture_in))
    if not fixture.messages:
        raise ValueError("Fixture has no messages")

    window_start = (
        datetime.fromisoformat(fixture.window_start)
        if fixture.window_start
        else datetime.now(timezone.utc) - timedelta(hours=24)
    )
    window_end = (
        datetime.fromisoformat(fixture.window_end)
        if fixture.window_end
        else datetime.now(timezone.utc)
    )
    window = Window(start=window_start, end=window_end)

    target_channel_id = settings.tg_target_channel_id or 0
    config = ChatConfig(
        chat_id=fixture.chat_id or 0,
        enabled=True,
        title="Fixture Run",
        target_channel_id=target_channel_id,
    )

    from app.graph.build import build_graph

    graph = build_graph()
    result = graph.invoke(
        {
            "config": config,
            "window": window,
            "fixture_messages": fixture.messages,
            "last_message_id": None,
            "last_digest_hash": None,
            "dry_run": settings.dry_run,
            "post_to_telegram": settings.post_to_telegram,
        }
    )
    print(result.get("final_text", ""))


def main() -> None:
    args = _parse_args()
    setup_logging(get_settings().log_level)

    if args.command == "init-db":
        _cmd_init_db()
    elif args.command == "add-chat":
        _cmd_add_chat(args)
    elif args.command == "disable-chat":
        _cmd_disable_chat(args)
    elif args.command == "list-chats":
        _cmd_list_chats()
    elif args.command == "run-all":
        _apply_dry_run_override(args.dry_run)
        run_all()
    elif args.command == "run-one":
        _apply_dry_run_override(args.dry_run)
        run_one(args.chat_id)
    elif args.command == "telegram-login":
        _cmd_telegram_login()
    elif args.command == "record-fixture":
        _cmd_record_fixture(args)
    elif args.command == "run-from-fixture":
        _cmd_run_from_fixture(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
