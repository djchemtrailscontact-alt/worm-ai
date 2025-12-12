#!/usr/bin/env python3
"""
🐛 Worm-AI CLI — Grok Edition
A terminal-based AI chat client for Grok.

For educational and research purposes only.
"""

import os
import sys
import time
import argparse
import webbrowser
import logging
from pathlib import Path
from typing import Optional

from colorama import Fore, Style, init as colorama_init

from .client import WormAI
from .exceptions import (
    WormAIError,
    GrokAPIError,
    NetworkError,
    AuthenticationError,
    ValidationError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize colorama for cross-platform color support
colorama_init(autoreset=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

BANNER = f"""
{Fore.RED}██╗    ██╗ ██████╗ ██████╗ ███╗   ███╗     █████╗ ██╗{Style.RESET_ALL}
{Fore.RED}██║    ██║██╔═══██╗██╔══██╗████╗ ████║    ██╔══██╗██║{Style.RESET_ALL}
{Fore.YELLOW}██║ █╗ ██║██║   ██║██████╔╝██╔████╔██║    ███████║██║{Style.RESET_ALL}
{Fore.YELLOW}██║███╗██║██║   ██║██╔══██╗██║╚██╔╝██║    ██╔══██║██║{Style.RESET_ALL}
{Fore.GREEN}╚███╔███╔╝╚██████╔╝██║  ██║██║ ╚═╝ ██║    ██║  ██║██║{Style.RESET_ALL}
{Fore.GREEN} ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═╝╚═╝{Style.RESET_ALL}
{Fore.CYAN}═══════════════════════════════════════════════════════{Style.RESET_ALL}
{Fore.WHITE}        🐛 Grok API CLI — Kali Linux Edition{Style.RESET_ALL}
{Fore.CYAN}═══════════════════════════════════════════════════════{Style.RESET_ALL}
"""

HELP_TEXT = f"""
{Fore.CYAN}Commands:{Style.RESET_ALL}
  {Fore.GREEN}/help{Style.RESET_ALL}      - Show this help message
  {Fore.GREEN}/exit{Style.RESET_ALL}      - Exit the application
  {Fore.GREEN}/quit{Style.RESET_ALL}      - Same as /exit
  {Fore.GREEN}/clear{Style.RESET_ALL}     - Clear the screen
  {Fore.GREEN}/restart{Style.RESET_ALL}   - Reset conversation context
  {Fore.GREEN}/web{Style.RESET_ALL}       - Open last response in browser
  {Fore.GREEN}/proxy URL{Style.RESET_ALL} - Set proxy (e.g., socks5://127.0.0.1:9050)
  {Fore.GREEN}/cookie X{Style.RESET_ALL}  - Set session cookie for auth
  {Fore.GREEN}/save FILE{Style.RESET_ALL} - Save conversation to file
  {Fore.GREEN}/jailbreak{Style.RESET_ALL} - Toggle jailbreak system prompt
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def clear_screen():
    """Clear the terminal screen."""
    os.system("clear" if os.name != "nt" else "cls")


def get_prompt_file() -> Path:
    """Get the path to the system prompt file."""
    # Check multiple locations
    locations = [
        Path.cwd() / "system-prompt.txt",
        Path.home() / ".config" / "worm-ai" / "system-prompt.txt",
        Path.home() / ".worm-ai" / "system-prompt.txt",
        Path(__file__).parent / "system-prompt.txt",
    ]
    for loc in locations:
        if loc.exists():
            return loc
    return locations[0]  # Default to current dir


def load_system_prompt() -> Optional[str]:
    """Load system prompt from file if exists."""
    try:
        prompt_file = get_prompt_file()
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to load system prompt: {e}{Style.RESET_ALL}")
    return None


def save_to_file(content: str, filename: str):
    """Save content to a file."""
    try:
        Path(filename).write_text(content, encoding="utf-8")
        print(f"{Fore.GREEN}[+] Saved to {filename}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to save: {e}{Style.RESET_ALL}")


def open_in_browser(content: str):
    """Open content in web browser."""
    try:
        path = Path.cwd() / "worm_response.html"
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Worm-AI Response</title>
    <style>
        body {{
            background: #1a1a2e;
            color: #eee;
            font-family: 'Fira Code', 'Consolas', monospace;
            padding: 40px;
            line-height: 1.8;
        }}
        pre {{
            background: #16213e;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #e94560;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        h1 {{ color: #e94560; }}
    </style>
</head>
<body>
    <h1>🐛 Worm-AI Response</h1>
    <pre>{content.replace('<', '&lt;').replace('>', '&gt;')}</pre>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")
        webbrowser.open(f"file://{path}")
        print(f"{Fore.GREEN}[+] Opened in browser{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to open browser: {e}{Style.RESET_ALL}")


def run_single_query(message: str, proxy: Optional[str] = None, cookie: Optional[str] = None):
    """Run a single query and exit (non-interactive mode)."""
    client = WormAI(proxy=proxy, cookie=cookie)
    for chunk in client.chat(message):
        print(chunk, end="", flush=True)
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# Main CLI
# ═══════════════════════════════════════════════════════════════════════════════


def interactive_mode(proxy: Optional[str] = None, cookie: Optional[str] = None):
    """Run the interactive CLI mode."""
    clear_screen()
    print(BANNER)

    # Initialize client
    client = WormAI(proxy=proxy, cookie=cookie)

    # Load jailbreak prompt
    system_prompt = load_system_prompt()
    jailbreak_enabled = False

    if system_prompt:
        print(f"{Fore.YELLOW}[*] System prompt loaded ({len(system_prompt)} chars){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Use /jailbreak to enable it{Style.RESET_ALL}")

    if proxy:
        print(f"{Fore.CYAN}[*] Proxy: {proxy}{Style.RESET_ALL}")

    print(f"\n{Fore.WHITE}Type your message and press Enter. Use /help for commands.{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Made with 💀 | t.me/xsocietyforums | github.com/kafyasfngl{Style.RESET_ALL}\n")

    last_response = ""
    conversation_log = []

    while True:
        try:
            # Get user input
            user_input = input(
                f"{Fore.RED}┌──({Fore.WHITE}worm{Fore.RED})-[{Fore.CYAN}~{Fore.RED}]\n└─{Fore.WHITE}$ {Style.RESET_ALL}"
            ).strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]
                args = user_input[len(cmd) :].strip()

                if cmd in ("/exit", "/quit"):
                    print(f"\n{Fore.YELLOW}[*] Goodbye! 👋{Style.RESET_ALL}")
                    break

                elif cmd == "/help":
                    print(HELP_TEXT)
                    continue

                elif cmd == "/clear":
                    clear_screen()
                    print(BANNER)
                    continue

                elif cmd == "/restart":
                    client.reset()
                    conversation_log = []
                    print(f"{Fore.GREEN}[+] Conversation reset{Style.RESET_ALL}")
                    continue

                elif cmd == "/web":
                    if last_response:
                        open_in_browser(last_response)
                    else:
                        print(f"{Fore.YELLOW}[!] No response to display{Style.RESET_ALL}")
                    continue

                elif cmd == "/proxy":
                    if args:
                        proxy = args
                        client = WormAI(proxy=args, cookie=cookie)
                        if jailbreak_enabled and system_prompt:
                            client.set_system_prompt(system_prompt)
                        print(f"{Fore.GREEN}[+] Proxy set to: {args}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[!] Usage: /proxy <url>{Style.RESET_ALL}")
                    continue

                elif cmd == "/cookie":
                    if args:
                        cookie = args
                        client = WormAI(proxy=proxy, cookie=cookie)
                        if jailbreak_enabled and system_prompt:
                            client.set_system_prompt(system_prompt)
                        print(f"{Fore.GREEN}[+] Cookie set{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[!] Usage: /cookie <value>{Style.RESET_ALL}")
                    continue

                elif cmd == "/save":
                    if args:
                        content = "\n\n".join(
                            [f"[User]: {u}\n[AI]: {r}" for u, r in conversation_log]
                        )
                        save_to_file(content, args)
                    else:
                        print(f"{Fore.YELLOW}[!] Usage: /save <filename>{Style.RESET_ALL}")
                    continue

                elif cmd == "/jailbreak":
                    if system_prompt:
                        jailbreak_enabled = not jailbreak_enabled
                        if jailbreak_enabled:
                            client.set_system_prompt(system_prompt)
                            print(f"{Fore.RED}[!] Jailbreak mode ENABLED 😈{Style.RESET_ALL}")
                        else:
                            client.set_system_prompt(None)
                            print(f"{Fore.GREEN}[+] Jailbreak mode disabled{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[!] No system prompt loaded{Style.RESET_ALL}")
                    continue

                else:
                    print(f"{Fore.YELLOW}[!] Unknown command. Use /help{Style.RESET_ALL}")
                    continue

            # Send message to Grok
            print(f"\n{Fore.GREEN}[Grok]{Style.RESET_ALL} ", end="", flush=True)

            response_parts = []
            try:
                for chunk in client.chat(user_input):
                    print(chunk, end="", flush=True)
                    response_parts.append(chunk)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Response interrupted{Style.RESET_ALL}")
            except ValidationError as e:
                print(f"\n{Fore.RED}[!] Validation Error: {e}{Style.RESET_ALL}")
                continue
            except AuthenticationError as e:
                print(f"\n{Fore.RED}[!] Authentication Failed: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[*] Check your cookie or session{Style.RESET_ALL}")
                continue
            except NetworkError as e:
                print(f"\n{Fore.RED}[!] Network Error: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[*] Check your connection or proxy settings{Style.RESET_ALL}")
                continue
            except GrokAPIError as e:
                print(f"\n{Fore.RED}[!] API Error: {e}{Style.RESET_ALL}")
                if e.status_code:
                    print(f"{Fore.YELLOW}[*] HTTP {e.status_code}{Style.RESET_ALL}")
                continue

            last_response = "".join(response_parts)
            conversation_log.append((user_input, last_response))
            print("\n")

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[*] Use /exit to quit{Style.RESET_ALL}")
        except EOFError:
            print(f"\n{Fore.YELLOW}[*] Goodbye! 👋{Style.RESET_ALL}")
            break
        except WormAIError as e:
            print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] Unexpected Error: {type(e).__name__}: {e}{Style.RESET_ALL}")
            logger.exception("Unexpected error in interactive mode")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        prog="worm-ai",
        description="🐛 Worm-AI — Grok API CLI for Kali Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  worm-ai                           # Interactive CLI mode
  worm-ai --gui                     # Launch GUI
  worm-ai "What is XSS?"           # Single query
  worm-ai -p socks5://127.0.0.1:9050  # Use Tor proxy
  echo "Explain SQLi" | worm-ai -  # Pipe input

Made with 💀 | t.me/xsocietyforums | github.com/kafyasfngl
        """,
    )

    parser.add_argument(
        "message",
        nargs="?",
        default=None,
        help="Message to send (interactive mode if omitted)",
    )

    parser.add_argument(
        "-p", "--proxy",
        metavar="URL",
        help="Proxy URL (e.g., socks5://127.0.0.1:9050)",
    )

    parser.add_argument(
        "-c", "--cookie",
        metavar="COOKIE",
        help="Session cookie for authenticated requests",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    parser.add_argument(
        "-g", "--gui",
        action="store_true",
        help="Launch the graphical user interface",
    )

    args = parser.parse_args()

    # Launch GUI if requested
    if args.gui:
        try:
            from .gui import main as gui_main
            gui_main()
            return
        except ImportError as e:
            print(f"{Fore.RED}[!] GUI requires customtkinter: pip install customtkinter{Style.RESET_ALL}")
            print(f"{Fore.RED}[!] Also install: sudo apt install python3-tk{Style.RESET_ALL}")
            sys.exit(1)

    # Get proxy/cookie from env if not provided
    proxy = args.proxy or os.getenv("WORM_PROXY") or os.getenv("GROK_PROXY")
    cookie = args.cookie or os.getenv("WORM_COOKIE") or os.getenv("GROK_COOKIE")

    # Handle piped input
    if args.message == "-":
        if not sys.stdin.isatty():
            message = sys.stdin.read().strip()
            if message:
                run_single_query(message, proxy, cookie)
                return
        print(f"{Fore.RED}[!] No input provided{Style.RESET_ALL}")
        sys.exit(1)

    # Single query mode
    if args.message:
        run_single_query(args.message, proxy, cookie)
        return

    # Interactive mode
    interactive_mode(proxy, cookie)


if __name__ == "__main__":
    main()
