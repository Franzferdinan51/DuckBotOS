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
6. Add Newest Desktop Control to packages
7. Configure Weston kiosk + Chromium kiosk service
8. Build first Hermes-only ISO

~3.5 hrs of build work from unblocked state to first bootable ISO.

---

## ✅ RESOLVED Issues (2026-06-29)

### v0.2.0 — Config path audit found 4 bugs

Every MCP/brain registration postinst was writing to nonexistent/wrong files:

| Was (broken) | Correct |
|---|---|
| `/var/lib/openclaw/workspace/openclaw.json` | `~/.openclaw/openclaw.json` |
| `~/.openclaw/mcp.json` (separate file — doesn't exist) | `mcp.servers` block in openclaw.json |
| `~/.hermes/mcp.json` (Hermes doesn't use this) | `~/hermes-config.json` (mcp_servers.{name} value is JSON-STRINGIFIED) |

Also discovered OpenClaw has **two completely different config formats**:

- **MCP servers**: `mcp.servers.{name}` — nested object under `mcp`
- **Plugins/extensions**: `plugins.entries.{name}.enabled` + `.config` — separate block

The 4 fixed packages: `duckbotos-{openclaw,brain,computer-use,cua-bridge}`. Committed in `3f31bfc`.

### v0.2.1 — Hermes + OpenClaw formats documented

`docs/desktop-control.md` now has a 200+ line reference including:
- "Two different concepts in OpenClaw" table
- Hermes mcp_servers format (stringified value) verified against real `~/hermes-config.json`
- OpenClaw mcp.servers format (nested object) verified against `~/.openclaw/openclaw.json`
- "Path bug summary" at the end so other agents don't repeat the mistakes

Also added `scripts/verify-config-formats.py` — read-only integration check that validates the formats. Committed in `68c0a13`, `96d7a25`.

### v0.2.2 — Packaging audit found 6 more bugs

`scripts/audit-debian-packages.py` (re-runnable, < 1 sec) catches both bug classes:

1. **Binary package name collisions** — `duckbotos-meta` was generating binaries `duckbotos-{hermes,openclaw,hybrid}` that collided with the standalone source packages. Renamed → `duckbotos-mode-{hermes,openclaw,hybrid}`.

2. **Missing `duckbotos-kiosk/debian/postinst`** — the service file existed, rules installed it, but no postinst enabled it. Created one that seeds the kiosk URL + enables the service.

3. **`duckbotos-kiosk-openclaw` was a phantom package** referenced by `Conflicts:`. Created the full package as a sibling of `duckbotos-kiosk-hermes`.

4. **`duckbotos-branding` was empty** — promised Plymouth/GDM/wallpapers, installed 0 bytes. Created real assets: Plymouth theme (`.plymouth` + `.script` + 32×32 gold duck PNG), MOTD, `/etc/profile.d/duckbotos-branding.sh`, `/etc/duckbotos/branding` shell prompt config.

5. **`duckbotos-base` had no postinst** — `/etc/duckbotos/` directory was never created. All later packages writing to it would silently fail. Created postinst that makes the layout + stamps version + writes `/etc/duckbotos/defaults.conf` with canonical service URLs.

6. **Install mod had stale "computer-use-linux" references** + missing `duckbotos-cua-bridge` + `duckbotos-brain` in `duckbotos-hybrid` Depends. Rewrote all meta descriptions + added the missing Depends.

Committed in `223e87e`.

### v0.2.3 — Docs pass

All 24 docs updated:
- `computer-use-linux` → `Newest Desktop Control` (Lobster Edition) everywhere
- `/var/lib/openclaw/*` → `~/.openclaw/*` everywhere (where applicable — some references in `docs/desktop-control.md` "Path bug summary" table are intentionally preserved)
- Package counts: 14 → 15 source packages, 18 unique binary packages
- `docs/debian-packaging.md §14` added: "Pre-Build Audit (REQUIRED before committing changes)" with v0.2.2 collision-fix story
- `README.md`: audit banner added

### Final state (2026-06-29 15:30 EDT)

- 15 source packages verified clean by `scripts/audit-debian-packages.py`
- 18 unique binary package names → 0 collisions → 0 missing files → 0 Depends violations
- ✅ **READY for dpkg-buildpackage** (once UTM VM is created)

Next unresolved: setting up the Linux build VM (UTM, Ubuntu 24.04) to actually run `./src/build.sh`.

---

### v0.2.4 — cx-distro Fork Merge (2026-06-29 18:00 EDT)

cx-distro fork (Franzferdinan51/cx-distro, duckbotos branch) cloned into DuckBotOS/cx-distro/:

| Fix | Detail | Commit |
|-----|--------|--------|
| cx-distro not cloned | Fork cloned to DuckBotOS/cx-distro/ | local |
| 7 stale stub packages | Replaced with 15 complete packages | `38c543e` |
| 8 missing packages | duckbotos-brain, branding, cua-bridge, hybrid, kiosk, kiosk-hermes, kiosk-openclaw, session-picker | `38c543e` |
| audit-debian-packages.py path | Auto-detects cx-distro as sibling repo | `fa16928` |
| verify-config-formats.py 4 paths | All hardcoded → env vars | `fa16928` |
| build-iso.yml wrong branch | Trigger: main+duckbotos (was duckbotos only) | `88ad96d` |
| build-iso.yml no cx-distro step | Clones fork fresh in a workflow step | `88ad96d` |
| build-iso.yml wrong path refs | All DuckBotOS/ → duckbot-os-repo/ | `88ad96d` |
| hermes-gateway.service User=duckets | → User=%h (portable) | `722d018` |
| Stale GitHub URLs | desktop-control.md, HANDOFF-STATUS.md, README.md, cx-distro README.md | `fa16928`, `722d018` |

Audit result: 15 source packages, 18 binary packages, 0 failures, 0 collisions, 0 violations ✅

**Next step**: Push to main/duckbotos → GitHub Actions runs `build-iso.yml` → surfaces real `dpkg-buildpackage` errors.
