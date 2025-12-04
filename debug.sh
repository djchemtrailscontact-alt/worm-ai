#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Worm-AI Comprehensive Debug Tool
# Checks both application and QEMU setup
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

banner() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        🐛 Worm-AI Comprehensive Debug${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

check_python() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[1] Checking Python Environment${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if command -v python3 &> /dev/null; then
        local PYTHON_VERSION=$(python3 --version)
        echo -e "${GREEN}[+] Python found: $PYTHON_VERSION${NC}"

        # Check Python version
        local MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
        local MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

        if [[ "$MAJOR" -ge 3 ]] && [[ "$MINOR" -ge 9 ]]; then
            echo -e "${GREEN}[+] ✅ Python version OK (3.9+)${NC}"
        else
            echo -e "${RED}[!] Python 3.9+ required${NC}"
        fi
    else
        echo -e "${RED}[!] Python 3 not found${NC}"
        return 1
    fi

    # Check virtual environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo -e "${GREEN}[+] Virtual environment active: $VIRTUAL_ENV${NC}"
    else
        echo -e "${YELLOW}[!] No virtual environment (recommended)${NC}"
        echo -e "${CYAN}[*] Create with: python3 -m venv venv${NC}"
    fi

    echo ""
}

check_package() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[2] Checking Worm-AI Package${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Check if package is installed
    if python3 -c "import wormai" 2>/dev/null; then
        echo -e "${GREEN}[+] ✅ Worm-AI package installed${NC}"

        # Try to get version
        python3 -c "import wormai; print('  Package location:', wormai.__file__)" 2>/dev/null || true
    else
        echo -e "${YELLOW}[!] Worm-AI package not installed${NC}"
        echo -e "${CYAN}[*] Install with: pip install -e .${NC}"
        echo -e "${CYAN}[*] Or dev mode: make dev-install${NC}"
    fi

    # Check command availability
    if command -v worm-ai &> /dev/null; then
        echo -e "${GREEN}[+] ✅ worm-ai command available${NC}"
        local CMD_PATH=$(which worm-ai)
        echo -e "${CYAN}[*] Location: $CMD_PATH${NC}"
    else
        echo -e "${YELLOW}[!] worm-ai command not found${NC}"
        echo -e "${CYAN}[*] Install package to get command${NC}"
    fi

    echo ""
}

check_dependencies() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[3] Checking Dependencies${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local DEPS=("curl_cffi" "colorama" "customtkinter")
    local MISSING=()

    for DEP in "${DEPS[@]}"; do
        if python3 -c "import ${DEP//-/_}" 2>/dev/null; then
            echo -e "${GREEN}[+] $DEP installed${NC}"
        else
            echo -e "${RED}[!] $DEP missing${NC}"
            MISSING+=("$DEP")
        fi
    done

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        echo -e "${YELLOW}[*] Install missing: pip install ${MISSING[*]}${NC}"
    else
        echo -e "${GREEN}[+] ✅ All dependencies installed${NC}"
    fi

    echo ""
}

check_project_structure() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[4] Checking Project Structure${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local FILES=(
        "src/wormai/__init__.py"
        "src/wormai/client.py"
        "src/wormai/cli.py"
        "src/wormai/gui.py"
        "pyproject.toml"
        "README.md"
    )

    local MISSING=()
    for FILE in "${FILES[@]}"; do
        if [[ -f "$SCRIPT_DIR/$FILE" ]]; then
            echo -e "${GREEN}[+] $FILE${NC}"
        else
            echo -e "${RED}[!] $FILE missing${NC}"
            MISSING+=("$FILE")
        fi
    done

    if [[ ${#MISSING[@]} -eq 0 ]]; then
        echo -e "${GREEN}[+] ✅ Project structure OK${NC}"
    fi

    echo ""
}

check_qemu() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[5] Checking QEMU Setup${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [[ -d "$SCRIPT_DIR/qemu" ]]; then
        cd "$SCRIPT_DIR/qemu"
        if [[ -f "debug.sh" ]]; then
            ./debug.sh 2>&1 | grep -E "\[+\]|\[!\]|WARNING|Found.*issues" | head -10
        else
            echo -e "${YELLOW}[!] QEMU debug script not found${NC}"
        fi
    else
        echo -e "${YELLOW}[!] QEMU directory not found${NC}"
    fi

    echo ""
}

check_dev_tools() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[6] Checking Development Tools${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local TOOLS=("pytest" "black" "ruff" "mypy")
    local MISSING=()

    for TOOL in "${TOOLS[@]}"; do
        if command -v "$TOOL" &> /dev/null || python3 -c "import ${TOOL}" 2>/dev/null; then
            echo -e "${GREEN}[+] $TOOL available${NC}"
        else
            echo -e "${YELLOW}[!] $TOOL not found${NC}"
            MISSING+=("$TOOL")
        fi
    done

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        echo -e "${CYAN}[*] Install dev tools: make dev-install${NC}"
    else
        echo -e "${GREEN}[+] ✅ Development tools available${NC}"
    fi

    # Check Makefile
    if [[ -f "$SCRIPT_DIR/Makefile" ]]; then
        echo -e "${GREEN}[+] Makefile found${NC}"
    else
        echo -e "${YELLOW}[!] Makefile not found${NC}"
    fi

    echo ""
}

generate_summary() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[7] Summary & Quick Fixes${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    echo -e "${CYAN}[*] Quick Setup Commands:${NC}"
    echo ""
    echo -e "  ${GREEN}# Install package${NC}"
    echo -e "  pip install -e ."
    echo ""
    echo -e "  ${GREEN}# Install with dev tools${NC}"
    echo -e "  make dev-install"
    echo ""
    echo -e "  ${GREEN}# Test installation${NC}"
    echo -e "  worm-ai --version"
    echo ""
    echo -e "  ${GREEN}# Run tests${NC}"
    echo -e "  make test"
    echo ""
    echo -e "  ${GREEN}# QEMU setup${NC}"
    echo -e "  cd qemu && make debug"
    echo ""
}

main() {
    banner

    check_python
    check_package
    check_dependencies
    check_project_structure
    check_qemu
    check_dev_tools
    generate_summary

    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        ✅ Debug Complete${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

main "$@"
