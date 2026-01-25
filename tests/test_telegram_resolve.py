from __future__ import annotations

from app.tools.telegram_resolve import _parse_identifier


class TestParseIdentifier:
    """Tests for _parse_identifier function."""

    def test_numeric_id_positive(self) -> None:
        """Positive numeric IDs should be returned as integers."""
        assert _parse_identifier("123456") == 123456
        assert _parse_identifier("1") == 1

    def test_numeric_id_negative(self) -> None:
        """Negative numeric IDs (channels/groups) should be returned as integers."""
        assert _parse_identifier("-1001234567890") == -1001234567890
        assert _parse_identifier("-123456") == -123456

    def test_numeric_id_with_whitespace(self) -> None:
        """Numeric IDs with leading/trailing whitespace should be handled."""
        assert _parse_identifier("  123456  ") == 123456
        assert _parse_identifier("\t-100123\n") == -100123

    def test_username_with_at(self) -> None:
        """Usernames starting with @ should be returned as-is."""
        assert _parse_identifier("@durov") == "@durov"
        assert _parse_identifier("@test_user") == "@test_user"

    def test_username_without_at(self) -> None:
        """Plain usernames should have @ prepended."""
        assert _parse_identifier("durov") == "@durov"
        assert _parse_identifier("test_user") == "@test_user"

    def test_tme_username_link(self) -> None:
        """t.me/username links should be converted to @username."""
        assert _parse_identifier("t.me/durov") == "@durov"
        assert _parse_identifier("https://t.me/durov") == "@durov"
        assert _parse_identifier("http://t.me/test_channel") == "@test_channel"

    def test_tme_invite_link_plus_format(self) -> None:
        """t.me/+hash invite links should be converted to full URL."""
        result = _parse_identifier("t.me/+fU06TpWYrmBkNjM0")
        assert result == "https://t.me/+fU06TpWYrmBkNjM0"

        result = _parse_identifier("https://t.me/+abc123")
        assert result == "https://t.me/+abc123"

    def test_tme_invite_link_joinchat_format(self) -> None:
        """t.me/joinchat/hash links should be converted to plus format."""
        result = _parse_identifier("t.me/joinchat/abc123")
        assert result == "https://t.me/+abc123"

        result = _parse_identifier("https://t.me/joinchat/fU06TpWYrmBkNjM0")
        assert result == "https://t.me/+fU06TpWYrmBkNjM0"

    def test_invalid_short_username(self) -> None:
        """Usernames shorter than 4 chars aren't valid Telegram usernames."""
        # Should be returned as-is (let Telethon handle the error)
        result = _parse_identifier("abc")
        assert result == "abc"

    def test_username_starting_with_number(self) -> None:
        """Usernames starting with numbers aren't valid, returned as-is."""
        result = _parse_identifier("123abc")
        # This starts with digits but isn't fully numeric, so it's returned as-is
        assert result == "123abc"


class TestParseIdentifierEdgeCases:
    """Edge case tests for _parse_identifier."""

    def test_empty_string(self) -> None:
        """Empty string should be returned as-is."""
        result = _parse_identifier("")
        assert result == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string should be returned as empty after strip."""
        result = _parse_identifier("   ")
        assert result == ""

    def test_long_numeric_id(self) -> None:
        """Very large numeric IDs should be handled."""
        assert _parse_identifier("9999999999999") == 9999999999999

    def test_mixed_case_username(self) -> None:
        """Usernames with mixed case should be preserved."""
        assert _parse_identifier("@DurovChat") == "@DurovChat"
        assert _parse_identifier("DurovChat") == "@DurovChat"
