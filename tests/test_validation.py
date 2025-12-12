"""Tests for validation module."""

import pytest

from wormai.exceptions import ValidationError
from wormai.validation import (
    validate_cookie,
    validate_message,
    validate_proxy_url,
    validate_system_prompt,
)


class TestProxyValidation:
    """Test proxy URL validation."""

    def test_valid_socks5_proxy(self):
        """Test valid SOCKS5 proxy."""
        result = validate_proxy_url("socks5://127.0.0.1:9050")
        assert result == "socks5://127.0.0.1:9050"

    def test_valid_http_proxy(self):
        """Test valid HTTP proxy."""
        result = validate_proxy_url("http://proxy.example.com:8080")
        assert result == "http://proxy.example.com:8080"

    def test_proxy_without_scheme(self):
        """Test proxy without scheme (should add socks5://)."""
        result = validate_proxy_url("127.0.0.1:9050")
        assert result.startswith("socks5://")

    def test_invalid_proxy_scheme(self):
        """Test invalid proxy scheme."""
        with pytest.raises(ValidationError, match="Invalid proxy scheme"):
            validate_proxy_url("ftp://example.com:8080")

    def test_proxy_without_hostname(self):
        """Test proxy without hostname."""
        with pytest.raises(ValidationError, match="hostname"):
            validate_proxy_url("socks5://:9050")

    def test_invalid_proxy_port(self):
        """Test invalid proxy port."""
        with pytest.raises(ValidationError, match="port"):
            validate_proxy_url("socks5://127.0.0.1:99999")

    def test_empty_proxy(self):
        """Test empty proxy."""
        with pytest.raises(ValidationError):
            validate_proxy_url("")


class TestCookieValidation:
    """Test cookie validation."""

    def test_valid_cookie(self):
        """Test valid cookie."""
        cookie = "session_id=abc123def456; path=/"
        result = validate_cookie(cookie)
        assert result == cookie

    def test_short_cookie(self):
        """Test cookie that's too short."""
        with pytest.raises(ValidationError, match="too short"):
            validate_cookie("abc")

    def test_long_cookie(self):
        """Test cookie that's too long."""
        long_cookie = "a" * 5000
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_cookie(long_cookie)

    def test_invalid_cookie_characters(self):
        """Test cookie with invalid characters."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_cookie("cookie=value<script>alert('xss')</script>")


class TestMessageValidation:
    """Test message validation."""

    def test_valid_message(self):
        """Test valid message."""
        message = "Hello, this is a test message"
        result = validate_message(message)
        assert result == message

    def test_empty_message(self):
        """Test empty message."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_message("")

    def test_whitespace_only_message(self):
        """Test whitespace-only message."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_message("   \n\t  ")

    def test_long_message(self):
        """Test message that's too long."""
        long_message = "a" * 200000
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_message(long_message)

    def test_custom_max_length(self):
        """Test custom max length."""
        message = "a" * 50
        result = validate_message(message, max_length=100)
        assert result == message


class TestSystemPromptValidation:
    """Test system prompt validation."""

    def test_valid_prompt(self):
        """Test valid system prompt."""
        prompt = "You are a helpful assistant."
        result = validate_system_prompt(prompt)
        assert result == prompt

    def test_none_prompt(self):
        """Test None prompt."""
        result = validate_system_prompt(None)
        assert result is None

    def test_empty_prompt(self):
        """Test empty prompt (should return None)."""
        result = validate_system_prompt("   ")
        assert result is None

    def test_long_prompt(self):
        """Test prompt that's too long."""
        long_prompt = "a" * 20000
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_system_prompt(long_prompt)
