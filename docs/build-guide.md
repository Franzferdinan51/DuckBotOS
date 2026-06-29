# DuckBotOS — Build Guide

> Step-by-step: fork the repo, set up the Linux build VM, create packages, and build your first DuckBotOS ISO.
> Status: Draft v0.1 — 2026-06-29

---

## Prerequisites

- macOS host (this guide)
- ~50 GB free disk space for the VM + build artifacts
- GitHub account with fork permissions
- USB drive (8 GB+) or VM hypervisor for ISO testing

---

## Phase 1: Fork the Repository

### 1.1 Fork cxlinux-ai/cx-distro

```bash
# On GitHub web UI:
# 1. Go to https://github.com/cxlinux-ai/cx-distro
# 2. Click "Fork" → your account
# 3. Rename fork: Franzferdinan51/duckbotos-distro

# Or use GitHub CLI:
gh repo fork cxlinux-ai/cx-distro --clone --org Franzferdinan51
cd ~/path/to/duckbotos-distro
```

### 1.2 Rename All References

```bash
# Clone the fork
git clone https://github.com/Franzferdinan51/duckbotos-distro
cd duckbotos-distro

# Replace all cx-linux/cxlinux/cxlinux-ai references with duckbotos
find . -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.yml" -o -name "Makefile" -o -name "*.json" \) \
  -exec sed -i '' \
    -e 's/cx-linux/DuckBotOS/g' \
    -e 's/cxlinux/DuckBotOS/g' \
    -e 's/cxlinux-ai/duckbotos/g' \
    -e 's/CX Linux/DuckBotOS/g' \
    -e 's/cx-ai/duckbotos/g' \
    -e 's/CX-LINUX/DUCKBOTOS/g' \
    -e 's/CX_/DUCKBOTOS_/g' \
    {} \;

# Rename package directories
mv packages/cx-archive-keyring packages/duckbotos-keyring
mv packages/cx-core            packages/duckbotos-base
mv packages/cx-full            packages/duckbotos-meta

# Push
git add -A
git commit -m "Rename cxlinux to DuckBotOS"
git push origin main
```

### 1.3 Change Base OS: Debian Trixie → Ubuntu Noble

In `Makefile`, find the live-build configuration:

```bash
# In Makefile, change distribution:
LBDISTRO = noble          # was: trixie (Debian 13)

# In iso/live-build/config/package-lists/, update debootstrap script:
# Replace "trixie" with "noble" in any config files
grep -r "trixie" iso/ config/ --include="*.sh" --include="*.txt"
```

---

## Phase 2: Set Up the Linux Build VM

live-build requires a **Linux host** — it cannot run on macOS.

### Option A: UTM (Recommended for macOS)

```bash
# Install UTM (if not already installed)
brew install --cask utm

# Download Ubuntu 24.04 LTS Server ISO
# https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso

# Create VM in UTM:
#   CPUs: 4
#   RAM: 8 GB
#   Disk: 100 GB (expanding)
#   OS: Ubuntu 24.04 LTS (select the ISO as boot image)

# Install Ubuntu Server (not Desktop — lighter weight)
# During install:
#   - Enable SSH server
#   - Create user: builder / builder
#   - Partition: default LVM
```

### Option B: Vagrant + VirtualBox

```bash
brew install --cask virtualbox vagrant
vagrant init ubuntu/noble64
vagrant up
vagrant ssh
```

### 2.1 Install Build Dependencies (in VM)

```bash
sudo apt-get update
sudo apt-get install -y \
    live-build \
    debootstrap \
    squashfs-tools \
    xorriso \
    isolinux \
    syslinux-efi \
    grub-pc-bin \
    grub-efi-amd64-bin \
    mtools \
    dosfstools \
    dpkg-dev \
    devscripts \
    debhelper \
    fakeroot \
    gnupg \
    curl \
    wget \
    git

# Also install for SBOM generation (optional but recommended)
sudo apt-get install -y \
    syft \
    cyclonedx-cli

# Verify live-build is installed
lb --version
```

---

## Phase 3: Clone and Prepare the Fork

```bash
# In the Linux VM:
git clone https://github.com/Franzferdinan51/duckbotos-distro
cd duckbotos-distro

# Install dependencies
sudo make deps

# Initialize live-build config (generates iso/live-build/)
sudo lb config

# Verify config was generated
ls iso/live-build/
# Should show: auto/  config/  local/
```

---

## Phase 4: Create the DuckBotOS Packages

The cx-distro packages are `cx-archive-keyring`, `cx-core`, `cx-full`. We replace these with DuckBotOS equivalents.

### 4.1 Package: `duckbotos-keyring` (GPG Keyring)

**Purpose:** Installs the GPG public key for the DuckBotOS APT repository.

```bash
mkdir -p packages/duckbotos-keyring/debian
cd packages/duckbotos-keyring

cat > debian/control << 'EOF'
Source: duckbotos-keyring
Section: admin
Priority: optional
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: all
Description: GPG keyring for DuckBotOS APT repository
 Installs the GPG public key used to verify packages from the
 DuckBotOS embedded APT repository.
EOF

cat > debian/rules << 'EOF'
#!/usr/bin/make -f
%:
	dh $@
override_dh_systemd_enable:
	# No systemd services for keyring package
EOF

chmod +x debian/rules
cd ../..
```

**Build:**
```bash
dpkg-buildpackage -us -uc -b -d
# Output: duckbotos-keyring_*.deb
```

### 4.2 Package: `duckbotos-base` (Core OS)

**Purpose:** Core system packages — Weston, NetworkManager, systemd, basic utilities.

```bash
mkdir -p packages/duckbotos-base/debian
cd packages/duckbotos-base

cat > debian/control << 'EOF'
Source: duckbotos-base
Section: base
Priority: optional
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Depends: ${misc:Depends},
    weston,
    network-manager,
    systemd,
    udisks2,
    eject,
    curl,
    wget,
    gnupg,
    apt-transport-https,
    ca-certificates,
    python3,
    python3-yaml,
    dbus-x11
Description: DuckBotOS base system packages
 Installs the core system packages for DuckBotOS:
 Weston compositor, NetworkManager, D-Bus, and essential utilities.
EOF

cat > debian/rules << 'EOF'
#!/usr/bin/make -f
%:
	dh $@
override_dh_systemd_enable:
	dh_systemd_enable --no-enable  # don't enable services at package install time
override_dh_systemd_start:
	dh_systemd_start --no-start
EOF

chmod +x debian/rules
cd ../..
```

### 4.3 Package: `duckbotos-lm-studio`

**Purpose:** Install LM Studio headless (llmster) + systemd service.

```bash
mkdir -p packages/duckbotos-lm-studio/debian
mkdir -p packages/duckbotos-lm-studio/usr/lib/systemd/system

cd packages/duckbotos-lm-studio

cat > debian/control << 'EOF'
Source: duckbotos-lm-studio
Section: ai
Priority: optional
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Depends: ${misc:Depends}, curl, ca-certificates
Description: LM Studio headless inference server (llmster)
 Installs llmster daemon + lms CLI for local LLM inference.
 Provides OpenAI-compatible REST API on port 1234.
 Homepage: https://lmstudio.ai
EOF

cat > debian/postinst << 'POSTINST'
#!/bin/bash
set -e
# Install LM Studio headless (llmster)
curl -fsSL https://lmstudio.ai/install.sh | bash
# Enable user service (per-user, not system-wide)
systemctl --user enable lmstudio.service || true
POSTINST

cat > debian/prerm << 'PRERM'
#!/bin/bash
set -e
systemctl --user stop lmstudio.service || true
systemctl --user disable lmstudio.service || true
PRERM

cat > usr/lib/systemd/user/lmstudio.service << 'SERVICE'
[Unit]
Description=LM Studio llmster daemon
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=%h/.local/bin/lms daemon up
Restart=always
RestartSec=10
Environment=LMSTUDIO_API_KEY=
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
SERVICE

chmod +x debian/postinst debian/prerm
cd ../..
```

### 4.4 Package: `duckbotos-browseros`

**Purpose:** Install BrowserOS from .deb + set as default browser + MCP service.

```bash
mkdir -p packages/duckbotos-browseros/debian
mkdir -p packages/duckbotos-browseros/usr/lib/systemd/system
mkdir -p packages/duckbotos-browseros/usr/share/applications
mkdir -p packages/duckbotos-browseros/usr/bin

cd packages/duckbotos-browseros

cat > debian/control << 'EOF'
Source: duckbotos-browseros
Section: web
Priority: optional
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Depends: ${misc:Depends}, curl, libnss3, libatk1.0-0, libatk-bridge2.0-0, libc6 (>= 2.34)
Description: BrowserOS — AI-native Chromium browser
 BrowserOS is an open-source Chromium fork with native AI agent support.
 Default browser for DuckBotOS kiosk. AGPL-3.0 licensed.
 Homepage: https://browseros.ai
EOF

cat > debian/postinst << 'POSTINST'
#!/bin/bash
set -e
# Download and install BrowserOS .deb
curl -fsSL https://cdn.browseros.com/download/BrowserOS.deb \
    -o /tmp/browseros.deb
dpkg -i /tmp/browseros.deb || apt-get install -f -y
rm /tmp/browseros.deb

# Set BrowserOS as default browser via update-alternatives
update-alternatives --install /usr/bin/x-www-browser browseros /opt/browseros/browseros 200 || true
update-alternatives --install /usr/bin/gnome-www-browser browseros /opt/browseros/browseros 200 || true

# Set as default XDG browser
mkdir -p /etc/profile.d/
echo 'export BROWSER=/opt/browseros/browseros' >> /etc/profile.d/duckbotos-browser.sh
echo 'export XDG_CURRENT_DESKTOP=DuckBotOS' >> /etc/profile.d/duckbotos-browser.sh

# Enable BrowserOS MCP service
systemctl --user enable browseros-mcp.service || true
POSTINST

cat > usr/lib/systemd/user/browseros-mcp.service << 'SERVICE'
[Unit]
Description=BrowserOS MCP Server
After=network-online.target
PartOf=browseros.service

[Service]
ExecStart=/opt/browseros/bin/browseros-cli server start --port 9003
Restart=always
RestartSec=10
Environment=BROWSEROS_CLI_PORT=9003

[Install]
WantedBy=default.target
SERVICE

chmod +x debian/postinst
cd ../..
```

### 4.5 Package: `duckbotos-hermes`

**Purpose:** Install Hermes agent + gateway service.

```bash
mkdir -p packages/duckbotos-hermes/debian
mkdir -p packages/duckbotos-hermes/usr/lib/hermes
mkdir -p packages/duckbotos-hermes/usr/lib/systemd/system
mkdir -p packages/duckbotos-hermes/usr/local/bin

cd packages/duckbotos-hermes

cat > debian/control << 'EOF'
Source: duckbotos-hermes
Section: ai
Priority: optional
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Depends: ${misc:Depends}, duckbotos-base, python3, pipx
Description: Hermes Agent for DuckBotOS
 NousResearch Hermes agent — AI assistant with tool use and memory.
 Provides the Hermes Web Dashboard on port 9119.
 Homepage: https://github.com/nousresearch/hermes-agent
EOF

cat > debian/postinst << 'POSTINST'
#!/bin/bash
set -e
# Install Hermes via official installer
curl -fsSL https://raw.githubusercontent.com/nousresearch/hermes-agent/main/install.sh | bash

# Create hermes user if not exists
id hermes >/dev/null 2>&1 || useradd -m -s /bin/bash hermes

# Set up hermes workspace
mkdir -p ~hermes/.hermes/workspace
chown -R hermes:hermes ~hermes/.hermes

# Enable service
systemctl enable hermes-gateway.service
POSTINST

cat > usr/lib/systemd/system/hermes-gateway.service << 'SERVICE'
[Unit]
Description=Hermes Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=hermes
Group=hermes
ExecStart=/usr/local/bin/hermes gateway start --port 9119
Restart=always
RestartSec=10
Environment="HERMES_CONFIG=/etc/hermes/config.yaml"
WorkingDirectory=/var/lib/hermes

[Install]
WantedBy=multi-user.target
SERVICE

chmod +x debian/postinst
cd ../..
```

### 4.6 Package: `duckbotos-computer-use`

**Purpose:** Install `computer-use-linux` MCP server for desktop control.

```bash
mkdir -p packages/duckbotos-computer-use/debian
mkdir -p packages/duckbotos-computer-use/usr/local/bin
mkdir -p packages/duckbotos-computer-use/usr/lib/systemd/system

cd packages/duckbotos-computer-use

cat > debian/control << 'EOF'
Source: duckbotos-computer-use
Section: ai
Priority: optional
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Depends: ${misc:Depends}, libatspi2.0-0, libxtst6, python3
Description: computer-use-linux — AT-SPI2 + Wayland portal MCP
 Rust MCP server exposing AT-SPI2 accessibility + Wayland portal
 for AI agent desktop control (click, type, screenshot).
 Homepage: https://github.com/agent-sh/computer-use-linux
EOF

cat > usr/lib/systemd/system/computer-use-linux.service << 'SERVICE'
[Unit]
Description=computer-use-linux MCP server
After=hermes-gateway.service openclaw-gateway.service
Wants=hermes-gateway.service openclaw-gateway.service

[Service]
Type=simple
ExecStart=/usr/local/bin/computer-use-linux --port 9600
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

chmod +x debian/postinst
cd ../..
```

---

## Phase 5: Build the ISO

### 5.1 Add Packages to live-build Package Lists

```bash
# Create package list for Hermes ISO variant
cat > iso/live-build/config/package-lists/duckbotos-hermes.list.chroot << 'EOF'
# DuckBotOS Hermes-only ISO package list
# Core
weston
network-manager
dbus-x11
python3
python3-yaml
curl
wget
gnupg
apt-transport-https
ca-certificates

# DuckBotOS packages
duckbotos-keyring
duckbotos-base
duckbotos-lm-studio
duckbotos-browseros
duckbotos-computer-use
duckbotos-hermes

# Kiosk
xwayland
EOF

# Create package list for OpenClaw ISO variant
cat > iso/live-build/config/package-lists/duckbotos-openclaw.list.chroot << 'EOF'
# DuckBotOS OpenClaw-only ISO package list
# (similar structure, duckbotos-openclaw package instead of duckbotos-hermes)
EOF

# Create package list for Both ISO variant
cat > iso/live-build/config/package-lists/duckbotos-both.list.chroot << 'EOF'
# DuckBotOS Both-mode ISO package list
# Includes both agent packages + GDM
gdm3
ubuntu-desktop-minimal
duckbotos-hermes
duckbotos-openclaw
EOF
```

### 5.2 Configure ISO Branding

```bash
# Set ISO label and hostname
cat > iso/live-build/config/bootloaders/isolinux/live.cfg << 'EOF'
include live.cfg
label duckbotos-hermes
    menu label ^DuckBotOS (Hermes)
    linux /live/vmlinuz
    initrd /live/initrd.img
    append boot=casper iso-scan/filename=${ISO} hostname=duckbotos-hermes quiet splash
EOF

# Update Plymouth theme (boot splash)
mkdir -p iso/live-build/config/includes.chroot/usr/share/plymouth/duckbotos/
cp branding/duckbotos-splash.png iso/live-build/config/includes.chroot/usr/share/plymouth/duckbotos/
```

### 5.3 Build the ISO

```bash
# In the Linux VM, from the duckbotos-distro directory:

# Clean previous builds
sudo lb clean --all

# Reconfigure (apply all our changes)
sudo lb config

# Build the ISO (takes 30-60 minutes depending on download speed)
sudo lb build

# Output is in:
ls -lh *.iso
```

### 5.4 Build All Three Variants

```bash
# Makefile targets (add to existing Makefile)
build-hermes:
	sudo lb clean --all
	sudo lb config --packages-lists duckbotos-hermes.list.chroot
	sudo lb build
	mv live-image-amd64.iso duckbotos-hermes-x86_64.iso

build-openclaw:
	sudo lb clean --all
	sudo lb config --packages-lists duckbotos-openclaw.list.chroot
	sudo lb build
	mv live-image-amd64.iso duckbotos-openclaw-x86_64.iso

build-both:
	sudo lb clean --all
	sudo lb config --packages-lists duckbotos-both.list.chroot
	sudo lb build
	mv live-image-amd64.iso duckbotos-both-x86_64.iso
```

---

## Phase 6: Verify the ISO

### 6.1 Mount and Inspect

```bash
# Mount the ISO (read-only)
sudo mount -o loop duckbotos-hermes-x86_64.iso /mnt
ls /mnt/          # Should see: EFI, live, .disk
ls /mnt/live/     # Should see: filesystem.squashfs, vmlinuz, initrd.img
sudo umount /mnt
```

### 6.2 Boot in VM

```bash
# In UTM or VirtualBox:
# 1. Create new VM from the .iso file
# 2. Start the VM
# 3. Verify it boots to DuckBotOS splash screen
# 4. Verify Weston compositor starts
# 5. Verify Chromium kiosk launches with Hermes/OpenClaw URL
```

### 6.3 Automated Verification Script

```bash
# From cx-distro/tests/verify-iso.sh — adapt for DuckBotOS:
cat > tests/verify-iso.sh << 'EOF'
#!/bin/bash
set -e
ISO="$1"

echo "=== DuckBotOS ISO Verification ==="
echo "ISO: $ISO"

# 1. Check ISO exists and is > 1GB
SIZE=$(stat -f%z "$ISO")
if [ "$SIZE" -lt 1000000000 ]; then
    echo "FAIL: ISO too small ($SIZE bytes)"
    exit 1
fi
echo "✓ ISO size OK: $(numfmt --to=iec $SIZE)"

# 2. Check it's a valid ISO
file "$ISO" | grep -q "ISO 9660" && echo "✓ Valid ISO format" || { echo "FAIL: Not an ISO"; exit 1; }

# 3. Mount and check contents
TMPDIR=$(mktemp -d)
sudo mount -o loop "$ISO" "$TMPDIR"
trap "sudo umount $TMPDIR; rmdir $TMPDIR" EXIT

# 4. Check for DuckBotOS-specific files
grep -q "duckbotos" "$TMPDIR/.disk/info" && echo "✓ DuckBotOS disk info found"
ls "$TMPDIR/live/" | grep -q filesystem.squashfs && echo "✓ SquashFS found"
ls "$TMPDIR/live/" | grep -q vmlinuz && echo "✓ Kernel found"

echo "=== All checks passed ==="
EOF
chmod +x tests/verify-iso.sh
```

---

## Phase 7: Publish

```bash
# Tag the release
git tag -a v0.1.0 -m "DuckBotOS v0.1.0 — First bootable ISO"
git push origin v0.1.0

# Upload ISO to GitHub Releases
gh release create v0.1.0 \
    --title "DuckBotOS v0.1.0" \
    --notes "First DuckBotOS ISO release. See docs/build-guide.md for build instructions." \
    duckbotos-hermes-x86_64.iso \
    duckbotos-openclaw-x86_64.iso \
    duckbotos-both-x86_64.iso

# Generate checksums
sha256sum duckbotos-*.iso > duckbotos-SHA256SUMS.txt
```

---

## Quick Reference: Build Commands

```bash
# Full build (one variant)
sudo lb clean --all && sudo lb config && sudo lb build

# Quick rebuild (skip clean)
sudo lb build

# Build specific variant
sudo lb config --packages-lists duckbotos-hermes.list.chroot
sudo lb build

# Check package status in chroot
sudo chroot binary /bin/bash -c "dpkg -l | grep duckbotos"

# Rebuild single package
dpkg-buildpackage -us -uc -b -d
```

---

## Troubleshooting

### "lb: command not found"
```bash
sudo apt-get install live-build
```

### "E: No such method: hook"
```bash
# Your live-build version is old. Update:
sudo apt-get update && sudo apt-get install live-build
```

### "debootstrap failed"
```bash
# Check internet connectivity in VM
ping -c 3 archive.ubuntu.com
# If it fails, configure DNS: echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### "out of memory during build"
```bash
# Increase VM RAM to 8GB+ and swap:
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

*Build Guide v0.1 — 2026-06-29*
