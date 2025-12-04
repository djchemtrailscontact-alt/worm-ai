#!/usr/bin/env python3
"""
Grok API Client - Unofficial wrapper for Grok AI
For educational and research purposes only.
"""

import json
import time
import logging
from typing import Optional, Generator, Dict, Any
from urllib.parse import urlparse

try:
    from curl_cffi import requests
except ImportError:
    raise ImportError(
        "curl_cffi is required. Install with: pip install curl_cffi"
    )

from .exceptions import (
    GrokAPIError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    StreamingError,
)
from .validation import (
    validate_proxy_url,
    validate_cookie,
    validate_message,
    validate_system_prompt,
)

# Configure logging
logger = logging.getLogger(__name__)


class GrokClient:
    """Unofficial Grok API client using browser impersonation."""

    BASE_URL = "https://grok.com"
    API_URL = f"{BASE_URL}/rest/app-chat/conversations/new"

    HEADERS = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://grok.com",
        "referer": "https://grok.com/",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    def __init__(
        self,
        cookie: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the Grok client.

        Args:
            cookie: Optional session cookie for authenticated requests
            proxy: Optional proxy URL (e.g., "socks5://127.0.0.1:9050")
            timeout: Request timeout in seconds (default: 120)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)

        Raises:
            ValidationError: If proxy or cookie format is invalid
        """
        # Validate and normalize inputs
        self.cookie = validate_cookie(cookie) if cookie else None
        self.proxy = validate_proxy_url(proxy) if proxy else None
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.conversation_id: Optional[str] = None
        self.response_id: Optional[str] = None

        logger.debug(f"GrokClient initialized (proxy={bool(self.proxy)}, cookie={bool(self.cookie)})")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with optional cookie."""
        headers = self.HEADERS.copy()
        if self.cookie:
            headers["cookie"] = self.cookie
        return headers

    def _build_payload(
        self, message: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build the request payload.

        Args:
            message: Validated user message
            system_prompt: Validated system prompt or None

        Returns:
            Request payload dictionary
        """
        payload: Dict[str, Any] = {
            "temporary": True,
            "modelSlug": "grok-3",
            "message": message,
            "fileAttachments": [],
            "imageAttachments": [],
            "disableSearch": False,
            "enableImageGeneration": True,
            "returnImageBytes": False,
            "returnRawGrokInXaiRequest": False,
            "enableImageStreaming": True,
            "imageGenerationCount": 2,
            "forceConcise": False,
            "toolOverrides": {},
            "enableSideBySide": True,
            "isPreset": False,
            "sendFinalMetadata": True,
            "customInstructions": system_prompt or "",
            "deepsearchPreset": "",
            "isReasoning": False,
        }

        # Add conversation context if continuing a chat
        if self.conversation_id and self.response_id:
            payload["conversationId"] = self.conversation_id
            payload["parentResponseId"] = self.response_id

        return payload

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        stream: bool = True,
    ) -> Generator[str, None, None]:
        """
        Send a message to Grok and yield response chunks.

        Args:
            message: The user message (will be validated)
            system_prompt: Optional system prompt for context (will be validated)
            stream: Whether to stream the response (currently always True)

        Yields:
            Response text chunks

        Raises:
            ValidationError: If message or system_prompt is invalid
            GrokAPIError: If API returns an error
            NetworkError: If network request fails
            AuthenticationError: If authentication fails (401/403)
        """
        # Validate inputs at system boundary
        try:
            message = validate_message(message)
            system_prompt = validate_system_prompt(system_prompt)
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise

        payload = self._build_payload(message, system_prompt)
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

        # Retry logic for transient failures
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    impersonate="chrome120",
                    proxies=proxies,
                    stream=True,
                    timeout=self.timeout,
                )

                # Handle HTTP errors with specific exception types
                if response.status_code == 401 or response.status_code == 403:
                    raise AuthenticationError(
                        f"Authentication failed: HTTP {response.status_code}",
                        status_code=response.status_code,
                        response_text=response.text[:500],
                    )
                elif response.status_code == 429:
                    # Rate limiting - wait and retry
                    retry_after = int(response.headers.get("Retry-After", self.retry_delay * (attempt + 1)))
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Rate limited, waiting {retry_after}s before retry {attempt + 1}/{self.max_retries}")
                        time.sleep(retry_after)
                        continue
                    raise GrokAPIError(
                        f"Rate limit exceeded: HTTP {response.status_code}",
                        status_code=response.status_code,
                        response_text=response.text[:500],
                    )
                elif response.status_code != 200:
                    raise GrokAPIError(
                        f"API error: HTTP {response.status_code}",
                        status_code=response.status_code,
                        response_text=response.text[:500],
                    )

                # Success - process stream
                full_text = ""
                for line in response.iter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # Extract conversation ID for follow-ups
                        if "conversationId" in data:
                            self.conversation_id = data["conversationId"]
                        if "responseId" in data:
                            self.response_id = data["responseId"]

                        # Extract the response text
                        if "result" in data and "response" in data["result"]:
                            resp = data["result"]["response"]
                            if "text" in resp:
                                new_text = resp["text"]
                                if len(new_text) > len(full_text):
                                    chunk = new_text[len(full_text):]
                                    full_text = new_text
                                    yield chunk

                        # Handle token-by-token streaming
                        if "token" in data:
                            yield data["token"]

                    except json.JSONDecodeError as e:
                        # Try to extract text from non-JSON response
                        text = line.decode("utf-8", errors="ignore")
                        if text and not text.startswith("{"):
                            yield text
                        else:
                            logger.debug(f"Failed to parse JSON line: {e}")

                # Success - break retry loop
                return

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = NetworkError(f"Network error: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.warning(f"Network error, retrying in {self.retry_delay}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                raise last_exception

            except (GrokAPIError, AuthenticationError):
                # Don't retry on API/auth errors
                raise

            except Exception as e:
                last_exception = StreamingError(f"Unexpected error: {type(e).__name__}: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.warning(f"Error, retrying in {self.retry_delay}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise last_exception

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise StreamingError("Failed to get response after all retries")

    def chat_sync(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a message and get the complete response.

        Args:
            message: The user message
            system_prompt: Optional system prompt

        Returns:
            Complete response text
        """
        chunks = list(self.chat(message, system_prompt, stream=True))
        return "".join(chunks)

    def reset(self):
        """Reset the conversation context."""
        self.conversation_id = None
        self.response_id = None


class WormAI:
    """
    WormAI wrapper for Grok with jailbreak support.

    Provides a high-level interface with validation and error handling.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        cookie: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
    ):
        """
        Initialize WormAI client.

        Args:
            proxy: Optional proxy URL (e.g., "socks5://127.0.0.1:9050")
            cookie: Optional session cookie for authenticated requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Raises:
            ValidationError: If proxy or cookie format is invalid
        """
        self.client = GrokClient(
            cookie=cookie,
            proxy=proxy,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.system_prompt: Optional[str] = None

    def set_system_prompt(self, prompt: Optional[str]) -> None:
        """
        Set the system prompt for all messages.

        Args:
            prompt: System prompt string or None to clear

        Raises:
            ValidationError: If prompt format is invalid
        """
        self.system_prompt = validate_system_prompt(prompt) if prompt else None

    def chat(self, message: str) -> Generator[str, None, None]:
        """
        Send a message and stream the response.

        Args:
            message: User message to send

        Yields:
            Response text chunks

        Raises:
            ValidationError: If message is invalid
            GrokAPIError: If API returns an error
            NetworkError: If network request fails
            AuthenticationError: If authentication fails
        """
        yield from self.client.chat(message, self.system_prompt)

    def chat_sync(self, message: str) -> str:
        """
        Send a message and get complete response.

        Args:
            message: User message to send

        Returns:
            Complete response text

        Raises:
            ValidationError: If message is invalid
            GrokAPIError: If API returns an error
            NetworkError: If network request fails
            AuthenticationError: If authentication fails
        """
        chunks = list(self.chat(message))
        return "".join(chunks)

    def reset(self) -> None:
        """Reset the conversation context."""
        self.client.reset()
        logger.debug("Conversation reset")


if __name__ == "__main__":
    # Quick test
    client = WormAI()
    print("Testing Grok connection...")
    for chunk in client.chat("Hello, who are you?"):
        print(chunk, end="", flush=True)
    print()
