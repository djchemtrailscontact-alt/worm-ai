"""Improved tests for Worm-AI client with error handling."""

import json
from unittest.mock import Mock, patch

import pytest

from wormai.client import GrokClient, WormAI
from wormai.exceptions import (
    AuthenticationError,
    GrokAPIError,
    NetworkError,
    ValidationError,
)


class TestGrokClientValidation:
    """Test client initialization with validation."""

    def test_client_with_valid_proxy(self):
        """Test client with valid proxy."""
        client = GrokClient(proxy="socks5://127.0.0.1:9050")
        assert client.proxy == "socks5://127.0.0.1:9050"

    def test_client_with_invalid_proxy(self):
        """Test client with invalid proxy."""
        with pytest.raises(ValidationError):
            GrokClient(proxy="invalid://proxy")

    def test_client_with_valid_cookie(self):
        """Test client with valid cookie."""
        cookie = "session_id=abc123def456"
        client = GrokClient(cookie=cookie)
        assert client.cookie == cookie

    def test_client_with_invalid_cookie(self):
        """Test client with invalid cookie."""
        with pytest.raises(ValidationError):
            GrokClient(cookie="abc")  # Too short


class TestGrokClientErrorHandling:
    """Test error handling in GrokClient."""

    @patch("wormai.client.requests.post")
    def test_authentication_error_401(self, mock_post):
        """Test handling of 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        client = GrokClient()
        with pytest.raises(AuthenticationError) as exc_info:
            list(client.chat("test message"))

        assert exc_info.value.status_code == 401

    @patch("wormai.client.requests.post")
    def test_authentication_error_403(self, mock_post):
        """Test handling of 403 forbidden error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response

        client = GrokClient()
        with pytest.raises(AuthenticationError):
            list(client.chat("test message"))

    @patch("wormai.client.requests.post")
    def test_rate_limit_error(self, mock_post):
        """Test handling of 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"
        mock_response.headers = {"Retry-After": "5"}
        mock_post.return_value = mock_response

        client = GrokClient(max_retries=1)
        with pytest.raises(GrokAPIError) as exc_info:
            list(client.chat("test message"))

        assert exc_info.value.status_code == 429

    @patch("wormai.client.requests.post")
    def test_generic_api_error(self, mock_post):
        """Test handling of generic API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = GrokClient()
        with pytest.raises(GrokAPIError) as exc_info:
            list(client.chat("test message"))

        assert exc_info.value.status_code == 500

    @patch("wormai.client.requests.post")
    def test_network_timeout(self, mock_post):
        """Test handling of network timeout."""
        from curl_cffi import requests as cffi_requests

        mock_post.side_effect = cffi_requests.exceptions.Timeout("Connection timeout")

        client = GrokClient(max_retries=1)
        with pytest.raises(NetworkError):
            list(client.chat("test message"))

    @patch("wormai.client.requests.post")
    def test_network_connection_error(self, mock_post):
        """Test handling of connection error."""
        from curl_cffi import requests as cffi_requests

        mock_post.side_effect = cffi_requests.exceptions.ConnectionError("Connection failed")

        client = GrokClient(max_retries=1)
        with pytest.raises(NetworkError):
            list(client.chat("test message"))


class TestWormAIWrapper:
    """Test WormAI wrapper class."""

    def test_wormai_initialization(self):
        """Test WormAI initialization."""
        client = WormAI()
        assert client.client is not None
        assert client.system_prompt is None

    def test_set_system_prompt(self):
        """Test setting system prompt."""
        client = WormAI()
        prompt = "You are a helpful assistant."
        client.set_system_prompt(prompt)
        assert client.system_prompt == prompt

    def test_set_system_prompt_none(self):
        """Test clearing system prompt."""
        client = WormAI()
        client.set_system_prompt("test")
        client.set_system_prompt(None)
        assert client.system_prompt is None

    def test_reset_conversation(self):
        """Test resetting conversation."""
        client = WormAI()
        client.client.conversation_id = "test_id"
        client.client.response_id = "test_response"
        client.reset()
        assert client.client.conversation_id is None
        assert client.client.response_id is None

    def test_chat_with_invalid_message(self):
        """Test chat with invalid message."""
        client = WormAI()
        with pytest.raises(ValidationError):
            list(client.chat(""))  # Empty message

    @patch("wormai.client.requests.post")
    def test_chat_sync(self, mock_post):
        """Test synchronous chat returns complete response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"result": {"response": {"text": "Hello"}}}).encode(),
            json.dumps({"result": {"response": {"text": "Hello world"}}}).encode(),
        ]
        mock_post.return_value = mock_response

        client = WormAI()
        result = client.chat_sync("test")
        assert result == "Hello world"


class TestGrokClientHelpers:
    """Test GrokClient helper methods."""

    def test_get_headers_without_cookie(self):
        """Test headers without cookie."""
        client = GrokClient()
        headers = client._get_headers()
        assert "cookie" not in headers
        assert headers["content-type"] == "application/json"

    def test_get_headers_with_cookie(self):
        """Test headers include cookie when set."""
        client = GrokClient(cookie="session=test123456")
        headers = client._get_headers()
        assert headers["cookie"] == "session=test123456"

    def test_build_payload_new_conversation(self):
        """Test payload for new conversation."""
        client = GrokClient()
        payload = client._build_payload("Hello", system_prompt="Be helpful")

        assert payload["message"] == "Hello"
        assert payload["customInstructions"] == "Be helpful"
        assert payload["modelSlug"] == "grok-3"
        assert "conversationId" not in payload
        assert "parentResponseId" not in payload

    def test_build_payload_continuing_conversation(self):
        """Test payload includes conversation context."""
        client = GrokClient()
        client.conversation_id = "conv-123"
        client.response_id = "resp-456"

        payload = client._build_payload("Follow up", system_prompt=None)

        assert payload["message"] == "Follow up"
        assert payload["conversationId"] == "conv-123"
        assert payload["parentResponseId"] == "resp-456"
        assert payload["customInstructions"] == ""

    def test_reset(self):
        """Test reset clears conversation context."""
        client = GrokClient()
        client.conversation_id = "conv-123"
        client.response_id = "resp-456"

        client.reset()

        assert client.conversation_id is None
        assert client.response_id is None


class TestGrokClientStreaming:
    """Test streaming response handling."""

    @patch("wormai.client.requests.post")
    def test_streaming_response(self, mock_post):
        """Test streaming yields chunks correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"result": {"response": {"text": "Hello"}}}).encode(),
            json.dumps({"result": {"response": {"text": "Hello world"}}}).encode(),
            json.dumps({"result": {"response": {"text": "Hello world!"}}}).encode(),
        ]
        mock_post.return_value = mock_response

        client = GrokClient()
        chunks = list(client.chat("test"))

        assert chunks == ["Hello", " world", "!"]

    @patch("wormai.client.requests.post")
    def test_streaming_token_response(self, mock_post):
        """Test token-by-token streaming."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"token": "Hello"}).encode(),
            json.dumps({"token": " "}).encode(),
            json.dumps({"token": "world"}).encode(),
        ]
        mock_post.return_value = mock_response

        client = GrokClient()
        chunks = list(client.chat("test"))

        assert chunks == ["Hello", " ", "world"]

    @patch("wormai.client.requests.post")
    def test_streaming_extracts_conversation_id(self, mock_post):
        """Test conversation ID is extracted from response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"conversationId": "conv-new", "responseId": "resp-new"}).encode(),
            json.dumps({"result": {"response": {"text": "Hi"}}}).encode(),
        ]
        mock_post.return_value = mock_response

        client = GrokClient()
        list(client.chat("test"))

        assert client.conversation_id == "conv-new"
        assert client.response_id == "resp-new"

    @patch("wormai.client.requests.post")
    def test_streaming_skips_empty_lines(self, mock_post):
        """Test empty lines are skipped."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"",
            json.dumps({"result": {"response": {"text": "Hello"}}}).encode(),
            b"",
            b"",
        ]
        mock_post.return_value = mock_response

        client = GrokClient()
        chunks = list(client.chat("test"))

        assert chunks == ["Hello"]

    @patch("wormai.client.requests.post")
    def test_streaming_handles_invalid_json(self, mock_post):
        """Test invalid JSON lines are handled gracefully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"not valid json",
            json.dumps({"result": {"response": {"text": "Hello"}}}).encode(),
        ]
        mock_post.return_value = mock_response

        client = GrokClient()
        chunks = list(client.chat("test"))

        # Non-JSON text starting without { is yielded
        assert "not valid json" in chunks
        assert "Hello" in chunks


class TestGrokClientRetry:
    """Test retry logic."""

    @patch("wormai.client.time.sleep")
    @patch("wormai.client.requests.post")
    def test_rate_limit_retry_succeeds(self, mock_post, mock_sleep):
        """Test rate limit triggers retry and eventually succeeds."""
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.text = "Rate limited"
        rate_limit_response.headers = {"Retry-After": "1"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.iter_lines.return_value = [
            json.dumps({"result": {"response": {"text": "OK"}}}).encode()
        ]

        mock_post.side_effect = [rate_limit_response, success_response]

        client = GrokClient(max_retries=2, retry_delay=0.1)
        chunks = list(client.chat("test"))

        assert chunks == ["OK"]
        assert mock_sleep.called

    @patch("wormai.client.time.sleep")
    @patch("wormai.client.requests.post")
    def test_network_error_retry(self, mock_post, mock_sleep):
        """Test network errors trigger retry with backoff."""
        from curl_cffi import requests as cffi_requests

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"result": {"response": {"text": "Success"}}}).encode()
        ]

        mock_post.side_effect = [
            cffi_requests.exceptions.ConnectionError("Failed"),
            mock_response,
        ]

        client = GrokClient(max_retries=2, retry_delay=0.1)
        chunks = list(client.chat("test"))

        assert chunks == ["Success"]
        mock_sleep.assert_called()

    @patch("wormai.client.time.sleep")
    @patch("wormai.client.requests.post")
    def test_unexpected_error_retry(self, mock_post, mock_sleep):
        """Test unexpected errors trigger retry."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"result": {"response": {"text": "OK"}}}).encode()
        ]

        mock_post.side_effect = [RuntimeError("Unexpected"), mock_response]

        client = GrokClient(max_retries=2, retry_delay=0.1)
        chunks = list(client.chat("test"))

        assert chunks == ["OK"]

    @patch("wormai.client.time.sleep")
    @patch("wormai.client.requests.post")
    def test_all_retries_exhausted(self, mock_post, mock_sleep):
        """Test error raised after all retries fail."""
        from curl_cffi import requests as cffi_requests

        mock_post.side_effect = cffi_requests.exceptions.Timeout("Timeout")

        client = GrokClient(max_retries=3, retry_delay=0.1)

        with pytest.raises(NetworkError):
            list(client.chat("test"))

        # Should have retried max_retries times
        assert mock_post.call_count == 3

    @patch("wormai.client.requests.post")
    def test_auth_error_no_retry(self, mock_post):
        """Test authentication errors don't trigger retry."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        client = GrokClient(max_retries=3)

        with pytest.raises(AuthenticationError):
            list(client.chat("test"))

        # Should NOT retry on auth error
        assert mock_post.call_count == 1
