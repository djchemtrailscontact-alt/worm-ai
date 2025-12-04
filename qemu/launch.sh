#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Worm-AI QEMU Launcher
# Launch Worm-AI in an isolated QEMU virtual machine
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORM_AI_DIR="$(dirname "$SCRIPT_DIR")"
VM_DIR="$SCRIPT_DIR/vm"
DISK_IMAGE="$VM_DIR/worm-ai.qcow2"
DISK_SIZE="8G"
RAM="2048"
CPUS="2"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

banner() {
    echo -e "${RED}"
    cat << 'EOF'
██╗    ██╗ ██████╗ ██████╗ ███╗   ███╗     █████╗ ██╗
██║    ██║██╔═══██╗██╔══██╗████╗ ████║    ██╔══██╗██║
██║ █╗ ██║██║   ██║██████╔╝██╔████╔██║    ███████║██║
██║███╗██║██║   ██║██╔══██╗██║╚██╔╝██║    ██╔══██║██║
╚███╔███╔╝╚██████╔╝██║  ██║██║ ╚═╝ ██║    ██║  ██║██║
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═╝╚═╝
EOF
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        🐛 QEMU Virtual Machine Launcher${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

check_qemu() {
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        echo -e "${RED}[!] QEMU not found. Installing...${NC}"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install qemu
            else
                echo -e "${RED}[!] Please install Homebrew first: https://brew.sh${NC}"
                exit 1
            fi
        elif command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y qemu-system-x86 qemu-utils
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y qemu-system-x86 qemu-img
        elif command -v pacman &> /dev/null; then
            sudo pacman -Sy qemu-full
        else
            echo -e "${RED}[!] Please install QEMU manually${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}[+] QEMU is installed${NC}"
}

download_iso() {
    local ISO_DIR="$VM_DIR/iso"
    local ISO_FILE="$ISO_DIR/debian-netinst.iso"
    local MIN_SIZE=100000000  # 100MB minimum for a valid ISO

    mkdir -p "$ISO_DIR"

    # Check if ISO exists and is valid
    if [[ -f "$ISO_FILE" ]]; then
        local FILE_SIZE=$(stat -f%z "$ISO_FILE" 2>/dev/null || stat -c%s "$ISO_FILE" 2>/dev/null || echo "0")
        local FILE_TYPE=$(file "$ISO_FILE" 2>/dev/null | grep -i "iso\|cd\|disk" || echo "")

        if [[ "$FILE_SIZE" -gt "$MIN_SIZE" ]] || [[ -n "$FILE_TYPE" ]]; then
            echo -e "${GREEN}[+] Debian ISO already downloaded ($(numfmt --to=iec-i --suffix=B $FILE_SIZE 2>/dev/null || echo "${FILE_SIZE} bytes"))${NC}" >&2
            echo "$ISO_FILE"
            return 0
        else
            echo -e "${YELLOW}[!] Existing ISO file appears invalid, re-downloading...${NC}" >&2
            rm -f "$ISO_FILE"
        fi
    fi

    echo -e "${YELLOW}[*] Downloading Debian minimal ISO (this may take a while)...${NC}" >&2

    # Try multiple mirrors and methods
    local MIRRORS=(
        "https://mirror.fcix.net/debian-cd/current/amd64/iso-cd/"
        "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/"
        "https://deb.debian.org/debian-cd/current/amd64/iso-cd/"
    )

    # First, try to find the actual filename
    local ISO_FILENAME=""
    for MIRROR in "${MIRRORS[@]}"; do
        echo -e "${CYAN}[*] Checking mirror: $MIRROR${NC}" >&2
        ISO_FILENAME=$(curl -s "$MIRROR" | grep -o 'debian-[0-9.]*-amd64-netinst\.iso' | head -1)
        if [[ -n "$ISO_FILENAME" ]]; then
            echo -e "${GREEN}[+] Found ISO: $ISO_FILENAME${NC}" >&2
            break
        fi
    done

    # If we couldn't find it, use a known working URL
    if [[ -z "$ISO_FILENAME" ]]; then
        echo -e "${YELLOW}[!] Could not auto-detect ISO filename, using direct download${NC}" >&2
        # Use a smaller Alpine Linux ISO as fallback (faster download for testing)
        echo -e "${CYAN}[*] Using Alpine Linux for quick setup (smaller, faster)${NC}" >&2
        ISO_FILE="$ISO_DIR/alpine-virt.iso"
        local ALPINE_URL="https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-virt-3.19.0-x86_64.iso"

        if curl -L --progress-bar -o "$ISO_FILE" "$ALPINE_URL"; then
            local FILE_SIZE=$(stat -f%z "$ISO_FILE" 2>/dev/null || stat -c%s "$ISO_FILE" 2>/dev/null || echo "0")
            if [[ "$FILE_SIZE" -gt 50000000 ]]; then
                echo -e "${GREEN}[+] Alpine ISO downloaded successfully${NC}" >&2
                echo "$ISO_FILE"
                return 0
            fi
        fi
        return 1
    fi

    # Try downloading from mirrors
    for MIRROR in "${MIRRORS[@]}"; do
        local ISO_URL="${MIRROR}${ISO_FILENAME}"
        echo -e "${CYAN}[*] Trying: $ISO_URL${NC}" >&2

        if curl -L --progress-bar -o "$ISO_FILE" "$ISO_URL"; then
            # Validate downloaded file
            local FILE_SIZE=$(stat -f%z "$ISO_FILE" 2>/dev/null || stat -c%s "$ISO_FILE" 2>/dev/null || echo "0")
            if [[ "$FILE_SIZE" -gt "$MIN_SIZE" ]]; then
                echo -e "${GREEN}[+] ISO downloaded successfully ($(numfmt --to=iec-i --suffix=B $FILE_SIZE 2>/dev/null || echo "${FILE_SIZE} bytes"))${NC}" >&2
                echo "$ISO_FILE"
                return 0
            else
                echo -e "${YELLOW}[!] File too small, trying next mirror...${NC}" >&2
                rm -f "$ISO_FILE"
            fi
        fi
    done

    echo -e "${RED}[!] All download attempts failed${NC}" >&2
    echo -e "${YELLOW}[*] You can manually download Debian ISO and place it in: $ISO_DIR${NC}" >&2
    return 1
}

create_disk() {
    mkdir -p "$VM_DIR"

    if [[ -f "$DISK_IMAGE" ]]; then
        echo -e "${GREEN}[+] Disk image already exists${NC}"
    else
        echo -e "${YELLOW}[*] Creating disk image ($DISK_SIZE)...${NC}"
        qemu-img create -f qcow2 "$DISK_IMAGE" "$DISK_SIZE"
    fi
}

create_cloud_init() {
    local CLOUD_DIR="$VM_DIR/cloud-init"
    mkdir -p "$CLOUD_DIR"

    # User-data for cloud-init
    cat > "$CLOUD_DIR/user-data" << 'USERDATA'
#cloud-config
hostname: worm-ai
users:
  - name: worm
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    groups: sudo
    lock_passwd: false
    # Password: worm (hashed)
    passwd: $6$rounds=4096$xyz$LkKQHvEU1J3A8gMQKjMgPLqh1J7L8QKnDjJgL8zKpQsL8K8QKjM8PLq1J7L8QKnDjJ8L8zKpQsL8K

packages:
  - python3
  - python3-pip
  - python3-venv
  - python3-tk
  - git
  - curl
  - libcurl4-openssl-dev
  - libssl-dev
  - tor

runcmd:
  - systemctl enable tor
  - pip3 install --break-system-packages worm-ai || pip3 install worm-ai
  - echo 'alias worm="worm-ai"' >> /home/worm/.bashrc
  - echo 'export WORM_PROXY=socks5://127.0.0.1:9050' >> /home/worm/.bashrc
  - chown -R worm:worm /home/worm

final_message: "🐛 Worm-AI VM is ready! Login: worm / worm"
USERDATA

    # Meta-data
    cat > "$CLOUD_DIR/meta-data" << 'METADATA'
instance-id: worm-ai-vm
local-hostname: worm-ai
METADATA

    # Create cloud-init ISO
    if command -v genisoimage &> /dev/null; then
        genisoimage -output "$VM_DIR/cloud-init.iso" -volid cidata -joliet -rock \
            "$CLOUD_DIR/user-data" "$CLOUD_DIR/meta-data" 2>/dev/null
    elif command -v mkisofs &> /dev/null; then
        mkisofs -output "$VM_DIR/cloud-init.iso" -volid cidata -joliet -rock \
            "$CLOUD_DIR/user-data" "$CLOUD_DIR/meta-data" 2>/dev/null
    elif command -v hdiutil &> /dev/null; then
        # macOS alternative
        hdiutil makehybrid -o "$VM_DIR/cloud-init.iso" -hfs -joliet -iso -default-volume-name cidata \
            "$CLOUD_DIR" 2>/dev/null || true
    fi

    echo -e "${GREEN}[+] Cloud-init configuration created${NC}"
}

setup_shared_folder() {
    # Create a shared folder for easy file transfer
    local SHARED_DIR="$VM_DIR/shared"
    mkdir -p "$SHARED_DIR"

    # Copy worm-ai source for local install
    cp -r "$WORM_AI_DIR/src" "$SHARED_DIR/" 2>/dev/null || true
    cp "$WORM_AI_DIR/pyproject.toml" "$SHARED_DIR/" 2>/dev/null || true
    cp "$WORM_AI_DIR/requirements.txt" "$SHARED_DIR/" 2>/dev/null || true
    cp "$WORM_AI_DIR/system-prompt.txt" "$SHARED_DIR/" 2>/dev/null || true

    echo -e "${GREEN}[+] Shared folder prepared: $SHARED_DIR${NC}"
}

launch_vm() {
    local MODE="${1:-run}"
    local ISO_FILE=""
    local EXTRA_ARGS=""

    # Determine QEMU accelerator
    local ACCEL=""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - TCG with optimizations
        ACCEL="-accel tcg,thread=multi"
        echo -e "${YELLOW}[*] Using TCG with multi-threading (macOS)${NC}"
        echo -e "${CYAN}[*] For HVF support: Consider UTM app or manual QEMU build${NC}"
    else
        # Linux - use KVM if available
        if [[ -r /dev/kvm ]]; then
            ACCEL="-enable-kvm"
            echo -e "${GREEN}[+] Using KVM acceleration${NC}"
        else
            ACCEL="-accel tcg"
            echo -e "${YELLOW}[*] Using TCG emulation (slower)${NC}"
        fi
    fi

    case "$MODE" in
        install)
            # Check for existing ISO first (Alpine or Debian)
            if [[ -f "$VM_DIR/iso/alpine-virt.iso" ]]; then
                ISO_FILE="$VM_DIR/iso/alpine-virt.iso"
                echo -e "${GREEN}[+] Using Alpine Linux ISO${NC}"
            elif [[ -f "$VM_DIR/iso/debian-netinst.iso" ]]; then
                ISO_FILE="$VM_DIR/iso/debian-netinst.iso"
                echo -e "${GREEN}[+] Using Debian ISO${NC}"
            else
                ISO_FILE=$(download_iso)
            fi

            if [[ ! -f "$ISO_FILE" ]]; then
                echo -e "${RED}[!] ISO file not found: $ISO_FILE${NC}"
                exit 1
            fi

            # Validate ISO size
            local ISO_SIZE=$(stat -f%z "$ISO_FILE" 2>/dev/null || stat -c%s "$ISO_FILE" 2>/dev/null || echo "0")
            if [[ "$ISO_SIZE" -lt 50000000 ]]; then
                echo -e "${RED}[!] ISO file appears invalid (too small: ${ISO_SIZE} bytes)${NC}"
                echo -e "${YELLOW}[*] Run: make fix (to download a valid ISO)${NC}"
                exit 1
            fi

            # Boot from CDROM first, then hard disk
            # Use -boot d to boot from first CDROM drive
            if [[ -f "$VM_DIR/cloud-init.iso" ]]; then
                EXTRA_ARGS="-drive file=$ISO_FILE,media=cdrom,index=0,if=ide -drive file=$VM_DIR/cloud-init.iso,media=cdrom,index=1,if=ide -boot d"
            else
                EXTRA_ARGS="-cdrom $ISO_FILE -boot d"
            fi
            echo -e "${YELLOW}[*] Starting installation mode...${NC}"
            echo -e "${CYAN}[*] Boot order: CDROM -> Hard Disk${NC}"
            echo -e "${CYAN}[*] ISO: $(basename "$ISO_FILE") ($(numfmt --to=iec-i --suffix=B $ISO_SIZE 2>/dev/null || echo "${ISO_SIZE} bytes"))${NC}"
            if [[ "$ISO_FILE" == *alpine* ]]; then
                echo -e "${CYAN}[*] Follow the Alpine installer, then run './launch.sh run' to boot${NC}"
            else
                echo -e "${CYAN}[*] Follow the Debian installer, then run './launch.sh run' to boot${NC}"
            fi
            ;;
        run)
            if [[ ! -f "$DISK_IMAGE" ]]; then
                echo -e "${RED}[!] No disk image found. Run './launch.sh install' first${NC}"
                exit 1
            fi
            # Boot from hard disk only (c = hard disk)
            EXTRA_ARGS="-boot c"
            echo -e "${GREEN}[+] Booting Worm-AI VM from hard disk...${NC}"
            echo -e "${YELLOW}[!] If VM doesn't boot, you may need to install an OS first with './launch.sh install'${NC}"
            ;;
        quick)
            # Quick boot with pre-built image
            create_quick_image
            EXTRA_ARGS="-boot order=c"
            echo -e "${GREEN}[+] Quick booting Worm-AI VM...${NC}"
            ;;
    esac

    # Port forwarding for SSH and potential web interfaces
    local NET_ARGS="-netdev user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:8080"
    NET_ARGS="$NET_ARGS -device virtio-net-pci,netdev=net0"

    # Shared folder via 9p (Linux host) or virtio-fs
    local SHARE_ARGS=""
    if [[ -d "$VM_DIR/shared" ]]; then
        SHARE_ARGS="-virtfs local,path=$VM_DIR/shared,mount_tag=shared,security_model=mapped-xattr"
    fi

    # Display options
    local DISPLAY_ARGS=""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        DISPLAY_ARGS="-display cocoa"
    else
        DISPLAY_ARGS="-display gtk"
    fi

    # Add cloud-init if available
    local CLOUD_ARGS=""
    if [[ -f "$VM_DIR/cloud-init.iso" ]]; then
        CLOUD_ARGS="-cdrom $VM_DIR/cloud-init.iso"
    fi

    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  SSH:  ssh -p 2222 worm@localhost${NC}"
    echo -e "${GREEN}  User: worm | Password: worm${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""

    # Select CPU type based on accelerator
    local CPU_TYPE=""
    if [[ "$ACCEL" == *hvf* ]] || [[ "$ACCEL" == *kvm* ]]; then
        CPU_TYPE="-cpu host"
    else
        CPU_TYPE="-cpu qemu64"
    fi

    # Performance optimizations
    local PERF_ARGS=""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS-specific optimizations for TCG
        PERF_ARGS="-rtc base=localtime"
    fi

    # Machine type for better compatibility (use pc-i440fx if q35 not available)
    local MACHINE_TYPE="-machine pc-i440fx-9.2"

    # Disk drive - use IDE for boot compatibility during install
    local DISK_DRIVE=""
    if [[ "$MODE" == "install" ]]; then
        # During install, use IDE for better boot compatibility
        DISK_DRIVE="-drive file=$DISK_IMAGE,format=qcow2,if=ide,index=1"
    else
        # After install, can use virtio for better performance
        DISK_DRIVE="-drive file=$DISK_IMAGE,format=qcow2,if=virtio,cache=writeback"
    fi

    # Launch QEMU
    qemu-system-x86_64 \
        $ACCEL \
        $MACHINE_TYPE \
        -m "$RAM" \
        -smp "$CPUS" \
        $CPU_TYPE \
        $DISK_DRIVE \
        $NET_ARGS \
        $SHARE_ARGS \
        $DISPLAY_ARGS \
        $PERF_ARGS \
        $EXTRA_ARGS \
        $CLOUD_ARGS \
        -usb \
        -device usb-tablet
}

create_quick_image() {
    # Create a quick-start image using Alpine Linux (smaller/faster)
    local ALPINE_URL="https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-virt-3.19.0-x86_64.iso"
    local ALPINE_ISO="$VM_DIR/iso/alpine-virt.iso"

    mkdir -p "$VM_DIR/iso"

    if [[ ! -f "$ALPINE_ISO" ]]; then
        echo -e "${YELLOW}[*] Downloading Alpine Linux (lightweight)...${NC}"
        curl -L -o "$ALPINE_ISO" "$ALPINE_URL"
    fi

    create_disk
}

show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install    - Start with Debian ISO for fresh installation"
    echo "  run        - Boot existing VM (default)"
    echo "  quick      - Quick boot with Alpine Linux"
    echo "  build      - Build a pre-configured image"
    echo "  ssh        - Connect via SSH to running VM"
    echo "  clean      - Remove all VM files"
    echo "  help       - Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  WORM_RAM   - RAM in MB (default: 2048)"
    echo "  WORM_CPUS  - Number of CPUs (default: 2)"
    echo ""
}

ssh_connect() {
    echo -e "${CYAN}[*] Connecting to VM via SSH...${NC}"
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -p 2222 worm@localhost
}

clean_vm() {
    echo -e "${YELLOW}[*] Removing VM files...${NC}"
    rm -rf "$VM_DIR"
    echo -e "${GREEN}[+] Cleaned${NC}"
}

# Override defaults from environment
RAM="${WORM_RAM:-$RAM}"
CPUS="${WORM_CPUS:-$CPUS}"

# Main
banner
check_qemu

case "${1:-run}" in
    install)
        create_disk
        create_cloud_init
        setup_shared_folder
        launch_vm install
        ;;
    run)
        launch_vm run
        ;;
    quick)
        launch_vm quick
        ;;
    build)
        create_disk
        create_cloud_init
        setup_shared_folder
        echo -e "${GREEN}[+] VM files prepared in $VM_DIR${NC}"
        ;;
    ssh)
        ssh_connect
        ;;
    clean)
        clean_vm
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}[!] Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
