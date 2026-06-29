# DuckBotOS — Open Issues

## Confirmed (from Duckets)
- **NOT** running on this Mac mini — separate hardware target
- Will live on GitHub eventually — documentation is important
- **GitHub repo CONFIRMED**: https://github.com/Franzferdinan51/DuckBotOS (main branch)
- Search web + GitHub for existing similar projects FIRST → DONE
- May be an OpenClaw-based OS project to pull from → **FOUND: thesysdev/openclaw-os**
- "Agent-first OS" — boot into an agent instead of a desktop
- "Deeply integrated as deep as we can go" — both Hermes AND OpenClaw at the OS level
- **Name: DuckBotOS** — picked (Duckets approved 00:06, 2026-06-29)
- RTX Spark inspiration (DGX OS / Ubuntu remix for AI desktop)
- **REJECTED: FydeOS/Chromium OS** (Duckets 23:44) — going with Ubuntu base
- **LM Studio first-class provider** — installed by default, URL input, model load/select from OS UI
- **BrowserOS as default browser** — https://github.com/browseros-ai/BrowserOS
- **All Hermes + OpenClaw providers included** — MiniMax, Grok, OpenAI, Anthropic, OpenRouter, LM Studio, etc.
- **Cool AI features required** — see docs/features.md (Tier 1: 5 flagship features)

## ✅ D1-D5 ALL DECIDED (Duckets 2026-06-29 09:25)

| # | Decision | Answer | Notes |
|---|----------|--------|-------|
| D1 | GPU target | **CPU-only** | v1 ships without NVIDIA/AMD drivers |
| D2 | Boot type | **Both** | Live USB + full install |
| D3 | License | **Apache 2.0** | CX Linux attribution ok |
| D4 | Both mode GDM picker | **Yes** | Hermes / OpenClaw / Hybrid session picker |
| D5 | LM Studio rule scope | **HermesOS/DuckBotOS only** | Cloud-only stays for other projects |

## CRITICAL: Base OS Decision
- [x] **Path B: Ubuntu 24.04 + custom kiosk** (REJECTED: FydeOS/Chromium OS)
  - Fork cxlinux-ai/cx-distro build pipeline
  - Full systemd control
  - Build on Linux VM (live-build needs Linux)

## Phase 2 — Ready to Start (D1-D5 Unblocked)

### 1. Hardware target
- [x] **NVIDIA GPU** — target machine has NVIDIA GPU. Keep cx-gpu-nvidia package. LM Studio GPU inference a bonus. CPU-only fallback still works on other hardware.

### 2. Models & Providers (Confirmed)
- [x] **LM Studio first-class** — installed by default, URL input, model load/select from OS UI
- [x] **All Hermes + OpenClaw providers** — MiniMax, Grok, OpenAI, Anthropic, OpenRouter, etc.
- [ ] Self-hosted llama.cpp bundling in ISO? (separate from LM Studio — future)

### 3. Boot type
- [x] **Both** — Live USB + full disk install

### 4. GitHub repo
- [x] **https://github.com/Franzferdinan51/DuckBotOS** (Duckets 00:06)
- [x] Default branch: `main` ✓
- [x] Repo public ✓

### 5. License
- [x] **Apache 2.0** with CX Linux + Hermes/OpenClaw attribution — CONFIRMED

### 6. Both mode (session picker)
- [x] **GDM session picker: Hermes / OpenClaw / Hybrid Workstation** — CONFIRMED

## What's Built
- ✅ SPEC.md (DuckBotOS, comprehensive architecture)
- ✅ README.md (GitHub-ready)
- ✅ OPEN-ISSUES.md (this file, all D1-D5 resolved)
- ✅ docs/features.md (15 cool AI features — 5 Tier 1, 5 Tier 2, 5 Tier 3)
- ✅ TODO.md (full todo list — all phases, all priorities)
- ✅ 21 documentation files across docs/
- ✅ packages/duckbotos-meta/debian/control (7 packages specced)
- ⏳ Linux VM setup needed (UTM on Mac mini or separate Linux machine)
- ⏳ Fork cxlinux-ai/cx-distro (can start NOW via gh CLI)
- ⏳ First ISO build

## Cron Job Active
- Every 35 mins, isolated agent cycle on MiniMax M2.7
- Working on: cx-linux fork via gh CLI, VM setup prep, next priority tasks
- Cron ID: b311e619-9827-472c-a9f4-60ed5452aeb4

## Duckets' "Do It All" Scope (2026-06-29 00:10)
Duckets said "I wanna do it all" — full scope. TODO.md tracks ALL work. Brain updated each cycle.
## Phase 2 Kickoff — Ready to Build (2026-06-29 09:25 EDT)

D1-D5 all answered. All decision blockers cleared. Phase 2 can begin.

Immediate next steps:
1. Fork cxlinux-ai/cx-distro on GitHub (gh CLI, no VM needed)
2. Set up Linux build VM (UTM Ubuntu 24.04 on Mac mini)
3. Replace cx-terminal in fork with Hermes install
4. Add LM Studio headless .deb to packages
5. Add BrowserOS to packages
6. Add computer-use-linux to packages
7. Configure Weston kiosk + Chromium kiosk service
8. Build first Hermes-only ISO

~3.5 hrs of build work from unblocked state to first bootable ISO.
