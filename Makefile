# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Worm-AI Development Makefile
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: help install dev-install test format lint type-check check ci clean debug app desktop-app

SHELL := /bin/bash

# Default target
help:
	@echo ""
	@echo "═══════════════════════════════════════════════════════"
	@echo "🐛 Worm-AI Development Makefile"
	@echo "═══════════════════════════════════════════════════════"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  debug        Run comprehensive debug diagnostics"
	@echo "  dev-install  Install in development mode with dev deps"
	@echo "  test         Run tests"
	@echo "  format       Format code with black"
	@echo "  lint         Run ruff linter"
	@echo "  type-check   Run mypy type checker"
	@echo "  check        Run all quality checks"
	@echo "  ci           Run full CI checks"
	@echo ""
	@echo "Installation:"
	@echo "  install      Install package"
	@echo "  clean        Remove build artifacts"
	@echo ""
	@echo "Desktop App:"
	@echo "  app          Create macOS desktop app"
	@echo "  desktop-app  Same as 'app'"
	@echo ""
	@echo "QEMU:"
	@echo "  qemu-install Start QEMU VM installation"
	@echo "  qemu-test    Test QEMU VM"
	@echo "  qemu-debug   Debug QEMU setup"
	@echo ""

# Install package
install:
	pip install -e .

# Install with dev dependencies
dev-install:
	pip install -e ".[dev]"
	@echo "✅ Development environment ready!"

# Run tests
test:
	pytest -v

# Run tests with coverage
test-cov:
	pytest --cov=src/wormai --cov-report=html --cov-report=term
	@echo "📊 Coverage report: htmlcov/index.html"

# Format code
format:
	black src/ tests/
	@echo "✅ Code formatted!"

# Check formatting
format-check:
	black --check src/ tests/

# Run linter
lint:
	ruff check src/ tests/
	@echo "✅ Linting complete!"

# Auto-fix linting issues
lint-fix:
	ruff check --fix src/ tests/
	@echo "✅ Linting issues fixed!"

# Type checking
type-check:
	mypy src/
	@echo "✅ Type checking complete!"

# Run all quality checks
check: format-check lint type-check
	@echo "✅ All quality checks passed!"

# Full CI pipeline
ci: clean dev-install check test
	@echo "✅ CI pipeline complete!"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned build artifacts!"

# QEMU commands
qemu-install:
	cd qemu && make install

qemu-test:
	cd qemu && make test

qemu-debug:
	cd qemu && make debug

qemu-fix:
	cd qemu && make fix

# Development server (if needed)
dev:
	@echo "🚀 Starting development mode..."
	@echo "Run: worm-ai --gui"
	@echo "Or: worm-ai"

# Run comprehensive debug
debug:
	@chmod +x debug.sh
	@./debug.sh

# Create desktop app
app: desktop-app

desktop-app:
	@echo "📱 Creating desktop app..."
	@chmod +x make-desktop-app.sh
	@./make-desktop-app.sh
