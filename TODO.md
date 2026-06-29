# DuckBotOS — Todo List

> Last updated: 2026-06-29 00:10 EDT
> Priority: 🔴 Critical | 🟡 Important | 🟢 Nice-to-have

---

## 🔴 CRITICAL — Decision Blockers (need Duckets input)

| # | Task | Status | Notes |
|---|------|--------|-------|
| D1 | **GPU target** — NVIDIA / AMD / CPU-only for v1 ISO | ⏳ Pending | Affects driver bundling in ISO |
| D2 | **Boot type** — Live USB only / Full install / Both | ⏳ Pending | Affects preseed/installer design |
| D3 | **License** — Apache 2.0 with CX Linux attribution, ok? | ⏳ Pending | Blocks Phase 2 |
| D4 | **Both mode GDM picker** — Hermes / OpenClaw / Hybrid, ok? | ⏳ Pending | Affects Phase 4 |
| D5 | **Rule override scope** — LM Studio local models: HermesOS only or all projects? | ⏳ Pending (default: HermesOS only) | Was asked at 23:53, no reply yet |

---

## 🟡 PHASE 2 — Linux VM + ISO Build Environment

| # | Task | Status | Notes |
|---|------|--------|-------|
| P2-1 | Set up Linux build VM (Ubuntu 24.04) — UTM or Vagrant | ⏳ Pending | live-build needs Linux, can't do on Mac |
| P2-2 | Fork cxlinux-ai/cx-distro on GitHub | ⏳ Pending | Fork to Franzferdinan51 account |
| P2-3 | Replace `cx-terminal` (Rust) in fork with Hermes install script | ⏳ Pending | Swap cxlinux-ai cx-terminal for Hermes |
| P2-4 | Add LM Studio .deb package to ISO | ⏳ Pending | Headless install research needed |
| P2-5 | Add BrowserOS to ISO + set as default browser | ⏳ Pending | BrowserOS Linux install research needed |
| P2-6 | Add `computer-use-linux` to ISO as system service | ⏳ Pending | AT-SPI2 + Wayland portal MCP |
| P2-7 | Write `hermesos-meta` / `duckbotos-hermes` / `duckbotos-openclaw` / `duckbotos-hybrid` packages | ⏳ Pending | Meta-packages for install modes |
| P2-8 | Configure Weston kiosk + Chromium kiosk service | ⏳ Pending | Fullscreen dashboard loading |
| P2-9 | First bootable Hermes-only ISO | ⏳ Pending | Verify boots to Hermes dashboard |

---

## 🟡 PHASE 3 — Installer

| # | Task | Status | Notes |
|---|------|--------|-------|
| P3-1 | Subiquity OEM mode + `autoinstall.yaml` | ⏳ Pending | |
| P3-2 | Custom agent-selection page (whitelabel source-selection) | ⏳ Pending | Hermes-only / OpenClaw-only / Both |
| P3-3 | Model selection step — API key entry OR local model path | ⏳ Pending | |
| P3-4 | First-boot wizard — provider → channel → model config | ⏳ Pending | |
| P3-5 | OpenClaw-only ISO + verification | ⏳ Pending | |
| P3-6 | Both-mode ISO + verification | ⏳ Pending | |
| P3-7 | Custom GDM theme for session picker (Both mode) | ⏳ Pending | |

---

## 🟡 PHASE 4 — Dual-Agent + OS Integration

| # | Task | Status | Notes |
|---|------|--------|-------|
| P4-1 | Agent bus IPC daemon (`/run/hermes-claw/agent-bus.sock`) | ⏳ Pending | JSON-RPC 2.0 Unix socket |
| P4-2 | D-Bus session bus integration — cross-agent calls | ⏳ Pending | |
| P4-3 | Shared credential store (TPM-backed when available) | ⏳ Pending | |
| P4-4 | Dual-agent IPC: Hermes spawns → OpenClaw verifies (and vice versa) | ⏳ Pending | |
| P4-5 | GDM session picker: Hermes / OpenClaw / Hybrid Workstation | ⏳ Pending | |
| P4-6 | Hybrid mode: openclaw-os sidebar in GNOME Shell | ⏳ Pending | |

---

## 🟡 PHASE 5 — Documentation

| # | Task | Status | Notes |
|---|------|--------|-------|
| P5-1 | `docs/architecture.md` — full technical stack | 🔄 In Progress | Cron agent working on this |
| P5-2 | `docs/installer.md` — Subiquity OEM design | 🔄 In Progress | Cron agent working on this |
| P5-3 | `docs/providers.md` — LM Studio + all Hermes/OpenClaw providers | 🔄 In Progress | Cron agent working on this |
| P5-4 | `docs/lm-studio.md` — headless install + API + OS integration | ⏳ Pending | |
| P5-5 | `docs/browseros.md` — Linux install + default browser setup | ⏳ Pending | |
| P5-6 | `docs/cx-linux-fork.md` — what we changed from cx-distro | ⏳ Pending | |
| P5-7 | `docs/features.md` | ✅ Done | 15 features, 3 tiers |
| P5-8 | `SPEC.md` | ✅ Done | 15KB architecture |
| P5-9 | `README.md` | ✅ Done | GitHub-ready landing page |
| P5-10 | `OPEN-ISSUES.md` | ✅ Done | Decision tracker |
| P5-11 | `docs/contributing.md` | ⏳ Pending | |
| P5-12 | `docs/license.md` | ⏳ Pending | |

---

## 🟢 PHASE 6 — Cool AI Features (Tier 1 Flagships)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| F1 | 🛠️ Natural Language Package Manager | ⏳ Pending | apt/snap/flatpak/pip intent resolution |
| F2 | ⚙️ Predictive Resource Orchestrator | ⏳ Pending | hermesos-watchdog daemon, online stats |
| F3 | 🔗 Multi-Agent Pipeline | ⏳ Pending | DAG visualization, IPC coordination |
| F4 | 📊 OS-Wide Activity Graph | ⏳ Pending | netdata + hermesos-graph daemon |
| F5 | 🎙️ Voice-Native Interaction | ⏳ Pending | openWakeWord + Whisper.cpp + Piper |

---

## 🟢 PHASE 6b — Cool AI Features (Tier 2)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| F6 | 🔒 Privacy Sentinel | ⏳ Pending | Outbound traffic monitor + intercept |
| F7 | 💾 Semantic File Memory | ⏳ Pending | Full $HOME semantic index |
| F8 | 🖱️ Accessibility API Control | ⏳ Pending | computer-use-linux integration |
| F9 | 🔥 Natural Language Firewall | ⏳ Pending | iptables/nftables via NL |
| F10 | 🦆 Startup Storyteller | ⏳ Pending | Animated boot graph |

---

## 🟢 PHASE 6c — Cool AI Features (Tier 3 Research)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| F11 | 📱 Cross-Device Context Sync | ⏳ Pending | Agent state sync across machines |
| F12 | 🧠 Agent-Visible Process Tree | ⏳ Pending | See agent thinking in real-time |
| F13 | 💻 Live Coding Environment Bootstrap | ⏳ Pending | Auto-dev-environment on first boot |
| F14 | ⚡ Agentic Boot | ⏳ Pending | Instrumented boot, agent can optimize |
| F15 | ⏪ Time-Travel Debugging | ⏳ Pending | Replay system state from timestamps |

---

## 🟢 PHASE 7 — Polish & Release

| # | Task | Status | Notes |
|---|------|--------|-------|
| P7-1 | Plymouth boot theme (DuckBotOS branding) | ⏳ Pending | |
| P7-2 | Wallpaper + icon assets | ⏳ Pending | |
| P7-3 | GitHub Actions ISO build CI | ⏳ Pending | Reproducible `.iso` + `.sha256` + SBOM |
| P7-4 | MkDocs documentation site | ⏳ Pending | |
| P7-5 | v0.1.0 release — first bootable ISO | ⏳ Pending | |

---

## ✅ DONE

| # | What | When |
|---|------|------|
| ✅ | Project named DuckBotOS | 2026-06-29 00:06 |
| ✅ | GitHub repo: Franzferdinan51/DuckBotOS, main branch pushed | 2026-06-29 00:15 |
| ✅ | SPEC.md (15KB, full architecture) | 2026-06-28 23:38 |
| ✅ | README.md (GitHub-ready landing page) | 2026-06-29 00:15 |
| ✅ | OPEN-ISSUES.md (decision tracker) | 2026-06-28 23:37 |
| ✅ | docs/features.md (15 features, 3 tiers) | 2026-06-29 00:15 |
| ✅ | LM Studio as first-class provider — CONFIRMED | 2026-06-28 23:49 |
| ✅ | BrowserOS as default browser — CONFIRMED | 2026-06-28 23:49 |
| ✅ | All Hermes + OpenClaw providers — CONFIRMED | 2026-06-28 23:49 |
| ✅ | Base OS: Ubuntu 24.04 LTS — CONFIRMED | 2026-06-28 23:44 |
| ✅ | Build approach: Fork cxlinux-ai/cx-distro — CONFIRMED | 2026-06-28 23:38 |
| ✅ | 3 install modes: Hermes-only / OpenClaw-only / Both — CONFIRMED | 2026-06-28 23:38 |
| ✅ | Cron job: every 35 min, M2.7 isolated agent cycle | 2026-06-28 23:58 |
| ✅ | Brain updated with DuckBotOS decisions | Multiple updates |

---

## 📋 Priority Order (what cron should tackle next)

```
1. ✅ Already done (repo pushed)
2. ⏳ P5-1 docs/architecture.md (cron: in progress)
3. ⏳ P5-2 docs/installer.md (cron: in progress)
4. ⏳ P5-3 docs/providers.md (cron: in progress)
5. ⏳ P2-1 Set up Linux build VM
6. ⏳ P2-2 Fork cxlinux-ai/cx-distro
7. ⏳ P2-4 LM Studio .deb for Ubuntu (headless install research)
8. ⏳ P2-5 BrowserOS Linux install research
9. ⏳ P2-6 computer-use-linux package
10. ⏳ P2-3 Replace cx-terminal in fork
```

---

*This file is the living todo for DuckBotOS. Updated after every significant work cycle.*