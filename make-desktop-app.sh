#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Create Worm-AI Desktop App
# Creates a macOS .app bundle and optionally installs to Desktop/Applications
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Worm-AI.app"
APP_PATH="$SCRIPT_DIR/$APP_NAME"
DESKTOP_PATH="$HOME/Desktop/$APP_NAME"
APPLICATIONS_PATH="/Applications/$APP_NAME"

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        🐛 Creating Worm-AI Desktop App${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Ensure app structure exists
echo -e "${CYAN}[*] Creating app structure...${NC}"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"
mkdir -p "$APP_PATH/Contents/Resources"

# Make launcher executable
if [[ -f "$APP_PATH/Contents/MacOS/launch" ]]; then
    chmod +x "$APP_PATH/Contents/MacOS/launch"
    echo -e "${GREEN}[+] App launcher ready${NC}"
else
    echo -e "${YELLOW}[!] Launcher script not found${NC}"
    exit 1
fi

# Create a simple icon placeholder (text-based)
if [[ ! -f "$APP_PATH/Contents/Resources/AppIcon.icns" ]]; then
    echo -e "${CYAN}[*] Creating app icon placeholder...${NC}"
    # Create a simple text file as placeholder
    echo "🐛" > "$APP_PATH/Contents/Resources/AppIcon.txt"
    echo -e "${YELLOW}[!] Note: Custom icon can be added later${NC}"
fi

echo -e "${GREEN}[+] App bundle created: $APP_PATH${NC}"
echo ""

# Ask where to install
echo -e "${CYAN}[*] Where would you like to install the app?${NC}"
echo "  1) Desktop"
echo "  2) Applications folder"
echo "  3) Both"
echo "  4) Just create (don't install)"
echo ""
read -p "Choice (1-4): " choice

case $choice in
    1)
        echo -e "${CYAN}[*] Installing to Desktop...${NC}"
        if [[ -d "$DESKTOP_PATH" ]]; then
            rm -rf "$DESKTOP_PATH"
        fi
        cp -R "$APP_PATH" "$DESKTOP_PATH"
        echo -e "${GREEN}[+] ✅ Installed to Desktop!${NC}"
        ;;
    2)
        echo -e "${CYAN}[*] Installing to Applications...${NC}"
        if [[ -d "$APPLICATIONS_PATH" ]]; then
            sudo rm -rf "$APPLICATIONS_PATH"
        fi
        sudo cp -R "$APP_PATH" "$APPLICATIONS_PATH"
        sudo chown -R $(whoami) "$APPLICATIONS_PATH"
        echo -e "${GREEN}[+] ✅ Installed to Applications!${NC}"
        ;;
    3)
        echo -e "${CYAN}[*] Installing to both locations...${NC}"
        if [[ -d "$DESKTOP_PATH" ]]; then
            rm -rf "$DESKTOP_PATH"
        fi
        cp -R "$APP_PATH" "$DESKTOP_PATH"
        if [[ -d "$APPLICATIONS_PATH" ]]; then
            sudo rm -rf "$APPLICATIONS_PATH"
        fi
        sudo cp -R "$APP_PATH" "$APPLICATIONS_PATH"
        sudo chown -R $(whoami) "$APPLICATIONS_PATH"
        echo -e "${GREEN}[+] ✅ Installed to Desktop and Applications!${NC}"
        ;;
    4)
        echo -e "${GREEN}[+] ✅ App bundle created (not installed)${NC}"
        ;;
    *)
        echo -e "${YELLOW}[!] Invalid choice, app bundle created but not installed${NC}"
        ;;
esac

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        ✅ Desktop App Ready!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}[*] Usage:${NC}"
echo -e "  Double-click the app to launch Worm-AI GUI"
echo ""
echo -e "${CYAN}[*] Location:${NC}"
if [[ -d "$DESKTOP_PATH" ]]; then
    echo -e "  Desktop: $DESKTOP_PATH"
fi
if [[ -d "$APPLICATIONS_PATH" ]]; then
    echo -e "  Applications: $APPLICATIONS_PATH"
fi
echo -e "  Source: $APP_PATH"
echo ""
