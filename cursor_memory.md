# 🧠 Worm-AI — Cursor Memory

> Adaptive knowledge base for debugging patterns, fixes, and solutions.
> Updated automatically during development sessions.

---

## 📋 Table of Contents

- [Error Patterns](#error-patterns)
- [Validated Fixes](#validated-fixes)
- [Architecture Notes](#architecture-notes)
- [Dependency Constraints](#dependency-constraints)
- [User Preferences](#user-preferences)

---

## Error Patterns

### Pattern: `curl_cffi` Import Failure

**Symptoms:**
- `ModuleNotFoundError: No module named 'curl_cffi'`
- `ImportError: libcurl.so.4: cannot open shared object file`

**Root Cause:** Missing system-level curl/SSL libraries before pip install.

**Solution:**
```bash
# Debian/Kali
sudo apt install libcurl4-openssl-dev libssl-dev build-essential
pip install curl_cffi
```

**Prevention:** Install script checks for system deps first.

---

### Pattern: Tkinter Not Found (GUI)

**Symptoms:**
- `ModuleNotFoundError: No module named '_tkinter'`
- `ImportError: customtkinter is required for GUI`

**Root Cause:** Python compiled without Tk support, or `python3-tk` not installed.

**Solution:**
```bash
# Debian/Kali
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

**Notes:** GUI gracefully degrades — CLI still works without tkinter.

---

### Pattern: SSL Certificate Errors

**Symptoms:**
- `ssl.SSLCertVerificationError`
- `[SSL: CERTIFICATE_VERIFY_FAILED]`

**Root Cause:** Missing/outdated CA certificates or proxy intercepting traffic.

**Solution:**
```bash
# Update certificates
sudo apt install ca-certificates
sudo update-ca-certificates

# Or disable verification (NOT recommended for production)
export CURL_CA_BUNDLE=""
```

---

### Pattern: Grok API Rate Limit / 429

**Symptoms:**
- `[Error] HTTP 429: Too Many Requests`
- Responses stop mid-stream

**Root Cause:** Grok rate limiting unauthenticated requests.

**Solution:**
1. Use authenticated cookie: `worm-ai -c "your_cookie"`
2. Add delays between requests
3. Use proxy rotation

---

## Validated Fixes

### Fix #001: Package Structure Migration

**Problem Summary:** Original single-file structure didn't support pip install.

**Exact Error:** `pip install .` failed, no entry points created.

**Root Cause:** Missing `pyproject.toml` and proper `src/` layout.

**Solution Implemented:**
- Created `src/wormai/` package structure
- Added `pyproject.toml` with entry points
- Split code into `client.py`, `cli.py`, `gui.py`

**Alternative Solutions:**
- `setup.py` (legacy, still works)
- Single-file with `__main__.py`

**Added Tests:** None yet — manual verification.

**Relevant Links:**
- https://packaging.python.org/en/latest/tutorials/packaging-projects/

**Notes for Future Debugging:** Always use `src/` layout for new packages.

**Recognised Pattern:** Python packaging migration

---

### Fix #002: GUI Integration

**Problem Summary:** User requested GUI for VM usage.

**Solution Implemented:**
- Added `customtkinter` dependency
- Created `src/wormai/gui.py` with dark theme
- Added `--gui` flag to CLI
- Updated installer to include `python3-tk`

**Design Decisions:**
- CustomTkinter chosen over PyQt (lighter, easier install)
- Dark theme matches Kali aesthetic
- Threaded streaming to keep UI responsive

**Notes for Future Debugging:** GUI requires display — fails gracefully in headless.

---

## Architecture Notes

### Project Structure
```
worm-ai/
├── src/wormai/
│   ├── __init__.py    # Package exports + launch_gui()
│   ├── client.py      # GrokClient, WormAI classes
│   ├── cli.py         # CLI with argparse
│   └── gui.py         # CustomTkinter GUI
├── install.sh         # One-liner installer
├── pyproject.toml     # Package metadata
└── system-prompt.txt  # Jailbreak prompt
```

### Key Classes
- `GrokClient` — Low-level API wrapper with streaming
- `WormAI` — High-level wrapper with system prompt support
- `WormAIApp` — GUI application (CTk)

### Data Flow
```
User Input → WormAI.chat() → GrokClient._build_payload()
           → curl_cffi POST → Stream chunks → Yield to UI
```

---

## Dependency Constraints

| Package | Min Version | Notes |
|---------|-------------|-------|
| Python | 3.9+ | f-strings, typing |
| curl_cffi | 0.6.0+ | Browser impersonation |
| colorama | 0.4.6+ | Terminal colors |
| customtkinter | 5.2.0+ | GUI (optional for CLI) |

### System Dependencies (Debian/Kali)
```bash
libcurl4-openssl-dev  # curl_cffi build
libssl-dev            # SSL support
build-essential       # Compilation
python3-tk            # GUI support
```

---

## User Preferences

| Preference | Value | Source |
|------------|-------|--------|
| Target Platform | Kali Linux VM | User request |
| Install Method | One-liner curl | User preference |
| Docker Support | Removed | User request |
| Theme | Dark/Hacker | Implicit (Kali) |

---

## Session Log

### 2024-11-29
- ✅ Converted to installable package
- ✅ Added GUI with CustomTkinter
- ✅ Removed Docker support
- ✅ Created cursor_memory.md

---

*Last updated: 2024-11-29*
