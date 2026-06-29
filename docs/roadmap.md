# DuckBotOS Roadmap

**DuckBotOS** is an Ubuntu-based, agent-first operating system where Hermes and OpenClaw are first-class desktop citizens. The desktop *is* the agent.

- **Base**: Ubuntu 24.04 Noble (forked from cxlinux-ai/cx-distro)
- **Build system**: live-build + custom ISO pipeline
- **Agents**: Hermes (primary conversational) + OpenClaw (secondary orchestration + tools)
- **First-class components**: LM Studio (port 1234), BrowserOS (Chromium kiosk)
- **Session model**: GDM picker (Hermes / OpenClaw / Hybrid)
- **Target users**: Developers, researchers, power users who want an agent-native desktop
- **Licensing**: BSL 1.1 (build pipeline), Apache 2.0 (DuckBotOS original code)

---

## Overview

- **Release cadence**: ~monthly minor releases, quarterly major milestones
- **Versioning**: Semantic Versioning (`MAJOR.MINOR.PATCH`)
  - `MAJOR`: Breaking changes or Tier 3 research features
  - `MINOR`: New Tier 1/2 features or significant UX changes
  - `PATCH`: Bug fixes, security updates, packaging improvements
- **Release channels**:
  - `alpha`: Unstable, bleeding-edge, for core contributors
  - `beta`: Pre-release, feature-complete, for early adopters
  - `stable`: Production-ready, supported
- **Support policy**: Current stable + one previous minor release receive security and critical bug fixes

---

## v0.1.0 "Hermes Alpha" — Target: Q3 2026

**Goal**: First bootable ISO that runs Hermes agent on a kiosk desktop.

### What's included

- [ ] Fork `cxlinux-ai/cx-distro` → `Franzferdinan51/duckbotos`
- [ ] Change base OS from Debian Trixie to Ubuntu 24.04 Noble
- [ ] Remove `cx-terminal` (not applicable), add Hermes install script
- [ ] Build Hermes-only ISO (`cx-hermes` variant)
- [ ] Live USB boots to Weston kiosk → Chromium kiosk
- [ ] Chromium loads Hermes dashboard (local web app or hosted)
- [ ] Hermes CLI accessible from terminal (`Ctrl+Alt+T`)
- [ ] LM Studio bundled, daemon starts on boot, listening on port 1234
- [ ] BrowserOS as default browser (APT package from CDN)
- [ ] Basic LM Studio model browser (available models, GPU offload status)
- [ ] Plymouth boot theme with DuckBotOS branding
- [ ] API key entry via CLI: `hermes-cli config set provider minimax --api-key KEY`
- [ ] ISO builds successfully via `make iso-hermes`

### What's NOT included
- OpenClaw agent
- Dual-agent / hybrid mode
- Full graphical installer
- Any Tier 1 AI features
- Persistence layer
- GPU driver bundling

### Known limitations
- Manual API key configuration only (no UI)
- No persistence (live boot only)
- No GPU drivers (NVIDIA/AMD require manual post-boot install)
- Single ISO variant only (Hermes mode)

---

## v0.2.0 "OpenClaw Landing" — Target: Q3 2026

**Goal**: OpenClaw ISO variant + shared build infrastructure for both agents.

### New in v0.2

- [ ] OpenClaw-only ISO (`cx-openclaw` variant)
  - Same base as Hermes ISO but installs OpenClaw instead
  - OpenClaw gateway service + Telegram/Discord bridges
  - DuckBot Brain MCP server included
  - BrowserOS + OpenClaw browser control integration
- [ ] Common package infrastructure
  - `duckbotos-base` metapackage (shared by both ISOs)
  - `duckbotos-hermes` / `duckbotos-openclaw` split packages
  - Single `.deb` repository structure
- [ ] Live persistence (toram boot)
  - Home directory persistence on USB via `persistence.conf`
  - `cow_paths` configured for full rootfs persistence
- [ ] OpenClaw provider config CLI: `openclaw config`
- [ ] Basic shared CI: GitHub Actions builds both ISOs on every push
- [ ] SHA256 checksums + SBOM included in every ISO

### What's NOT included
- Both-mode ISO
- GDM session picker
- First-boot wizard
- Tier 1 AI features
- Full documentation site

---

## v0.3.0 "The Hybrid Drop" — Target: Q4 2026

**Goal**: Both-mode ISO with GDM session picker + first-boot wizard.

### New in v0.3

- [ ] Both-mode ISO (`cx-both` variant)
  - Installs both Hermes and OpenClaw side-by-side
  - GDM session picker: "Hermes Agent" / "OpenClaw Agent" / "Hybrid Workstation"
  - Shared `/var/lib/duckbotos/` for credentials and config
- [ ] First-boot wizard (GTK or web app in kiosk)
  - Step 1: Mode selection (Hermes / OpenClaw / Both)
  - Step 2: API key entry (per provider, validated)
  - Step 3: Channel + model selection (cascading dropdowns)
  - Step 4: LM Studio setup (server URL, model browser, GPU offload)
  - Step 5: Finishing touches (network, shortcuts, summary)
  - Writes config to `/var/lib/duckbotos/first-boot.yaml`
- [ ] Agent bus IPC daemon
  - Unix socket at `/run/duckbotos/agent-bus.sock`
  - JSON-RPC 2.0 protocol
  - Hermes and OpenClaw can call each other's tools
  - D-Bus session bus integration for notifications
- [ ] Shared credential store
  - `/var/lib/duckbotos/creds/` (0600, owned by `hermesos:duckbotos`)
  - Both agents read the same API keys
  - TPM-backed sealing when hardware is available
- [ ] Plymouth boot theme finalized (DuckBotOS duck logo + progress animation)
- [ ] Wallpaper + icon assets (duck logos, agent icons)
- [ ] `duckbotos-diag` CLI (gathers logs for bug reports)
- [ ] Subiquity OEM autoinstall support — 3 ISOs built from same base

### What's NOT included
- Tier 1 AI features (NL Package Manager, etc.)
- Full `docs.duckbotos.ai` MkDocs site
- Security hardening (AppArmor, firejail, nftables)

---

## v0.4.0 "Feature Day One" — Target: Q4 2026

**Goal**: Ship the five Tier 1 AI flagship features.

### New in v0.4

- [ ] **F1: Natural Language Package Manager** (`hermes-nlpkg`)
  - Daemon: `hermes-nlpkg.service` (D-Bus interface)
  - Resolves natural language requests ("install Firefox but not from snap") → `apt install firefox-esr`
  - Supports: apt, snap, flatpak, pip (auto-detects backend)
  - Intent classifier: "remove X", "update Y", "search for Z"
  - Tool contract: `nlpkg_install`, `nlpkg_remove`, `nlpkg_search`, `nlpkg_update`

- [ ] **F2: Predictive Resource Orchestrator** (`hermesos-watchdog`)
  - Monitors: CPU, RAM, GPU, network via `/proc` + LM Studio API
  - Holt-Winters predictor forecasts resource needs 5–30 min ahead
  - Auto-loads/unloads LM Studio models based on predicted demand
  - Dashboard: `localhost:9120` (netdata + custom panels)
  - Tool contracts: `resource_get`, `resource_predict`, `model_preload`

- [ ] **F3: Multi-Agent Pipeline** (from dual-agent-ipc.md)
  - JSON-RPC over `/run/duckbotos/pipeline.sock`
  - Modes: H→O (Hermes→OpenClaw), O→H, parallel
  - DAG visualization in browser (D3.js)
  - Tool: `pipeline_submit(task, mode, agents)`
  - Session locking prevents agents from stealing each other's tools mid-pipeline

- [ ] **F4: OS-Wide Activity Graph**
  - NetworkX graph engine in `hermesos-graph.service`
  - Walks: `/proc/`, Hermes/OpenClaw event streams, D-Bus
  - Entities: processes, files, network connections, agent thoughts
  - Dashboard: React + D3 at `localhost:9120/graph`
  - Tool: `graph_query(entity, depth, relationship_type)`

- [ ] **F5: Voice-Native Interaction**
  - openWakeWord for always-on, low-CPU wake word detection
  - whisper.cpp for local STT (no cloud)
  - Piper TTS for local, fast responses
  - Voice command router interprets intent from transcribed text
  - Tool contracts: `voice_listen`, `voice_speak`, `voice_command`

- [ ] Basic troubleshooting documentation (`docs/troubleshooting.md`)
- [ ] `duckbotos-reset` factory reset script

### What's NOT included
- Tier 2/3 features
- Full MkDocs documentation site
- GitHub Actions auto-release pipeline

---

## v0.5.0 "Hardening Sprint" — Target: Q1 2027

**Goal**: Security hardening, stability, and release preparation.

### New in v0.5

- [ ] AppArmor profiles for all services (Hermes, OpenClaw, LM Studio, BrowserOS)
- [ ] firejail sandboxing for browser and CLI tools
- [ ] nftables outbound firewall (whitelist-based, per-provider)
- [ ] Audit logging (`/var/log/duckbotos/audit.log`)
- [ ] TPM credential sealing (when hardware available)
- [ ] Encrypted home directory support (LUKS2 + TPM)
- [ ] Kernel hardening (sysctl tuning, secure boot signing)
- [ ] SBOM (SPDX) included in every ISO
- [ ] Reproducible build verification
- [ ] `mkdocs` documentation site live at `docs.duckbotos.ai`
- [ ] Security model document (`docs/security-model.md`)
- [ ] Contributing guide (`docs/contributing.md`)
- [ ] Five Tier 2 features (F6–F10) — see `features.md`
- [ ] v0.5.0 stable release announcement

---

## v1.0.0 "Ship It" — Target: Q2 2027

**Goal**: Production-ready, community-ready, fully documented.

### New in v1.0

- [ ] All Tier 1 + Tier 2 features (F1–F10) shipped and stable
- [ ] Tier 3 research features (F11–F15) scoped and documented
- [ ] GPU driver bundling: NVIDIA CUDA + AMD ROCm packages in separate GPU ISOs
- [ ] Automated kernel updates with secure boot re-signing
- [ ] Release signing (DuckBotOS signing key; public key in ISO)
- [ ] ISO SHA256 reproducible builds via GitHub Actions
- [ ] `.deb` package repository at `packages.duckbotos.ai`
- [ ] Community infrastructure active:
  - Contributing guide
  - Issue templates
  - PR workflow
- [ ] Migration guide (stock Ubuntu → DuckBotOS)
- [ ] v1.0.0 release notes
- [ ] Marketing assets: website, demo video, benchmark data

---

## Post-v1.0 Direction (Backlog)

- **F11: Cross-device context sync** — Agent memory syncs across machines via encrypted mesh
- **F12: Agent-visible process tree** — Real-time reasoning visualization
- **F13: Live coding environment bootstrap** — Auto-dev-environment on first boot
- **F14: Agentic boot** — Instrumented boot; agent can optimize startup sequence
- **F15: Time-travel debugging** — Replay system state from arbitrary timestamps
- **ARM support** (Raspberry Pi 5, Apple Silicon) — Separate ARM ISOs
- **RISC-V** (future) — If hardware becomes available

---

## Build Milestones

| Quarter | Version     | Milestone                              |
|---------|-------------|----------------------------------------|
| Q3 2026 | v0.1.0-alpha | First Hermes-only ISO boots            |
| Q3 2026 | v0.2.0-alpha | OpenClaw-only ISO + shared infrastructure |
| Q4 2026 | v0.3.0-beta  | Both-mode ISO + wizard + IPC           |
| Q4 2026 | v0.4.0-beta  | Tier 1 AI features ship                |
| Q1 2027 | v0.5.0-rc1   | Security hardening + documentation     |
| Q2 2027 | v1.0.0       | Stable release                         |

---

## Dependency Graph

```
v0.1 ──────────────────────────────────────────► v0.2
 │ (fork, Hermes ISO, kiosk)                        │
 │                                                  │ (shared infra, OpenClaw ISO)
 ▼                                                  ▼
v0.3 ───────────────────────────────────────────────────────────► v0.4 ──► v0.5 ──► v1.0
 │ (both mode, wizard, IPC)                              │ (Tier 1 AI)    │ (hardening)
 │                                                       └───────────────┘
 └──────────────────────────────────────────────────────────────────────────────► (docs, infra)
```

---

**We are going to build this.**

*Last updated: 2026-06-29*