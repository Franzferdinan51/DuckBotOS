# DuckBotOS Troubleshooting Guide

This guide covers common problems encountered running and maintaining DuckBotOS. Each section targets a specific subsystem. Commands assume you are root or have sudo access.

---

## 1. Boot Problems

### Live USB Won't Boot

**Symptoms:** System skips USB in boot order, or shows a black screen after selecting the USB device.

**Check UEFI vs BIOS (CSM):**
```bash
# In your firmware (BIOS/UEFI setup):
# - Disable "Secure Boot" entirely, or sign the DuckBotOS kernel
# - If booting in BIOS mode, disable CSM (Compatibility Support Module) only if
#   you need pure UEFI. Many systems boot USB in BIOS mode by default.
#   Try both boot modes.
```

**USB 3.0 port issues:** Some USB 3.0 controllers don't hand off correctly to BIOS boot. Try a USB 2.0 port.

**ISO write method:**
```bash
# WRONG - this skips boot sector
cp Downloads/duckbotos.iso /dev/sdX

# CORRECT - raw write preserves boot sector
sudo dd if=Downloads/duckbotos.iso of=/dev/sdX bs=4M status=progress oflag=sync
sync
```

Verify the write:
```bash
sudo fdisk -l /dev/sdX
# Should show EFI System partition and Linux partition
```

---

### Plymouth Splash Stuck

**Symptoms:** Boot freezes at the purple/black splash screen with no cursor.

**Check kernel cmdline:**
```bash
cat /proc/cmdline
# Look for 'splash' and 'quiet'
# Remove 'splash quiet' to see boot messages
```

**Diagnose with plymouth:**
```bash
journalctl -b -u plymouth-start
# Look for " Plymouth watchdog timeout" or splash theme missing errors
```

**Fix:** Edit `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX_DEFAULT="splash"
```
Then run:
```bash
sudo update-grub
sudo reboot
```

If still stuck, disable splash to debug:
```
GRUB_CMDLINE_LINUX_DEFAULT=""
```

---

### Rootfs Not Found (Live Mode)

**Symptoms:** Boot drops to initramfs prompt with "Gave up waiting for root file system".

**Verify boot params:**
```bash
cat /proc/cmdline
# Must contain: boot=casper
# Example: boot=casper username=duckbotos union_size=10G
```

**Check block devices:**
```bash
sudo lsblk
# or
sudo fdisk -l
```
Identify your USB/ssd drives. The rootfs should be on a device like `/dev/sda2`.

**Reseed casper:**
```bash
sudo casper-generate-seed
sudo update-grub
sudo reboot
```

**If installing:** Ensure you unpacked the squashfs correctly:
```bash
sudo unsquashfs -d /target /lib/live/mount/persistence/squashfs/*.squashfs
```

---

### Persistence Not Working

**Symptoms:** System boots fresh every time despite creating a persistence partition.

**Check persistence partition exists:**
```bash
sudo fdisk -l /dev/sda
# Look for a partition with type "Linux" (id 83) labeled "persistence"
```

**Check persistence label:**
```bash
sudo e2label /dev/sda3
# Must be: persistence
```

**Check union_size on cmdline:**
```bash
cat /proc/cmdline | grep union_size
# If missing or too small, edit grub:
# Add: union_size=10G (or whatever size you need)
```

**Check home persistence path:**
```bash
# For home persistence, must have:
# persistent-path=/cow
# or explicitly:
# persistence-label=home
```

**After modifying, rebuild initramfs:**
```bash
sudo update-initramfs -u
sudo reboot
```

**Verify persistence is mounted:**
```bash
df -h
# Should show /cow or /media/cow overlay
mount | grep cow
```

---

### GDM Not Starting

**Symptoms:** System boots to CLI, no login screen appears.

**Check GDM status:**
```bash
systemctl status gdm
# or for GDM3:
systemctl status gdm3
```

**Check logs:**
```bash
journalctl -b -u gdm
# or
cat /var/log/gdm/*/*.log
```

**Common cause: GPU driver mismatch**

If you have an NVIDIA GPU and seeing a black screen from GDM:
```bash
# Switch to Wayland in GDM config
sudo nano /etc/gdm3/custom.conf
```
Change/add:
```
WaylandEnable=true
```
Or if Wayland has issues too, force Xorg:
```
WaylandEnable=false
```

**If Xorg is broken:**
```bash
# Check Xorg logs
cat /var/log/Xorg.0.log
# Look for (EE) errors

# Reconfigure GDM
sudo dpkg-reconfigure gdm3
```

**Start GDM manually:**
```bash
sudo systemctl start gdm3
```

---

## 2. Weston / Kiosk Problems

### Weston Crashes on Startup

**Check the service:**
```bash
systemctl status duckbotos-weston.service
journalctl -u duckbotos-weston.service -n 100
```

**Check weston.ini syntax:**
```bash
nano ~/.config/weston.ini
# or
nano /etc/xdg/weston/weston.ini
```

**Common weston.ini errors:**
```ini
[core]
# Missing or wrong seat section
# Extra commas in key=value lists

[output]
name=HDMI-A-1
# Mode must match actual connector name
# Run: weston-info to see actual names
```

**Verify with weston-info:**
```bash
sudo -u duckbotos weston-info
# If this fails, Weston itself is broken
```

**Check for missing EGL:**
```bash
dpkg -l | grep -i egl
# Should show libegl1, libegl1-mesa-dev
apt install libegl1-mesa-dev
```

**View Weston log:**
```bash
cat /var/log/weston.log
# Check for Segmentation fault, failed to create compositor, etc.
```

**Restart Weston:**
```bash
systemctl restart duckbotos-weston.service
```

---

### Chromium Not Launching in Kiosk

**Test kiosk mode manually:**
```bash
# As the kiosk user:
export WAYLAND_DISPLAY=wayland-0
chromium-browser --kiosk --app-mode=kiosk https://duckbotos.local
```

**Check Wayland port:**
```bash
echo $WAYLAND_DISPLAY
# Should be: wayland-0
# If empty:
export WAYLAND_DISPLAY=wayland-0
```

**Common kiosk flags:**
```bash
chromium-browser \
  --kiosk \
  --app-mode=kiosk \
  --no-first-run \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-dev-shm-usage \
  --ozone-platform=wayland
```

**Wayland portal issues (file picker crashes):**
```bash
# Set XDG desktop to kiosk
export XDG_CURRENT_DESKTOP=KOZMO
# Kill and restart the kiosk session
```

**Verify Chromium version supports Wayland:**
```bash
chromium-browser --version
# Very old versions don't support ozone-wayland
```

---

### Black Screen After Login

**Check kiosk service:**
```bash
systemctl status duckbotos-kiosk.service
journalctl -u duckbotos-kiosk -n 50
```

**Check Weston started:**
```bash
ps aux | grep weston
# Should show weston compositor running
```

**Check XDG_RUNTIME_DIR:**
```bash
echo $XDG_RUNTIME_DIR
# Should be: /run/user/1000 (or the kiosk user's UID)
# If missing:
export XDG_RUNTIME_DIR=/run/user/$(id -u)
```

**Test Weston directly:**
```bash
sudo -u kiosk weston-info
# If this errors, compositor is not running
```

**Restart full session:**
```bash
sudo systemctl restart duckbotos-weston.service
sudo systemctl restart duckbotos-kiosk.service
```

---

### Touch Input Not Working

**Install libinput:**
```bash
sudo apt install libinput-tools xinput
```

**List input devices:**
```bash
xinput list
weston-input-device-info
```

**Calibrate touch:**
```bash
weston-touch-calibrator
# Follow on-screen prompts
```

**Check udev rules:**
```bash
ls /lib/udev/rules.d/
# Should have touch device rules

# If touch not detected:
sudo udevadm trigger
sudo udevadm control --reload-rules
```

**Debug with evtest:**
```bash
sudo apt install evtest
sudo evtest
# Select your touch device
# Tap screen — events should appear
```

---

## 3. Hermes Agent Problems

### Hermes Not Responding

**Check service:**
```bash
systemctl status hermes-agent.service
journalctl -u hermes-agent.service -n 100
```

**Check for process:**
```bash
ps aux | grep hermes
```

**Check API keys loaded:**
```bash
sudo -u hermesos env | grep -i api
sudo -u hermesos cat /var/lib/duckbotos/creds/minimax.key
# File must exist and be readable only by hermesos user
chmod 600 /var/lib/duckbotos/creds/minimax.key
chown hermesos:hermesos /var/lib/duckbotos/creds/minimax.key
```

**Test connectivity:**
```bash
curl -s --max-time 10 https://api.minimax.chat/health
# or
curl -s --max-time 10 https://api.x.ai/health
```

**Check Hermes CLI:**
```bash
sudo -u hermesos hermes-cli doctor
sudo -u hermesos hermes-cli status
```

**Restart Hermes:**
```bash
sudo systemctl restart hermes-agent.service
```

**Debug mode — add to systemd unit:**
```bash
# Edit /etc/systemd/system/hermes-agent.service.d/override.conf
[Service]
Environment=DEBUG=1
```
Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart hermes-agent.service
journalctl -u hermes-agent.service -f
```

---

### Hermes Tools Not Executing

**Check tool permissions:**
```bash
# Hermes runs as hermesos user
sudo -u hermesos hermes-cli tools list
```

**Check AppArmor profile:**
```bash
cat /etc/apparmor.d/usr.bin.hermes-cli
# If profile is in enforce mode and blocking:
sudo aa-complain /usr/bin/hermes-cli
```

**Check if tools need root:**
```bash
# Some tools (shell, apt) require elevated permissions
# Hermes should use pkexec or sudo internally
# Check sudoers for hermesos:
sudo -l -u hermesos
```

**Tool execution logs:**
```bash
journalctl -u hermes-agent.service | grep -i tool
tail -f ~/.hermesos/logs/*.log
```

---

### Context Window Overflow

**Check session stats:**
```bash
sudo -u hermesos hermes-cli session stats
```

**Check for auto-summarization:**
```bash
tail -n 100 ~/.hermesos/logs/summarizer.log
```

**Increase context (if model supports it):**
```bash
# Edit hermes config:
nano ~/.hermesos/config/model.yaml
```
Set `context_window: 128000` or whatever your model supports.

**Clear old sessions:**
```bash
sudo -u hermesos hermes-cli session list
sudo -u hermesos hermes-cli session purge --older-than 7d
```

---

### Provider Auth Failures

**Locate credentials:**
```bash
ls /var/lib/duckbotos/creds/
```

**Check perms — must be 600:**
```bash
sudo -u hermesos ls -la /var/lib/duckbotos/creds/
# Should be: -rw------- 1 hermesos hermesos
```

**Read specific key:**
```bash
sudo -u hermesos cat /var/lib/duckbotos/creds/minimax.key
```

**Test with curl:**
```bash
# Test MiniMax auth
curl -H "Authorization: Bearer $(sudo -u hermesos cat /var/lib/duckbotos/creds/minimax.key)" \
  https://api.minimax.chat/v1/text/chatcompletion_v2
```

---

## 4. OpenClaw Agent Problems

### OpenClaw Gateway Down

**Check service:**
```bash
systemctl status openclaw-gateway.service
journalctl -u openclaw-gateway -n 100
```

**Check ports:**
```bash
ss -tlnp | grep -E '18797|18794'
# Should show listeners on both ports
```

**Gateway status:**
```bash
openclaw gateway status
openclaw status
```

**Restart:**
```bash
sudo systemctl restart openclaw-gateway.service
```

**If port is in use:**
```bash
sudo lsof -i :18797
sudo lsof -i :18794
# Kill the blocking process or change port in openclaw.json
```

**Debug:**
```bash
# Add debug to environment
sudo systemctl edit openclaw-gateway.service
```
Add:
```
[Service]
Environment=DEBUG=*
```
```bash
sudo systemctl daemon-reload
sudo systemctl restart openclaw-gateway.service
journalctl -u openclaw-gateway -f
```

---

### Telegram Bridge Not Working

**Check connected accounts:**
```bash
openclaw status
```

**Test Telegram bot:**
```bash
openclaw send "test ping" --provider telegram
```

**Check bot token:**
```bash
cat ~/.openclaw/config/openclaw.json | grep -i telegram
# Verify token is correct
```

**Reconnect Telegram:**
```bash
openclaw connect telegram --token YOUR_BOT_TOKEN
```

**Check Telegram logs:**
```bash
grep -i telegram ~/.openclaw/logs/*.log
```

---

### Memory Brain Not Loading

**Check brain service:**
```bash
systemctl status duckbot-brain.service
```

**Run brain doctor:**
```bash
cd ~/.duckbot-brain
python -m src.cli doctor
# or
python -m src.cli doctor --full
```

**Check ChromaDB:**
```bash
ls ~/.duckbot-brain/data/
# Should contain chroma.sqlite3 and other db files

# If corrupted:
python -m src.cli doctor --repair
```

**Check vector chunk count:**
```bash
python -c "
from brain import Brain
b = Brain()
print(b.stats())
"
```

**Restart brain:**
```bash
sudo systemctl restart duckbot-brain.service
```

**If brain is stuck/overloaded:**
```bash
# Check memory usage
free -h
# Reduce vector cache in config
```

---

## 5. LM Studio Problems

### LM Studio Server Not Starting

**Check service:**
```bash
systemctl status lmstudio.service
journalctl -u lmstudio -n 100
```

**Check binary:**
```bash
ls -la ~/.lmstudio/bin/lms
# Should exist and be executable
```

**Check port:**
```bash
ss -tlnp | grep 1234
# If something is on 1234, LM Studio can't bind
```

**Find what's using 1234:**
```bash
sudo lsof -i :1234
```

**Start manually to see errors:**
```bash
~/.lmstudio/bin/lms server
# Watch output for initialization errors
```

---

### Model Fails to Load

**GPU out of memory:**
```bash
# Reduce GPU offload when loading:
lms load <model> --gpu=max
# Or:
lms load <model> --gpu=half
# Or:
lms load <model> --no-gpu
```

**Check model file:**
```bash
ls -lh ~/.lmstudio/models/
# Verify file size — should be several GB for a 7B model
file ~/.lmstudio/models/<model>/model.gguf
```

**Redownload model:**
```bash
lms download <model>
```

**Check available VRAM:**
```bash
nvidia-smi
# or for AMD:
rocm-smi
```

---

### API Returns 503

**Model not loaded:**
```bash
# Check loaded models:
curl http://127.0.0.1:1234/v1/models

# Load a model via API:
curl -X POST http://127.0.0.1:1234/v1/models/{id}/load
```

**Enable JIT (loads model on first request):**
```bash
lms server start --jit
```

**Server overloaded — check running jobs:**
```bash
lms ps
# Shows all loaded models and context usage
```

---

### Hermes Can't Reach LM Studio

**Test connectivity:**
```bash
curl http://127.0.0.1:1234/v1/models
# If fails:
curl http://localhost:1234/v1/models
```

**Check firewall:**
```bash
sudo ufw status
# Allow localhost if blocked:
sudo ufw allow from 127.0.0.1
```

**LM Studio binds to localhost by default — verify:**
```bash
cat ~/.lmstudio/settings.json
```

**Change bind address if needed:**
```bash
nano ~/.lmstudio/settings.json
# Set "server": { "host": "0.0.0.0" } to accept from any interface
```

**Restart LM Studio:**
```bash
sudo systemctl restart lmstudio.service
```

---

## 6. BrowserOS Problems

### BrowserOS Won't Start

**Check service:**
```bash
systemctl status browseros.service
journalctl -u browseros -n 50
```

**Check environment:**
```bash
echo $XDG_CURRENT_DESKTOP
# Must be: KOZMO
```

**Use browseros-cli (trust `health` over `status`):**
```bash
browseros-cli health
browseros-cli status

# Restart:
browseros-cli restart
```

**Check the BrowserOS binary:**
```bash
ls /Applications/BrowserOS.app/Contents/MacOS/
# Should show BrowserOS executable
```

---

### BrowserOS MCP Not Connecting

**Check MCP port:**
```bash
curl http://localhost:9003/health
# Should return: {"status": "ok"}
```

**Check MCP server status:**
```bash
browseros-cli mcp status
browseros-cli mcp restart
```

**If port 9003 is not open:**
```bash
sudo ufw allow 9003
# Or check if BrowserOS is listening:
ss -tlnp | grep 9003
```

**Restart MCP:**
```bash
browseros-cli mcp stop
browseros-cli mcp start
```

---

### Can't Set as Default Browser

**Install browseros alternatives:**
```bash
sudo update-alternatives --install \
  /usr/bin/x-www-browser \
  browseros \
  /opt/browseros/browseros \
  200
```

**Set as default:**
```bash
sudo update-alternatives --set x-www-browser /opt/browseros/browseros
```

**Set XDG desktop:**
```bash
xdg-settings set default-web-browser browseros.desktop
xdg-mime default browseros.desktop x-scheme-handler/http
xdg-mime default browseros.desktop x-scheme-handler/https
```

**Verify:**
```bash
xdg-settings get default-web-browser
xdg-settings get default-url-scheme-handler http
```

---

## 7. Dual-Agent (Both Mode) Problems

### IPC Bus Not Working

**Check socket exists:**
```bash
ls -la /run/duckbotos/
# Should show: agent-bus.sock
```

**Check permissions:**
```bash
# Both agents must be in duckbotos group:
groups hermesos
groups openclaw
# Should include: duckbotos
```

**Add user to group:**
```bash
sudo usermod -aG duckbotos hermesos
sudo usermod -aG duckbotos openclaw
sudo systemctl restart hermes-agent.service
sudo systemctl restart openclaw-gateway.service
```

**Test D-Bus session bus:**
```bash
dbus-send --session \
  --dest=org.duckbotos.Bus \
  --print-reply \
  /org/duckbotos/Bus \
  org.duckbotos.Bus.Ping
```

**Restart IPC bus:**
```bash
sudo systemctl restart duckbotos-agent-bus.service
```

---

### GDM Session Picker Missing

**Check session files:**
```bash
ls /usr/share/xsessions/
# Should show: hermes.desktop, openclaw.desktop, duckbotos-hybrid.desktop
```

**If missing:**
```bash
sudo dpkg-reconfigure duckbotos-hybrid
# or reinstall:
sudo apt install --reinstall duckbotos-hybrid
```

**Check GDM theme — edit custom.conf:**
```bash
sudo nano /etc/gdm3/custom.conf
```
```
[daemon]
WaylandEnable=true
InitialSetupEnable=false
```

**Reset GDM:**
```bash
sudo systemctl restart gdm3
```

---

## 8. Live Build / ISO Problems

### `lb config` Fails

**Install deps:**
```bash
sudo apt install live-build debootstrap squashfs-tools xorriso grub-efi-amd64
```

**Check version:**
```bash
lb --version
# live-build 2024***
```

**Architecture mismatch:** You cannot build an ARM ISO on x86_64 or vice versa without QEMU.

**Clean and retry:**
```bash
lb clean --all
lb config
```

---

### `lb build` Runs Out of Space

**Check space:**
```bash
df -h
# Need ~20GB free
```

**Clean between builds:**
```bash
lb clean --all
```

**Check tmpfs:**
```bash
df /tmp
# If tmpfs is small, disable it for build:
lb config --tmpfs off
```

**Use more build space:**
```bash
# Move build to a bigger partition:
ln -sf /mnt/bigdrive/build build
lb build
```

---

### ISO Too Large (>4.7GB for single-layer DVD)

**Check size:**
```bash
du -sh binary/
```

**Remove non-essential packages:**
```bash
# In auto/config:
package-lists:
  - minimal
  # Remove: libreoffice, firefox, thunderbird, etc.
```

**Enable compression:**
```bash
lb config --binary-images iso
# Use gzip or xz compression on squashfs
```

**Split into multi-ISO:**
```bash
lb config --distribution trixie
# Create base ISO + addon ISOs
```

---

### `chroot` Fails in Build

**Check internet in chroot:**
```bash
# Inside chroot:
ping -c 3 debian.org
```

**Fix DNS:**
```bash
echo nameserver 8.8.8.8 > /etc/resolv.conf
```

**Mount proc/sys/dev:**
```bash
# Ensure auto/ mounts includes:
mount --bind /proc /build/proc
mount --bind /sys /build/sys
mount --bind /dev /build/dev
```

**Run in chroot with debug:**
```bash
lb build --debug
```

---

## 9. Key Log Locations

```
/var/log/syslog               General system events
/var/log/auth.log             SSH, sudo, PAM authentication
/var/log/kern.log             Kernel messages
/var/log/weston.log           Weston compositor output
/var/log/gdm3/*/*.log         GDM3 session logs
/var/log/hermesos/*.log       Hermes agent logs
/var/log/browseros/*          BrowserOS service logs
/run/hermes-claw/             IPC socket directory
/run/duckbotos/               DuckBotOS IPC directory
/run/user/1000/               XDG runtime (Weston, wayland sockets)
/home/*/.openclaw/logs/       OpenClaw gateway logs
/home/*/.lmstudio/logs/        LM Studio logs
/home/*/.lmstudio/llmster.log llmster daemon log
```

**Quick log dump:**
```bash
# Get last 200 lines from all key logs
for log in /var/log/syslog /var/log/weston.log /var/log/auth.log; do
  echo "=== $log ===" && tail -200 "$log"
done
```

---

## 10. Recovery Mode

### Boot into Recovery from Live USB

```bash
# Find installed partitions
sudo fdisk -l

# Mount root (adjust /dev/sda2 to your install)
sudo mount /dev/sda2 /mnt

# Mount EFI (adjust /dev/sda1)
sudo mount /dev/sda1 /mnt/boot/efi

# Mount persistence if used
sudo mount /dev/sda3 /mnt/cow

# Chroot in
sudo chroot /mnt
```

Inside chroot:
```bash
# Update GRUB
update-grub

# Reinstall kernel
apt install --reinstall linux-image-$(uname -r)

# Update initramfs
update-initramfs -u

# Exit chroot
exit
sudo reboot
```

---

### Reset GDM

```bash
sudo systemctl restart gdm3
```

If GDM is completely broken:
```bash
sudo dpkg-reconfigure gdm3
# Select gdm3 as default display manager
```

---

### Reset First-Run Wizard

```bash
sudo rm /var/lib/duckbotos/.wizard-complete
sudo systemctl restart duckbotos-first-boot-wizard.service
```

---

### Factory Reset

```bash
# WARNING: This wipes all user data and configs
sudo duckbotos-reset
# Or manually:
sudo rm -rf /var/lib/duckbotos/*
sudo rm -rf /home/*/.config/hermesos
sudo rm -rf /home/*/.config/openclaw
# Then reinstall services:
sudo apt install --reinstall duckbotos-core duckbotos-hermes duckbotos-openclaw
```

---

### Reinstall LM Studio

```bash
# From inside a running system (not chroot from live):
curl -fsSL https://lmstudio.ai/install.sh | bash

# From chroot:
chroot /mnt
curl -fsSL https://lmstudio.ai/install.sh | bash
exit
```

---

## 11. Getting Help

### Diagnostic CLI

**Run the full diagnostic suite:**
```bash
duckbotos-diag
# This gathers logs, system info, and pipes to a shareable gist
```

**Hermes doctor:**
```bash
sudo -u hermesos hermes-cli doctor
```

**OpenClaw doctor:**
```bash
openclaw gateway doctor
```

**Brain doctor:**
```bash
cd ~/.duckbot-brain && python -m src.cli doctor --full
```

### Debug Mode

Enable debug logging for any service:
```bash
sudo systemctl edit <service>.service
```
Add:
```
[Service]
Environment=DEBUG=1
```
Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart <service>
journalctl -f -u <service>
```

### Capture a Session

```bash
# Start script recording:
script -f /tmp/duckbotos-session-$(date +%Y%m%d-%H%M%S).txt

# ... perform actions ...

# Stop with Ctrl+D
```

### Report a Bug

When reporting issues, include:
1. Output of `duckbotos-diag`
2. `journalctl -b -u <failing-service> -n 50`
3. `cat /proc/cmdline`
4. GPU model and driver version: `nvidia-smi` or `lspci | grep -i vga`
5. Model of machine (NUC, desktop, laptop)
6. Whether using UEFI or BIOS boot

---

## Quick Reference Commands

```bash
# Status of everything
duckbotos-diag

# Check all services
systemctl list-units --state=failed
systemctl | grep duckbotos

# Restart everything
sudo systemctl restart hermes-agent.service openclaw-gateway.service lmstudio.service

# View all recent errors
journalctl -p err -b --no-pager

# Check disk space
df -h
lsblk

# Check memory
free -h

# Check GPU
nvidia-smi
# or
rocm-smi

# Check temps (if lm-sensors installed)
sensors

# Check network
ip addr
ping -c 3 8.8.8.8
```
