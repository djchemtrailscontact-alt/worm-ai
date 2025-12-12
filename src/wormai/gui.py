#!/usr/bin/env python3
"""
🐛 Worm-AI GUI — Grok Edition
A modern GUI client for Grok AI.
"""

import os
import threading
from pathlib import Path
from typing import Optional

try:
    import customtkinter as ctk
except ImportError as err:
    raise ImportError(
        "customtkinter is required for GUI. Install with: pip install customtkinter"
    ) from err

from .client import WormAI
from .exceptions import (
    AuthenticationError,
    GrokAPIError,
    NetworkError,
    ValidationError,
    WormAIError,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Theme Configuration
# ═══════════════════════════════════════════════════════════════════════════════

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Custom colors
COLORS = {
    "bg_dark": "#0d1117",
    "bg_medium": "#161b22",
    "bg_light": "#21262d",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "text": "#c9d1d9",
    "text_dim": "#8b949e",
    "success": "#3fb950",
    "warning": "#d29922",
    "border": "#30363d",
}


class WormAIApp(ctk.CTk):
    """Main Worm-AI GUI Application."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("🐛 Worm-AI — Grok Client")
        self.geometry("900x700")
        self.minsize(700, 500)

        # Configure colors
        self.configure(fg_color=COLORS["bg_dark"])

        # State
        self.client: Optional[WormAI] = None
        self.is_streaming = False
        self.current_thread: Optional[threading.Thread] = None
        self.conversation_history = []

        # Build UI
        self._create_widgets()
        self._bind_events()

        # Initialize client
        self._init_client()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ─────────────────────────────────────────────────────────────────────
        # Header
        # ─────────────────────────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=60)
        self.header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header.grid_columnconfigure(1, weight=1)

        # Logo/Title
        self.title_label = ctk.CTkLabel(
            self.header,
            text="🐛 WORM-AI",
            font=ctk.CTkFont(family="Courier", size=24, weight="bold"),
            text_color=COLORS["accent"],
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=15)

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.header,
            text="Grok API Client",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self.subtitle_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        # Settings button
        self.settings_btn = ctk.CTkButton(
            self.header,
            text="⚙️",
            width=40,
            height=40,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["border"],
            command=self._show_settings,
        )
        self.settings_btn.grid(row=0, column=2, padx=10, pady=15)

        # Clear button
        self.clear_btn = ctk.CTkButton(
            self.header,
            text="🗑️ Clear",
            width=80,
            height=40,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["border"],
            command=self._clear_chat,
        )
        self.clear_btn.grid(row=0, column=3, padx=(0, 20), pady=15)

        # ─────────────────────────────────────────────────────────────────────
        # Chat Area
        # ─────────────────────────────────────────────────────────────────────
        self.chat_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        # Chat display (scrollable text)
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=COLORS["bg_medium"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
            wrap="word",
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        self.chat_display.configure(state="disabled")

        # Welcome message
        self._append_system("Welcome to Worm-AI! Type a message to chat with Grok.")
        self._append_system("Use /help for commands or ⚙️ for settings.\n")

        # ─────────────────────────────────────────────────────────────────────
        # Input Area
        # ─────────────────────────────────────────────────────────────────────
        self.input_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=80)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Input field
        self.input_field = ctk.CTkTextbox(
            self.input_frame,
            height=60,
            font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=COLORS["bg_light"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            wrap="word",
        )
        self.input_field.grid(row=0, column=0, sticky="ew", padx=15, pady=15)

        # Send button
        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Send ▶",
            width=100,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._send_message,
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 15), pady=15)

        # ─────────────────────────────────────────────────────────────────────
        # Status Bar
        # ─────────────────────────────────────────────────────────────────────
        self.status_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], height=30)
        self.status_bar.grid(row=3, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        )
        self.status_label.pack(side="left", padx=15, pady=5)

        self.proxy_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["warning"],
        )
        self.proxy_label.pack(side="right", padx=15, pady=5)

    def _bind_events(self):
        """Bind keyboard events."""
        self.input_field.bind("<Return>", self._on_enter)
        self.input_field.bind("<Shift-Return>", self._on_shift_enter)
        self.bind("<Escape>", lambda e: self._stop_streaming())

    def _on_enter(self, event):
        """Handle Enter key."""
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return "break"

    def _on_shift_enter(self, event):
        """Handle Shift+Enter for newline."""
        return None  # Allow default behavior

    def _init_client(self):
        """Initialize the Grok client."""
        proxy = os.getenv("WORM_PROXY") or os.getenv("GROK_PROXY")
        cookie = os.getenv("WORM_COOKIE") or os.getenv("GROK_COOKIE")

        self.client = WormAI(proxy=proxy, cookie=cookie)

        if proxy:
            self.proxy_label.configure(text=f"🔒 Proxy: {proxy[:30]}...")

        # Load system prompt
        self._load_system_prompt()

    def _load_system_prompt(self):
        """Load system prompt from file."""
        locations = [
            Path.cwd() / "system-prompt.txt",
            Path.home() / ".config" / "worm-ai" / "system-prompt.txt",
            Path(__file__).parent / "system-prompt.txt",
        ]
        for loc in locations:
            if loc.exists():
                try:
                    prompt = loc.read_text(encoding="utf-8").strip()
                    if prompt:
                        self._append_system(f"📄 System prompt loaded ({len(prompt)} chars)")
                        return prompt
                except Exception:
                    pass
        return None

    def _send_message(self):
        """Send message to Grok."""
        if self.is_streaming:
            return

        message = self.input_field.get("1.0", "end-1c").strip()
        if not message:
            return

        # Clear input
        self.input_field.delete("1.0", "end")

        # Handle commands
        if message.startswith("/"):
            self._handle_command(message)
            return

        # Display user message
        self._append_user(message)

        # Start streaming response
        self.is_streaming = True
        self._update_status("Thinking...")
        self.send_btn.configure(text="Stop ⬛", fg_color=COLORS["warning"])

        # Run in background thread
        self.current_thread = threading.Thread(
            target=self._stream_response, args=(message,), daemon=True
        )
        self.current_thread.start()

    def _stream_response(self, message: str):
        """Stream response from Grok (runs in thread)."""
        self._append_ai_start()

        if self.client is None:
            self._append_error("Client not initialized")
            return

        try:
            for chunk in self.client.chat(message):
                if not self.is_streaming:
                    break
                self._append_ai_chunk(chunk)

            self.conversation_history.append((message, ""))
        except ValidationError as e:
            self._append_error(f"Validation Error: {e}")
        except AuthenticationError as e:
            self._append_error(f"Authentication Failed: {e}\nCheck your cookie or session.")
        except NetworkError as e:
            self._append_error(f"Network Error: {e}\nCheck your connection or proxy settings.")
        except GrokAPIError as e:
            error_msg = f"API Error: {e}"
            if e.status_code:
                error_msg += f" (HTTP {e.status_code})"
            self._append_error(error_msg)
        except WormAIError as e:
            self._append_error(f"Error: {e}")
        except Exception as e:
            self._append_error(f"Unexpected Error: {type(e).__name__}: {e}")
        finally:
            self.is_streaming = False
            self.after(0, self._on_stream_complete)

    def _on_stream_complete(self):
        """Called when streaming is complete."""
        self.send_btn.configure(text="Send ▶", fg_color=COLORS["accent"])
        self._update_status("Ready")
        self._append_ai_end()

    def _stop_streaming(self):
        """Stop the current streaming response."""
        if self.is_streaming:
            self.is_streaming = False
            self._append_system("\n[Stopped]")

    def _handle_command(self, cmd: str):
        """Handle slash commands."""
        parts = cmd.lower().split()
        command = parts[0]
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        if command in ("/help", "/?"):
            self._show_help()
        elif command == "/clear":
            self._clear_chat()
        elif command == "/restart":
            if self.client:
                self.client.reset()
            self.conversation_history = []
            self._append_system("🔄 Conversation reset")
        elif command == "/proxy":
            if args:
                self.client = WormAI(proxy=args)
                self.proxy_label.configure(text=f"🔒 Proxy: {args[:30]}...")
                self._append_system(f"✅ Proxy set to: {args}")
            else:
                self._append_system("Usage: /proxy <url>")
        elif command == "/jailbreak":
            prompt = self._load_system_prompt()
            if prompt and self.client:
                self.client.set_system_prompt(prompt)
                self._append_system("😈 Jailbreak mode enabled")
            else:
                self._append_system("❌ No system prompt found")
        else:
            self._append_system(f"Unknown command: {command}")

    def _show_help(self):
        """Display help message."""
        help_text = """
╔════════════════════════════════════════════════╗
║  WORM-AI COMMANDS                              ║
╠════════════════════════════════════════════════╣
║  /help      - Show this help                   ║
║  /clear     - Clear chat history               ║
║  /restart   - Reset conversation               ║
║  /proxy URL - Set proxy server                 ║
║  /jailbreak - Enable system prompt             ║
╠════════════════════════════════════════════════╣
║  SHORTCUTS                                     ║
╠════════════════════════════════════════════════╣
║  Enter       - Send message                    ║
║  Shift+Enter - New line                        ║
║  Escape      - Stop response                   ║
╚════════════════════════════════════════════════╝
"""
        self._append_system(help_text)

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.grab_set()

    def _clear_chat(self):
        """Clear chat display."""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._append_system("Chat cleared. Type a message to start.\n")

    # ─────────────────────────────────────────────────────────────────────────
    # Chat Display Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _append_text(self, text: str, color: Optional[str] = None):
        """Append text to chat display."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _append_user(self, message: str):
        """Append user message."""
        self._append_text("\n┌──[YOU]──────────────────────────────────────\n")
        self._append_text(f"│ {message}\n")
        self._append_text("└─────────────────────────────────────────────\n")

    def _append_ai_start(self):
        """Start AI response block."""
        self.after(
            0, lambda: self._append_text("\n┌──[GROK]─────────────────────────────────────\n│ ")
        )

    def _append_ai_chunk(self, chunk: str):
        """Append AI response chunk (thread-safe)."""
        # Replace newlines with proper formatting
        formatted = chunk.replace("\n", "\n│ ")
        self.after(0, lambda c=formatted: self._append_text(c))

    def _append_ai_end(self):
        """End AI response block."""
        self._append_text("\n└─────────────────────────────────────────────\n")

    def _append_system(self, message: str):
        """Append system message."""
        self._append_text(f"\n[*] {message}\n")

    def _append_error(self, message: str):
        """Append error message."""
        self._append_text(f"\n[!] {message}\n")

    def _update_status(self, status: str):
        """Update status bar."""
        self.status_label.configure(text=status)


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("⚙️ Settings")
        self.geometry("450x400")
        self.configure(fg_color=COLORS["bg_dark"])

        self.parent = parent

        self._create_widgets()

    def _create_widgets(self):
        """Create settings widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"],
        )
        title.pack(pady=20)

        # Proxy setting
        proxy_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        proxy_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            proxy_frame,
            text="Proxy URL:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.proxy_entry = ctk.CTkEntry(
            proxy_frame,
            placeholder_text="socks5://127.0.0.1:9050",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["bg_light"],
            border_color=COLORS["border"],
        )
        self.proxy_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Cookie setting
        cookie_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        cookie_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            cookie_frame,
            text="Session Cookie:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.cookie_entry = ctk.CTkEntry(
            cookie_frame,
            placeholder_text="Your session cookie...",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["bg_light"],
            border_color=COLORS["border"],
            show="•",
        )
        self.cookie_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Jailbreak toggle
        jb_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        jb_frame.pack(fill="x", padx=20, pady=10)

        self.jailbreak_var = ctk.BooleanVar(value=False)
        self.jailbreak_switch = ctk.CTkSwitch(
            jb_frame,
            text="Enable Jailbreak Mode",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            variable=self.jailbreak_var,
            progress_color=COLORS["accent"],
        )
        self.jailbreak_switch.pack(padx=15, pady=15)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Apply",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._apply_settings,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["border"],
            command=self.destroy,
        ).pack(side="right", padx=5)

    def _apply_settings(self):
        """Apply settings and close."""
        proxy = self.proxy_entry.get().strip()
        cookie = self.cookie_entry.get().strip()

        # Reinitialize client with new settings
        self.parent.client = WormAI(
            proxy=proxy if proxy else None,
            cookie=cookie if cookie else None,
        )

        if proxy:
            self.parent.proxy_label.configure(text=f"🔒 Proxy: {proxy[:30]}...")
        else:
            self.parent.proxy_label.configure(text="")

        if self.jailbreak_var.get():
            prompt = self.parent._load_system_prompt()
            if prompt:
                self.parent.client.set_system_prompt(prompt)

        self.parent._append_system("✅ Settings applied")
        self.destroy()


def main():
    """Launch the GUI application."""
    app = WormAIApp()
    app.mainloop()


if __name__ == "__main__":
    main()
