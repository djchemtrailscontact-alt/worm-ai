#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Build QEMU from Source with HVF Support
# Manual build script for QEMU with Hardware Virtualization Framework
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BUILD_DIR="$HOME/qemu-build"
QEMU_VERSION="9.2.0"  # Stable version with good HVF support
INSTALL_PREFIX="/opt/homebrew"  # or /usr/local for Intel Macs

banner() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        🐛 QEMU Manual Build with HVF${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

check_dependencies() {
    echo -e "${YELLOW}[*] Checking dependencies...${NC}"

    local MISSING=()

    # Check for required tools
    command -v git >/dev/null || MISSING+=("git")
    command -v make >/dev/null || MISSING+=("make")
    command -v python3 >/dev/null || MISSING+=("python3")
    command -v pkg-config >/dev/null || MISSING+=("pkg-config")
    command -v meson >/dev/null || MISSING+=("meson")
    command -v ninja >/dev/null || MISSING+=("ninja")

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        echo -e "${RED}[!] Missing dependencies: ${MISSING[*]}${NC}"
        echo -e "${YELLOW}[*] Install with: brew install ${MISSING[*]}${NC}"
        exit 1
    fi

    echo -e "${GREEN}[+] All dependencies found${NC}"
}

install_build_deps() {
    echo -e "${YELLOW}[*] Installing build dependencies...${NC}"

    brew install \
        git \
        make \
        python3 \
        pkg-config \
        meson \
        ninja \
        glib \
        pixman \
        libslirp \
        capstone \
        dtc \
        vde \
        jpeg-turbo \
        libpng \
        gnutls \
        nettle \
        lzo \
        snappy \
        zstd \
        spice-protocol || true

    echo -e "${GREEN}[+] Build dependencies installed${NC}"
}

detect_arch() {
    local ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        echo "arm64"
        INSTALL_PREFIX="/opt/homebrew"
    else
        echo "x86_64"
        INSTALL_PREFIX="/usr/local"
    fi
}

clone_qemu() {
    echo -e "${YELLOW}[*] Cloning QEMU source...${NC}"

    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"

    if [[ -d "qemu" ]]; then
        echo -e "${CYAN}[*] QEMU directory exists, updating...${NC}"
        cd qemu
        git fetch origin
        git checkout master
        git pull origin master
    else
        git clone https://gitlab.com/qemu-project/qemu.git
        cd qemu
    fi

    # Checkout stable version or use latest
    if [[ -n "$QEMU_VERSION" ]]; then
        echo -e "${CYAN}[*] Checking out version $QEMU_VERSION...${NC}"
        git checkout "v$QEMU_VERSION" 2>/dev/null || git checkout master
    fi

    echo -e "${GREEN}[+] QEMU source ready${NC}"
}

configure_qemu() {
    echo -e "${YELLOW}[*] Configuring QEMU build...${NC}"

    cd "$BUILD_DIR/qemu"

    # Clean previous build
    if [[ -d "build" ]]; then
        echo -e "${CYAN}[*] Cleaning previous build...${NC}"
        rm -rf build
    fi

    mkdir -p build
    cd build

    # Configure with HVF support
    ../configure \
        --prefix="$INSTALL_PREFIX" \
        --enable-hvf \
        --enable-cocoa \
        --enable-virtfs \
        --enable-slirp=system \
        --enable-capstone=system \
        --enable-dtc=system \
        --enable-vde \
        --enable-libssh \
        --enable-libusb \
        --enable-jpeg \
        --enable-png \
        --enable-gnutls \
        --enable-nettle \
        --enable-lzo \
        --enable-snappy \
        --enable-zstd \
        --enable-spice \
        --disable-bsd-user \
        --disable-guest-agent \
        --disable-sdl \
        --disable-gtk \
        --python=python3

    echo -e "${GREEN}[+] Configuration complete${NC}"
    echo -e "${CYAN}[*] Build options:${NC}"
    echo -e "    Prefix: $INSTALL_PREFIX"
    echo -e "    HVF: enabled"
    echo -e "    Cocoa: enabled (macOS display)"
}

build_qemu() {
    echo -e "${YELLOW}[*] Building QEMU (this will take 15-30 minutes)...${NC}"
    echo -e "${CYAN}[*] Using $(sysctl -n hw.ncpu) CPU cores${NC}"

    cd "$BUILD_DIR/qemu/build"

    # Build with all available cores
    make -j$(sysctl -n hw.ncpu)

    echo -e "${GREEN}[+] Build complete!${NC}"
}

install_qemu() {
    echo -e "${YELLOW}[*] Installing QEMU...${NC}"

    cd "$BUILD_DIR/qemu/build"

    # Backup existing QEMU if installed via Homebrew
    if command -v qemu-system-x86_64 >/dev/null 2>&1; then
        local OLD_QEMU=$(which qemu-system-x86_64)
        echo -e "${CYAN}[*] Backing up existing QEMU: $OLD_QEMU${NC}"
        sudo mv "$OLD_QEMU" "${OLD_QEMU}.backup" 2>/dev/null || true
    fi

    # Install
    sudo make install

    echo -e "${GREEN}[+] QEMU installed to $INSTALL_PREFIX${NC}"
}

verify_installation() {
    echo -e "${YELLOW}[*] Verifying installation...${NC}"

    # Update PATH
    export PATH="$INSTALL_PREFIX/bin:$PATH"

    if command -v qemu-system-x86_64 >/dev/null; then
        local QEMU_PATH=$(which qemu-system-x86_64)
        local QEMU_VERSION=$(qemu-system-x86_64 --version | head -1)

        echo -e "${GREEN}[+] QEMU found: $QEMU_PATH${NC}"
        echo -e "${GREEN}[+] Version: $QEMU_VERSION${NC}"

        # Check for HVF support
        if qemu-system-x86_64 -accel help 2>/dev/null | grep -q hvf; then
            echo -e "${GREEN}[+] ✅ HVF acceleration is available!${NC}"
        else
            echo -e "${YELLOW}[!] ⚠️  HVF not found in accelerator list${NC}"
            echo -e "${CYAN}[*] Check with: qemu-system-x86_64 -accel help${NC}"
        fi
    else
        echo -e "${RED}[!] QEMU not found in PATH${NC}"
        echo -e "${YELLOW}[*] Add to PATH: export PATH=\"$INSTALL_PREFIX/bin:\$PATH\"${NC}"
    fi
}

update_path() {
    local SHELL_RC=""
    if [[ "$SHELL" == *zsh* ]]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.bashrc"
    fi

    if ! grep -q "$INSTALL_PREFIX/bin" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# QEMU with HVF support" >> "$SHELL_RC"
        echo "export PATH=\"$INSTALL_PREFIX/bin:\$PATH\"" >> "$SHELL_RC"
        echo -e "${GREEN}[+] Added to $SHELL_RC${NC}"
        echo -e "${CYAN}[*] Run: source $SHELL_RC${NC}"
    fi
}

main() {
    banner

    ARCH=$(detect_arch)
    echo -e "${CYAN}[*] Detected architecture: $ARCH${NC}"
    echo -e "${CYAN}[*] Install prefix: $INSTALL_PREFIX${NC}"
    echo ""

    read -p "Install build dependencies? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_build_deps
    fi

    check_dependencies
    clone_qemu
    configure_qemu

    echo ""
    read -p "Start build? This will take 15-30 minutes (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_qemu

        echo ""
        read -p "Install QEMU? (requires sudo) (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_qemu
            verify_installation
            update_path

            echo ""
            echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}        ✅ QEMU Build Complete!${NC}"
            echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
            echo ""
            echo -e "  ${GREEN}🚀 Test with: cd qemu && make install${NC}"
            echo -e "  ${GREEN}⚡ You should now have HVF acceleration!${NC}"
            echo ""
        fi
    else
        echo -e "${YELLOW}[*] Build cancelled${NC}"
        echo -e "${CYAN}[*] To build later: cd $BUILD_DIR/qemu/build && make -j\$(sysctl -n hw.ncpu)${NC}"
    fi
}

main "$@"
