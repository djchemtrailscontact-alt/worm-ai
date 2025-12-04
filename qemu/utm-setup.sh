#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Worm-AI UTM Setup Script
# Create UTM configuration for faster HVF-based virtualization
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$SCRIPT_DIR/vm"
UTM_CONFIG_DIR="$HOME/Library/Containers/com.utmapp.UTM/Data/Documents"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        🐛 Worm-AI UTM Setup${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check if UTM is installed
if ! [ -d "/Applications/UTM.app" ]; then
    echo -e "${RED}[!] UTM not found in /Applications${NC}"
    echo -e "${YELLOW}[*] Install UTM: brew install --cask utm${NC}"
    exit 1
fi

echo -e "${GREEN}[+] UTM is installed${NC}"

# Check VM files
if [ ! -f "$VM_DIR/worm-ai.qcow2" ]; then
    echo -e "${RED}[!] VM disk not found. Run 'make build' first${NC}"
    exit 1
fi

echo -e "${GREEN}[+] VM disk found: $VM_DIR/worm-ai.qcow2${NC}"

# Create UTM configuration
create_utm_config() {
    local CONFIG_FILE="$UTM_CONFIG_DIR/Worm-AI.utm"

    # Create config directory if it doesn't exist
    mkdir -p "$UTM_CONFIG_DIR"

    # Create UTM configuration (plist format)
    cat > "$CONFIG_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>ConfigurationVersion</key>
    <integer>2</integer>
    <key>Debug</key>
    <dict>
        <key>DebugLog</key>
        <false/>
        <key>DebugLogFile</key>
        <string></string>
    </dict>
    <key>Display</key>
    <dict>
        <key>ConsoleOnly</key>
        <false/>
        <key>DisplayOrigin</key>
        <string>0,0</string>
        <key>DisplayResolution</key>
        <string>1024x768</string>
        <key>DisplayScaling</key>
        <integer>1</integer>
        <key>DisplayType</key>
        <string>fullscreen</string>
    </dict>
    <key>Drives</key>
    <array>
        <dict>
            <key>DriveName</key>
            <string>Worm-AI Disk</string>
            <key>DrivePath</key>
            <string>worm-ai.qcow2</string>
            <key>DriveType</key>
            <string>disk</string>
        </dict>
    </array>
    <key>Information</key>
    <dict>
        <key>IconPath</key>
        <string></string>
        <key>Name</key>
        <string>Worm-AI</string>
        <key>Notes</key>
        <string>Grok AI client VM for security research</string>
        <key>SystemArchitecture</key>
        <string>x86_64</string>
        <key>SystemBootDevice</key>
        <string></string>
        <key>SystemMemory</key>
        <string>2048</string>
        <key>SystemTarget</key>
        <string>q35</string>
    </dict>
    <key>Input</key>
    <dict>
        <key>InputLegacy</key>
        <false/>
        <key>InputTouchscreenMode</key>
        <integer>0</integer>
    </dict>
    <key>Network</key>
    <array>
        <dict>
            <key>NetworkCard</key>
            <string>virtio-net-pci</string>
            <key>NetworkMode</key>
            <string>shared</string>
            <key>NetworkPortForward</key>
            <array>
                <dict>
                    <key>Protocol</key>
                    <string>tcp</string>
                    <key>GuestPort</key>
                    <integer>22</integer>
                    <key>HostPort</key>
                    <integer>2222</integer>
                </dict>
                <dict>
                    <key>Protocol</key>
                    <string>tcp</string>
                    <key>GuestPort</key>
                    <integer>8080</integer>
                    <key>HostPort</key>
                    <integer>8080</integer>
                </dict>
            </array>
        </dict>
    </array>
    <key>Printing</key>
    <dict>
        <key>PrintingEnabled</key>
        <false/>
    </dict>
    <key>SharedDirectories</key>
    <array>
        <dict>
            <key>SharedDirectoryName</key>
            <string>worm-ai-shared</string>
            <key>SharedDirectoryPath</key>
            <string>shared</string>
            <key>SharedDirectoryReadOnly</key>
            <false/>
        </dict>
    </array>
    <key>System</key>
    <dict>
        <key>AddArgs</key>
        <string></string>
        <key>BootLoader</key>
        <string></string>
        <key>UEFIVariableStore</key>
        <dict>
            <key>UEFIVariableStorePath</key>
            <string></string>
            <key>UEFIVariableStoreSize</key>
            <integer>0</integer>
        </dict>
    </dict>
</dict>
</plist>
EOF

    echo -e "${GREEN}[+] UTM configuration created: $CONFIG_FILE${NC}"
}

# Copy VM files to UTM directory
copy_vm_files() {
    local UTM_VM_DIR="$UTM_CONFIG_DIR/Worm-AI.utm"

    mkdir -p "$UTM_VM_DIR/Data"

    # Copy disk image
    cp "$VM_DIR/worm-ai.qcow2" "$UTM_VM_DIR/Data/"

    # Copy shared folder
    cp -r "$VM_DIR/shared" "$UTM_VM_DIR/Data/"

    echo -e "${GREEN}[+] VM files copied to UTM directory${NC}"
}

# Main setup
main() {
    echo -e "${YELLOW}[*] Setting up Worm-AI for UTM...${NC}"

    create_utm_config
    copy_vm_files

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        ✅ UTM Setup Complete!${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}🚀 Launch UTM and open 'Worm-AI'${NC}"
    echo -e "  ${GREEN}🔗 SSH: ssh -p 2222 worm@localhost${NC}"
    echo -e "  ${GREEN}👤 User: worm | Password: worm${NC}"
    echo ""
    echo -e "  ${YELLOW}⚡ Performance: HVF acceleration (much faster!)${NC}"
    echo ""
}

main "$@"
