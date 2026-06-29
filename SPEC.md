# DuckBotOS — SPEC.md

> Custom Ubuntu-based OS distro with Hermes + OpenClaw as the primary agent surface.
> Deep OS integration for AI-first computing.

---

## 1. Vision

**What it is:** A Ubuntu-derived OS where an AI agent is the first thing that boots, owns the display, and mediates between the user and the machine — not an app you open, but the environment you live in.

**Inspiration:** NVIDIA DGX Spark (Ubuntu-based DGX OS for AI desktops) and RTX Spark (agent runtime on Windows) — but **agent-first, Linux-native**. We do for Hermes + OpenClaw what DGX OS does for the AI dev stack.

**Core metaphor:** Your OS has an intelligent butler (Hermes or OpenClaw) who lives in every room of the house, knows how everything works, and can operate anything in it.

---

## 2. Why This Isn't From Scratch

Duckets' clarification: search existing projects first — there may be one for OpenClaw to pull from. There is.

### 2.1 Reference Projects Identified

| Project | License | What we take from it |
|---------|---------|------------------------|
| **cxlinux-ai/cx-distro** | BSL 1.1 (free for personal; converts to Apache 2032) | **ISO build pipeline:** `live-build`, preseed, Debian packaging, APT repo, SBOM, AppArmor/Firejail. PRIMARY INHERITANCE. |
| **cxlinux-ai/cx-core** (CX Terminal) | BSL 1.1 | Natural-language OS admin UX pattern; Rust daemon with Unix-socket IPC. |
| **thesysdev/openclaw-os** | TBD | **The OpenClaw web workspace** — Next.js UI served at `/plugins/openclawos`. THIS becomes our "OpenClaw desktop." |
| **nousresearch/hermes-agent** | MIT | Agent core. Ships **Hermes Web Dashboard** at `http://127.0.0.1:9119` + Hermes Desktop (Electron app). We use the web dashboard. |
| **Newest Desktop Control (Lobster Edition)** | TBD | **Rust MCP server for AT-SPI2 + Wayland portal desktop control.** This is the bridge letting agents *act on* the desktop — click, type, window-manage. CRITICAL for "deeply integrated." |
| **agentkernel/openclaw-desktop** | TBD | First-run wizard UX (provider → channel → gateway). |
| **MYusufY/agenticcore** | GPLv2 (Tiny Core Linux) | Reference only (Tiny Core too minimal). |
| **nextain/naia-os** | TBD | Tauri/Rust desktop shell reference. |
| **NVIDIA DGX OS** (DGX Spark Linux) | Proprietary | Conceptual reference (Ubuntu remix + AI stack). |
| **Bytebot** | TBD | Docker-virtual-desktop concept (agent gets its own isolated desktop). |
| **Fedora AI OS proposal** | N/A | GNOME-native agent design, not a shell replacement. |
| **Hermes `hermes claw migrate`** | (function of Hermes) | Hermes already imports OpenClaw state — they share memory/skill format. |

### 2.2 Big Insight — The "Desktop" Is Already a Web Page

**Both Hermes and OpenClaw already ship web-based frontends:**
- **Hermes** → `http://127.0.0.1:9119` (Hermes Web Dashboard — chat-first, multiple sessions, TUI embedded)
- **OpenClaw** → `http://127.0.0.1:18789/plugins/openclawos` (openclaw-os — Live React components, persistent apps)

This collapses the major UI scope. We don't build a custom desktop shell from scratch. We need:
1. A kiosk-mode Wayland session that auto-loads the agent's web URL
2. systemd services for both gateways + `Newest Desktop Control` MCP server
3. An installer that lets users pick which agent(s) to install
4. A login-screen session picker for the running config

**The OS-integration work is plumbing (startup, installer, dual-agent IPC, desktop control via Newest Desktop Control), not UI.**

### 2.3 What We Inherit vs. Build From Scratch

**Inherited (from CX Linux):**
- All ISO build infrastructure (live-build, preseed, squashfs)
- All Debian packaging (cx-core, cx-full meta-packages)
- All SBOM/CycloneDX/SPDX generation
- All AppArmor profiles + Firejail sandboxing
- All security defaults (sysctl, nftables, SSH hardening)
- First-boot idempotent provisioning

**Built from scratch:**
- The kiosk shell wrapper (`weston.service` + `chromium.service`)
- The agent-selector installer page (Subiquity OEM mode)
- The dual-agent IPC bus (`/run/hermes-claw/agent-bus.sock`)
- The session picker UI for "Both" mode
- The first-run wizard (provider → channel → model selection)
- Branding / Plymouth theme / wallpaper
- Documentation

**Replaced:**
- CX Linux's Rust `cx-terminal` agent → swap for Hermes (or OpenClaw)
- CX Linux's custom AI Side-Panel → swap for openclaw-os + Hermes dashboard

---

## 3. Core Features

### 3.1 Modes (Installer Choice)

| Mode | What Installs | What Boots |
|------|--------------|------------|
| **Hermes-only** | Hermes + Hermes web dashboard + `Newest Desktop Control` MCP | Weston kiosk → Chromium → `http://127.0.0.1:9119` |
| **OpenClaw-only** | OpenClaw + openclaw-os plugin + `Newest Desktop Control` MCP | Weston kiosk → Chromium → `http://127.0.0.1:18789/plugins/openclawos` |
| **Both** | Both, with session picker | Login GDM: pick "Hermes" / "OpenClaw" / "Hybrid" per session |

### 3.2 Agent Capabilities (Both Modes)

Both modes give the agent these OS-level capabilities (handled by the agent's own toolset, plus `Newest Desktop Control` MCP for desktop control):

- **Package management** — `apt`, `snap`, `flatpak` via natural language
- **Service management** — systemd units, startup apps
- **File system** — home directory, external drives, cloud mounts
- **Process management** — top, kill, htop, background jobs
- **Network** — WiFi, VPN, firewall rules
- **Display** — brightness, resolution, multi-monitor
- **User accounts** — add/remove users, sudo access (with policy gates)
- **Cron / scheduled tasks** — manage via natural language
- **Logs** — journalctl reading and summarization
- **Desktop control** — `Newest Desktop Control` lets the agent click, type, screenshot
- **System control** — lockscreen, sleep, restart, shutdown

### 3.3 OpenClaw Integration (Both Mode + Dual-Agent IPC)

When both are installed, OpenClaw Gateway + openclaw-os plugin run as system services; Hermes runs alongside (different ports). Shared infrastructure:
- `Newest Desktop Control` MCP server — shared desktop control backend
- D-Bus session bus — both can register and call methods
- IPC bus `/run/hermes-claw/agent-bus.sock` (JSON-RPC 2.0)
- `hermes claw migrate` — Hermes can import OpenClaw's workspace

### 3.4 Installer

Custom Ubuntu OEM installer using Subiquity `autoinstall.yaml` + `whitelabel.yaml`:
1. Standard Ubuntu flow: language, keyboard, network, user, hostname
2. **Agent Selection page** (custom Ubiquity page or whitelabel source-selection):
   - **Hermes** (default)
   - **OpenClaw**
   - **Both** (with session picker)
3. **Model selection**: API key entry (OpenAI, MiniMax, OpenRouter) OR local model path (llama.cpp / GGUF)
4. Post-install first-boot script registers services, opens dashboard

Alternative simpler approach: prototype ISOs via Cubic with pre-installed agents + first-boot setup wizard.

### 3.5 Startup

```
GRUB → Kernel → systemd
  → hermes.service / openclaw-gateway.service / both
  → Newest Desktop Control.service (MCP on port, app control)
  → weston-kiosk.service  (Wayland compositor)
  → chromium-kiosk.service  (fullscreen dashboard URL)
  → Agent active on login
```

For "Both" mode, GDM shows three sessions on login:
- **Hermes Desktop** → boots Hermes kiosk
- **OpenClaw Desktop** → boots OpenClaw kiosk
- **Hybrid Workstation** → boots GNOME with both agents accessible from a side panel (replace GNOME Shell's panel with openclaw-os side panel)

---

## 4. Technical Architecture

### 4.1 Base OS

```
Ubuntu 24.04 LTS (Noble Numbat)
├── linux-image-generic (HWE kernel, NVIDIA/AMD drivers enabled)
├── wayland / weston (kiosk compositor)
├── gnome-shell (fallback desktop)
├── systemd (system + user services)
└── xorg (fallback for non-Weston apps)
```

### 4.2 Agent Layers

```
HermesAgent/                          OpenClawAgent/
├── /usr/lib/hermes/                  ├── /opt/openclaw/
├── ~/.hermes/                        ├── ~/.openclaw/extensions/
├── systemd/hermes.service            ├── systemd/openclaw-gateway.service
├── /etc/hermes/weston-kiosk.sh       ├── /etc/openclaw/weston-kiosk.sh
└── /etc/hermes/chromium-kiosk.sh     └── /etc/openclaw/chromium-kiosk.sh

Shared/
├── /usr/bin/Newest Desktop Control     # Rust MCP for desktop control
├── /run/hermes-claw/agent-bus.sock # JSON-RPC IPC bus
└── /etc/hermes-claw/credentials/   # TPM-backed shared secrets
```

### 4.3 Desktop Shell

```
[weston-kiosk.service]
└── [chromium-kiosk.service]
    ├── --kiosk
    ├── --noerrdialogs
    ├── --disable-features=Translate
    ├── --window-size=1920,1080
    ├── --start-fullscreen
    └── URL  =  http://127.0.0.1:9119                 (Hermes)
            OR http://127.0.0.1:18789/plugins/openclawos  (OpenClaw)
            OR http://localhost/agent-picker              (Hybrid mode login)
```

### 4.4 Dual-Agent IPC Bus

```
[Hermes Gateway]   ⇄  Unix Socket  ⇄  [OpenClaw Gateway]
                        /run/hermes-claw/agent-bus.sock
        ↑
        │
[Newest Desktop Control MCP server on port 9600]
        ↑
        │
    Both agents connect as MCP clients → desktop control via AT-SPI2 + portals
```

Plus D-Bus session bus for additional agent inter-call, and Hermes `claw migrate` for state import.

### 4.5 Login & Session Picker

In "Both" mode, GDM is customized (theme + sessions.list) to show three sessions:
- **Hermes Desktop** — boots Hermes kiosk
- **OpenClaw Desktop** — boots OpenClaw kiosk
- **Hybrid Workstation** — boots GNOME Shell with both agent panels in a side dock

---

## 5. Build System

### 5.1 ISO Builder
**Tool**: Fork `cxlinux-ai/cx-distro` build pipeline (uses Debian `live-build`).
- VM-based customization
- Produces bootable `.iso`
- Preseed for OEM installation
- SquashFS layers

**Why fork CX Linux vs raw debootstrap**: Their pipeline is production-ready, well-documented (live-build + preseed + meta-packages + SBOM), and targets the same Ubuntu base. Saves weeks of build infrastructure work.

### 5.2 Build Machine
- **Primary:** Linux VM (Ubuntu 24.04) — `live-build` won't run on macOS
- **CI:** GitHub Actions (`ubuntu-24.04` runner) for reproducible ISO builds
- **Output:** GitHub Releases (`.iso` + `.sha256` + SBOM)

### 5.3 Package Management
- `hermesos-meta` — pulls Hermes + dependencies
- `openclawos-meta` — pulls OpenClaw + openclaw-os plugin
- `hermesos-hybrid-meta` — both with session picker
- `hermesos-kiosk` — weston + chromium kiosk config
- `Newest Desktop Control` MCP package
- Custom APT repo: `apt.hermes-os.dev`

---

## 6. What Changes From CX Linux

| CX Linux | DuckBotOS |
|----------|----------|
| `cx-terminal` (Rust agent) | Hermes (NousResearch) OR OpenClaw |
| `cx ask` command | `hermes` or `openclaw` command |
| Custom AI Side-Panel (Ctrl+Space) | openclaw-os sidebar (already shipped) |
| CX Linux branding | DuckBotOS branding (rebrand assets) |
| BSL 1.1 license | Apache 2.0 (clean inheritance: we wrote our scripts fresh; fork is permitted under BSL; combined with MIT Hermes/OpenClaw contributions makes Apache 2.0 viable) |

We inherit: AppArmor profiles, Firejail sandboxing, security defaults (sysctl, nftables, SSH hardening), SBOM, all ISO build infrastructure.

---

## 7. Out of Scope (v1)

- Multi-user simultaneous sessions (single user at a time)
- Mobile companion app
- On-device model fine-tuning
- Custom Wayland compositor
- Hardware-specific drivers beyond standard Ubuntu HWE

---

## 8. Open Questions

1. **GPU target** — x86_64 PC with NVIDIA, AMD, or CPU-only?
2. **Models** — Self-hosted llama.cpp/Ollama at install time, or pull API keys from cloud?
3. **Memory persistence** — local SQLite for Hermes skills, or sync to cloud?
4. **Boot type** — Live USB, full disk install, both?
5. **Branding** — Name: "DuckBotOS" / "AgentOS" / "ClawOS" / something else?
6. **License** — Combined inheritance from CX (BSL 1.1) + Hermes (MIT) + OpenClaw (MIT). Plan: Apache 2.0 + attribution.
7. **Repo location** — Public GitHub org/name? (Current working name: `duckets-ai/hermesos` — unconfirmed)

---

## 9. Phases

### Phase 1 — Research & Planning (NOW) ✅
- ✅ Searched web + GitHub for existing AI-OS projects
- ✅ Found: CX Linux, Hermes dashboard, openclaw-os, Newest Desktop Control, agentkernel/openclaw-desktop
- ✅ Drafted SPEC.md (this file)
- ✅ Drafted README.md (GitHub-ready)
- ✅ Drafted OPEN-ISSUES.md
- ⏳ Wait on Duckets' decisions on branding / license / repo

### Phase 2 — Minimal Bootable (Linux VM)
- Set up Linux build VM (UTM? Vagrant?)
- Fork cxlinux-ai/cx-distro
- Replace `cx-terminal` with shell that installs Hermes on first boot
- Build ISO with **Hermes-only mode**, verify boots to Hermes dashboard

### Phase 3 — Installer Choice
- Custom Subiquity OEM page (or whitelabel source-selection) with agent selection
- Three packages: hermesos-meta, openclawos-meta, hermesos-hybrid-meta
- First-boot wizard for provider/model config
- Verify install of all three modes

### Phase 4 — Dual Mode
- GDM theme with three session entries
- Agent bus IPC daemon
- Shared credential store (TPM-backed when available)
- `Newest Desktop Control` MCP server running as system service

### Phase 5 — Polish & Release
- Plymouth boot theme
- Wallpaper + branding
- GitHub Actions ISO build CI
- MkDocs documentation site
- v0.1.0 release

---

## 10. Repo Layout

```
hermesos/
├── README.md
├── LICENSE                          # Apache 2.0
├── SPEC.md
├── docs/
│   ├── architecture.md
│   ├── dual-agent.md
│   └── installer.md
├── iso/                             # Forked from cxlinux-ai/cx-distro
│   ├── live-build/
│   ├── preseed/
│   └── packages/
│       ├── hermesos-meta/
│       ├── openclawos-meta/
│       ├── hermesos-hybrid-meta/
│       ├── hermesos-kiosk/
│       └── hermesos-sources.list   # APT repo config
├── shell/
│   ├── weston-kiosk.service
│   ├── chromium-kiosk.service
│   ├── agent-picker.html           # Hybrid mode login dropdown
│   └── plymouth/                    # Boot theme
├── dual-agent/
│   ├── agent-bus.sock              # JSON-RPC bridge
│   └── credentials/                # TPM-backed keyring
├── branding/
│   ├── wallpaper.png
│   └── icon.svg
├── .github/workflows/
│   └── build-iso.yml
└── scripts/
    ├── build.sh                    # Master ISO build
    └── firstboot.sh                # Post-install setup
```

---

*SPEC.md — DuckBotOS project. Status: research complete, architectural decision made (kiosk mode + forked CX Linux build pipeline), planning finalized.*
