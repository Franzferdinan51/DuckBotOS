# DuckBotOS — BrowserOS Integration

> How BrowserOS is installed, configured, and set as the default browser in DuckBotOS.
> Status: Updated v0.2 — 2026-06-29 (research-verified)

---

## 1. Overview

BrowserOS is an **open-source Chromium fork** with native AI agent support (AGPL-3.0, Felafax Inc.). In DuckBotOS, it serves two roles:

1. **Default browser** — opens all web content (Weston kiosk, links from the OS)
2. **Agentic browser** — provides MCP-driven browser control for the AI agent (click, type, screenshot, JavaScript execution)

BrowserOS is bundled on all three DuckBotOS ISO variants. The kiosk compositor (Weston) launches BrowserOS in fullscreen kiosk mode, loading the agent's web dashboard URL.

**Key fact:** BrowserOS's CLI (`browseros-cli`) is **separate** from the BrowserOS browser itself. The CLI controls a running BrowserOS instance, and the MCP server provides programmatic browser control. All three components (browser, CLI, MCP) are part of the BrowserOS monorepo.

---

## 2. BrowserOS vs. Stock Chromium

| | BrowserOS | Stock Chromium |
|---|---|---|
| **Agentic features** | Native MCP server (port 9003) | None |
| **CLI tool** | `browseros-cli` for automation | None |
| **AI extension port** | Yes (MCP on port 9003) | No |
| **AI agent built-in** | Yes (Bun MCP server, 53+ tools) | No |
| **LLM providers** | 13+ including LM Studio + Ollama | None |
| **DuckBotOS fit** | ✅ Agent-native | ❌ Generic |

**Note:** BrowserOS's agent mode currently recommends Claude Opus 4.5 for best results. Local models (Ollama, LM Studio) work in Chat Mode but Agent Mode recommends cloud models. This is fine for DuckBotOS — users can choose cloud or local per-session.

---

## 3. BrowserOS Monorepo Structure

The BrowserOS repo (`github.com/browseros-ai/BrowserOS`) is a monorepo with two main subsystems:

```
packages/
├── browseros/              # Chromium fork + build system (C++/Python)
│   ├── browseros.cc        # Main browser binary
│   └── ...                 # Chromium source + BrowserOS patches
├── browseros-agent/        # AI agent platform
│   └── apps/
│       ├── server/         # Bun MCP server (53+ tools)
│       │   └── index.ts    # MCP server entry point
│       └── cli/            # Go CLI tool (browseros-cli)
│           └── main.go     # browseros-cli source
└── agent-sdk/              # @browseros-ai/agent-sdk (npm)
    └── ...
```

### Component Details

| Component | Tech | Purpose | Binaries |
|-----------|------|---------|----------|
| **Browser** | Chromium fork (C++) | Web browsing | `/opt/browseros/browseros` |
| **CLI** | Go | Terminal control of BrowserOS | `browseros-cli` |
| **MCP Server** | Bun (TypeScript) | 53+ browser automation tools for AI agents | `browseros-mcp-server` |
| **Agent SDK** | TypeScript npm | AI agent integration | `@browseros-ai/agent-sdk` |

---

## 4. Installation Methods

### 4.1 Linux .deb (Recommended for DuckBotOS)

Direct from GitHub releases:
```bash
curl -L https://github.com/browseros-ai/BrowserOS/releases/latest/download/browseros-linux-amd64.deb \
  -o /tmp/browseros.deb
dpkg -i /tmp/browseros.deb
```

Or via CDN:
```bash
curl -fsSL https://cdn.browseros.com/download/BrowserOS.deb -o /tmp/browseros.deb
dpkg -i /tmp/browseros.deb
```

### 4.2 Linux AppImage

```bash
curl -fsSL https://files.browseros.com/download/BrowserOS.AppImage -o /tmp/browseros.AppImage
chmod +x /tmp/browseros.AppImage
# Run directly or install to path
```

### 4.3 browseros-cli Install Script

```bash
curl -fsSL https://www.browseros.ai/install.sh | bash
```

This installs `browseros-cli` to PATH. The CLI controls a running BrowserOS instance.

### 4.4 DuckBotOS Package: `duckbotos-browseros`

```
packages/duckbotos-browseros/
├── DEBIAN/
│   ├── control          # Package metadata
│   └── postinst         # Post-install: install .deb + set as default browser
├── opt/browseros/       # BrowserOS binary + resources (from .deb)
├── usr/share/applications/
│   └── browseros.desktop # Desktop entry
├── usr/bin/
│   └── browseros        # Symlink → /opt/browseros/browseros
└── usr/lib/systemd/system/
    ├── browseros.service     # BrowserOS itself
    └── browseros-mcp.service # MCP server for AI agents
```

**`DEBIAN/control`:**
```
Package: duckbotos-browseros
Version: 1.0.0
Section: web
Priority: optional
Depends: curl, libc6 (>= 2.34), libnss3, libatk1.0-0, libatk-bridge2.0-0, libdrm2, libgbm1
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Description: BrowserOS — AI-native Chromium browser for DuckBotOS
 BrowserOS is an open-source Chromium fork with native AI agent support.
 Includes browseros-cli for terminal control and MCP server for agent
 browser automation. 13+ LLM providers including LM Studio and Ollama.
```

**`DEBIAN/postinst`:**
```bash
#!/bin/bash
set -e

# Download and install BrowserOS .deb
curl -fsSL https://cdn.browseros.com/download/BrowserOS.deb \
  -o /tmp/browseros.deb
dpkg -i /tmp/browseros.deb || apt-get install -f

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

# Create mimeapps.list for GTK apps
mkdir -p ~/.config
cat >> ~/.config/mimeapps.list << 'EOF'
[Default Applications]
x-scheme-handler/http=browseros.desktop
x-scheme-handler/https=browseros.desktop
text/html=browseros.desktop
application/xhtml+xml=browseros.desktop
EOF

echo "[DuckBotOS] BrowserOS installed and set as default browser."
```

---

## 5. Desktop Entry

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
X-Desktop-File-Install-Version=0.26
```

---

## 6. Set as Default Browser

### 6.1 update-alternatives (Legacy)

```bash
# Register BrowserOS as a browser alternative
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

### 6.2 xdg-settings (Modern)

```bash
# Set default browser for all XDG-aware apps
xdg-settings set default-web-browser browseros.desktop

# Verify
xdg-settings get default-web-browser
# Expected: browseros.desktop
```

### 6.3 mimeapps.list (GTK/GNOME Fallback)

For apps that read `.desktop` associations directly:

```bash
mkdir -p ~/.config
cat >> ~/.config/mimeapps.list << 'EOF'
[Default Applications]
x-scheme-handler/http=browseros.desktop
x-scheme-handler/https=browseros.desktop
text/html=browseros.desktop
application/xhtml+xml=browseros.desktop
EOF
```

### 6.4 Manual Symlink (Last Resort)

```bash
sudo rm /etc/alternatives/gnome-www-browser
sudo ln -s /opt/browseros/browseros /etc/alternatives/gnome-www-browser
sudo rm /etc/alternatives/x-www-browser
sudo ln -s /opt/browseros/browseros /etc/alternatives/x-www-browser
```

---

## 7. browseros-cli Reference

Once BrowserOS is running, `browseros-cli` controls it:

```bash
# Initialize connection to running BrowserOS instance
browseros-cli init

# Open a URL
browseros-cli open https://example.com

# Get page text
browseros-cli text

# Take screenshot
browseros-cli ss /tmp/screenshot.png

# List open tabs
browseros-cli tabs

# X Trending topics
browseros-cli x-trending

# GitHub repo page
browseros-cli github browseros-ai/BrowserOS
```

**⚠️ Known issue:** `browseros-cli status` is buggy — may report "disconnected" even when working. Trust `browseros-cli health` and `browseros-cli pages` instead.

---

## 8. MCP Server (Agent Browser Control)

BrowserOS's MCP server exposes 53+ browser automation tools for AI agents.

### 8.1 MCP Service Unit

```ini
# /usr/lib/systemd/system/browseros-mcp.service
[Unit]
Description=BrowserOS MCP Server
After=network.target browseros.service
Wants=browseros.service

[Service]
Type=simple
User=root
Group=root
ExecStart=/opt/browseros/bin/browseros-mcp-server --port 9003
Restart=on-failure
RestartSec=5
Environment="BROWSEROS_SERVER_PORT=9200"
Environment="BROWSEROS_CDP_PORT=9110"

[Install]
WantedBy=multi-user.target
```

### 8.2 MCP Connection (Hermes/OpenClaw)

Both Hermes and OpenClaw connect to `http://localhost:9003` for:
- `browser_navigate` — go to a URL
- `browser_snapshot` — get page structure (ARIA/snapshot)
- `browser_click` — click an element
- `browser_type` — type text
- `browser_screenshot` — take a screenshot
- And 49 more tools...

### 8.3 MCP Tool Categories

| Category | Tools |
|----------|-------|
| **Navigation** | navigate, back, forward, refresh |
| **Content** | snapshot, text, html, markdown |
| **Interaction** | click, type, hover, scroll, drag |
| **Media** | screenshot, ss |
| **Tab management** | tabs, new-tab, close-tab, switch-tab |
| **X/Twitter** | x-search, x-trending |
| **GitHub** | github |
| **Automation** | wait-for, wait-for-selector, evaluate |

---

## 9. Kiosk Mode Launch

### 9.1 BrowserOS Kiosk Launcher

```bash
#!/bin/bash
# /usr/local/bin/browseros-kiosk.sh
# Called by the Weston kiosk service

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

### 9.2 Weston Kiosk Service

Weston (the Wayland compositor) runs BrowserOS as its sole output:

```ini
# /etc/systemd/system/duckbotos-kiosk.service
[Unit]
Description=DuckBotOS Kiosk (Weston + BrowserOS)
After=lmstudio.service
Wants=lmstudio.service network-online.target
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
# Reads DuckBotOS mode and launches Weston + BrowserOS

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

exec weston \
  --backend=drm-backend.so \
  --shell=kiosk-shell.so \
  --idle-time=0 \
  --shell-plugin=/usr/lib/weston/desk-shell.so \
  2>&1 | logger -t duckbotos-kiosk &
```

---

## 10. Supported LLM Providers

BrowserOS supports 13+ LLM providers natively:

| Provider | Type | Auth |
|-----------|------|------|
| Kimi K2.5 | Cloud (default) | Built-in |
| ChatGPT Pro/Plus | Cloud | OAuth |
| GitHub Copilot | Cloud | OAuth |
| Qwen Code | Cloud | OAuth |
| Claude (Anthropic) | Cloud | API key |
| GPT-4o / o3 (OpenAI) | Cloud | API key |
| Gemini (Google) | Cloud | API key |
| Azure OpenAI | Cloud | IAM |
| AWS Bedrock | Cloud | IAM |
| OpenRouter | Cloud | API key |
| Ollama | Local | Setup |
| **LM Studio** | **Local** | **Setup** |
| + more | | |

**BrowserOS ↔ DuckBotOS LM Studio integration:** BrowserOS can use LM Studio as a local provider. When both are installed in DuckBotOS, users can configure BrowserOS to use LM Studio's local API (`http://127.0.0.1:1234/v1`) directly from BrowserOS settings.

---

## 11. Troubleshooting

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

### browseros-cli can't connect
```bash
# Make sure BrowserOS is running first
browseros-cli health
browseros-cli pages
# If both work, CLI is connected
```

---

## 12. Build Checklist

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

## 13. Key Sources

- [BrowserOS GitHub](https://github.com/browseros-ai/BrowserOS) — official monorepo
- [BrowserOS Website](https://www.browseros.com) — marketing + downloads
- [BrowserOS Docs](https://docs.browseros.com) — official documentation

*BrowserOS integration v0.2 — 2026-06-29 (research-verified)*
