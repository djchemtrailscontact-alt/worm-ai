# AI Notes — Worm-AI

## Stack Notes

| Component | Details |
|-----------|---------|
| Language | Python 3.9+ (tested on 3.14) |
| HTTP Client | `curl_cffi` (browser impersonation) |
| GUI | `customtkinter` |
| CLI Colors | `colorama` |
| Testing | `pytest`, `pytest-cov` |
| Linting | `ruff`, `black` |
| Type Checking | `mypy` |
| Pre-commit | hooks for black, ruff, mypy |

## Conventions

### Folder Structure

```
worm-ai/
├── src/wormai/          # Main package (CLI, GUI, client)
├── core/                # Obfuscated pyarmor module (legacy entry)
├── tests/               # pytest tests
├── docs/                # Documentation
├── qemu/                # VM setup scripts
└── .cursor/commands/    # Cursor AI commands
```

### Entry Points

| Entry | Location | Description |
|-------|----------|-------------|
| `worm-ai` CLI | `src/wormai/cli.py:main()` | Main CLI entry point |
| `worm-ai --gui` | `src/wormai/gui.py:main()` | GUI mode via CLI flag |
| `worm-ai-gui` | `src/wormai/gui.py:main()` | Direct GUI entry |
| `python main.py` | `main.py` → `core/` | Legacy entry using obfuscated pyarmor module |

### Desktop Apps (macOS .app bundles)

| App | Location | Purpose |
|-----|----------|---------|
| `Worm-AI.app` | `/Worm-AI.app` | Native GUI launcher (runs `worm-ai --gui`) |
| `Worm-AI.app` | `/qemu/Worm-AI.app` | QEMU VM launcher (runs `qemu/launch.sh`) |

**Note:** The two `.app` bundles are intentionally different — one launches the native app, the other boots a QEMU virtual machine.

### Naming

- Classes: PascalCase (`GrokClient`, `WormAI`)
- Functions: snake_case (`validate_proxy_url`)
- Constants: UPPER_SNAKE (`BASE_URL`, `COLORS`)

### Error Handling

- Use custom exceptions from `wormai.exceptions`
- Validate inputs at system boundaries using `wormai.validation`
- Use `raise X from err` pattern in exception handlers

### Testing

- Run: `make test` or `pytest -v`
- Coverage: `make test-cov` → HTML report at `htmlcov/index.html`
- Tests in `tests/` directory, prefix with `test_`
- Mock `curl_cffi.requests.post` not standard `requests`

### Coverage Status (as of last run)

| Module | Coverage | Notes |
|--------|----------|-------|
| `exceptions.py` | 100% | ✅ Fully covered |
| `validation.py` | 91% | ✅ Good coverage |
| `client.py` | 89% | ✅ Streaming, retry, helpers covered |
| `cli.py` | 93% | ✅ All commands + error handling tested |
| `gui.py` | 0% | ⚠️ GUI testing requires special setup |
| **TOTAL** | 57% | Progress: 23% → 34% → 40% → 53% → 57% |

**109 tests total** (108 pass, 1 skipped)

**Remaining:** GUI module requires `pytest-qt` or headless testing

## Error Playbook

### Pattern: Import Sorting (I001)

- **Symptom**: Ruff complains about unsorted imports
- **Solution**: Use `ruff check --fix` or organize: stdlib → third-party → local

### Pattern: Exception Re-raise (B904)

- **Symptom**: `raise X` inside `except` block
- **Solution**: Use `raise X from err` or `raise X from None`

### Pattern: Unused f-string (F541)

- **Symptom**: f-string without placeholders
- **Solution**: Remove `f` prefix for plain strings

### Pattern: WormAI vs GrokClient attributes

- **Symptom**: `AttributeError: 'WormAI' has no attribute 'proxy'`
- **Solution**: Access via `wormai_instance.client.proxy`

## Gotchas

1. **Two entry points**: `main.py` uses obfuscated `core/` module; `worm-ai` CLI uses `src/wormai/`

2. **curl_cffi not requests**: The HTTP client is `curl_cffi.requests`, not standard `requests`. Mock paths accordingly.

3. **pyarmor protection**: The `core/core/grok.py` is obfuscated with pyarmor — don't try to modify it.

4. **macOS dev env**: Use virtual environment (`.venv/`) to avoid pip system package errors.

5. **Python 3.14 compatibility**: All code runs on Python 3.14, type hints use modern syntax.
