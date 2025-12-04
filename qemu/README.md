# 🐛 Worm-AI QEMU Virtual Machine

Run Worm-AI in an isolated QEMU virtual machine for enhanced security and privacy.

```
██╗    ██╗ ██████╗ ██████╗ ███╗   ███╗     █████╗ ██╗
██║    ██║██╔═══██╗██╔══██╗████╗ ████║    ██╔══██╗██║
██║ █╗ ██║██║   ██║██████╔╝██╔████╔██║    ███████║██║
██║███╗██║██║   ██║██╔══██╗██║╚██╔╝██║    ██╔══██║██║
╚███╔███╔╝╚██████╔╝██║  ██║██║ ╚═╝ ██║    ██║  ██║██║
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═╝╚═╝
```

## ⚡ Quick Start

**Everything is ready!** See [QUICKSTART.md](QUICKSTART.md) for detailed installation steps.

### macOS

```bash
# Install QEMU
brew install qemu

# Navigate to qemu directory
cd qemu

# Start installation
make install
```

Or double-click `Worm-AI.app` to launch!

### Quick Commands

```bash
make install     # Start VM installation
make run         # Boot existing VM
make ssh         # Connect via SSH (port 2222)
make test        # Test VM boot
make debug       # Run diagnostics
make fix         # Fix warnings automatically
```

### Linux

```bash
# Debian/Ubuntu/Kali
sudo apt install qemu-system-x86 qemu-utils

# Fedora
sudo dnf install qemu-system-x86 qemu-img

# Start installation
cd qemu
./launch.sh install
```

## 📦 What's Included

```
qemu/
├── launch.sh          # Main launcher script
├── provision.sh       # VM setup script (run inside VM)
├── Makefile          # Build automation
├── Worm-AI.app/      # macOS app bundle
│   └── Contents/
│       ├── MacOS/launch
│       └── Info.plist
└── vm/               # VM files (created on first run)
    ├── worm-ai.qcow2 # Disk image
    ├── cloud-init/   # Auto-configuration
    └── shared/       # Shared folder
```

## 🚀 Usage

### Makefile Commands

```bash
make deps        # Install QEMU
make install     # Start fresh VM installation
make run         # Boot existing VM
make quick       # Quick boot (Alpine Linux)
make ssh         # SSH into running VM
make app         # Create macOS .app bundle
make install-app # Install to /Applications
make clean       # Remove VM files
make status      # Show current status
```

### Shell Commands

```bash
# Start installation with Debian ISO
./launch.sh install

# Boot existing VM
./launch.sh run

# Quick boot with Alpine Linux (faster, smaller)
./launch.sh quick

# SSH into running VM
./launch.sh ssh

# Clean all VM files
./launch.sh clean
```

## 🔧 VM Setup

After installation, run the provisioning script inside the VM:

```bash
# SSH into VM (from host)
ssh -p 2222 worm@localhost

# Run provisioning script
curl -sSL https://raw.githubusercontent.com/kafyasfngl/worm-ai/main/qemu/provision.sh | bash
```

Or if you have the shared folder mounted:

```bash
/mnt/shared/provision.sh
```

## 🔌 Networking

| Service | Host Port | VM Port | Description |
|---------|-----------|---------|-------------|
| SSH     | 2222      | 22      | Remote access |
| Web     | 8080      | 8080    | Web interfaces |

### SSH Access

```bash
# Default credentials
# User: worm
# Password: worm

ssh -p 2222 worm@localhost
```

### Port Forwarding

To add more ports, edit `launch.sh` and add to `NET_ARGS`:

```bash
hostfwd=tcp::LOCAL_PORT-:VM_PORT
```

## 📁 Shared Folder

Files in `qemu/vm/shared/` are accessible inside the VM at `/mnt/shared/`.

Mount in VM:

```bash
sudo mkdir -p /mnt/shared
sudo mount -t 9p -o trans=virtio shared /mnt/shared
```

## ⚙️ Configuration

### Environment Variables

```bash
export WORM_RAM=4096   # RAM in MB (default: 2048)
export WORM_CPUS=4     # Number of CPUs (default: 2)
```

### VM Specifications

| Resource | Default | Recommended |
|----------|---------|-------------|
| RAM      | 2 GB    | 4 GB        |
| CPUs     | 2       | 4           |
| Disk     | 8 GB    | 16 GB       |

## 🔒 Security Benefits

- **Isolation**: Worm-AI runs in a completely isolated environment
- **Tor Integration**: Built-in Tor proxy support
- **Snapshot**: Take VM snapshots before risky operations
- **Disposable**: Easy to reset to clean state

### Creating Snapshots

```bash
# Create snapshot
qemu-img snapshot -c clean_state vm/worm-ai.qcow2

# List snapshots
qemu-img snapshot -l vm/worm-ai.qcow2

# Restore snapshot
qemu-img snapshot -a clean_state vm/worm-ai.qcow2
```

## 🚀 Performance Optimization

### Current Setup (TCG Multi-threaded)

Your current QEMU setup uses **TCG with multi-threading** - the best available for macOS with the stable QEMU build.

### Performance Comparison

| Acceleration | macOS | Linux | Speed | Status |
|-------------|-------|-------|-------|--------|
| **TCG Multi-thread** | ✅ | ✅ | Good | **Current** |
| HVF (HEAD QEMU) | ❌¹ | ❌ | **Fastest** | Unavailable |
| KVM | ❌ | ✅ | **Fastest** | Linux only |

¹ *HEAD builds currently fail due to subproject issues*

### Manual Build with HVF

For guaranteed HVF support, build QEMU from source:

```bash
cd qemu
./build-qemu.sh  # Automated build script
```

Or follow manual steps in [BUILD.md](BUILD.md)

This gives you:
- ✅ Guaranteed HVF acceleration
- ✅ Full control over build options
- ✅ Latest features and fixes
- ⏱️ Takes 15-30 minutes to build

### Alternative: UTM for HVF

For true HVF performance with a GUI:

```bash
brew install --cask utm  # macOS virtualization app
# Then manually import your VM files
```

UTM provides hardware acceleration and a nice GUI interface.

## 🖥️ Display Options

### Headless Mode

Run without display (SSH only):

```bash
# Add to launch.sh
DISPLAY_ARGS="-display none -daemonize"
```

### VNC Access

```bash
# Add to launch.sh
DISPLAY_ARGS="-vnc :0"
# Connect with: vnc://localhost:5900
```

## 🐧 Supported Guest OS

| OS | Status | Notes |
|----|--------|-------|
| Debian 12 | ✅ Recommended | Full support |
| Kali Linux | ✅ Supported | Ideal for security work |
| Ubuntu | ✅ Supported | Works well |
| Alpine | ✅ Supported | Lightweight, fast boot |
| Arch | ✅ Supported | Rolling release |

## 🛠️ Troubleshooting

### QEMU not starting

```bash
# Check if virtualization is enabled
# macOS:
sysctl kern.hv_support

# Linux:
grep -E 'vmx|svm' /proc/cpuinfo
```

### Slow performance

1. Ensure hardware virtualization is enabled in BIOS
2. On macOS, HVF should be detected automatically
3. On Linux, ensure KVM is available: `ls -la /dev/kvm`

### Network issues

```bash
# Check if ports are in use
lsof -i :2222
lsof -i :8080

# Try different ports in launch.sh
```

### Shared folder not working

```bash
# Inside VM, check if 9p is supported
cat /proc/filesystems | grep 9p

# If not, install:
# Debian: sudo apt install qemu-guest-agent
```

## 📜 License

MIT License - see [LICENSE](../LICENSE)

---

<p align="center">
  Made with 💀 by the community<br>
  <a href="https://t.me/xsocietyforums">Telegram</a> •
  <a href="https://github.com/kafyasfngl">GitHub</a>
</p>
