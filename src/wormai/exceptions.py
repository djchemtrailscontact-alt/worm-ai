"""
Custom exceptions for Worm-AI.
Provides specific error types for better error handling.
"""

from typing import Optional


class WormAIError(Exception):
    """Base exception for all Worm-AI errors."""
    pass


class GrokAPIError(WormAIError):
    """Error from Grok API."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class NetworkError(WormAIError):
    """Network-related errors (timeout, connection, etc.)."""
    pass


class AuthenticationError(WormAIError):
    """Authentication/authorization errors."""
    pass


class ValidationError(WormAIError):
    """Input validation errors."""
    pass


class ConfigurationError(WormAIError):
    """Configuration/setup errors."""
    pass


class StreamingError(WormAIError):
    """Errors during response streaming."""
    pass
