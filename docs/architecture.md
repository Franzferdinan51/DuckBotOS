# DuckBotOS — Architecture

> How DuckBotOS is built: the full technical stack, component integration, and build pipeline.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Design Philosophy

DuckBotOS is **not** a general-purpose Linux distro with an AI app bolted on. It is an **agent-first OS** — the AI runtime *is* the desktop. On boot, the user sees a Wayland kiosk running Chromium, loading either the Hermes Web Dashboard (`http://127.0.0.1:9119`) or the OpenClaw web workspace (`http://127.0.0.1:18789/plugins/openclawos`). There is no GNOME/KDE shell competing for the display.

The core insight: both Hermes and OpenClaw already ship web-based frontends. We don't build a custom desktop shell; we build:
1. A kiosk-mode Wayland session that auto-loads the agent's web URL
2. systemd services for both gateways + `Newest Desktop Control` MCP server
3. An installer that lets users pick which agent(s) to install
4. A login-screen session picker for "Both" mode

---

## 2. Reference Stack

DuckBotOS is built by forking and extending existing projects rather than starting from scratch:

| Project | Role in DuckBotOS | License |
|---------|-------------------|---------|
| **cxlinux-ai/cx-distro** | ISO build pipeline (live-build, preseed, APT repo, SBOM, AppArmor). **Primary inheritance.** | BSL 1.1 |
| **cxlinux-ai/cx-core** | Meta-package pattern (minimal install). Reference only. | BSL 1.1 |
| **thesysdev/openclaw-os** | OpenClaw web workspace at `/plugins/openclawos`. Becomes our "OpenClaw desktop." | TBD |
| **nousresearch/hermes-agent** | Hermes Web Dashboard at `http://127.0.0.1:9119`. Agent core. | MIT |
| **Newest Desktop Control (Lobster Edition)** | Rust MCP server for AT-SPI2 + Wayland portal desktop control. Lets agents click/type/screenshot. | TBD |
| **lmstudio-ai/lm-studio** | Local LLM server. `llmster` daemon + REST API on port 1234. First-class provider. | Proprietary |
| **browseros-ai/BrowserOS** | Chromium-based agentic browser. Default browser for kiosk. | AGPL v3 |
| **Weston** (Wayland) | Kiosk compositor. Auto-starts on tty1, no login required. | MIT |
| **Subiquity** (Ubuntu) | Official Ubuntu installer. OEM mode + autoinstall.yaml for unattended installs. | GPLv3 |

---

## 3. Base OS

```
Ubuntu 24.04 LTS (Noble Numbat)
├── linux-image-generic-hwe-amd64   # HWE kernel (newer drivers)
├── weston                          # Wayland compositor (kiosk mode)
├── chromium-browser                # Kiosk browser (or BrowserOS)
├── gnome-shell                     # Fallback desktop for "Both" mode GDM
├── systemd                         # Service management
├── network-manager                 # WiFi/VPN
├── apt / snap / flatpak            # Package management
└── firejail / apparmor             # Sandboxing
```

---

## 4. Agent Layers

### 4.1 Hermes-Only Install

```
/usr/lib/hermes/
├── hermes/                         # Hermes agent installation
├── hermes-gateway.service          # systemd: hermes gateway on port 9119
├── weston-kiosk.service            # systemd: Weston compositor
├── chromium-kiosk.service          # systemd: Chromium kiosk → http://127.0.0.1:9119
└── Newest Desktop Control.service      # systemd: MCP server on port 9600

~/.hermes/
├── workspace/                      # Skills, memory, sessions
├── config.yaml                     # Provider keys, model preferences
└── .hermesrc                       # Shell aliases
```

### 4.2 OpenClaw-Only Install

```
/opt/openclaw/
├── openclaw/                       # OpenClaw gateway + plugins
├── openclaw-gateway.service        # systemd: gateway on port 18797
├── openclaw-os/                    # Web workspace plugin (served at /plugins/openclawos)
├── weston-kiosk.service            # systemd: Weston compositor
├── chromium-kiosk.service          # systemd: Chromium → http://127.0.0.1:18789/plugins/openclawos
└── Newest Desktop Control.service      # systemd: MCP server on port 9600

~/.openclaw/
├── openclaw.json                   # Config (plugins.entries + mcp.servers) — per src/config/paths.ts
├── workspace/                      # Skills, memory, sessions (user-state)
└── extensions/duckbot-memory/      # Brain plugin (installed by duckbotos-brain)
```

### 4.3 Both Mode (Hybrid)

```
/run/hermes-claw/
└── agent-bus.sock                  # JSON-RPC 2.0 Unix socket IPC bridge

/etc/hermes-claw/
├── hermes/                         # Hermes config
├── openclaw/                       # OpenClaw config
└── credentials/                    # TPM-backed shared secrets (when available)

# GDM session entries:
# 1. Hermes Desktop → boots Hermes kiosk
# 2. OpenClaw Desktop → boots OpenClaw kiosk
# 3. Hybrid Workstation → boots GNOME Shell with both agents in side panel
```

---

## 5. Kiosk Shell

The kiosk is the core UX surface. It replaces the display manager's user-facing shell.

### 5.1 Boot Sequence

```
[Systemd bootstrap]
  └─ multi-user.target
      ├─ hermes-gateway.service      (Hermes-only or Both)
      ├─ openclaw-gateway.service    (OpenClaw-only or Both)
      ├─ Newest Desktop Control.service  (all modes) — MCP on port 9600
      ├─ weston-kiosk.service        (all modes) — Wayland compositor
      └─ chromium-kiosk.service      (all modes) — fullscreen browser

[Weston compositor starts on tty1]
  └─ chromium-kiosk.service
      └─ chromium --kiosk \
          --noerrdialogs \
          --disable-features=Translate \
          --window-size=1920,1080 \
          --start-fullscreen \
          --app=http://127.0.0.1:9119         ← Hermes
          OR --app=http://127.0.0.1:18789/plugins/openclawos  ← OpenClaw
          OR --app=http://localhost/agent-picker                 ← Both (picker)
```

### 5.2 Weston Kiosk Service

```ini
# /etc/systemd/system/weston-kiosk.service
[Unit]
Description=Weston Kiosk Compositor
After=local-fs.target
Wants=local-fs.target

[Service]
Type=idle
ExecStart=/usr/local/bin/weston-kiosk.sh
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
```

### 5.3 Chromium Kiosk Service

```ini
# /etc/systemd/system/chromium-kiosk.service
[Unit]
Description=Chromium Kiosk
After=weston-kiosk.service network.target
Wants=weston-kiosk.service

[Service]
ExecStartPre=/usr/bin/sleep 3
ExecStart=/usr/local/bin/chromium-kiosk.sh
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
```

```bash
#!/usr/local/bin/chromium-kiosk.sh
# Sets KIOSK_URL based on selected mode (hermes/openclaw/hybrid)
# then launches chromium in kiosk mode:
chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-features=Translate \
  --start-fullscreen \
  --app="$KIOSK_URL"
```

---

## 6. LM Studio Integration (First-Class Provider)

LM Studio is a **first-class provider** in DuckBotOS — installed by default, with UI for URL input and model selection.

### 6.1 Headless Install (`llmster`)

LM Studio provides a headless daemon called `llmster` for server environments:

```bash
# Install llmster (recommended for DuckBotOS)
curl -fsSL https://lmstudio.ai/install.sh | bash

# This installs:
#   ~/.local/bin/lms          # CLI tool
#   ~/.local/share/lm-studio/ # models, config

# Start the daemon
lms daemon up

# The REST API is now available on port 1234
# OpenAI-compatible endpoints: /v1/chat/completions, /v1/models, etc.
```

### 6.2 LM Studio REST API (Port 1234)

**Base URL:** `http://127.0.0.1:1234`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List downloaded models |
| `/v1/chat/completions` | POST | Chat completion (OpenAI-compatible) |
| `/v1/completions` | POST | Text completion (OpenAI-compatible) |
| `/v1/embeddings` | POST | Embeddings |
| `/v1/models/{id}/load` | POST | Load a model into memory |
| `/v1/models/{id}/unload` | POST | Unload a model |
| `/v1/download` | POST | Download a model from HuggingFace |

**JIT Loading:** When JIT is on (default), calling an inference endpoint auto-loads the model if not already in memory. When off, you must explicitly `POST /v1/models/{id}/load` first.

**Authentication:** Bearer token via `LMSTUDIO_API_KEY` env var (set in `~/.hermes/config.yaml` or `/etc/openclaw/providers.yaml`).

### 6.3 LM Studio OS Integration

```bash
# User service for auto-start (systemd user)
# ~/.config/systemd/user/lmstudio.service
[Unit]
Description=LM Studio llmster daemon
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=%h/.local/bin/lms daemon up
Restart=always
RestartSec=10
Environment="LMSTUDIO_API_KEY=%any_provided_key%"

[Install]
WantedBy=default.target
```

**Provider config example** (for Hermes `config.yaml` or OpenClaw `providers.yaml`):
```yaml
providers:
  - name: lm-studio
    type: openai-compatible
    api_key: "${LMSTUDIO_API_KEY:-local}"
    base_url: http://127.0.0.1:1234/v1
    default_model: null  # user selects at runtime
    models:
      - id: null  # populated from /v1/models at startup
        required_capabilities: [chat]
```

### 6.4 Model Selection UI

DuckBotOS includes a model selection screen in the first-boot wizard:

1. Lists models downloaded via `GET /v1/models`
2. User picks default model (can change later)
3. Model path stored in provider config

---

## 7. BrowserOS Integration (Default Browser)

BrowserOS is the **default browser** in DuckBotOS, used exclusively for the kiosk display.

### 7.1 What is BrowserOS

BrowserOS is an open-source Chromium fork (`AGPL v3`) with native AI agent support. It provides:
- Chrome DevTools Protocol (CDP) for agent control
- MCP server integration
- Built-in AI agent loop (Bun runtime)
- Local model support via Ollama

**Repo:** https://github.com/browseros-ai/BrowserOS

### 7.2 Linux Install

BrowserOS provides a `.deb` package for Debian/Ubuntu:

```bash
# Download and install BrowserOS .deb
curl -fsSL https://browseros.ai/download/linux | bash
# Or manually:
# wget https://github.com/browseros-ai/BrowserOS/releases/latest/download/browseros_amd64.deb
# sudo apt install ./browseros_amd64.deb
```

For the ISO build, the `.deb` is added to the custom APT repository or bundled directly in the live-build packages.

### 7.3 Set as Default Browser

After install, register BrowserOS as the default browser:

```bash
# Via xdg-settings (correct Ubuntu way)
xdg-settings set default-web-browser browseros.desktop

# Via update-alternatives (fallback)
sudo update-alternatives --install \
  /usr/bin/x-www-browser x-www-browser /usr/bin/browseros 100

# Verify
xdg-settings get default-web-browser  # → browseros.desktop
```

### 7.4 BrowserOS Kiosk Mode

```bash
# /usr/local/bin/browseros-kiosk.sh
#!/bin/bash
export BROWSEROS_KIOSK_URL="${KIOSK_URL:-http://127.0.0.1:9119}"
export BROWSEROS_HEADLESS=false

# Launch BrowserOS in app mode (kiosk)
browseros \
  --app="$BROWSEROS_KIOSK_URL" \
  --kiosk \
  --noerrdialogs \
  --start-fullscreen \
  --disable-features=Translate \
  --window-size=1920,1080
```

**For the ISO:** BrowserOS replaces `chromium-browser` in the kiosk service. The `browseros-kiosk.service` mirrors `chromium-kiosk.service` but launches BrowserOS instead.

### 7.5 BrowserOS MCP

BrowserOS exposes an MCP server (port 9003) that can be connected to both Hermes and OpenClaw for browser automation. This enables the agent to control the browser programmatically.

```yaml
# In OpenClaw providers.yaml:
mcp_servers:
  - name: browseros
    command: browseros-cli
    args: [--mcp]
    # Or connect via HTTP to BrowserOS MCP port 9003
```

---

## 8. `Newest Desktop Control` Integration

`Newest Desktop Control` is a Rust MCP server that gives the agent full desktop control via AT-SPI2 (accessibility bus) and Wayland portals. This is the bridge that lets agents click buttons, type text, read screen content, and manage windows.

**Repo:** https://github.com/Newest Desktop Control (Lobster Edition)

```ini
# /etc/systemd/system/Newest Desktop Control.service
[Unit]
Description=Computer Use Linux MCP Server
After=network.target

[Service]
ExecStart=/usr/local/bin/Newest Desktop Control --port 9600
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
```

**Usage:** Both Hermes and OpenClaw connect to `http://127.0.0.1:9600` as MCP clients. The agent can then issue commands like:
- `computer_use.desktop_click(x=512, y=384)`
- `computer_use.desktop_type("hello world")`
- `computer_use.screenshot()`

---

## 9. Dual-Agent IPC Bus

When both Hermes and OpenClaw are installed (Both mode), they communicate via a Unix socket IPC bus:

**Socket:** `/run/hermes-claw/agent-bus.sock`
**Protocol:** JSON-RPC 2.0

```
[Hermes Gateway]  ←→  agent-bus.sock  ←→  [OpenClaw Gateway]
                           ↑
                           ↓
              [Newest Desktop Control MCP on port 9600]
```

**IPC calls available:**
- `hermes.spawn_task(task)` → OpenClaw verifies
- `openclaw.delegate_to_hermes(task)` → Hermes executes
- `agent.status()` → returns running state of both agents
- `agent.migrate(from, to)` → migrate workspace (Hermes `claw migrate`)

---

## 10. Build System (Forking cxlinux-ai/cx-distro)

### 10.1 Why Fork

CX Linux's `cx-distro` provides a production-ready ISO build pipeline using `live-build`. Key features we inherit:
- Reproducible `.iso` builds
- Preseed automation for OEM installs
- Signed APT repository with GPG key management
- Meta-packages (`cx-core`, `cx-full`) as templates for our `hermesos-meta`, `openclawos-meta`, etc.
- SBOM generation (CycloneDX/SPDX)
- AppArmor profiles + Firejail sandboxing

### 10.2 Directory Structure (Forked from cx-distro)

```
duckbotos/
├── iso/
│   ├── live-build/
│   │   ├── auto/
│   │   │   ├── build      # live-build auto script
│   │   │   ├── clean
│   │   │   └── config
│   │   └── config/
│   │       ├── package-lists/
│   │       │   ├── hermes.list         # Hermes-only packages
│   │       │   ├── openclaw.list       # OpenClaw-only packages
│   │       │   └── both.list           # Both-mode packages
│   │       ├── includes/
│   │       │   └── packages/
│   │       │       ├── hermesos-meta/  # Meta-package
│   │       │       ├── openclawos-meta/
│   │       │       ├── hermesos-hybrid-meta/
│   │       │       ├── hermesos-kiosk/
│   │       │       ├── Newest Desktop Control/
│   │       │       ├── browseros/      # BrowserOS .deb
│   │       │       └── lm-studio/      # llmster install
│   │       └── hooks/
│   │           └── live/chroot-early/
│   │               └── 05-kiosk-setup.chroot
│   └── preseed/
│       ├── hermes-autoinstall.yaml
│       ├── openclaw-autoinstall.yaml
│       └── both-autoinstall.yaml
├── packages/
│   ├── duckbotos-meta/           # Base install (shared by all modes)
│   ├── hermesos-meta/            # Hermes-only meta-package
│   ├── openclawos-meta/          # OpenClaw-only meta-package
│   ├── hermesos-hybrid-meta/     # Both-mode meta-package
│   ├── hermesos-kiosk/           # Weston + Chromium/BrowserOS kiosk
│   ├── Newest Desktop Control/       # MCP desktop control server
│   ├── browseros/                # BrowserOS .deb packaging
│   └── lm-studio/                # llmster + systemd user service
├── repository/
│   └── apt/                      # Custom APT repo (signed, deb822 format)
├── branding/
│   ├── plymouth/                 # DuckBotOS boot splash
│   ├── wallpaper.png
│   └── icons/
├── scripts/
│   ├── build.sh                  # Master build script
│   ├── firstboot.sh              # Post-install provisioning
│   └── lm-studio-setup.sh        # llmster install + model cache prep
├── sbom/                         # CycloneDX + SPDX SBOMs
└── .github/workflows/
    └── build-iso.yml             # GitHub Actions CI
```

### 10.3 Replacing cx-terminal with Hermes

CX Linux uses a Rust-based `cx-terminal` agent. DuckBotOS replaces this in the fork:

1. **Remove** `packages/cx-terminal/` from the live-build config
2. **Add** `packages/hermesos-meta/` with a `DEBIAN/control` that depends on:
   - `hermes-agent` (or `hermes` CLI from NousResearch)
   - `Newest Desktop Control`
   - `weston`, `chromium-browser` (or `browseros`)
3. **Add** hook: `config/hooks/live/chroot-early/05-hermes-install.chroot` that:
   - Downloads and installs Hermes from official source
   - Generates `~/.hermes/config.yaml` with default providers
   - Sets up systemd services

### 10.4 Meta-packages

**duckbotos-meta** (all modes):
```
Depends: ubuntu-base, weston, network-manager, firejail, apparmor
```

**hermesos-meta** (Hermes-only):
```
Depends: duckbotos-meta, hermes-agent, lm-studio (or llmster),
         browseros, hermesos-kiosk
```

**openclawos-meta** (OpenClaw-only):
```
Depends: duckbotos-meta, openclaw, openclawos-plugin,
         lm-studio (or llmster), browseros, openclawos-kiosk
```

**hermesos-hybrid-meta** (Both):
```
Depends: duckbotos-meta, hermes-agent, openclaw, openclawos-plugin,
         lm-studio (or llmster), browseros, hermesos-hybrid-kiosk
Conflicts: hermesos-meta, openclawos-meta
```

### 10.5 live-build Auto Script

```bash
#!/bin/sh
# iso/live-build/auto/build
set -e

lb build noauto \
    "${@}"
```

### 10.6 Package List (hermes.list example)

```
# hermes.list — packages for Hermes-only mode
# Base
ubuntu-desktop-minimal
weston
network-manager
firejail
apparmor

# Hermes agent
hermes-agent

# LM Studio headless (llmster)
lm-studio-headless

# BrowserOS
browseros

# Kiosk
hermesos-kiosk

# Desktop control
Newest Desktop Control
```

---

## 11. Installer (Subiquity OEM Mode)

DuckBotOS uses Ubuntu's Subiquity installer in OEM mode with `autoinstall.yaml`.

### 11.1 OEM Mode

OEM mode shows a "Preparing for shipping" screen on first boot, then runs the autoinstall. For DuckBotOS, the OEM setup:
1. ISO boots to OEM install screen
2. OEM installer runs Subiquity with `autoinstall.yaml` embedded in the ISO
3. Autoinstall configures disk, user, and **agent selection**
4. On first boot, first-run wizard runs for provider/model setup

### 11.2 autoinstall.yaml Structure

```yaml
# iso/preseed/hermes-autoinstall.yaml
version: 1
identity:
  hostname: duckbotos
  username: duckbot
  password: <crypted-password>
early-commands:
  - systemctl stop subiquity-submit-logs.service 2>/dev/null || true
late-commands:
  # Register DuckBotOS OEM identity
  - curtin in-target --target /target systemctl enable oem-config.service
  # Copy agent selection to post-install
  - echo 'DUCKBOTOS_MODE=hermes' > /target/etc/duckbotos mode
storage:
  layout:
    name: lvm
    gut: all
```

### 11.3 Agent Selection (whitelabel source-selection)

Ubuntu's Subiquity supports `source-selection` hooks for custom installer pages. For DuckBotOS:

1. Custom `oem-config.service` runs on first boot (not during OEM install)
2. Shows a simple TUI or web page: "Choose your agent:"
   - **Hermes** — NousResearch Hermes agent (default)
   - **OpenClaw** — OpenClaw gateway
   - **Both** — Hybrid mode with session picker
3. Selection is written to `/etc/duckbotos/mode`
4. systemd presets enable the appropriate services

**Simpler approach (Phase 1):** Skip custom installer page. Three separate ISOs:
- `duckbotos-hermes-x86_64.iso` — Hermes-only
- `duckbotos-openclaw-x86_64.iso` — OpenClaw-only
- `duckbotos-both-x86_64.iso` — Both mode

### 11.4 First-Boot Wizard

After OS install, the first-boot wizard runs:

1. **Provider setup** — API key entry for cloud providers (OpenAI, MiniMax, Grok, OpenRouter)
2. **LM Studio setup** — local URL (default `http://127.0.0.1:1234`), model selection
3. **Default model** — pick from available LM Studio models or cloud defaults
4. **Channel selection** — Telegram, CLI, etc.

Configuration is written to ``~/hermes-config.json` or `~/.openclaw/openclaw.json`.

---

## 12. Provider Aggregation

DuckBotOS includes all providers from both Hermes and OpenClaw:

### 12.1 Hermes Providers (via `hermes` CLI)
- MiniMax (MiniMax-M3, MiniMax-M2.7, MiniMax-M2.5)
- OpenAI (GPT-4o, GPT-4o-mini, o3, o4-mini)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Grok (xai/grok-4.3, grok-4.20-beta)
- OpenRouter (mixed free/paid models)
- LM Studio (local, via `http://127.0.0.1:1234/v1`)

### 12.2 OpenClaw Providers (via `openclaw` gateway)
- MiniMax (minimax-portal/MiniMax-M3, M2.7, M2.5)
- Grok / xai (xai/grok-4.3, xai/grok-4.20-beta)
- Free GLM (zai/glm-4.7-flash, zai/glm-4.6v-flash — free tier)
- OpenAI (via OpenAI API)
- Anthropic (via Anthropic API)
- OpenRouter (free tier models)
- LM Studio (local, via OpenAI-compatible endpoint)
- Any OpenAI-compatible API

### 12.3 Unified Provider Config

```yaml
# /etc/duckbotos/providers.yaml
# All providers available in DuckBotOS
providers:
  # Cloud providers
  - name: minimax
    type: openai-compatible
    api_key_env: MINIMAX_API_KEY
    base_url: https://api.minimaxi.chat/v1
    default_model: minimax-portal/MiniMax-M2.7

  - name: openai
    type: openai-compatible
    api_key_env: OPENAI_API_KEY
    base_url: https://api.openai.com/v1
    default_model: gpt-4o

  - name: anthropic
    type: anthropic
    api_key_env: ANTHROPIC_API_KEY
    default_model: claude-sonnet-4-20250514

  - name: grok
    type: openai-compatible
    api_key_env: XAI_API_KEY
    base_url: https://api.x.ai/v1
    default_model: xai/grok-4.3

  - name: openrouter
    type: openai-compatible
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1
    default_model: google/gemini-2.0-flash-exp

  # Local provider
  - name: lm-studio
    type: openai-compatible
    api_key: local
    base_url: http://127.0.0.1:1234/v1
    default_model: null  # user selects at runtime
```

---

## 13. GDM Session Picker (Both Mode)

For "Both" mode, GDM is customized to show three sessions:

**Files changed:**
- `/usr/share/xsessions/duckbotos-hermes.desktop` — Hermes session
- `/usr/share/xsessions/duckbotos-openclaw.desktop` — OpenClaw session
- `/usr/share/xsessions/duckbotos-hybrid.desktop` — Hybrid GNOME session

```ini
# /usr/share/xsessions/duckbotos-hermes.desktop
[Desktop Entry]
Name=DuckBotOS (Hermes)
Comment=AI-first OS with Hermes agent
Exec=/usr/local/bin/duckbotos-launch hermes
Type=Application
```

GDM theme customized with DuckBotOS branding (colors, logo).

---

## 14. Security

### 14.1 Sandboxing

- **Firejail** — per-service sandboxing (Hermes gateway, OpenClaw gateway)
- **AppArmor** — kernel-level MAC for system services
- **Chromium** — sandboxed in kiosk mode, no user interaction required

### 14.2 Credential Storage

- API keys stored in ``~/hermes-config.json` / `~/.openclaw/openclaw.json`
- Permissions: `chmod 600` on config files (user-only read)
- **Future:** TPM-backed credential store (`/etc/hermes-claw/credentials/`)
- LM Studio API key: optional Bearer auth on port 1234

### 14.3 Network

- All cloud API traffic over HTTPS
- LM Studio REST API bound to `127.0.0.1:1234` (localhost only) — not exposed
- `Newest Desktop Control` MCP on port 9600 (localhost only)
- Firewall: default deny outbound, allow HTTPS (443) only for cloud APIs

---

## 15. What's Inherited vs. Built Fresh

| From cxlinux-ai/cx-distro | Built Fresh |
|---------------------------|-------------|
| live-build ISO pipeline | Kiosk shell (Weston + Chromium/BrowserOS) |
| Preseed automation | Agent selection page / three ISOs |
| APT repo tooling | First-boot wizard |
| Meta-package structure | GDM session picker |
| SBOM generation | Dual-agent IPC bus |
| AppArmor + Firejail profiles | Branding / Plymouth theme |
| Security defaults | All documentation |

## 16. Deeper Documentation References

This document covers the high-level stack. For detailed specifications, see:

| Doc | What It Covers |
|-----|---------------|
| `docs/phase7-implementation.md` | Full Tier 1 feature specs (F1–F5): NL Package Manager, Resource Orchestrator, Multi-Agent Pipeline, Activity Graph, Voice — CLI contracts, systemd units, data flows, checklists |
| `docs/computer-use.md` | AT-SPI2 + Wayland portal MCP server, Newest Desktop Control service, security model |
| `docs/dual-agent-ipc.md` | JSON-RPC bus design, D-Bus integration, shared credentials, tool locking, GDM picker, conflict resolution rules |
| `docs/build-guide.md` | Full fork → VM → packages → ISO build step-by-step |
| `docs/system-boot-flow.md` | Complete boot sequence: service order, ports, failure handling |
| `docs/lm-studio.md` | llmster headless install, systemd service, OpenAI-compatible API (port 1234) |
| `docs/browseros.md` | .deb install, default browser setup, kiosk launcher, MCP server (port 9003) |
| `docs/cx-linux-fork.md` | What changed from cx-distro: Debian→Ubuntu Noble, live-build config, package structure |
| `docs/providers.md` | Full provider matrix: all cloud + local providers, unified providers.yaml |
| `docs/installer.md` | Three ISOs, Subiquity OEM mode, autoinstall.yaml, first-boot wizard |

---

*Architecture v0.2 — 2026-06-29. All cross-references verified against live docs.*