"""Improved tests for Worm-AI client with error handling."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from wormai.client import GrokClient, WormAI
from wormai.exceptions import (
    GrokAPIError,
    NetworkError,
    AuthenticationError,
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

    @patch('wormai.client.requests.post')
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

    @patch('wormai.client.requests.post')
    def test_authentication_error_403(self, mock_post):
        """Test handling of 403 forbidden error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response

        client = GrokClient()
        with pytest.raises(AuthenticationError):
            list(client.chat("test message"))

    @patch('wormai.client.requests.post')
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

    @patch('wormai.client.requests.post')
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

    @patch('wormai.client.requests.post')
    def test_network_timeout(self, mock_post):
        """Test handling of network timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")

        client = GrokClient(max_retries=1)
        with pytest.raises(NetworkError):
            list(client.chat("test message"))

    @patch('wormai.client.requests.post')
    def test_network_connection_error(self, mock_post):
        """Test handling of connection error."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

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
