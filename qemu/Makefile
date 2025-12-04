# ═══════════════════════════════════════════════════════════════════════════════
# 🐛 Worm-AI QEMU Makefile
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: all install run build clean help app ssh deps build-qemu debug fix test

SHELL := /bin/bash
QEMU_DIR := $(shell pwd)
VM_DIR := $(QEMU_DIR)/vm
APP_NAME := Worm-AI.app

# Default target
all: help

# Install QEMU dependencies
deps:
	@echo "🔧 Installing dependencies..."
	@if command -v brew &>/dev/null; then \
		brew install qemu; \
	elif command -v apt &>/dev/null; then \
		sudo apt update && sudo apt install -y qemu-system-x86 qemu-utils; \
	elif command -v dnf &>/dev/null; then \
		sudo dnf install -y qemu-system-x86 qemu-img; \
	else \
		echo "Please install QEMU manually"; \
	fi

# Build QEMU from source with HVF support
build-qemu:
	@echo "🔨 Building QEMU from source with HVF..."
	@chmod +x build-qemu.sh
	@./build-qemu.sh

# Run debug diagnostics
debug:
	@echo "🔍 Running diagnostics..."
	@chmod +x debug.sh
	@./debug.sh

# Fix warnings automatically
fix:
	@echo "🔧 Fixing warnings..."
	@chmod +x fix-warnings.sh
	@./fix-warnings.sh

# Test VM launch
test:
	@echo "🧪 Testing VM..."
	@chmod +x test-vm.sh
	@./test-vm.sh

# Build/prepare VM files
build:
	@echo "🔨 Building VM files..."
	@chmod +x launch.sh
	@./launch.sh build

# Start fresh installation
install:
	@echo "💿 Starting VM installation..."
	@chmod +x launch.sh
	@./launch.sh install

# Run existing VM
run:
	@echo "🚀 Launching VM..."
	@chmod +x launch.sh
	@./launch.sh run

# Quick boot (Alpine)
quick:
	@echo "⚡ Quick boot..."
	@chmod +x launch.sh
	@./launch.sh quick

# SSH into VM
ssh:
	@echo "🔗 Connecting via SSH..."
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 2222 worm@localhost

# Create macOS app bundle
app:
	@echo "📦 Creating macOS app bundle..."
	@chmod +x $(APP_NAME)/Contents/MacOS/launch
	@echo "✅ App created: $(APP_NAME)"
	@echo "   You can now move it to /Applications"

# Install app to /Applications
install-app: app
	@echo "📲 Installing to /Applications..."
	@cp -R $(APP_NAME) /Applications/
	@echo "✅ Installed to /Applications/$(APP_NAME)"

# Clean VM files
clean:
	@echo "🧹 Cleaning VM files..."
	@rm -rf $(VM_DIR)
	@echo "✅ Cleaned"

# Clean everything including app
clean-all: clean
	@rm -rf $(APP_NAME)

# Download Debian ISO
iso:
	@echo "📥 Downloading Debian ISO..."
	@mkdir -p $(VM_DIR)/iso
	@curl -L -o $(VM_DIR)/iso/debian-netinst.iso \
		"https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.8.0-amd64-netinst.iso"

# Create disk image only
disk:
	@echo "💾 Creating disk image..."
	@mkdir -p $(VM_DIR)
	@qemu-img create -f qcow2 $(VM_DIR)/worm-ai.qcow2 8G

# Show status
status:
	@echo "═══════════════════════════════════════════════════════"
	@echo "🐛 Worm-AI QEMU Status"
	@echo "═══════════════════════════════════════════════════════"
	@echo "QEMU Dir:    $(QEMU_DIR)"
	@echo "VM Dir:      $(VM_DIR)"
	@echo ""
	@echo "Files:"
	@ls -la $(VM_DIR)/ 2>/dev/null || echo "  (No VM files yet)"
	@echo ""
	@echo "QEMU Version:"
	@qemu-system-x86_64 --version 2>/dev/null | head -1 || echo "  QEMU not installed"

# Help
help:
	@echo ""
	@echo "═══════════════════════════════════════════════════════"
	@echo "🐛 Worm-AI QEMU Makefile"
	@echo "═══════════════════════════════════════════════════════"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  deps        Install QEMU (brew/apt/dnf)"
	@echo "  build-qemu  Build QEMU from source with HVF (macOS)"
	@echo "  debug       Run diagnostics and check setup"
	@echo "  fix         Fix warnings (ISO, HVF, etc.)"
	@echo "  test        Test VM launch (quick boot test)"
	@echo "  build       Prepare VM files"
	@echo "  install     Start fresh VM installation"
	@echo "  run         Boot existing VM"
	@echo "  quick       Quick boot with Alpine Linux"
	@echo "  ssh         SSH into running VM"
	@echo "  app         Create macOS .app bundle"
	@echo "  install-app Install app to /Applications"
	@echo "  iso         Download Debian ISO"
	@echo "  disk        Create disk image only"
	@echo "  status      Show current status"
	@echo "  clean       Remove VM files"
	@echo "  clean-all   Remove everything"
	@echo "  help        Show this help"
	@echo ""
	@echo "Quick Start:"
	@echo "  make deps        # Install QEMU (stable)"
	@echo "  make build-qemu  # Build QEMU with HVF (better performance)"
	@echo "  make install     # Install Debian in VM"
	@echo "  make run         # Boot VM"
	@echo "  make ssh         # Connect to VM"
	@echo ""
