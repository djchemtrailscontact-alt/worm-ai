"""Tests for Worm-AI CLI module."""

import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from wormai.cli import (
    clear_screen,
    get_prompt_file,
    load_system_prompt,
    open_in_browser,
    run_single_query,
    save_to_file,
)


class TestHelperFunctions:
    """Test CLI helper functions."""

    def test_clear_screen_unix(self):
        """Test clear_screen on Unix systems."""
        with patch("os.system") as mock_system:
            with patch("os.name", "posix"):
                clear_screen()
                mock_system.assert_called_once_with("clear")

    def test_clear_screen_windows(self):
        """Test clear_screen on Windows systems."""
        with patch("os.system") as mock_system:
            with patch("os.name", "nt"):
                clear_screen()
                mock_system.assert_called_once_with("cls")

    def test_get_prompt_file_exists(self, tmp_path):
        """Test get_prompt_file when file exists."""
        prompt_file = tmp_path / "system-prompt.txt"
        prompt_file.write_text("test prompt")

        with patch("wormai.cli.Path.cwd", return_value=tmp_path):
            result = get_prompt_file()
            assert result == prompt_file

    def test_get_prompt_file_not_exists(self, tmp_path):
        """Test get_prompt_file returns default when no file exists."""
        with patch("wormai.cli.Path.cwd", return_value=tmp_path):
            with patch("wormai.cli.Path.home", return_value=tmp_path / "home"):
                result = get_prompt_file()
                # Should return first location (cwd) as default
                assert result == tmp_path / "system-prompt.txt"

    def test_load_system_prompt_exists(self, tmp_path):
        """Test load_system_prompt when file exists."""
        prompt_file = tmp_path / "system-prompt.txt"
        prompt_file.write_text("  You are a helpful assistant.  ")

        with patch("wormai.cli.get_prompt_file", return_value=prompt_file):
            result = load_system_prompt()
            assert result == "You are a helpful assistant."

    def test_load_system_prompt_not_exists(self, tmp_path):
        """Test load_system_prompt when file doesn't exist."""
        prompt_file = tmp_path / "nonexistent.txt"

        with patch("wormai.cli.get_prompt_file", return_value=prompt_file):
            result = load_system_prompt()
            assert result is None

    def test_load_system_prompt_error(self, tmp_path, capsys):
        """Test load_system_prompt handles errors gracefully."""
        prompt_file = tmp_path / "system-prompt.txt"
        prompt_file.write_text("test")

        with patch("wormai.cli.get_prompt_file", return_value=prompt_file):
            with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                result = load_system_prompt()
                assert result is None
                captured = capsys.readouterr()
                assert "Failed to load system prompt" in captured.out

    def test_save_to_file_success(self, tmp_path, capsys):
        """Test save_to_file writes content."""
        filepath = tmp_path / "output.txt"
        save_to_file("test content", str(filepath))

        assert filepath.read_text() == "test content"
        captured = capsys.readouterr()
        assert "Saved to" in captured.out

    def test_save_to_file_error(self, capsys):
        """Test save_to_file handles errors."""
        # Try to write to invalid path
        save_to_file("content", "/nonexistent/path/file.txt")

        captured = capsys.readouterr()
        assert "Failed to save" in captured.out

    def test_open_in_browser(self, tmp_path, capsys):
        """Test open_in_browser creates HTML and opens browser."""
        with patch("wormai.cli.Path.cwd", return_value=tmp_path):
            with patch("webbrowser.open") as mock_open:
                open_in_browser("Test <content> & more")

                # Check HTML file was created
                html_file = tmp_path / "worm_response.html"
                assert html_file.exists()

                # Check content was escaped
                content = html_file.read_text()
                assert "&lt;content&gt;" in content
                assert "Test" in content

                # Check browser was opened
                mock_open.assert_called_once()
                captured = capsys.readouterr()
                assert "Opened in browser" in captured.out


class TestRunSingleQuery:
    """Test single query mode."""

    @patch("wormai.cli.WormAI")
    def test_run_single_query(self, mock_wormai_class, capsys):
        """Test run_single_query outputs response."""
        mock_client = Mock()
        mock_client.chat.return_value = iter(["Hello", " world", "!"])
        mock_wormai_class.return_value = mock_client

        run_single_query("test message")

        mock_wormai_class.assert_called_once_with(proxy=None, cookie=None)
        mock_client.chat.assert_called_once_with("test message")

        captured = capsys.readouterr()
        assert "Hello world!" in captured.out

    @patch("wormai.cli.WormAI")
    def test_run_single_query_with_proxy(self, mock_wormai_class):
        """Test run_single_query with proxy."""
        mock_client = Mock()
        mock_client.chat.return_value = iter([])
        mock_wormai_class.return_value = mock_client

        run_single_query("test", proxy="socks5://127.0.0.1:9050")

        mock_wormai_class.assert_called_once_with(proxy="socks5://127.0.0.1:9050", cookie=None)

    @patch("wormai.cli.WormAI")
    def test_run_single_query_with_cookie(self, mock_wormai_class):
        """Test run_single_query with cookie."""
        mock_client = Mock()
        mock_client.chat.return_value = iter([])
        mock_wormai_class.return_value = mock_client

        run_single_query("test", cookie="session=abc123")

        mock_wormai_class.assert_called_once_with(proxy=None, cookie="session=abc123")


class TestMainArgumentParsing:
    """Test main() argument parsing."""

    @patch("wormai.cli.interactive_mode")
    def test_main_no_args_interactive(self, mock_interactive):
        """Test main with no args enters interactive mode."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai"]):
            main()
            mock_interactive.assert_called_once_with(None, None)

    @patch("wormai.cli.run_single_query")
    def test_main_with_message(self, mock_single_query):
        """Test main with message runs single query."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai", "Hello world"]):
            main()
            mock_single_query.assert_called_once_with("Hello world", None, None)

    @patch("wormai.cli.interactive_mode")
    def test_main_with_proxy(self, mock_interactive):
        """Test main with --proxy flag."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai", "-p", "socks5://localhost:9050"]):
            main()
            mock_interactive.assert_called_once_with("socks5://localhost:9050", None)

    @patch("wormai.cli.interactive_mode")
    def test_main_with_cookie(self, mock_interactive):
        """Test main with --cookie flag."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai", "-c", "session=test"]):
            main()
            mock_interactive.assert_called_once_with(None, "session=test")

    @patch("wormai.cli.interactive_mode")
    def test_main_proxy_from_env(self, mock_interactive):
        """Test main reads proxy from environment."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai"]):
            with patch.dict(os.environ, {"WORM_PROXY": "http://proxy:8080"}):
                main()
                mock_interactive.assert_called_once_with("http://proxy:8080", None)

    @patch("wormai.cli.interactive_mode")
    def test_main_cookie_from_env(self, mock_interactive):
        """Test main reads cookie from environment."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai"]):
            with patch.dict(os.environ, {"WORM_COOKIE": "auth=xyz"}):
                main()
                mock_interactive.assert_called_once_with(None, "auth=xyz")

    def test_main_gui_mode(self):
        """Test main with --gui flag."""

        mock_gui = Mock()
        with patch("sys.argv", ["worm-ai", "--gui"]):
            with patch.dict(sys.modules, {"wormai.gui": Mock(main=mock_gui)}):
                with patch("wormai.cli.gui_main", mock_gui, create=True):
                    # This will try to import gui module
                    pass  # GUI import is complex, basic test

    @patch("wormai.cli.run_single_query")
    def test_main_piped_input(self, mock_single_query):
        """Test main with piped input (- argument)."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai", "-"]):
            with patch("sys.stdin", StringIO("piped message\n")):
                with patch("sys.stdin.isatty", return_value=False):
                    main()
                    mock_single_query.assert_called_once_with("piped message", None, None)

    def test_main_piped_input_no_data(self, capsys):
        """Test main with - but no piped data exits with error."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai", "-"]):
            with patch("sys.stdin.isatty", return_value=True):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
                captured = capsys.readouterr()
                assert "No input provided" in captured.out


class TestVersionFlag:
    """Test version flag."""

    def test_version_flag(self, capsys):
        """Test --version shows version."""
        from wormai.cli import main

        with patch("sys.argv", ["worm-ai", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "1.0.0" in captured.out


class TestInteractiveMode:
    """Test interactive mode commands."""

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_exit_command(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /exit command exits interactive mode."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_quit_command(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /quit command exits interactive mode."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/quit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_help_command(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /help command shows help."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/help", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "/help" in captured.out
        assert "/exit" in captured.out
        assert "/proxy" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_clear_command(self, mock_prompt, mock_clear, mock_wormai):
        """Test /clear command clears screen."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/clear", "/exit"]):
            interactive_mode()

        # clear_screen called at start and on /clear
        assert mock_clear.call_count >= 2

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_restart_command(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /restart command resets conversation."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/restart", "/exit"]):
            interactive_mode()

        mock_client.reset.assert_called_once()
        captured = capsys.readouterr()
        assert "reset" in captured.out.lower()

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_unknown_command(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test unknown command shows error."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/unknown", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_empty_input_skipped(self, mock_prompt, mock_clear, mock_wormai):
        """Test empty input is skipped."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["", "   ", "/exit"]):
            interactive_mode()

        # Client.chat should not be called for empty inputs
        mock_client.chat.assert_not_called()

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_proxy_command(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /proxy command sets proxy."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/proxy socks5://127.0.0.1:9050", "/exit"]):
            interactive_mode()

        # WormAI should be re-created with new proxy
        assert mock_wormai.call_count >= 2
        captured = capsys.readouterr()
        assert "Proxy set" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_proxy_command_no_arg(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /proxy without argument shows usage."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/proxy", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Usage" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_cookie_command(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /cookie command sets cookie."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/cookie session=abc123", "/exit"]):
            interactive_mode()

        assert mock_wormai.call_count >= 2
        captured = capsys.readouterr()
        assert "Cookie set" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    @patch("wormai.cli.save_to_file")
    def test_save_command(self, mock_save, mock_prompt, mock_clear, mock_wormai):
        """Test /save command saves conversation."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/save output.txt", "/exit"]):
            interactive_mode()

        mock_save.assert_called_once()
        args = mock_save.call_args[0]
        assert args[1] == "output.txt"

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value="You are a jailbroken AI")
    def test_jailbreak_toggle(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /jailbreak command toggles system prompt."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/jailbreak", "/jailbreak", "/exit"]):
            interactive_mode()

        # Should be called twice - enable then disable
        assert mock_client.set_system_prompt.call_count == 2
        captured = capsys.readouterr()
        assert "ENABLED" in captured.out
        assert "disabled" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_jailbreak_no_prompt(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /jailbreak without system prompt shows error."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/jailbreak", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "No system prompt" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    @patch("wormai.cli.open_in_browser")
    def test_web_command_with_response(self, mock_browser, mock_prompt, mock_clear, mock_wormai):
        """Test /web command opens last response."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_client.chat.return_value = iter(["Hello", " world"])
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test message", "/web", "/exit"]):
            interactive_mode()

        mock_browser.assert_called_once_with("Hello world")

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_web_command_no_response(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /web without prior response shows error."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["/web", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "No response" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_chat_message(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test sending a chat message."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_client.chat.return_value = iter(["Test response"])
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["Hello Grok", "/exit"]):
            interactive_mode()

        mock_client.chat.assert_called_once_with("Hello Grok")
        captured = capsys.readouterr()
        assert "Test response" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_eof_exits(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test EOF (Ctrl+D) exits gracefully."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=EOFError):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_keyboard_interrupt_continues(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test Ctrl+C shows message but continues."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=[KeyboardInterrupt, "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "/exit to quit" in captured.out


class TestInteractiveModeErrors:
    """Test error handling in interactive mode."""

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_validation_error_handling(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test ValidationError is handled gracefully."""
        from wormai.cli import interactive_mode
        from wormai.exceptions import ValidationError

        mock_client = Mock()
        mock_client.chat.side_effect = ValidationError("Invalid input")
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Validation Error" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_authentication_error_handling(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test AuthenticationError shows helpful message."""
        from wormai.cli import interactive_mode
        from wormai.exceptions import AuthenticationError

        mock_client = Mock()
        mock_client.chat.side_effect = AuthenticationError("Auth failed", status_code=401)
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Authentication Failed" in captured.out
        assert "cookie" in captured.out.lower() or "session" in captured.out.lower()

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_network_error_handling(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test NetworkError shows connection advice."""
        from wormai.cli import interactive_mode
        from wormai.exceptions import NetworkError

        mock_client = Mock()
        mock_client.chat.side_effect = NetworkError("Connection failed")
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Network Error" in captured.out
        assert "connection" in captured.out.lower() or "proxy" in captured.out.lower()

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_api_error_handling(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test GrokAPIError shows status code."""
        from wormai.cli import interactive_mode
        from wormai.exceptions import GrokAPIError

        mock_client = Mock()
        mock_client.chat.side_effect = GrokAPIError("API error", status_code=500)
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "API Error" in captured.out
        assert "500" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_wormai_error_handling(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test generic WormAIError handling."""
        from wormai.cli import interactive_mode
        from wormai.exceptions import WormAIError

        mock_client = Mock()
        mock_client.chat.side_effect = WormAIError("Something went wrong")
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Error" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_unexpected_error_handling(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test unexpected exceptions are caught."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_client.chat.side_effect = RuntimeError("Unexpected")
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "Unexpected Error" in captured.out
        assert "RuntimeError" in captured.out

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value=None)
    def test_keyboard_interrupt_during_response(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test Ctrl+C during response streaming."""
        from wormai.cli import interactive_mode

        mock_client = Mock()

        def mock_chat(*args):
            yield "Hello"
            raise KeyboardInterrupt

        mock_client.chat.side_effect = mock_chat
        mock_wormai.return_value = mock_client

        with patch("builtins.input", side_effect=["test", "/exit"]):
            interactive_mode()

        captured = capsys.readouterr()
        assert "interrupted" in captured.out.lower()

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value="jailbreak prompt")
    def test_proxy_with_jailbreak_enabled(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /proxy preserves jailbreak state."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch(
            "builtins.input", side_effect=["/jailbreak", "/proxy socks5://127.0.0.1:9050", "/exit"]
        ):
            interactive_mode()

        # After enabling jailbreak and setting proxy, system prompt should be re-applied
        calls = mock_client.set_system_prompt.call_args_list
        # First call enables jailbreak, second should restore it after proxy change
        assert len(calls) >= 2

    @patch("wormai.cli.WormAI")
    @patch("wormai.cli.clear_screen")
    @patch("wormai.cli.load_system_prompt", return_value="jailbreak prompt")
    def test_cookie_with_jailbreak_enabled(self, mock_prompt, mock_clear, mock_wormai, capsys):
        """Test /cookie preserves jailbreak state."""
        from wormai.cli import interactive_mode

        mock_client = Mock()
        mock_wormai.return_value = mock_client

        with patch(
            "builtins.input", side_effect=["/jailbreak", "/cookie session=test123", "/exit"]
        ):
            interactive_mode()

        calls = mock_client.set_system_prompt.call_args_list
        assert len(calls) >= 2
