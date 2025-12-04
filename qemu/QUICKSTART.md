# 🚀 Worm-AI QEMU Quick Start Guide

## ✅ Everything is Ready!

Your QEMU VM setup is tested and working. Here's how to use it:

## 📋 Installation Steps

### 1. Start VM Installation

```bash
cd qemu
make install
```

This will:
- Boot from Alpine Linux ISO
- Show the installer interface
- Allow you to install the OS

### 2. Alpine Linux Installation

When the VM boots, you'll see the Alpine installer:

1. **Login**: Type `root` (no password needed)
2. **Setup**: Run `setup-alpine`
3. **Follow prompts**:
   - Keyboard: `us` (or your preference)
   - Hostname: `worm-ai`
   - Network: Choose your interface (usually `eth0`)
   - IP: `dhcp` (automatic)
   - Root password: Set a password (remember it!)
   - Timezone: Your timezone
   - Proxy: `none`
   - NTP: `chrony` (or `none`)
   - SSH: `openssh` (recommended)
   - Disk: `sda` (or auto)
   - Mode: `sys` (install to disk)
   - Erase and use: `y`

4. **Wait for installation** (5-10 minutes)
5. **Reboot**: Type `reboot`

### 3. After Installation

Once Alpine is installed:

```bash
# SSH into the VM (from host)
ssh -p 2222 root@localhost
# Password: (the one you set)
```

### 4. Install Worm-AI

Inside the VM, run:

```bash
# Update system
apk update && apk upgrade

# Install dependencies
apk add python3 py3-pip py3-virtualenv git curl wget

# Install Worm-AI
pip3 install --user git+https://github.com/kafyasfngl/worm-ai.git

# Or from shared folder (if mounted)
cd /mnt/shared
pip3 install --user -e .
```

### 5. Configure Environment

```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Test
worm-ai --version
```

## 🎯 Quick Commands

```bash
# Start installation
make install

# Boot existing VM
make run

# SSH into VM
make ssh
# Or: ssh -p 2222 root@localhost

# Test VM
make test

# Debug issues
make debug

# Fix warnings
make fix
```

## 🔧 VM Management

### Start VM
```bash
make run
```

### Stop VM
- Press `Ctrl+C` in the terminal, or
- Close the QEMU window, or
- From another terminal: `pkill -f qemu-system-x86_64`

### SSH Access
```bash
ssh -p 2222 root@localhost
# Default: root / (your password)
```

### Shared Folder

Files in `qemu/vm/shared/` are accessible in the VM:

```bash
# Inside VM (if 9p is mounted)
ls /mnt/shared

# Or mount manually
mkdir -p /mnt/shared
mount -t 9p -o trans=virtio shared /mnt/shared
```

## 📊 VM Specifications

- **OS**: Alpine Linux 3.19.0
- **RAM**: 2GB (configurable)
- **CPU**: 2 cores (configurable)
- **Disk**: 8GB (expandable)
- **Network**: NAT with port forwarding
- **SSH**: Port 2222
- **Web**: Port 8080

## 🐛 Troubleshooting

### VM Won't Boot

```bash
make debug    # Check for issues
make test     # Test boot
```

### Can't SSH

```bash
# Check if VM is running
ps aux | grep qemu

# Check port
lsof -i :2222

# Try different port in launch.sh
```

### ISO Not Found

```bash
make fix      # Downloads ISO
```

### Performance Issues

```bash
# Build QEMU with HVF (much faster)
make build-qemu
```

## 📝 Next Steps

1. ✅ **Install Alpine Linux** in the VM
2. ✅ **Install Worm-AI** inside the VM
3. ✅ **Configure** proxy/settings
4. ✅ **Start using** Worm-AI!

## 🎉 You're Ready!

Everything is tested and working. Just run `make install` to start!

---

**Need help?** Run `make debug` for diagnostics.
