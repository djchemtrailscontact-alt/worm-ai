"""
Input validation and sanitization for Worm-AI.
Security-first validation at system boundaries.
"""

import re
from typing import Optional
from urllib.parse import urlparse

from .exceptions import ValidationError


def validate_proxy_url(proxy: str) -> str:
    """
    Validate and normalize proxy URL.

    Args:
        proxy: Proxy URL string

    Returns:
        Normalized proxy URL

    Raises:
        ValidationError: If proxy URL is invalid
    """
    if not proxy or not isinstance(proxy, str):
        raise ValidationError("Proxy must be a non-empty string")

    proxy = proxy.strip()

    # Check for valid proxy schemes
    valid_schemes = ("http", "https", "socks4", "socks5", "socks4a", "socks5h")
    parsed = urlparse(proxy)

    if not parsed.scheme:
        # Try to add socks5:// if no scheme
        if "://" not in proxy:
            proxy = f"socks5://{proxy}"
            parsed = urlparse(proxy)

    if parsed.scheme not in valid_schemes:
        raise ValidationError(
            f"Invalid proxy scheme: {parsed.scheme}. " f"Must be one of: {', '.join(valid_schemes)}"
        )

    if not parsed.hostname:
        raise ValidationError("Proxy URL must include a hostname")

    # Validate port if specified
    # Validate port - urlparse raises ValueError for ports > 65535
    try:
        port = parsed.port
        if port is not None and port < 1:
            raise ValidationError(f"Invalid proxy port: {port}")
    except ValueError as e:
        raise ValidationError(f"Invalid proxy port: {e}") from e

    return proxy


def validate_cookie(cookie: str) -> str:
    """
    Validate session cookie format.

    Args:
        cookie: Cookie string

    Returns:
        Validated cookie string

    Raises:
        ValidationError: If cookie format is invalid
    """
    if not cookie or not isinstance(cookie, str):
        raise ValidationError("Cookie must be a non-empty string")

    cookie = cookie.strip()

    if len(cookie) < 10:  # Minimum reasonable cookie length
        raise ValidationError("Cookie appears too short to be valid")

    if len(cookie) > 4096:  # HTTP cookie size limit
        raise ValidationError("Cookie exceeds maximum length (4096 characters)")

    # Basic format check (allow common cookie characters including space, /, :, etc.)
    if not re.match(r"^[a-zA-Z0-9_\-=.;:/ ]+$", cookie):
        raise ValidationError("Cookie contains invalid characters")

    return cookie


def validate_message(message: str, max_length: int = 100000) -> str:
    """
    Validate user message.

    Args:
        message: User message string
        max_length: Maximum message length

    Returns:
        Validated message string

    Raises:
        ValidationError: If message is invalid
    """
    if not isinstance(message, str):
        raise ValidationError("Message must be a string")

    message = message.strip()

    if not message:
        raise ValidationError("Message cannot be empty")

    if len(message) > max_length:
        raise ValidationError(
            f"Message exceeds maximum length ({max_length} characters). "
            f"Current length: {len(message)}"
        )

    # Check for potentially malicious patterns (basic)
    # This is a simple check - more sophisticated validation could be added
    if len(message.encode("utf-8")) > max_length * 4:  # Account for multi-byte chars
        raise ValidationError("Message contains invalid encoding")

    return message


def validate_system_prompt(prompt: Optional[str], max_length: int = 10000) -> Optional[str]:
    """
    Validate system prompt.

    Args:
        prompt: System prompt string or None
        max_length: Maximum prompt length

    Returns:
        Validated prompt string or None

    Raises:
        ValidationError: If prompt is invalid
    """
    if prompt is None:
        return None

    if not isinstance(prompt, str):
        raise ValidationError("System prompt must be a string or None")

    prompt = prompt.strip()

    if len(prompt) > max_length:
        raise ValidationError(f"System prompt exceeds maximum length ({max_length} characters)")

    return prompt if prompt else None
