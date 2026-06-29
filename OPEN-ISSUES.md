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

## CRITICAL: Base OS Decision
- [x] **Path B: Ubuntu 24.04 + custom kiosk** (REJECTED: FydeOS/Chromium OS)
  - Fork cxlinux-ai/cx-distro build pipeline
  - Full systemd control
  - Build on Linux VM (live-build needs Linux)

## Still Pending Decisions

### 1. Hardware target
- [ ] GPU class? (NVIDIA / AMD / CPU-only for v1 ISO drivers) ← CRITICAL FOR BUILD
- [ ] x86_64 PC? Or ARM (RPi)?

### 2. License (Decision Needed)
- [ ] **BSL 1.1** for ISO build pipeline (forked from cxlinux-ai/cx-distro) — ok? BSL 1.1 means: free for personal/educational/open-source, commercial needs HashiCorp license or wait until 2029-08-01. See docs/license.md for full analysis.

### 2. Models & Providers (Mostly Confirmed)
- [x] **LM Studio first-class** — installed by default, URL input, model load/select from OS UI
- [x] **All Hermes + OpenClaw providers** — MiniMax, Grok, OpenAI, Anthropic, OpenRouter, etc.
- [ ] Self-hosted llama.cpp bundling in ISO? (separate from LM Studio)

### 3. Boot type
- [ ] Live USB only / Full disk install / Both?

### 4. GitHub repo
- [x] **https://github.com/Franzferdinan51/DuckBotOS** (Duckets 00:06)
- [ ] Default branch: `main` ✓
- [ ] Make public? (Default: yes per Duckets)

### 5. License
- [ ] Apache 2.0 with CX Linux + Hermes/OpenClaw attribution — ok?

### 6. Both mode (session picker)
- [ ] GDM session picker: Hermes / OpenClaw / Hybrid Workstation — ok?

## What's Built
- ✅ SPEC.md (DuckBotOS, comprehensive architecture)
- ✅ README.md (GitHub-ready)
- ✅ OPEN-ISSUES.md (this file, updated)
- ✅ docs/features.md (kinds of really cool AI features — 5 Tier 1 flagships)
- ✅ P5-1 docs/architecture.md (740 lines — full technical stack documented)
- ✅ P5-2 docs/installer.md (510 lines — Subiquity OEM, autoinstall, three ISOs)
- ✅ P5-3 docs/providers.md (477 lines — provider matrix, LM Studio config)
- ✅ P5-4 docs/lm-studio.md (8443 bytes — llmster install, systemd, API endpoints)
- ✅ P5-5 docs/browseros.md (9265 bytes — .deb install, default browser, kiosk mode)
- ✅ P5-6 docs/cx-linux-fork.md (8671 bytes — fork process, file map, inheritance guide)
- ✅ P5-11 docs/contributing.md (10746 bytes — fork process, build cmds, package dev, git workflow)
- ✅ P5-12 docs/license.md (11082 bytes — BSL 1.1 decision, upstream licenses, compatibility matrix)
- ⏳ Phase 2 needs Linux VM (cxlinux-ai build env)
- ⏳ P2-2 Fork cxlinux-ai/cx-distro on GitHub
- ⏳ First ISO build

## What's Built
- ✅ SPEC.md (DuckBotOS, comprehensive architecture)
- ✅ README.md (GitHub-ready)
- ✅ OPEN-ISSUES.md (this file, updated)
- ✅ docs/features.md (15 cool AI features — 5 Tier 1, 5 Tier 2, 5 Tier 3)
- ✅ TODO.md (full todo list — all phases, all priorities, updated each cycle)
- ✅ All Phase 5 docs completed (P5-1 through P5-6)
- ⏳ Phase 2 needs Linux VM (cxlinux-ai build env)
- ⏳ P2-2 Fork cxlinux-ai/cx-distro on GitHub
- ⏳ First ISO build

## Cron Job Active
- Every 35 mins, isolated agent cycle on MiniMax M2.7
- Working on: docs/architecture.md, docs/installer.md, docs/providers.md, CX Linux fork study, LM Studio Linux install research, BrowserOS Linux setup research
- Cron ID: b311e619-9827-472c-a9f4-60ed5452aeb4
- Cron also updates TODO.md after each cycle to mark progress

## Duckets' "Do It All" Scope (2026-06-29 00:10)
Duckets said "I wanna do it all make sure your making a Todo list to keep track of what we wanna do and updating memory as well"
→ TODO.md created at ~/Desktop/DuckBotOS/TODO.md with all phases tracked
→ Brain updated with full todo state
→ Cron updated to maintain TODO.md per cycle