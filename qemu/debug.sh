#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Worm-AI QEMU Debug Tool
# Comprehensive diagnostics for QEMU and VM setup
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
VM_DIR="$SCRIPT_DIR/vm"

banner() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        🐛 Worm-AI QEMU Debug Tool${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

check_qemu() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[1] Checking QEMU Installation${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if command -v qemu-system-x86_64 &> /dev/null; then
        local QEMU_PATH=$(which qemu-system-x86_64)
        local QEMU_VERSION=$(qemu-system-x86_64 --version 2>/dev/null | head -1)

        echo -e "${GREEN}[+] QEMU found: $QEMU_PATH${NC}"
        echo -e "${GREEN}[+] Version: $QEMU_VERSION${NC}"

        # Check accelerators
        echo -e "${CYAN}[*] Available accelerators:${NC}"
        qemu-system-x86_64 -accel help 2>/dev/null | grep -v "^$" || echo -e "${RED}[!] Could not list accelerators${NC}"

        # Check for HVF
        if qemu-system-x86_64 -accel help 2>/dev/null | grep -q hvf; then
            echo -e "${GREEN}[+] ✅ HVF acceleration available!${NC}"
        else
            echo -e "${YELLOW}[!] ⚠️  HVF not available (using TCG)${NC}"
        fi

        # Check for KVM (Linux)
        if [[ "$OSTYPE" != "darwin"* ]] && [[ -r /dev/kvm ]]; then
            echo -e "${GREEN}[+] ✅ KVM available${NC}"
        fi
    else
        echo -e "${RED}[!] QEMU not found in PATH${NC}"
        echo -e "${YELLOW}[*] Install with: brew install qemu${NC}"
        return 1
    fi
    echo ""
}

check_system() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[2] Checking System Configuration${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # OS Info
    echo -e "${CYAN}[*] Operating System:${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sw_vers
        echo -e "${CYAN}[*] Architecture: $(uname -m)${NC}"
        echo -e "${CYAN}[*] CPU Cores: $(sysctl -n hw.ncpu)${NC}"
        echo -e "${CYAN}[*] RAM: $(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}')${NC}"

        # Check HVF support
        local HV_SUPPORT=$(sysctl -n kern.hv_support 2>/dev/null || echo "0")
        if [[ "$HV_SUPPORT" == "1" ]]; then
            echo -e "${GREEN}[+] ✅ Hardware virtualization supported${NC}"
        else
            echo -e "${YELLOW}[!] ⚠️  Hardware virtualization not supported${NC}"
        fi
    else
        uname -a
        echo -e "${CYAN}[*] CPU Cores: $(nproc)${NC}"

        # Check KVM
        if [[ -r /dev/kvm ]]; then
            echo -e "${GREEN}[+] ✅ KVM device available${NC}"
            ls -l /dev/kvm
        else
            echo -e "${YELLOW}[!] ⚠️  KVM not available${NC}"
        fi
    fi
    echo ""
}

check_vm_files() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[3] Checking VM Files${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [[ ! -d "$VM_DIR" ]]; then
        echo -e "${RED}[!] VM directory not found: $VM_DIR${NC}"
        return 1
    fi

    echo -e "${CYAN}[*] VM Directory: $VM_DIR${NC}"

    # Disk image
    local DISK_IMAGE="$VM_DIR/worm-ai.qcow2"
    if [[ -f "$DISK_IMAGE" ]]; then
        local DISK_SIZE=$(stat -f%z "$DISK_IMAGE" 2>/dev/null || stat -c%s "$DISK_IMAGE" 2>/dev/null || echo "0")
        local DISK_INFO=$(qemu-img info "$DISK_IMAGE" 2>/dev/null || echo "")

        echo -e "${GREEN}[+] Disk image found: $DISK_IMAGE${NC}"
        echo -e "${CYAN}[*] Size: $(numfmt --to=iec-i --suffix=B $DISK_SIZE 2>/dev/null || echo "${DISK_SIZE} bytes")${NC}"

        if [[ -n "$DISK_INFO" ]]; then
            echo -e "${CYAN}[*] Disk info:${NC}"
            echo "$DISK_INFO" | head -5
        fi
    else
        echo -e "${YELLOW}[!] Disk image not found${NC}"
    fi

    # ISO files
    echo -e "${CYAN}[*] ISO Files:${NC}"
    local ISO_COUNT=0
    local VALID_ISO_COUNT=0
    for ISO in "$VM_DIR/iso"/*.iso; do
        if [[ -f "$ISO" ]]; then
            ISO_COUNT=$((ISO_COUNT + 1))
            local ISO_SIZE=$(stat -f%z "$ISO" 2>/dev/null || stat -c%s "$ISO" 2>/dev/null || echo "0")
            local ISO_TYPE=$(file "$ISO" 2>/dev/null | cut -d: -f2 || echo "unknown")

            echo -e "  ${GREEN}[+] $(basename "$ISO")${NC}"
            echo -e "     Size: $(numfmt --to=iec-i --suffix=B $ISO_SIZE 2>/dev/null || echo "${ISO_SIZE} bytes")${NC}"
            echo -e "     Type: $ISO_TYPE${NC}"

            # Check if valid ISO (50MB minimum for Alpine, 100MB for Debian)
            if [[ "$ISO_SIZE" -gt 50000000 ]]; then
                VALID_ISO_COUNT=$((VALID_ISO_COUNT + 1))
                echo -e "     ${GREEN}[+] ✅ Valid bootable ISO${NC}"
            else
                echo -e "     ${RED}[!] ⚠️  File too small - may be invalid${NC}"
            fi
        fi
    done

    if [[ $ISO_COUNT -eq 0 ]]; then
        echo -e "${YELLOW}[!] No ISO files found${NC}"
    elif [[ $VALID_ISO_COUNT -gt 0 ]]; then
        echo -e "${GREEN}[+] ✅ $VALID_ISO_COUNT valid ISO(s) found${NC}"
    fi

    # Cloud-init
    if [[ -f "$VM_DIR/cloud-init.iso" ]]; then
        echo -e "${GREEN}[+] Cloud-init ISO found${NC}"
    else
        echo -e "${YELLOW}[!] Cloud-init ISO not found${NC}"
    fi

    # Shared folder
    if [[ -d "$VM_DIR/shared" ]]; then
        local SHARED_FILES=$(find "$VM_DIR/shared" -type f | wc -l)
        echo -e "${GREEN}[+] Shared folder found ($SHARED_FILES files)${NC}"
    else
        echo -e "${YELLOW}[!] Shared folder not found${NC}"
    fi

    echo ""
}

check_network() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[4] Checking Network Configuration${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Check if ports are in use
    local PORTS=(2222 8080)
    for PORT in "${PORTS[@]}"; do
        if lsof -i :$PORT &>/dev/null; then
            echo -e "${YELLOW}[!] Port $PORT is in use:${NC}"
            lsof -i :$PORT | head -2
        else
            echo -e "${GREEN}[+] Port $PORT is available${NC}"
        fi
    done

    echo ""
}

check_scripts() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[5] Checking Scripts${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local SCRIPTS=("launch.sh" "provision.sh" "build-qemu.sh")
    for SCRIPT in "${SCRIPTS[@]}"; do
        local SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT"
        if [[ -f "$SCRIPT_PATH" ]]; then
            if [[ -x "$SCRIPT_PATH" ]]; then
                echo -e "${GREEN}[+] $SCRIPT (executable)${NC}"
            else
                echo -e "${YELLOW}[!] $SCRIPT (not executable)${NC}"
                echo -e "${CYAN}[*] Fix with: chmod +x $SCRIPT_PATH${NC}"
            fi
        else
            echo -e "${RED}[!] $SCRIPT not found${NC}"
        fi
    done

    echo ""
}

test_qemu_command() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[6] Testing QEMU Command${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local DISK_IMAGE="$VM_DIR/worm-ai.qcow2"

    if [[ ! -f "$DISK_IMAGE" ]]; then
        echo -e "${YELLOW}[!] No disk image to test with${NC}"
        echo ""
        return
    fi

    echo -e "${CYAN}[*] Testing QEMU launch command (dry-run)...${NC}"

    # Build test command
    local TEST_CMD="qemu-system-x86_64"
    TEST_CMD="$TEST_CMD -accel tcg"
    TEST_CMD="$TEST_CMD -machine q35"
    TEST_CMD="$TEST_CMD -m 2048"
    TEST_CMD="$TEST_CMD -smp 2"
    TEST_CMD="$TEST_CMD -cpu qemu64"
    TEST_CMD="$TEST_CMD -drive file=$DISK_IMAGE,format=qcow2,if=ide"
    TEST_CMD="$TEST_CMD -netdev user,id=net0,hostfwd=tcp::2222-:22"
    TEST_CMD="$TEST_CMD -device virtio-net-pci,netdev=net0"
    TEST_CMD="$TEST_CMD -display cocoa"
    TEST_CMD="$TEST_CMD -boot c"
    TEST_CMD="$TEST_CMD -nographic -no-reboot"

    echo -e "${CYAN}[*] Command:${NC}"
    echo "$TEST_CMD" | fold -w 80 -s

    # Test syntax
    if qemu-system-x86_64 -help | grep -q "q35"; then
        echo -e "${GREEN}[+] QEMU supports q35 machine type${NC}"
    else
        echo -e "${YELLOW}[!] QEMU may not support q35${NC}"
    fi

    echo ""
}

generate_report() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}[7] Summary & Recommendations${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local ISSUES=0
    local WARNINGS=0

    # Check QEMU
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        echo -e "${RED}[!] ISSUE: QEMU not installed${NC}"
        echo -e "${CYAN}[*] Fix: brew install qemu${NC}"
        ISSUES=$((ISSUES + 1))
    fi

    # Check HVF
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! qemu-system-x86_64 -accel help 2>/dev/null | grep -q hvf; then
            echo -e "${YELLOW}[!] WARNING: HVF not available${NC}"
            echo -e "${CYAN}[*] Fix: make build-qemu (build from source)${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi

    # Check disk
    if [[ ! -f "$VM_DIR/worm-ai.qcow2" ]]; then
        echo -e "${YELLOW}[!] WARNING: No disk image${NC}"
        echo -e "${CYAN}[*] Fix: make build (creates disk)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check ISO
    local VALID_ISO_COUNT=$(find "$VM_DIR/iso" -name "*.iso" -type f -size +50M 2>/dev/null | wc -l)
    if [[ $VALID_ISO_COUNT -eq 0 ]]; then
        echo -e "${YELLOW}[!] WARNING: No valid ISO files${NC}"
        echo -e "${CYAN}[*] Fix: make fix (downloads ISO)${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}[+] ✅ Valid ISO found${NC}"
    fi

    echo ""
    if [[ $ISSUES -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}[+] ✅ All checks passed!${NC}"
    else
        echo -e "${CYAN}[*] Found $ISSUES issues and $WARNINGS warnings${NC}"
    fi

    echo ""
    echo -e "${CYAN}[*] Quick fixes:${NC}"
    echo -e "  make deps        # Install QEMU"
    echo -e "  make build-qemu   # Build QEMU with HVF"
    echo -e "  make build        # Create VM files"
    echo -e "  make install      # Download ISO and start install"
    echo ""
}

main() {
    banner

    check_qemu
    check_system
    check_vm_files
    check_network
    check_scripts
    test_qemu_command
    generate_report

    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        ✅ Debug Complete${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
}

main "$@"
