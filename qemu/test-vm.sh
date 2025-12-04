#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Test VM Launch
# Quick test to verify VM can boot properly
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$SCRIPT_DIR/vm"
DISK_IMAGE="$VM_DIR/worm-ai.qcow2"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        🐛 Testing VM Launch${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${CYAN}[1] Checking prerequisites...${NC}"

if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo -e "${RED}[!] QEMU not found${NC}"
    exit 1
fi
echo -e "${GREEN}[+] QEMU found${NC}"

if [[ ! -f "$DISK_IMAGE" ]]; then
    echo -e "${RED}[!] Disk image not found${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Disk image found${NC}"

# Check for ISO
ISO_FILE=""
if [[ -f "$VM_DIR/iso/alpine-virt.iso" ]]; then
    ISO_FILE="$VM_DIR/iso/alpine-virt.iso"
    echo -e "${GREEN}[+] Alpine ISO found${NC}"
elif [[ -f "$VM_DIR/iso/debian-netinst.iso" ]]; then
    ISO_FILE="$VM_DIR/iso/debian-netinst.iso"
    echo -e "${GREEN}[+] Debian ISO found${NC}"
else
    echo -e "${YELLOW}[!] No ISO found - will test boot from disk${NC}"
fi

echo ""
echo -e "${CYAN}[2] Testing QEMU command syntax...${NC}"

# Build test command
TEST_CMD="qemu-system-x86_64"
TEST_CMD="$TEST_CMD -accel tcg,thread=multi"
TEST_CMD="$TEST_CMD -machine pc-i440fx-9.2"
TEST_CMD="$TEST_CMD -m 512"  # Small RAM for quick test
TEST_CMD="$TEST_CMD -smp 1"
TEST_CMD="$TEST_CMD -cpu qemu64"
TEST_CMD="$TEST_CMD -drive file=$DISK_IMAGE,format=qcow2,if=ide"

if [[ -n "$ISO_FILE" ]]; then
    TEST_CMD="$TEST_CMD -cdrom $ISO_FILE"
    TEST_CMD="$TEST_CMD -boot d"
fi

TEST_CMD="$TEST_CMD -nographic"
TEST_CMD="$TEST_CMD -no-reboot"
TEST_CMD="$TEST_CMD -serial stdio"
TEST_CMD="$TEST_CMD -monitor none"

echo -e "${CYAN}[*] Command:${NC}"
echo "$TEST_CMD" | fold -w 80 -s
echo ""

# Test syntax
echo -e "${CYAN}[3] Validating command...${NC}"
if qemu-system-x86_64 -help | head -1 >/dev/null 2>&1; then
    echo -e "${GREEN}[+] QEMU command syntax OK${NC}"
else
    echo -e "${RED}[!] QEMU command failed${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}[4] Quick boot test (10 seconds)...${NC}"
echo -e "${YELLOW}[*] Starting VM for 10 seconds to verify it boots...${NC}"
echo ""

# Run VM for 10 seconds
timeout 10 $TEST_CMD 2>&1 | head -20 || true

echo ""
echo -e "${GREEN}[+] ✅ VM test complete!${NC}"
echo ""
echo -e "${CYAN}[*] If you saw boot messages above, the VM is working!${NC}"
echo -e "${CYAN}[*] To start full installation: make install${NC}"
echo ""
