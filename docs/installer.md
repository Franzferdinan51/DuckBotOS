# DuckBotOS — Installer Design

> How DuckBotOS handles installation: Subiquity OEM mode, autoinstall.yaml, whitelabel source-selection, and first-boot wizard.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Design Goals

1. **Zero user configuration during install** — the installer handles disk partitioning and user creation only
2. **Agent selection via first-boot wizard** — not a custom installer page (simpler, faster to build)
3. **Three ISOs for v1** — separate ISOs for Hermes-only, OpenClaw-only, and Both mode (avoids complex installer branching)
4. **OEM mode for pre-installed hardware** — standard Ubuntu OEM workflow

---

## 2. Three ISOs vs. Single ISO with Agent Picker

### Decision: Three Separate ISOs (v1)

Building one ISO with an agent-selection page in Subiquity adds significant complexity:
- Requires custom `source-selection` hook in Subiquity
- Requires different package sets per choice
- Testing surface doubles (one installer × three outcomes)

**Simpler v1 approach:** Build three separate ISOs:
```
duckbotos-hermes-x86_64.iso     # Hermes-only
duckbotos-openclaw-x86_64.iso   # OpenClaw-only
duckbotos-both-x86_64.iso       # Both modes
```

**Future (v0.2+):** Single ISO with agent picker if the workflow proves common.

### ISO Package Contents

| Package | hermes | openclaw | both |
|---------|--------|----------|------|
| `duckbotos-base` | ✅ | ✅ | ✅ |
| `weston` | ✅ | ✅ | ✅ |
| `browseros` | ✅ | ✅ | ✅ |
| `hermes-agent` | ✅ | ❌ | ✅ |
| `openclaw` | ❌ | ✅ | ✅ |
| `openclawos-plugin` | ❌ | ✅ | ✅ |
| `Newest Desktop Control` | ✅ | ✅ | ✅ |
| `lm-studio-headless` | ✅ | ✅ | ✅ |
| `hermesos-kiosk` | ✅ | ❌ | ❌ |
| `openclawos-kiosk` | ❌ | ✅ | ❌ |
| `hermesos-hybrid-kiosk` | ❌ | ❌ | ✅ |
| `gdm3` (with sessions) | ❌ | ❌ | ✅ |

---

## 3. Subiquity OEM Mode

### 3.1 What is OEM Mode

OEM mode is Ubuntu's built-in mechanism for system builders. The ISO boots to a "Preparing Ubuntu for shipping" screen, which runs the installer automatically on first boot (not on the builder's machine).

For DuckBotOS:
1. Build the ISO with OEM-mode enabled
2. Write the `autoinstall.yaml` into the ISO's `Casper` partition
3. The OEM install screen appears when the end user first boots the USB/VM
4. Installation runs unattended, then the machine is ready to ship

### 3.2 Autoinstall.yaml

```yaml
# iso/preseed/duckbotos-hermes-autoinstall.yaml
version: 1
reporting:
  hook:
    type: i 日志
    command: echo "DuckBotOS install: [[[STATUS]]]"

# Don't ask anything — fully automated
interactive-sections:
  - "*"

identity:
  hostname: duckbotos
  username: duckbot
  # Password set via OEM config or cloud-init
  # In production: use hashed password from OEM config
  realname: DuckBotOS User
  password: <!calcute-hash>

# Storage configuration
storage:
  layout:
    name: lvm
    gut: all  # Use entire disk

# Package installation (none needed — all in live image)
packages:
  - ubuntu-standard
  - ubuntu-desktop-minimal

# Post-install commands (run in installer chroot)
late-commands:
  # Mark as OEM install (will show "Preparing for shipping" on next boot)
  - curtin in-target --target /target \
      mkdir -p /var/lib/systemd/oem-configured

  # Enable DuckBotOS first-boot service
  - curtin in-target --target /target \
      systemctl enable duckbotos-firstboot.service

  # Write agent mode for first-boot to read
  - echo 'DUCKBOTOS_MODE=hermes' > /target/etc/duckbotos/mode

  # Disable Subiquity's automatic reboot hook (replaced by our service)
  - rm -f /target/etc/systemd/system/multi-user.target.wants/subiquity-submit-logs.service

# First boot runs the firstboot service, not the installer
firstboot commands:
  # (handled by duckbotos-firstboot.service, not autoinstall)
```

### 3.3 Whitelabel.yaml (OEM Branding)

```yaml
# iso/preseed/duckbotos-whitelabel.yaml
# OEM branding for the installer screen
name: DuckBotOS
identifier: com.duckbotos
icon: /usr/share/icons/duckbotos.png
short-description: "AI-first operating system"
long-description: |
  DuckBotOS is an AI-native operating system powered by Hermes.
  Boot directly into your AI agent — no desktop, no app drawer,
  just your intelligent assistant.
```

---

## 4. First-Boot Wizard

After OEM installation, the first-boot wizard runs. This is a Node.js/web app served on a local port, displayed in a Chromium window before the kiosk starts.

**Service:** `duckbotos-firstboot.service`

```ini
# /etc/systemd/system/duckbotos-firstboot.service
[Unit]
Description=DuckBotOS First-Boot Setup Wizard
After=getty@tty1.service
Requires=getty@tty1.service

[Service]
Type=simple
ExecStartPre=/bin/sleep 5
ExecStart=/usr/local/bin/duckbotos-firstboot.sh
StandardInput=tty
StandardOutput=tty
TTYPath=/dev/tty2
# Don't use=tty1 — the kiosk is there

[Install]
WantedBy=multi-user.target
```

### 4.1 First-Boot Wizard Steps

The wizard runs in a **fullscreen Chromium window** (not Weston kiosk yet). Steps:

```
Step 1/5: Welcome
  "Welcome to DuckBotOS"
  [Continue →]

Step 2/5: Network
  - Check network connectivity
  - If offline: show WiFi picker (NMcli TUI)
  - If online: auto-continue

Step 3/5: Cloud Providers
  - MiniMax API key (optional, can skip)
  - OpenAI API key (optional)
  - Anthropic API key (optional)
  - Grok API key (optional)
  - "Skip for now" button
  - Keys stored with chmod 600

Step 4/5: LM Studio (Local Models)
  - Is LM Studio installed? (auto-detected: lms daemon status)
  - If yes: enter server URL (default: http://127.0.0.1:1234)
  - "Use cloud only" option
  - Select default model from downloaded list (GET /v1/models)

Step 5/5: Ready
  - Summary of configured providers
  - "Start DuckBotOS →" button
  - Writes config → disables itself → starts kiosk
```

### 4.2 First-Boot Config Output

```yaml
# ~/.hermes/config.yaml (Hermes mode)
providers:
  minimax:
    api_key: "${MINIMAX_API_KEY}"
    default_model: minimax-portal/MiniMax-M2.7
  openai:
    api_key: "${OPENAI_API_KEY}"
    default_model: gpt-4o

lm_studio:
  url: http://127.0.0.1:1234
  default_model: null  # user selected

channel: telegram  # or: cli, web, etc.

# ~/.hermes/config.yaml (OpenClaw mode)
# ~/.openclaw/config.yaml
providers:
  minimax:
    type: openai-compatible
    api_key: "${MINIMAX_API_KEY}"
    base_url: https://api.minimaxi.chat/v1
  lm-studio:
    type: openai-compatible
    api_key: local
    base_url: http://127.0.0.1:1234/v1
```

### 4.3 First-Boot Service Disables Itself

After successful wizard completion:

```bash
# In firstboot.sh — final step:
systemctl disable duckbotos-firstboot.service
systemctl stop duckbotos-firstboot.service

# Start the kiosk
systemctl start weston-kiosk.service
```

---

## 5. Per-Mode ISOs

### 5.1 Hermes-Only ISO

**Target:** `duckbotos-hermes-x86_64.iso`
**Use case:** Users who want the NousResearch Hermes agent experience

**Package list (`config/package-lists/hermes.list`):**
```
# Base
ubuntu-desktop-minimal
weston
network-manager
firejail
apparmor
ubuntu-standard

# Hermes agent
hermes-agent

# LM Studio headless
lm-studio-headless

# BrowserOS (default browser)
browseros

# Kiosk
hermesos-kiosk

# Desktop control
Newest Desktop Control

# DuckBotOS base
duckbotos-base
duckbotos-firstboot
```

### 5.2 OpenClaw-Only ISO

**Target:** `duckbotos-openclaw-x86_64.iso`
**Use case:** Users who prefer OpenClaw's agent framework

**Package list:**
```
# Base
ubuntu-desktop-minimal
weston
network-manager
firejail
apparmor
ubuntu-standard

# OpenClaw
openclaw
openclawos-plugin

# LM Studio headless
lm-studio-headless

# BrowserOS
browseros

# Kiosk
openclawos-kiosk

# Desktop control
Newest Desktop Control

# DuckBotOS base
duckbotos-base
duckbotos-firstboot
```

### 5.3 Both-Mode ISO

**Target:** `duckbotos-both-x86_64.iso`
**Use case:** Power users who want both agents, or want to evaluate

**Package list:**
```
# Base
ubuntu-desktop-minimal
weston
network-manager
firejail
apparmor
gnome-shell
gdm3
ubuntu-standard

# Both agents
hermes-agent
openclaw
openclawos-plugin

# LM Studio headless
lm-studio-headless

# BrowserOS
browseros

# Kiosk + GDM sessions
hermesos-hybrid-kiosk
duckbotos-gdm-sessions

# Desktop control
Newest Desktop Control

# DuckBotOS base
duckbotos-base
duckbotos-firstboot
```

### 5.4 GDM Session Files (Both Mode)

```ini
# /usr/share/xsessions/duckbotos-hermes.desktop
[Desktop Entry]
Name=DuckBotOS (Hermes)
Comment=AI-first OS with Hermes agent
Exec=/usr/local/bin/duckbotos-launch hermes
Type=Application
```

```ini
# /usr/share/xsessions/duckbotos-openclaw.desktop
[Desktop Entry]
Name=DuckBotOS (OpenClaw)
Comment=AI-first OS with OpenClaw gateway
Exec=/usr/local/bin/duckbotos-launch openclaw
Type=Application
```

```ini
# /usr/share/xsessions/duckbotos-hybrid.desktop
[Desktop Entry]
Name=DuckBotOS (Hybrid)
Comment=Full GNOME desktop with both agents
Exec=/usr/local/bin/duckbotos-launch hybrid
Type=Application
```

```bash
#!/usr/local/bin/duckbotos-launch
#!/bin/bash
# Reads /etc/duckbotos/mode or uses argument to decide kiosk launch
MODE="${1:-$(cat /etc/duckbotos/mode 2>/dev/null || echo 'hermes')}"
export KIOSK_URL

case "$MODE" in
  hermes)
    export KIOSK_URL="http://127.0.0.1:9119"
    systemctl start hermes-gateway.service
    systemctl start Newest Desktop Control.service
    systemctl start weston-kiosk.service
    systemctl start browseros-kiosk.service
    ;;
  openclaw)
    export KIOSK_URL="http://127.0.0.1:18789/plugins/openclawos"
    systemctl start openclaw-gateway.service
    systemctl start Newest Desktop Control.service
    systemctl start weston-kiosk.service
    systemctl start browseros-kiosk.service
    ;;
  hybrid)
    # GNOME desktop, agents in side panel
    systemctl start hermes-gateway.service
    systemctl start openclaw-gateway.service
    systemctl start Newest Desktop Control.service
    systemctl start gnome-session
    ;;
esac
```

---

## 6. live-build Configuration

### 6.1 Build Script

```bash
#!/bin/bash
# scripts/build-hermes-iso.sh
set -e

export LB_BOOTSTRAP_INCLUDE="config/package-lists/hermes.list"
export LB_CHROOT_HOOKS="config/hooks/live/chroot-early"
export MODE="hermes"

lb config noauto \
    --distribution noble \
    --archive-areas "main universe multiverse" \
    --binary-images iso-hybrid \
    --bootloader grub-efi \
    --iso-volume "DuckBotOS-Hermes"

lb build noauto "${@}"
```

### 6.2 Hook: Early Chroot Setup

```bash
#!/bin/sh
# config/hooks/live/chroot-early/05-kiosk-setup.chroot
#!/bin/sh
set -e

echo "[DuckBotOS] Setting up kiosk environment..."

# Create kiosk launch script
cat > /usr/local/bin/chromium-kiosk.sh << 'KIOSK_EOF'
#!/bin/bash
export KIOSK_URL="${KIOSK_URL:-http://127.0.0.1:9119}"
exec chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-features=Translate \
  --start-fullscreen \
  --app="$KIOSK_URL"
KIOSK_EOF
chmod +x /usr/local/bin/chromium-kiosk.sh

# Copy BrowserOS kiosk launcher
cat > /usr/local/bin/browseros-kiosk.sh << 'BROS_EOF'
#!/bin/bash
export BROWSEROS_KIOSK_URL="${KIOSK_URL:-http://127.0.0.1:9119}"
exec browseros \
  --app="$BROWSEROS_KIOSK_URL" \
  --kiosk \
  --noerrdialogs \
  --start-fullscreen
BROS_EOF
chmod +x /usr/local/bin/browseros-kiosk.sh

# Create DuckBotOS mode file
echo "hermes" > /etc/duckbotos/mode
mkdir -p /etc/duckbotos

echo "[DuckBotOS] Kiosk setup complete."
```

---

## 7. Phase 2 Build Checklist

- [ ] Set up Linux build VM (Ubuntu 24.04, UTM or Vagrant)
- [ ] Fork cxlinux-ai/cx-distro to Franzferdinan51/cx-distro
- [ ] Clone fork as `duckbotos/` base
- [ ] Create `packages/duckbotos-base/DEBIAN/control`
- [ ] Create `packages/hermesos-meta/DEBIAN/control` (Depends: duckbotos-base, hermes-agent, lm-studio-headless, browseros, hermesos-kiosk, Newest Desktop Control)
- [ ] Create `packages/openclawos-meta/DEBIAN/control`
- [ ] Create `packages/hermesos-hybrid-meta/DEBIAN/control`
- [ ] Create `iso/live-build/config/package-lists/hermes.list`
- [ ] Create `iso/live-build/config/package-lists/openclaw.list`
- [ ] Create `iso/live-build/config/package-lists/both.list`
- [ ] Create `iso/live-build/config/hooks/live/chroot-early/05-kiosk-setup.chroot`
- [ ] Create `iso/preseed/duckbotos-hermes-autoinstall.yaml`
- [ ] Create `iso/preseed/duckbotos-openclaw-autoinstall.yaml`
- [ ] Create `iso/preseed/duckbotos-both-autoinstall.yaml`
- [ ] Create `duckbotos-firstboot.service` + `duckbotos-firstboot.sh`
- [ ] Create `duckbotos-gdm-sessions` package with 3 .desktop files
- [ ] Build hermes ISO in VM → test in UTM
- [ ] Test: does it boot to Hermes dashboard?
- [ ] Test: does LM Studio llmster start on first boot?
- [ ] Test: does first-boot wizard complete and write config?

---

## 8. Related Documentation

| Doc | What It Covers |
|-----|---------------|
| `docs/build-guide.md` | Fork → VM → live-build → ISO — the actual build commands to run after this design is implemented |
| `docs/system-boot-flow.md` | Complete boot sequence showing where firstboot.service fits in the startup order |
| `docs/architecture.md` §5 | Kiosk shell: boot sequence, Weston kiosk service, Chromium/BrowserOS kiosk service |
| `docs/phase7-implementation.md` | Tier 1 features (F1–F5) including firstboot wizard internals for provider/model setup |
| `docs/lm-studio.md` | llmster install + LM Studio setup in first-boot wizard (Step 2/5) |
| `docs/cx-linux-fork.md` | How live-build config carries over from cx-distro, what changes for DuckBotOS |

---

*Installer design v0.2 — 2026-06-29.*