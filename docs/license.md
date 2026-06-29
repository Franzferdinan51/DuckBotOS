# DuckBotOS — License Guide

> Which open-source licenses DuckBotOS uses and why, and what Duckets needs to decide.
> Status: Decision Needed — 2026-06-29

---

## 1. Overview

DuckBotOS is a multi-component project that **inherits** from several upstream projects. Each component may use a different license. This doc explains the licensing landscape and the decision Duckets needs to make.

---

## 2. Upstream Licenses

DuckBotOS builds on several projects, each with their own license:

| Component | Project | License | Notes |
|-----------|---------|---------|-------|
| **ISO Build Pipeline** | cxlinux-ai/cx-distro | **BSL 1.1** | Build system, live-build config, Debian packaging patterns |
| **Hermes Agent** | nousresearch/hermes-agent | **MIT** | Our primary agent runtime |
| **OpenClaw** | openclaw/openclaw | **Apache 2.0** | Our secondary agent runtime |
| **LM Studio** | lmstudio-ai/lm-studio | **Proprietary** | Bundled as binary; llmster is the headless runtime |
| **BrowserOS** | browseros-ai/BrowserOS | **AGPL v3** | Chromium-based agentic browser |
| **Newest Desktop Control** | Newest Desktop Control (Lobster Edition) | **MIT** | Rust MCP server for desktop control |
| **Weston** | wayland-project/weston | **MIT** | Wayland compositor (kiosk mode) |
| **Ubuntu Base** | canonical/ubuntu | **GPLv2/GPLv3** | Base OS packages |
| **DuckBotOS Docs** | (ours) | **CC BY 4.0** | This documentation |

---

## 3. The BSL 1.1 Question

### 3.1 What is BSL 1.1?

The **Business Source License 1.1** (BSL 1.1) is a source-available license from HashiCorp. Key terms:

- **Use**: Can use, modify, and distribute the software
- **Free for non-production**: Free for personal, educational, and open-source development
- **Production fee required after**: Software becomes freely available under GPLv3 **after 4 years** from the release date
- **No attribution requirement** for free use

### 3.2 cx-distro BSL 1.1

cxlinux-ai/cx-distro uses BSL 1.1. Their LICENSE file states:

> "This Source Code is also licensed under the Business Source License 1.1 (BSL 1.1),
> alongside the HashiCorp BSL 1.1 License.
> [...]
> The change date is August 1, 2029 (4 years from initial release).
> After the Change Date, the Program will be subject to GPLv3."

### 3.3 Our Options

We have three paths for the DuckBotOS ISO build pipeline:

#### Option A: Keep BSL 1.1 (Same as cx-distro) — ✅ Recommended

```
DuckBotOS fork of cx-distro (ISO build pipeline) → BSL 1.1
```

- No license change needed — we simply fork cx-distro and replace packages
- BSL 1.1 applies to our build system changes
- cx-distro contributors retain their rights
- Our new packages (duckbotos-*) can use any license we choose
- **Downside**: Our build pipeline can't be used commercially without HashiCorp's permission until 2029-08-01

#### Option B: Switch to Apache 2.0

```
DuckBotOS fork of cx-distro → Apache 2.0 + attribution to cxlinux-ai
```

- Requires explicit permission or dual-licensing from cxlinux-ai
- Apache 2.0 is more permissive (no production use restriction)
- **Complicated**: Need to confirm with cxlinux-ai that Apache 2.0 is an acceptable alternative
- **Not recommended** without cxlinux-ai's explicit approval

#### Option C: Replace build pipeline entirely

We could write a fresh build system from scratch (no live-build inheritance), avoiding the BSL 1.1 question entirely. This is a **lot more work** (~100+ hours) and is not recommended.

### 3.4 Duckets Decision Needed: BSL 1.1

> **Duckets: Do you accept the cx-distro BSL 1.1 license for the ISO build pipeline?**
>
> - BSL 1.1 on our fork means we can use it freely for personal, educational, and open-source purposes
> - Commercial deployment in a product requires either waiting until 2029-08-01 or negotiating with HashiCorp
> - For an open-source hobby project (which DuckBotOS currently is), BSL 1.1 is fine
> - Our own packages (duckbotos-*) are separate and can use any license

---

## 4. Our Packages (duckbotos-*)

Our Debian packages are **our own work** and can use any license we choose. Recommended approach:

| Package | License | Rationale |
|---------|---------|-----------|
| `duckbotos-base` | **Apache 2.0** | Base system, permissive |
| `duckbotos-lm-studio` | **Apache 2.0** | Wrapper package, not the LM Studio binary itself |
| `duckbotos-browseros` | **Apache 2.0** | Install wrapper, BrowserOS itself is AGPLv3 |
| `duckbotos-hermes` | **MIT** (same as Hermes) | Clean compatibility with upstream |
| `duckbotos-openclaw` | **Apache 2.0** (same as OpenClaw) | Clean compatibility with upstream |
| `duckbotos-computer-use` | **MIT** (same as upstream) | Clean compatibility |
| `duckbotos-kiosk` | **Apache 2.0** | Our kiosk compositor config |
| `hermesos-meta` | **Apache 2.0** | Meta-package |
| `openclawos-meta` | **Apache 2.0** | Meta-package |
| `duckbotos-hybrid-meta` | **Apache 2.0** | Meta-package |

**Rationale**: We use the same license as each upstream agent project. Hermes = MIT, OpenClaw = Apache 2.0. No license conflicts.

---

## 5. License Compatibility Matrix

### 5.1 Agent Layer

| | Hermes (MIT) | OpenClaw (Apache 2.0) | Our wrapper (Apache 2.0) |
|--|--|--|--|
| **Hermes (MIT)** | ✅ Compatible | ✅ Compatible (Apache 2.0 §7 allows this) | ✅ Compatible |
| **OpenClaw (Apache 2.0)** | ✅ Compatible | ✅ Compatible | ✅ Compatible |
| **LM Studio (Proprietary)** | ✅ OK (local only) | ✅ OK (local only) | ✅ OK (local only) |
| **BrowserOS (AGPLv3)** | ⚠️ AGPL传染性 — but we're not distributing modified BrowserOS | ⚠️ Same | ⚠️ Same |

### 5.2 AGPLv3 Consideration

BrowserOS is **AGPLv3**. This is only relevant if we:
1. Modify the BrowserOS source code and distribute it, OR
2. Run BrowserOS as a networked service and let others access it

For DuckBotOS:
- We distribute BrowserOS **unchanged** (official .deb from their releases)
- BrowserOS MCP port (9003) is local to the machine
- This is **not** the kind of AGPL "network use" that triggers the license
- **We do not need to open-source DuckBotOS because of BrowserOS**

### 5.3 Hermes + OpenClaw Together

Running Hermes (MIT) and OpenClaw (Apache 2.0) on the same machine is **fully compatible**:
- Both are permissive licenses
- Neither传染the other
- Each runs as an independent service
- They communicate via our IPC bus (Unix socket JSON-RPC)

---

## 6. License File Locations

Each package in `packages/` must contain `DEBIAN/copyright`:

```
packages/duckbotos-hermes/DEBIAN/copyright:
---
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Source: https://github.com/nousresearch/hermes-agent

Files: *
Copyright: 2024-2026 Nous Research LLC
License: MIT

Files: debian/*
License: Apache-2.0 OR MIT
---

packages/duckbotos-openclaw/DEBIAN/copyright:
---
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Source: https://github.com/openclaw/openclaw

Files: *
Copyright: 2024-2026 OpenClaw Contributors
License: Apache-2.0
---

packages/duckbotos-browseros/DEBIAN/copyright:
---
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Source: https://github.com/browseros-ai/BrowserOS

Files: *
Copyright: 2024-2026 BrowserOS AI
License: AGPL-3.0-or-later
Comment: We distribute the official BrowserOS .deb unchanged.
 The AGPLv3 license applies to BrowserOS source code modifications.
 Our install wrapper (debian/*) is Apache-2.0.
---

packages/duckbotos-lm-studio/DEBIAN/copyright:
---
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Source: https://lmstudio.ai

Files: *
Copyright: 2024-2026 LM Studio AI
License: Proprietary
Comment: LM Studio is proprietary software. This package only installs
 the official lmstudio.ai binary. Users must agree to LM Studio's
 terms of service when they create an account at lmstudio.ai.
 Our install wrapper (debian/*) is Apache-2.0.
---
```

---

## 7. REUSE Compliance

We should aim for [REUSE Specification](https://reuse.software/) compliance:

```
# Every source file should have a license header
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 DuckBotOS Contributors

# Every binary package should include:
# - DEP-11 metadata (AppStream)
# - copyright file
# - license files in /usr/share/doc/<package>/
```

```bash
# Check REUSE compliance
sudo apt install reuse
reuse lint .
```

---

## 8. Open-Source Registry

Once DuckBotOS v0.1.0 is released, register in:

| Registry | URL |
|----------|-----|
| OSI Approved Licenses | https://opensource.org/licenses |
| SPDX License List | https://spdx.org/licenses |
| NixOS:nixpkgs | Submit PR to add DuckBotOS packages |

---

## 9. Summary: What Duckets Needs to Decide

| Decision | Options | Recommended | Status |
|----------|---------|-------------|--------|
| **ISO build pipeline license** | BSL 1.1 (keep) / Apache 2.0 (ask cxlinux) / Fresh build | **BSL 1.1** | ⏳ Pending |
| **DuckBotOS docs** | CC BY 4.0 | **CC BY 4.0** | ✅ Can proceed |
| **DuckBotOS packages** | Apache 2.0 (consistent) | **Apache 2.0** | ✅ Can proceed |

### What BSL 1.1 Means for DuckBotOS

- ✅ We can fork cx-distro and use it freely
- ✅ We can build and distribute DuckBotOS ISOs
- ✅ We can accept contributions
- ✅ DuckBotOS packages can use any license we want
- ⚠️ Commercial products using our build pipeline need to wait until 2029 or negotiate
- ✅ For an open-source hobbyist project, BSL 1.1 is not a blocker

---

## 10. Draft LICENSE File

For the `Franzferdinan51/DuckBotOS` repo (docs + SPEC + config, NOT the ISO build pipeline):

```markdown
# DuckBotOS Documentation License

All documentation, specifications, and non-code files in this repository
are licensed under the Creative Commons Attribution 4.0 International License
(CC BY 4.0).

You are free to:
- Share: copy and redistribute the material in any medium or format
- Adapt: remix, transform, and build upon the material for any purpose,
  including commercially

Under the following terms:
- Attribution: You must give appropriate credit to DuckBotOS, provide
  a link to the license, and indicate if changes were made.

https://creativecommons.org/licenses/by/4.0/

---

# DuckBotOS Packages

Individual packages in packages/ are licensed as follows:

| Package | License |
|---------|---------|
| duckbotos-base | Apache 2.0 |
| duckbotos-hermes | MIT |
| duckbotos-openclaw | Apache 2.0 |
| duckbotos-lm-studio | Apache 2.0 (wrapper) |
| duckbotos-browseros | Apache 2.0 (wrapper; AGPLv3 for BrowserOS itself) |
| duckbotos-computer-use | MIT |
| duckbotos-kiosk | Apache 2.0 |
| hermesos-meta | Apache 2.0 |
| openclawos-meta | Apache 2.0 |
| duckbotos-hybrid-meta | Apache 2.0 |

---

# ISO Build Pipeline (Forked from cxlinux-ai/cx-distro)

The ISO build pipeline is forked from cxlinux-ai/cx-distro and retains
the Business Source License 1.1 (BSL 1.1). See:
- cx-distro LICENSE file: https://github.com/cxlinux-ai/cx-distro/blob/main/LICENSE
- BSL 1.1 full text: https://www.hashicorp.com/bsl11

DuckBotOS fork: https://github.com/Franzferdinan51/cx-distro
```

---

*License Guide v0.1 — 2026-06-29 — Awaiting Duckets' BSL 1.1 decision*
