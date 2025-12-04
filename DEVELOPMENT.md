# 🛠️ Worm-AI Development Guide

## 🚀 Development Setup

### Prerequisites

```bash
# Python 3.9+
python3 --version

# Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Development Dependencies

```bash
# Install all dev dependencies
pip install -e ".[dev]"

# Or manually:
pip install pytest pytest-cov black ruff mypy
```

## 📁 Project Structure

```
worm-ai/
├── src/
│   └── wormai/
│       ├── __init__.py      # Package exports
│       ├── client.py        # Grok API client
│       ├── cli.py           # CLI interface
│       └── gui.py           # GUI interface
├── tests/                   # Test files
├── qemu/                    # QEMU VM setup
├── pyproject.toml          # Project config
├── requirements.txt         # Runtime deps
└── DEVELOPMENT.md          # This file
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/wormai --cov-report=html

# Specific test file
pytest tests/test_client.py

# Verbose output
pytest -v

# Watch mode (requires pytest-watch)
ptw
```

### Write Tests

Create tests in `tests/` directory:

```python
# tests/test_client.py
import pytest
from wormai.client import WormAI

def test_client_initialization():
    client = WormAI()
    assert client is not None

def test_client_with_proxy():
    client = WormAI(proxy="socks5://127.0.0.1:9050")
    assert client.proxy == "socks5://127.0.0.1:9050"
```

## 🎨 Code Quality

### Formatting

```bash
# Format code with black
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

```bash
# Run ruff linter
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### Type Checking

```bash
# Run mypy
mypy src/

# With strict mode
mypy --strict src/
```

## 🔧 Development Tools

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Development Scripts

```bash
# Run all quality checks
make check

# Format and lint
make format

# Run tests
make test

# Full CI check
make ci
```

## 🐛 Debugging

### CLI Debugging

```bash
# Verbose mode
worm-ai --verbose "test query"

# Debug proxy
WORM_PROXY=socks5://127.0.0.1:9050 worm-ai --debug
```

### GUI Debugging

```bash
# Run GUI with debug
python -m wormai.gui --debug
```

### QEMU Development

```bash
cd qemu

# Test VM
make test

# Debug VM
make debug

# Fix issues
make fix
```

## 📝 Adding Features

### 1. Create Feature Branch

```bash
git checkout -b feature/new-feature
```

### 2. Write Code

- Follow PEP 8 style guide
- Add type hints
- Write docstrings
- Add tests

### 3. Test

```bash
# Run tests
pytest

# Check code quality
black --check src/
ruff check src/
mypy src/
```

### 4. Commit

```bash
git add .
git commit -m "feat: add new feature"
```

## 🏗️ Architecture

### Client (`client.py`)

- Handles Grok API communication
- Manages conversation state
- Handles streaming responses
- Proxy support

### CLI (`cli.py`)

- Interactive terminal interface
- Command parsing
- User input handling
- Output formatting

### GUI (`gui.py`)

- Modern tkinter interface
- Real-time streaming
- Settings management
- Conversation history

## 🔄 Release Process

### Version Bump

```bash
# Update version in pyproject.toml
# Then:
git tag v1.0.1
git push origin v1.0.1
```

### Build Package

```bash
# Build distribution
python -m build

# Upload to PyPI (if maintainer)
twine upload dist/*
```

## 📚 Documentation

### Update Docs

```bash
# Generate API docs (if using sphinx)
cd docs
make html
```

### README Updates

- Keep README.md up to date
- Update examples
- Document new features

## 🎯 Development Goals

### Current Features
- ✅ CLI interface
- ✅ GUI interface
- ✅ Proxy support
- ✅ Tor integration
- ✅ QEMU VM setup

### Planned Features
- [ ] API rate limiting
- [ ] Conversation export
- [ ] Plugin system
- [ ] Multi-account support
- [ ] Enhanced error handling

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 🐛 Common Issues

### Import Errors

```bash
# Reinstall in dev mode
pip install -e .
```

### Test Failures

```bash
# Clear cache
pytest --cache-clear

# Run with verbose output
pytest -vv
```

### QEMU Issues

```bash
cd qemu
make debug
make fix
```

## 📞 Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Telegram: t.me/xsocietyforums

---

**Happy Coding! 🐛💻**
