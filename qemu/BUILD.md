# 🔨 Manual QEMU Build with HVF Support

Build QEMU from source with Hardware Virtualization Framework (HVF) support for maximum performance on macOS.

## ⚡ Quick Start

```bash
cd qemu
./build-qemu.sh
```

The script will guide you through:
1. Installing dependencies
2. Cloning QEMU source
3. Configuring with HVF support
4. Building (15-30 minutes)
5. Installing

## 📋 Manual Steps

### 1. Install Dependencies

```bash
brew install \
    git make python3 pkg-config meson ninja \
    glib pixman libslirp capstone dtc vde \
    jpeg-turbo libpng gnutls nettle lzo snappy zstd \
    spice-protocol
```

### 2. Clone QEMU

```bash
mkdir -p ~/qemu-build
cd ~/qemu-build
git clone https://gitlab.com/qemu-project/qemu.git
cd qemu
git checkout v9.2.0  # or use master for latest
```

### 3. Configure Build

```bash
mkdir build
cd build

../configure \
    --prefix=/opt/homebrew \
    --enable-hvf \
    --enable-cocoa \
    --enable-virtfs \
    --enable-slirp=system \
    --enable-capstone=system \
    --enable-dtc=system \
    --python=python3
```

**For Intel Macs**, use:
```bash
--prefix=/usr/local
```

### 4. Build

```bash
make -j$(sysctl -n hw.ncpu)
```

This uses all CPU cores. Takes 15-30 minutes.

### 5. Install

```bash
sudo make install
```

### 6. Verify HVF Support

```bash
qemu-system-x86_64 -accel help
```

You should see `hvf` in the list!

## 🎯 Build Options Explained

| Option | Description |
|--------|-------------|
| `--enable-hvf` | **Required** - Enables HVF acceleration |
| `--enable-cocoa` | macOS native display backend |
| `--enable-virtfs` | Shared folder support (9p) |
| `--enable-slirp=system` | Use system libslirp |
| `--prefix=/opt/homebrew` | Install location (ARM Mac) |
| `--prefix=/usr/local` | Install location (Intel Mac) |

## 🔧 Troubleshooting

### Build Fails with "missing subprojects"

```bash
cd ~/qemu-build/qemu
meson subprojects download
```

### HVF Not Available After Build

1. Check macOS version (HVF requires macOS 10.13+)
2. Verify hardware support:
   ```bash
   sysctl kern.hv_support
   ```
   Should output `1`

3. Check QEMU was built with HVF:
   ```bash
   qemu-system-x86_64 -accel help
   ```

### Permission Errors

```bash
sudo chown -R $(whoami) /opt/homebrew  # ARM Mac
sudo chown -R $(whoami) /usr/local     # Intel Mac
```

### PATH Issues

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="/opt/homebrew/bin:$PATH"  # ARM Mac
export PATH="/usr/local/bin:$PATH"    # Intel Mac
```

## 📊 Performance Comparison

| Method | Speed | Setup Time |
|--------|-------|------------|
| **Manual Build (HVF)** | ⚡⚡⚡ **Fastest** | 30 min |
| Homebrew Stable | ⚡ Slow | 5 min |
| Homebrew HEAD | ⚡⚡ Fast | 60+ min (often fails) |

## ✅ After Installation

Test your new QEMU:

```bash
cd qemu
make install  # Should now show HVF acceleration!
```

## 🗑️ Uninstall

```bash
cd ~/qemu-build/qemu/build
sudo make uninstall
```

Or manually:
```bash
sudo rm -rf /opt/homebrew/bin/qemu-*
sudo rm -rf /opt/homebrew/share/qemu
```

---

**Note**: Manual builds give you full control and guaranteed HVF support, but take longer than Homebrew. The automated script handles most of the complexity for you!
