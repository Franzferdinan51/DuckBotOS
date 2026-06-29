# DuckBotOS — BrowserOS Integration

> How BrowserOS is installed, configured, and set as the default browser in DuckBotOS.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Overview

BrowserOS is an open-source Chromium fork with native AI agent support. In DuckBotOS, it serves two roles:

1. **Default browser** — opens all web content (wayland-kiosk, links from the OS)
2. **Agentic browser** — provides MCP-driven browser control for the AI agent (click, type, screenshot, JavaScript execution)

BrowserOS is bundled on all three DuckBotOS ISO variants. The kiosk compositor (Weston) launches BrowserOS in fullscreen kiosk mode, loading the agent's web dashboard URL.

---

## 2. BrowserOS vs. Chromium

| | BrowserOS | Stock Chromium |
|---|---|---|
| **Agentic features** | Native MCP server (port 9003) | None |
| **CLI tool** | `browseros-cli` for automation | None |
| **AI extension port** | Yes (MCP on port 9003) | No |
| **Logged-in state** | Preserved across sessions | Same |
| **DuckBotOS fit** | ✅ Agent-native | ❌ Generic |

BrowserOS is purpose-built for AI agent workflows. Its MCP server lets the agent control the browser programmatically — essential for the "AI-first OS" experience.

---

## 3. Installation

### 3.1 Official .deb Package

BrowserOS provides an official Debian package at:

```
https://github.com/browseros-ai/BrowserOS/releases/latest/download/browseros-linux-amd64.deb
```

Direct download:
```bash
curl -L https://github.com/browseros-ai/BrowserOS/releases/latest/download/browseros-linux-amd64.deb \
  -o /tmp/browseros.deb
dpkg -i /tmp/browseros.deb
```

Or install via the CLI:
```bash
# The browseros-cli install script (macOS/Linux)
curl -fsSL https://www.browseros.ai/install.sh | bash
```

### 3.2 DuckBotOS Package: `duckbotos-browseros`

```
packages/duckbotos-browseros/
├── DEBIAN/
│   ├── control          # Package metadata
│   └── postinst         # Post-install: set as default browser
├── opt/browseros/       # BrowserOS binary + resources
├── usr/share/applications/
│   └── browseros.desktop
├── usr/bin/
│   └── browseros        # Symlink to /opt/browseros/browseros
└── usr/lib/systemd/system/
    └── browseros-mcp.service
```

**`DEBIAN/control`:**
```
Package: duckbotos-browseros
Version: 1.0.0
Section: web
Priority: optional
Depends: curl, libc6 (>= 2.34), libnss3, libatk1.0-0, libatk-bridge2.0-0
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Description: BrowserOS — AI-native Chromium browser for DuckBotOS
 BrowserOS is an open-source Chromium fork with native AI agent support.
 Includes browseros-cli for terminal control and MCP server for agent
 browser automation.
```

### 3.3 .desktop File

```ini
# /usr/share/applications/browseros.desktop
[Desktop Entry]
Name=BrowserOS
Comment=AI-native Chromium browser
Exec=/opt/browseros/browseros --kiosk %u
Icon=/opt/browseros/browseros.png
Terminal=false
Type=Application
Categories=Network;WebBrowser;
MimeType=text/html;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
StartupNotify=true
```

---

## 4. Set as Default Browser

### 4.1 update-alternatives

Register BrowserOS with the Debian alternatives system and set it as default:

```bash
# Register as browser
update-alternatives --install \
  /usr/bin/x-www-browser x-www-browser \
  /opt/browseros/browseros 200

update-alternatives --install \
  /usr/bin/gnome-www-browser gnome-www-browser \
  /opt/browseros/browseros 200

# Set as default
update-alternatives --set x-www-browser /opt/browseros/browseros
update-alternatives --set gnome-www-browser /opt/browseros/browseros
```

### 4.2 xdg-settings

Modern Ubuntu desktop uses XDG desktop utilities:

```bash
# Set default browser for all XDG-aware apps
xdg-settings set default-web-browser browseros.desktop

# Verify
xdg-settings get default-web-browser
# Expected: browseros.desktop
```

### 4.3 mimeapps.list

For GNOME/GTK apps that read `.desktop` associations directly:

```bash
# Add to user's MIME associations
mkdir -p ~/.config
cat >> ~/.config/mimeapps.list << 'EOF'
[Default Applications]
x-scheme-handler/http=browseros.desktop
x-scheme-handler/https=browseros.desktop
text/html=browseros.desktop
application/xhtml+xml=browseros.desktop
EOF
```

### 4.4 Post-install Hook

In `DEBIAN/postinst`:

```bash
#!/bin/bash
set -e

# Register with alternatives
update-alternatives --install \
  /usr/bin/x-www-browser x-www-browser \
  /opt/browseros/browseros 200 || true

update-alternatives --install \
  /usr/bin/gnome-www-browser gnome-www-browser \
  /opt/browseros/browseros 200 || true

# Set as default
update-alternatives --set x-www-browser /opt/browseros/browseros 2>/dev/null || true
update-alternatives --set gnome-www-browser /opt/browseros/browseros 2>/dev/null || true

# XDG default
xdg-settings set default-web-browser browseros.desktop 2>/dev/null || true

echo "[DuckBotOS] BrowserOS installed and set as default browser."
```

---

## 5. Kiosk Mode Launch

### 5.1 BrowserOS Kiosk Launcher

```bash
#!/bin/bash
# /usr/local/bin/browseros-kiosk.sh
# Called by Weston kiosk service

export BROWSEROS_KIOSK_URL="${KIOSK_URL:-http://127.0.0.1:9119}"
export BROWSEROS_SERVER_PORT=9200
export BROWSEROS_CDP_PORT=9110

exec /opt/browseros/browseros \
  --kiosk \
  --noerrdialogs \
  --start-fullscreen \
  --app="$BROWSEROS_KIOSK_URL" \
  --new-window \
  --disable-infobars \
  --disable-session-crashed-bubbles \
  --no-default-browser-check \
  --homepage="$BROWSEROS_KIOSK_URL"
```

### 5.2 Weston Kiosk Service

Weston (the Wayland compositor) runs BrowserOS as its sole output:

```ini
# /etc/systemd/system/duckbotos-kiosk.service
[Unit]
Description=DuckBotOS Kiosk (Weston + BrowserOS)
After=lmstudio.service
Wants=lmstudio.service
PartOf=graphical.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/usr/local/bin/duckbotos-kiosk-launch.sh
Restart=on-failure
RestartSec=5
Environment="WAYLAND_DISPLAY=wayland-0"
Environment="XDG_RUNTIME_DIR=/run/user/0"

[Install]
WantedBy=graphical.target
```

```bash
#!/bin/bash
# /usr/local/bin/duckbotos-kiosk-launch.sh
# Launches Weston in kiosk mode, then BrowserOS in the weston window

# Read the DuckBotOS mode (hermes | openclaw | hybrid)
MODE=$(cat /etc/duckbotos/mode 2>/dev/null || echo "hermes")

case "$MODE" in
  hermes)
    KIOSK_URL="http://127.0.0.1:9119"
    ;;
  openclaw)
    KIOSK_URL="http://127.0.0.1:18789/plugins/openclawos"
    ;;
  hybrid)
    KIOSK_URL="http://127.0.0.1:9119"
    ;;
  *)
    KIOSK_URL="http://127.0.0.1:9119"
    ;;
esac

export KIOSK_URL

# Start Weston
exec weston \
  --backend=drm-backend.so \
  --shell=kiosk-shell.so \
  --idle-time=0 \
  --shell-plugin=/usr/lib/weston/desk-shell.so \
  2>&1 | logger -t duckbotos-kiosk &
```

---

## 6. MCP Server (Agent Browser Control)

BrowserOS's MCP server enables the AI agent to control the browser programmatically.

### 6.1 MCP Service

```ini
# /usr/lib/systemd/system/browseros-mcp.service
[Unit]
Description=BrowserOS MCP Server
After=network.target browseros.service
PartOf=browseros.service

[Service]
Type=simple
User=root
ExecStart=/opt/browseros/browseros-mcp-server --port 9003
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 6.2 MCP Connection

The MCP server listens on `http://localhost:9003`. Both Hermes and OpenClaw connect to it for:
- `browser_navigate` — go to a URL
- `browser_snapshot` — get page structure
- `browser_click` — click an element
- `browser_type` — type text
- `browser_screenshot` — take a screenshot

---

## 7. CLI Tool: browseros-cli

BrowserOS ships with `browseros-cli` for terminal control:

```bash
# Check if BrowserOS is running
browseros-cli status

# Open a URL
browseros-cli open https://example.com

# Get page text
browseros-cli text

# Take screenshot
browseros-cli ss /tmp/screenshot.png

# X Trending
browseros-cli x-trending

# List open tabs
browseros-cli tabs
```

**Important:** `browseros-cli status` is known to sometimes report "disconnected" even when BrowserOS is working. Trust `browseros-cli health` and `browseros-cli pages` for status verification.

---

## 8. Troubleshooting

### BrowserOS won't start
```bash
# Check if GPU is available
ls /dev/dri/

# Try with software rendering
/opt/browseros/browseros --no-sandbox --disable-gpu
```

### MCP server not responding
```bash
# Check port 9003 is listening
ss -tlnp | grep 9003

# Check service
systemctl status browseros-mcp
```

### Not set as default browser
```bash
# Force reset
update-alternatives --set x-www-browser /opt/browseros/browseros
xdg-settings set default-web-browser browseros.desktop
```

---

## 9. Build Checklist

- [ ] Download BrowserOS .deb from GitHub releases
- [ ] Create `packages/duckbotos-browseros/DEBIAN/control`
- [ ] Create `packages/duckbotos-browseros/DEBIAN/postinst`
- [ ] Create `usr/share/applications/browseros.desktop`
- [ ] Create `usr/local/bin/browseros-kiosk.sh`
- [ ] Create `duckbotos-kiosk.service` (Weston + BrowserOS)
- [ ] Create `browseros-mcp.service`
- [ ] Add `duckbotos-browseros` to all three ISO package lists
- [ ] Verify `xdg-settings get default-web-browser` → `browseros.desktop` in live ISO
- [ ] Verify BrowserOS loads the agent dashboard URL on boot

---

*BrowserOS integration v0.1 — 2026-06-29*