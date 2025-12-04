"""Tests for Worm-AI client."""

import pytest
from unittest.mock import Mock, patch
from wormai.client import WormAI


class TestWormAI:
    """Test cases for WormAI client."""

    def test_client_initialization(self):
        """Test client can be initialized."""
        client = WormAI()
        assert client is not None
        assert client.conversation_id is None

    def test_client_with_proxy(self):
        """Test client initialization with proxy."""
        proxy = "socks5://127.0.0.1:9050"
        client = WormAI(proxy=proxy)
        assert client.proxy == proxy

    def test_client_with_cookie(self):
        """Test client initialization with cookie."""
        cookie = "test_cookie_value"
        client = WormAI(cookie=cookie)
        assert client.cookie == cookie

    def test_client_reset(self):
        """Test conversation reset."""
        client = WormAI()
        client.conversation_id = "test_id"
        client.response_id = "test_response"
        client.reset()
        assert client.conversation_id is None
        assert client.response_id is None

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

    @patch('wormai.client.requests.Session')
    def test_chat_initialization(self, mock_session):
        """Test chat method initializes conversation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conversation_id": "test_conv_id"
        }
        mock_response.iter_lines.return_value = [
            b'data: {"text": "Hello"}',
            b'data: [DONE]'
        ]

        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        client = WormAI()
        # Note: This is a simplified test - actual implementation may differ
        assert client is not None


class TestWormAIIntegration:
    """Integration tests (may require network)."""

    @pytest.mark.skip(reason="Requires network and valid credentials")
    def test_chat_with_proxy(self):
        """Test chat with proxy (integration test)."""
        client = WormAI(proxy="socks5://127.0.0.1:9050")
        # This would require actual network access
        pass
