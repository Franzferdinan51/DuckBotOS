# DuckBotOS — Todo List

> Last updated: 2026-06-29 19:00 EDT — v0.2.5: Soul.md added, CI/CD workflows fixed, cx-distro workflows added
> Audit: run `python3 scripts/audit-debian-packages.py` from DuckBotOS root
> Priority: 🔴 Critical | 🟡 Important | 🟢 Nice-to-have

---

## 🔴 CRITICAL — Decision Blockers (need Duckets input)

| # | Task | Status | Notes |
|---|------|--------|-------|
| D1 | **GPU target** — NVIDIA / AMD / CPU-only for v1 ISO | ✅ DONE — **CPU-only** (Duckets 09:25). NVIDIA GPU on target machine. cx-gpu-nvidia package kept. | Affects driver bundling in ISO |
| D2 | **Boot type** — Live USB only / Full install / Both | ✅ DONE — **Both** (Duckets 09:25) | Affects preseed/installer design |
| D3 | **License** — Apache 2.0 with CX Linux attribution, ok? | ✅ DONE — **Apache 2.0** confirmed (Duckets 09:25) | Blocks Phase 2 |
| D4 | **Both mode GDM picker** — Hermes / OpenClaw / Hybrid session picker | ✅ DONE — **Yes** (Duckets 09:25) | Affects Phase 4 |
| D5 | **LM Studio rule scope** — LM Studio local models: HermesOS only or all projects? | ✅ DONE — **HermesOS/DuckBotOS only** (Duckets 09:25) | Cloud-only stays for other projects |
| D6 | **cx-distro fork** — fork on GitHub + cloned to DuckBotOS/cx-distro | ✅ DONE — Forked, cloned, merged into main (2026-06-29) | Blocks all package builds |
| D7 | **build-iso.yml branch trigger** — fires on `duckbotos`, repo on `main` | ✅ DONE — Fixed to fire on `main` + `duckbotos`, clones cx-distro fresh (commit `88ad96d`) | Blocks CI |
| D8 | **audit-debian-packages.py path** — hardcoded to duckets' machine | ✅ DONE — Auto-detects `cx-distro` as sibling repo (commit `fa16928`) | Blocks local audit |
| D9 | **verify-config-formats.py hardcoded paths** — all 4 paths env-vared | ✅ DONE — NDC_REPO_DIR, NDC_PATH, HERMES_CONFIG, OPENCLAW_CONFIG all env-vared (commit `fa16928`) | Blocks local verify |
| D10 | **hermes-gateway.service User=duckets** — hardcoded username | ✅ DONE — Changed to `User=%h` (commit `722d018`) | Service won't start without this fix |

---

## 🟡 PHASE 2 — Linux VM + ISO Build Environment

| # | Task | Status | Notes |
|---|------|--------|-------|
| P2-0 | Fork cxlinux-ai/cx-distro on GitHub | ✅ DONE — Forked as Franzferdinan51/cx-distro, cloned to DuckBotOS/cx-distro/ |
| P2-1 | Merge cx-distro packages into DuckBotOS | ✅ DONE — 15 complete packages (8 new + 7 updated), 0 audit failures |
| P2-2 | Fix audit script, verify-config paths, workflow, User=%h | ✅ DONE — Commits `fa16928`, `88ad96d`, `722d018` |
| P2-3 | **Trigger ISO build** | 🔴 NEXT — Push to main/duckbotos → GitHub Actions runs `build-iso.yml` → surfaces any package errors | live-build needs Linux; CI on GitHub Actions handles this |
| P2-4 | Set up Linux build VM (UTM on Mac mini) | ⏳ Pending | For local iterative builds without CI |
| P2-5 | Fix any package errors surfaced by `dpkg-buildpackage` | ⏳ Pending | Dependent on P2-3 |
| P2-6 | Fork cxlinux-ai/cx-distro on GitHub — already done | ✅ DONE | |
| P2-7 | Replace `cx-terminal` (Rust) in fork with Hermes install script | ⏳ Pending | cx-terminal not in cx-distro source — it's an external dep |
| P2-8 | Add LM Studio .deb package to ISO | ⏳ Pending | Headless install: `curl -fsSL https://lmstudio.ai/install.sh \| bash` in postinst |
| P2-9 | ✅ BrowserOS installed as default browser | ✅ DONE | `duckbotos-browseros` — sets as default, configures xdg-mime |
| P2-10 | ✅ Newest Desktop Control (Lobster Edition) installed as system service | ✅ DONE | `duckbotos-computer-use` — MIT, replaces computer-use-linux |
| P2-11 | ✅ Install mode meta-packages written | ✅ DONE | `duckbotos-mode-{hermes,openclaw,hybrid}` |
| P2-12 | Configure Weston kiosk + Chromium kiosk service | ⏳ Pending | Fullscreen dashboard loading |
| P2-13 | First bootable Hermes-only ISO | ⏳ Pending | Verify boots to Hermes dashboard |

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
| P5-1 | `docs/architecture.md` — full technical stack | ✅ Done | 740 lines, full technical stack documented |
| P5-2 | `docs/installer.md` — Subiquity OEM design | ✅ Done | 510 lines, three ISOs, autoinstall.yaml, build checklist |
| P5-3 | `docs/providers.md` — LM Studio + all Hermes/OpenClaw providers | ✅ Done | 477 lines, provider matrix, config, security, first-boot wizard |
| P5-4 | `docs/lm-studio.md` — headless install + API + OS integration | ✅ Done | 8443 bytes, llmster install, systemd service, API endpoints, OS integration |
| P5-5 | `docs/browseros.md` — Linux install + default browser setup | ✅ Done | 9265 bytes, .deb install, default browser setup, kiosk launcher, MCP |
| P5-6 | `docs/cx-linux-fork.md` — what we changed from cx-distro | ✅ Done | 9835 bytes, CRITICAL: iso/live-build/ generated by `lb config` not in git; full package structure; cx-distro uses Debian Trixie not Ubuntu |
| P5-7 | `docs/features.md` | ✅ Done | 15 features, 3 tiers |
| P5-8 | `SPEC.md` | ✅ Done | 15KB architecture |
| P5-9 | `README.md` | ✅ Done | GitHub-ready landing page |
| P5-10 | `OPEN-ISSUES.md` | ✅ Done | Decision tracker |
| P5-11 | `docs/contributing.md` | ✅ Done | 10746 bytes — fork process, build cmds, package dev, git workflow, testing guide |
| P5-12 | `docs/license.md` | ✅ Done | 11082 bytes — BSL 1.1 decision, upstream licenses, compatibility matrix, license files |
| P5-13 | `docs/computer-use.md` | ✅ Done | 11571 bytes — AT-SPI2, Wayland portal, MCP server, systemd service, security model |
| P5-14 | `docs/dual-agent-ipc.md` | ✅ Done | 15194 bytes — JSON-RPC bus, D-Bus, shared creds, tool locking, GDM picker, conflict rules |

---

## 🟡 PHASE 6 — Documentation

| # | Task | Status | Notes |
|---|------|--------|-------|
| P6-1 | `docs/phase6-features.md` — Tier 1 feature specs | ✅ Done | 14364 bytes, F1–F5 fully specced (NL Package Mgr, Resource Orchestrator, Multi-Agent Pipeline, Activity Graph, Voice) |

## 🟢 PHASE 7 — Cool AI Features + Implementation Specs

| # | Task | Status | Notes |
|---|------|--------|-------|
| P7-0 | `docs/phase7-implementation.md` — F1-F5 full implementation specs | ✅ Done | 30.7KB — CLI contracts, systemd units, data flows, checklists |

## 🟢 PHASE 7b — Cool AI Features (Tier 1 Flagships)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| F1 | 🛠️ Natural Language Package Manager | ⏳ Pending | apt/snap/flatpak/pip intent resolution |
| F2 | ⚙️ Predictive Resource Orchestrator | ⏳ Pending | hermesos-watchdog daemon, online stats |
| F3 | 🔗 Multi-Agent Pipeline | ⏳ Pending | DAG visualization, IPC coordination |
| F4 | 📊 OS-Wide Activity Graph | ⏳ Pending | netdata + hermesos-graph daemon |
| F5 | 🎙️ Voice-Native Interaction | ⏳ Pending | openWakeWord + Whisper.cpp + Piper |

---

## 🟢 PHASE 8 — Cool AI Features (Tier 2)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| F6 | 🔒 Privacy Sentinel | ⏳ Pending | Outbound traffic monitor + intercept |
| F7 | 💾 Semantic File Memory | ⏳ Pending | Full $HOME semantic index |
| F8 | 🖱️ Accessibility API Control | ⏳ Pending | Newest Desktop Control integration |
| F9 | 🔥 Natural Language Firewall | ⏳ Pending | iptables/nftables via NL |
| F10 | 🦆 Startup Storyteller | ⏳ Pending | Animated boot graph |

---

## 🟢 PHASE 9 — Cool AI Features (Tier 3 Research)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| F11 | 📱 Cross-Device Context Sync | ⏳ Pending | Agent state sync across machines |
| F12 | 🧠 Agent-Visible Process Tree | ⏳ Pending | See agent thinking in real-time |
| F13 | 💻 Live Coding Environment Bootstrap | ⏳ Pending | Auto-dev-environment on first boot |
| F14 | ⚡ Agentic Boot | ⏳ Pending | Instrumented boot, agent can optimize |
| F15 | ⏪ Time-Travel Debugging | ⏳ Pending | Replay system state from timestamps |

---

## 🟢 PHASE 8 — Build Documentation

| # | Task | Status | Notes |
|---|------|--------|-------|
| P8-1 | `docs/build-guide.md` — Fork → VM → packages → ISO build | ✅ Done | 2026-06-29 04:59 — 17.7KB, full step-by-step from fork to ISO |
| P8-2 | `docs/system-boot-flow.md` — Complete boot sequence | ✅ Done | 2026-06-29 04:35 — 8.7KB, service order, ports, failure handling |
| P8-3 | `docs/phase10-readiness.md` — Docs→ISO bridge | ✅ Done | 2026-06-29 06:59 — 8.0KB, blockers + time estimates + parallel work |

## 🟢 PHASE 11 — CI/CD & Sync

| # | Task | Status | Notes |
|---|------|--------|-------|
| P11-1 | DuckBotOS `audit.yml` | ✅ DONE — Runs on push/PR to main+duckbotos, audits cx-distro packages |
| P11-2 | DuckBotOS `sync-to-cxdistro.yml` | ✅ DONE — Auto-syncs packages/scripts → cx-distro fork on push to main |
| P11-3 | cx-distro `audit.yml` | ✅ DONE — Runs on push/PR to duckbotos |
| P11-4 | cx-distro `sync-to-duckbotos.yml` | ✅ DONE — Mirrors packages from cx-distro → DuckBotOS main |
| P11-5 | cx-distro `release.yml` | ✅ DONE — Creates GitHub Release on version tag push |
| P11-6 | Package signing (GPG key setup) | ⏳ Pending | Sign .deb packages before release |

## 🟢 PHASE 12 — DuckBotOS ↔ cx-distro Relationship

| # | Task | Status | Notes |
|---|------|--------|-------|
| P12-1 | Document two-repo architecture | ✅ DONE — README.md architecture section + CLAUDE.md |
| P12-2 | Remove stale stubs, merge 15 packages | ✅ DONE — 7 stubs replaced, 8 new added |
| P12-3 | CLAUDE.md (DuckBotOS root) | ✅ DONE — Explains two-repo structure, key commands |
| P12-4 | CLAUDE.md (cx-distro root) | ⏳ Pending — Update cx-distro CLAUDE.md for DuckBotOS context |

## 🟡 PHASE 13 — OpenClaw Alignment

| # | Task | Status | Notes |
|---|------|--------|-------|
| P13-1 | `SOUL.md` (DuckBotOS root) | ✅ DONE — Agent personality, principles, current context |
| P13-2 | OpenClaw sync: DuckBotOS ↔ openclaw/openclaw | ⏳ Pending — Track upstream openclaw changes |
| P13-3 | duckbotos-* packages aligned to openclaw conventions | ⏳ Pending |

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
| ✅ | **cx-distro fork merged** (2026-06-29 18:00) | 2026-06-29 18:00 |
| ✅ | **15 complete packages** (8 new + 7 updated) — 0 audit failures | 2026-06-29 18:00 |
| ✅ | **build-iso.yml fixed** — fires on main+duckbotos, clones cx-distro fresh | 2026-06-29 18:00 |
| ✅ | **audit-debian-packages.py path** — auto-detects cx-distro sibling | 2026-06-29 18:00 |
| ✅ | **verify-config-formats.py paths** — all 4 env-vared | 2026-06-29 18:00 |
| ✅ | **hermes-gateway.service User=%h** — portable systemd user | 2026-06-29 18:00 |
| ✅ | **Stale GitHub URLs cleared** — desktop-control.md, HANDOFF-STATUS.md, README.md, cx-distro README.md | 2026-06-29 18:00 |

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

## 📋 Final Status (2026-06-29 14:05 EDT — Handoff Complete)

```
ALL PARALLEL-SAFE WORK DONE ✅

Docs (22 total):
  ✅ docs/architecture.md, installer.md, providers.md, lm-studio.md, browseros.md
  ✅ docs/cx-linux-fork.md, build-guide.md, system-boot-flow.md
  ✅ docs/features.md, first-boot-wizard.md, troubleshooting.md, security-model.md
  ✅ docs/roadmap.md, debian-packaging.md, dual-agent-ipc.md
  ✅ docs/computer-use.md, contributing.md, license.md, phase6-features.md
  ✅ docs/phase7-implementation.md, phase10-readiness.md, testing.md, apparmor-profiles.md

Packages (13 total — all have control + rules + changelog + postinst where needed):
  ✅ duckbotos-base, duckbotos-meta (3 mode-specific variants)
  ✅ duckbotos-hermes, duckbotos-openclaw (with brain plugin wiring)
  ✅ duckbotos-lm-studio, duckbotos-browseros, duckbotos-computer-use
  ✅ duckbotos-kiosk, duckbotos-kiosk-hermes
  ✅ duckbotos-session-picker (Both-mode UI)
  ✅ duckbotos-hybrid (Both-mode meta)
  ✅ duckbotos-brain (NEW — duckbot-rag-memory ships by default in all modes)
  ✅ duckbotos-branding (Plymouth + GDM + MOTD)

Build pipeline (cx-distro fork, branch duckbotos):
  ✅ Ubuntu 24.04 Noble base, DuckBotOS identity
  ✅ 13 Debian packages installed based on DUCKBOTOS_MODE
  ✅ All service files + postinst scripts
  ✅ GitHub Actions CI auto-builds ISO on every push
  ✅ HANDOFF.md written for the other agent

Remaining (needs Linux VM — automated via CI):
  ⏳ First ISO build (CI will surface errors, iterate from logs)
  ⏳ LM Studio binary install (config-only for now — needs actual binary)
  ⏳ BrowserOS binary install (default-only for now — needs actual binary)
  ⏳ Newest Desktop Control binary (build from source or pre-built)
  ⏳ Brain plugin ordering fix (workaround in HANDOFF.md)
```

## 🔬 Research Findings (2026-06-29 02:30 EDT)

### LM Studio (confirmed from lmstudio.ai/docs/cli)
- **CLI**: `lms` (MIT licensed) — ships with LM Studio, not standalone
- **Daemon**: `lms daemon up` — starts llmster daemon, prints PID, `--json` for scripting
- **Server**: `lms server start` — launches REST API on port 1234 (default 127.0.0.1)
  - `--port N` for custom port
  - `--bind 0.0.0.0` for network exposure (security risk — recommend auth)
  - `--cors` for dev use (security risk)
- **Model loading**: `lms load <model-id> -y` — non-interactive GPU-accelerated load
  - `--gpu=max|auto|0.0-1.0` for GPU offload control
  - `--context-length N` for context window size
- **Model listing**: `lms ls` — downloaded models; `lms ps` — currently loaded in memory
- **Headless install**: `npx lmstudio install-cli` adds `lms` to PATH
- **Server endpoint**: OpenAI-compatible `http://127.0.0.1:1234/v1`
- **Python SDK**: `pip install lmstudio` — `@lmstudio/sdk` npm package also available
- **MCP integration**: LM Studio as MCP client is documented at `/docs/developer/core/mcp`

### BrowserOS (confirmed from github.com/browseros-ai/BrowserOS + docs.browseros.com)
- **Linux .deb**: `https://cdn.browseros.com/download/BrowserOS.deb`
- **Linux AppImage**: `https://files.browseros.com/download/BrowserOS.AppImage`
- **CLI install**: `curl -fsSL https://cdn.browseros.com/cli/install.sh | bash`
- **Repo**: `https://github.com/browseros-ai/BrowserOS` (AGPL-3.0, monorepo)
- **Browser subsystem**: `packages/browseros/` — Chromium fork + build system (Python)
- **Agent subsystem**: `packages/browseros-agent/apps/server/` — Bun MCP server (53+ tools)
- **CLI**: `packages/browseros-agent/apps/cli/` — Go CLI (`browseros-cli`)
- **Agent SDK**: `@browseros-ai/agent-sdk` on npm
- **MCP tools**: 53+ browser automation tools (navigate, click, type, extract, screenshot)
- **Agent Mode**: recommends Claude Opus 4.5; local models "not yet powerful enough"
- **Chat Mode**: works with any model including local (Ollama, LM Studio)
- **LM Studio integration**: documented at `https://docs.browseros.com/features/lm-studio`
- **Note**: `browseros-cli status` is known buggy — trust `health` and `pages` instead

### cx-distro (confirmed from github.com/cxlinux-ai/cx-distro + API tree)
- **License**: BSL 1.1 (free for personal/educational/open-source; commercial needs license or wait 2029-08-01)
- **cx-terminal location**: ⚠️ **NOT in cx-distro** — lives in `cxlinux-ai/cx-core` (separate repo)
  - cx-distro's `cx-core` package depends on `cxlinux-ai/cx-core` as external APT dependency
  - **We do NOT need to remove or replace cx-terminal** — it's never imported into cx-distro source
- **CRITICAL**: `iso/live-build/` directory is NOT in git — generated by `lb config` at build time. Only these dirs exist in git: `apt/`, `packages/`, `config/`, `.github/`, root files. Do NOT look for live-build config in repo source.
- **Distribution**: Debian 13 "Trixie" (NOT Ubuntu) — DuckBotOS should change to Ubuntu 24.04 Noble
- **Build deps**: `live-build debootstrap squashfs-tools xorriso isolinux syslinux-efi grub-pc-bin grub-efi-amd64-bin mtools dosfstools dpkg-dev devscripts debhelper fakeroot gnupg`
- **cx-core pip pattern**: `cx-core` package installs via pip on first run (NOT bundled)
- **GPU packages**: `cx-gpu-nvidia/` (CUDA), `cx-gpu-amd/` (ROCm) — separate from main ISO
- **LLM packages**: `cx-llm/` → produces `cx-llm`, `cx-model-tiny`, `cx-model-base`, `cx-model-large`
- **cx-full meta-package**: depends on docker, nftables, fail2ban, prometheus-node-exporter, nginx, certbot

### Phase 5 Status (2026-06-29 02:30 EDT)
**ALL PHASE 5 DOCS COMPLETE** — P5-1 through P5-14 all marked ✅ Done

### Phase 8 Status (2026-06-29 04:59 EDT)
**Phase 8 docs complete** — P8-1 build-guide.md (17.7KB, full fork-to-ISO guide) + P8-2 system-boot-flow.md (8.7KB, complete boot sequence) written and pushed.

### Research Findings (2026-06-29 04:59 EDT) — Additional

**LM Studio headless (llmster) — confirmed from lmstudio.ai/docs/developer/core/headless:**
- Official install: `curl -fsSL https://lmstudio.ai/install.sh | bash` (Linux/macOS) — installs to `~/.lmstudio/bin/lms` + `~/.lmstudio/bin/llmster`
- Daemon: `lms daemon up` — starts llmster as background daemon, `--json` for scripted output
- llmster NOT the desktop app: no Electron, no GUI, server-native only
- Systemd service: Type=oneshot with RemainAfterExit=yes — daemon stays up, `ExecStartPre` loads model, `ExecStart` starts server, `ExecStop` shuts down
- Binary path: `~/.lmstudio/bin/lms` and `~/.lmstudio/bin/llmster`
- JIT loading: ON by default — `/v1/models` returns all downloaded models; inference auto-loads if not in memory
- When OFF: `/v1/models` returns only loaded models; must call `POST /v1/models/{id}/load` first
- **Critical for ISO**: The install script is a simple curl|bash — can be called in package postinst. Binary staging in `/opt/lmstudio/` is NOT needed (install script handles it)

**BrowserOS Linux — confirmed from github.com/browseros-ai/BrowserOS:**
- **Linux .deb**: `https://cdn.browseros.com/download/BrowserOS.deb` (also `browseros-linux-amd64.deb` on GitHub releases)
- **Linux AppImage**: `https://files.browseros.com/download/BrowserOS.AppImage`
- **Linux CLI**: `curl -fsSL https://cdn.browseros.com/cli/install.sh | bash`
- **Monorepo structure**: `packages/browseros/` (Chromium fork + build) + `packages/browseros-agent/apps/server/` (Bun MCP server, 53+ tools)
- **Agent Mode recommendation**: Claude Opus 4.5 only; local models "not yet powerful enough"
- **Chat Mode**: Any model works, including LM Studio
- **BrowserOS vs OpenClaw comparison doc**: `https://docs.browseros.com/comparisons/openclaw`
- **Linux install in ISO postinst**: `curl -fsSL https://cdn.browseros.com/download/BrowserOS.deb -o /tmp/browseros.deb && dpkg -i /tmp/browseros.deb`
- **Default browser setup**: `update-alternatives --install /usr/bin/x-www-browser browseros /opt/browseros/browseros 200`

**cx-distro confirmed directory structure (from README):**
- `iso/live-build/` IS committed to git (contrary to earlier notes) — contains versioned live-build config
- `iso/preseed/` — preseed files for Debian installer (DuckBotOS uses Subiquity autoinstall instead)
- cx-distro is Debian-based (Trixie), not Ubuntu — DuckBotOS fork must change to Ubuntu Noble in Makefile
- cx-distro README has complete directory tree + build instructions — reference for the fork
- **cx-terminal**: Lives in `cxlinux-ai/cx-core` (separate repo), NOT in cx-distro. cx-distro only declares it as a dependency

### Phase 2 Still Blocked
**Phase 2 now the active blocker** — needs Linux VM + GitHub fork action from Duckets

### Research Cycle 2026-06-29 05:50 EDT (This Cycle)
**What was done:**
- Significantly updated docs/lm-studio.md (358→712 lines, 8443→12551 bytes) — confirmed llmster/daemon architecture, CLI commands, JIT loading, systemd unit (correct binary path: `~/.lmstudio/bin/lms`), model identifiers
- Significantly updated docs/browseros.md (377→487 lines, 9265→13825 bytes) — confirmed monorepo structure (browser/CLI/MCP), 13+ LLM providers, browseros-cli install, MCP server port 9003
- Significantly updated docs/cx-linux-fork.md (319→527 lines, 8671→11953 bytes) — CORRECTED: `iso/live-build/` IS versioned in git; confirmed Makefile targets (`make iso`, `make deps`), output layout, distribution = Debian Trixie, live-build Ubuntu mode confirmed
- All three docs are now research-verified from official sources (lmstudio.ai/docs, github.com/browseros-ai/BrowserOS, github.com/cxlinux-ai/cx-distro)

**Still blocked:** D1-D5 (Duckets decisions needed), P2-1 (Linux VM setup needed)

---

### Research Cycle 2026-06-29 06:59 EDT (This Cycle)
**Status review:** All docs from P5, P6, P7, P8 (P8-1, P8-2) marked ✅ Done and verified comprehensive on file inspection (architecture.md 757L, installer.md 523L, providers.md 490L, lm-studio.md 446L, browseros.md 497L, cx-linux-fork.md 352L). The cron prompt's work-to-do items 3-10 are already complete from prior cycles.

**What was done this cycle:**
- Verified all P5/P6/P7/P8 docs exist with substantial content (no skeleton stubs)
- Wrote NEW `docs/phase10-readiness.md` (8012 bytes) — the bridge from "docs complete" → "first ISO boots": consolidates blockers B1 (Linux VM) + B2 (Duckets D1-D5), per-mutation time estimates (3.5 hrs total after unblock), parallel work that's possible without VM (first-boot-wizard, troubleshooting, security-model, roadmap docs), single best next step (Telegram ask for UTM + decisions)
- Added P8-3 to TODO Phase 8 build docs table
- 16 docs total now in repo (was 15)

**Next cycle priorities (parallel-safe without VM):**
- `docs/first-boot-wizard.md` (Step 1-5 UX design)
- `docs/troubleshooting.md` (boot failures, recovery, log locations)
- `docs/security-model.md` (TPM creds, AppArmor, firejail)
- `docs/roadmap.md` (v0.1 → v1.0 timeline)
- Continue `docs/dual-agent-ipc.md` — session-locking semantics
- Sketch `packages/duckbotos-base/debian/control` (first real package file)

**Still blocked:** B1 (Linux VM), D1-D5 (Duckets decisions)

---

---

*This file is the living todo for DuckBotOS. Updated after every significant work cycle.*

---

## Cycle 2026-06-29 18:00 EDT
- ✅ cx-distro fork cloned into DuckBotOS/cx-distro/
- ✅ 15 complete packages merged (8 new + 7 updated), audit clean
- ✅ build-iso.yml fixed: triggers on main+duckbotos, clones cx-distro fresh
- ✅ audit-debian-packages.py path: auto-detects cx-distro sibling
- ✅ verify-config-formats.py: all 4 hardcoded paths → env vars
- ✅ hermes-gateway.service: User=duckets → User=%h
- ✅ Stale GitHub URLs cleared (desktop-control.md, HANDOFF-STATUS.md, README.md, cx-distro README)
- 🔴 NEXT: Trigger ISO build (push to main/duckbotos → GitHub Actions runs build-iso.yml)
- ⏳ Remaining without VM: first-boot-wizard.md, troubleshooting.md, security-model.md, roadmap.md, CLAUDE.md files
