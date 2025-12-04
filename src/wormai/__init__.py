"""
🐛 Worm-AI — Grok API Client for Kali Linux
For educational and research purposes only.
"""

__version__ = "1.0.0"
__author__ = "Worm-AI Team"

from .client import GrokClient, WormAI
from .exceptions import (
    WormAIError,
    GrokAPIError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    StreamingError,
)

__all__ = [
    "GrokClient",
    "WormAI",
    "WormAIError",
    "GrokAPIError",
    "NetworkError",
    "AuthenticationError",
    "ValidationError",
    "StreamingError",
    "__version__",
]


def launch_gui():
    """Launch the GUI application."""
    from .gui import main
    main()
