#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Fix QEMU Warnings
# Automatically fixes common warnings from debug output
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$SCRIPT_DIR/vm"
ISO_DIR="$VM_DIR/iso"

banner() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        🐛 Fixing QEMU Warnings${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

fix_iso() {
    echo -e "${CYAN}[1] Fixing ISO Warning...${NC}"

    mkdir -p "$ISO_DIR"

    # Check if we have a valid ISO
    local VALID_ISO=""
    for ISO in "$ISO_DIR"/*.iso; do
        if [[ -f "$ISO" ]]; then
            local SIZE=$(stat -f%z "$ISO" 2>/dev/null || stat -c%s "$ISO" 2>/dev/null || echo "0")
            local TYPE=$(file "$ISO" 2>/dev/null | grep -i "iso\|cd\|disk" || echo "")
            if [[ "$SIZE" -gt 50000000 ]] || [[ -n "$TYPE" ]]; then
                VALID_ISO="$ISO"
                break
            fi
        fi
    done

    if [[ -n "$VALID_ISO" ]]; then
        echo -e "${GREEN}[+] Valid ISO found: $(basename "$VALID_ISO")${NC}"
        return 0
    fi

    echo -e "${YELLOW}[*] No valid ISO found, downloading Alpine Linux...${NC}"
    echo -e "${CYAN}[*] (Alpine is smaller and faster than Debian)${NC}"

    local ALPINE_URL="https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-virt-3.19.0-x86_64.iso"
    local ALPINE_ISO="$ISO_DIR/alpine-virt.iso"

    if curl -L --progress-bar -o "$ALPINE_ISO" "$ALPINE_URL"; then
        local SIZE=$(stat -f%z "$ALPINE_ISO" 2>/dev/null || stat -c%s "$ALPINE_ISO" 2>/dev/null || echo "0")
        if [[ "$SIZE" -gt 50000000 ]]; then
            echo -e "${GREEN}[+] ✅ ISO downloaded successfully!${NC}"
            echo -e "${CYAN}[*] File: $(basename "$ALPINE_ISO") ($(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "${SIZE} bytes"))${NC}"
            return 0
        fi
    fi

    echo -e "${RED}[!] Failed to download ISO${NC}"
    return 1
}

fix_hvf() {
    echo -e "${CYAN}[2] Fixing HVF Warning...${NC}"

    # Check if HVF is already available
    if qemu-system-x86_64 -accel help 2>/dev/null | grep -q hvf; then
        echo -e "${GREEN}[+] ✅ HVF is already available!${NC}"
        return 0
    fi

    echo -e "${YELLOW}[!] HVF not available in current QEMU build${NC}"
    echo ""
    echo -e "${CYAN}[*] Options:${NC}"
    echo -e "  1. Build QEMU from source with HVF (20-30 min, best performance)"
    echo -e "  2. Keep using TCG (works fine, just slower)"
    echo ""

    read -p "Build QEMU with HVF? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}[*] Starting QEMU build...${NC}"
        if [[ -f "$SCRIPT_DIR/build-qemu.sh" ]]; then
            chmod +x "$SCRIPT_DIR/build-qemu.sh"
            "$SCRIPT_DIR/build-qemu.sh"
        else
            echo -e "${RED}[!] build-qemu.sh not found${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}[*] Keeping TCG (you can build HVF later with: make build-qemu)${NC}"
    fi
}

stop_running_vm() {
    echo -e "${CYAN}[0] Stopping any running VMs...${NC}"

    local QEMU_PIDS=$(pgrep -f qemu-system-x86_64 2>/dev/null || true)
    if [[ -n "$QEMU_PIDS" ]]; then
        echo -e "${YELLOW}[*] Found running QEMU processes, stopping...${NC}"
        pkill -f qemu-system-x86_64 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}[+] Stopped${NC}"
    else
        echo -e "${GREEN}[+] No running VMs${NC}"
    fi
    echo ""
}

main() {
    banner

    stop_running_vm
    fix_iso
    echo ""
    fix_hvf

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        ✅ Warnings Fixed!${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}[*] Run debug again: make debug${NC}"
    echo -e "${CYAN}[*] Start VM: make install${NC}"
    echo ""
}

main "$@"
