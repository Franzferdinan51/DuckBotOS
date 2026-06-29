#!/bin/bash
# DuckBotOS — UTM VM Setup Guide
# Steps to create the Ubuntu 24.04 build VM in UTM
# After creating the VM, run: ./build-iso.sh

set -e

ISO_PATH="/tmp/ubuntu-24.04.4-live-server-amd64.iso"
VM_NAME="DuckBotOS-Build"
EXPECTED_SIZE="3.2G"

echo "🦆 DuckBotOS UTM Build VM — Setup Guide"
echo "========================================"
echo ""

# Step 0: Verify ISO
echo "📀 Step 0: Verify ISO"
if [ ! -f "$ISO_PATH" ]; then
    echo "   ❌ ISO not found at $ISO_PATH"
    echo "   Run this first:"
    echo "   curl -L -o $ISO_PATH https://releases.ubuntu.com/noble/ubuntu-24.04.4-live-server-amd64.iso"
    exit 1
fi
ISO_SIZE=$(du -h "$ISO_PATH" | cut -f1)
echo "   ✅ ISO found: $ISO_SIZE"
echo ""

# Step 1: Create VM in UTM GUI
echo "🖥️  Step 1: Create VM in UTM (GUI)"
echo "   1. Open UTM.app"
echo "   2. Click the + (New) button in the toolbar"
echo "   3. Select 'Virtualize'"
echo "   4. Select 'Linux'"
echo "   5. Under 'Boot ISO Image', click 'Browse' → select:"
echo "      $ISO_PATH"
echo "   6. Hardware settings:"
echo "      - CPUs: 4 (or however many you can spare)"
echo "      - Memory: 8192 MB (8 GB)"
echo "      - EFI Boot: ✓ (keep checked)"
echo "      - Headless mode: ✓ (uncheck — we want display)"
echo "   7. Storage settings:"
echo "      - Disk Size: 64 GB (minimum)"
echo "      - Type: QCOW2 ( Growing, pre-allocated)"
echo "   8. Shared Directory: Optional, skip for now"
echo "   9. Click 'Save' → name it: $VM_NAME"
echo ""
echo "   ⏸️  STOP HERE — don't start the VM yet!"
echo ""

# Step 2: Configure VM for Ubuntu Server install
echo "⚙️  Step 2: Fine-tune VM settings"
echo "   1. Right-click the VM → 'Edit'"
echo "   2. Under 'Display', set:"
echo "      - Resolution: 1920x1080 (or your screen)"
echo "      - Fullscreen: optional"
echo "   3. Under 'Network':"
echo "      - Mode: Emulated VLAN (NAT)"
echo "      - MAC: will auto-generate (keep)"
echo "   4. Under 'USB':"
echo "      - Add a USB tablet for better mouse support"
echo "   5. Click 'Save'"
echo ""

# Step 3: Start and install
echo "🚀 Step 3: Install Ubuntu Server"
echo "   Option A — GUI install (recommended):"
echo "   1. Double-click the VM to start it"
echo "   2. Select 'Try or Install Ubuntu Server'"
echo "   3. Walk through the Ubuntu Server installer:"
echo "      - Language: English"
echo "      - Install type: Ubuntu Server (minimized)"
echo "      - Network: DHCP (NAT) — auto"
echo "      - Storage: use entire disk (LVM optional)"
echo "      - Profile:"
echo "        - Your name: duckets"
echo "        - hostname: duckbotos-build"
echo "        - username: duckets"
echo "        - password: (set one)"
echo "      - SSH: ✓ Install OpenSSH server"
echo "      - Snaps: none needed"
echo "   4. Wait for install (~5-10 min)"
echo "   5. VM auto-reboots → login with duckets + password"
echo ""
echo "   Option B — UTM CLI start (after GUI creation):"
echo "   utmctl start '$VM_NAME'"
echo "   utmctl attach '$VM_NAME'  # for serial console"
echo ""

# Step 4: Post-install setup
echo "🔧 Step 4: Post-install (run inside the VM after login)"
echo "   # Update packages"
echo "   sudo apt update && sudo apt upgrade -y"
echo ""
echo "   # Install build deps"
echo "   sudo apt install -y \\"
echo "     live-build debootstrap squashfs-tools xorriso \\"
echo "     isolinux syslinux-efi grub-pc-bin grub-efi-amd64-bin \\"
echo "     mtools dosfstools dpkg-dev devscripts debhelper \\"
echo "     fakeroot gnupg syft cyclonedx-cli python3-pip \\"
echo "     wget curl git"
echo ""
echo "   # Clone the fork"
echo "   git clone https://github.com/Franzferdinan51/cx-distro \\"
echo "     -b duckbotos /tmp/cx-distro"
echo ""
echo "   # Build!"
echo "   cd /tmp/cx-distro"
echo "   make clean  # fresh start"
echo "   make deps"
echo "   make iso   # ~30-60 min build"
echo ""

# Step 5: Get the ISO out
echo "📦 Step 5: Get the built ISO"
echo "   # The ISO lands at: output/duckbotos-*.iso"
echo "   # Copy it to the Mac:"
echo "   IP=\$(utmctl ip-address '$VM_NAME' | grep '192.168' | head -1 | awk '{print \$2}')"
echo "   scp duckets@\$IP:/tmp/cx-distro/output/*.iso ./"
echo ""
echo "   # Or use UTM file sharing:"
echo "   utmctl file '$VM_NAME' get /tmp/cx-distro/output/*.iso ./"
echo ""

echo "========================================"
echo "✅ Setup guide complete!"
echo "   ISO is downloading: $ISO_PATH"
echo "   Create the VM in UTM GUI, install Ubuntu, then run the build."
echo "   ~3.5 hrs from VM-ready to first bootable DuckBotOS ISO."