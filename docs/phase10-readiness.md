# DuckBotOS — Phase 10 Build Readiness Checklist

> The exact steps from "all docs written" → "first bootable ISO".
> Status: v0.1 — 2026-06-29 (06:59 EDT cycle)

---

## 1. Where We Are

✅ All documentation complete (P5-1 through P5-14, P6-1, P7-0, P8-1, P8-2).
✅ All research verified from official sources (LM Studio, BrowserOS, cx-distro).
✅ Architecture, installer design, provider matrix, fork strategy, build guide, boot flow — all specced.
⏳ **Blocker:** No code has been written yet. No Linux build VM is set up.

This document is the bridge from "docs complete" → "first ISO boots."

---

## 2. The Hard Blockers (Need Duckets)

### B1: Linux Build VM (P2-1)

**Need:** Ubuntu 24.04 LTS VM on this Mac mini.

Two paths, both viable:

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **UTM** | Already installed on this Mac, GUI, easy | Slower IO than VirtualBox, ARM-only on Apple Silicon (use x86_64 emulation) | ✅ Default — Duckets already familiar |
| **Vagrant + VirtualBox** | Reproducible, scriptable, CI-friendly | Adds vagrant layer, needs VB install | Good for CI later |

**Recommended v1 setup (single line):**
```bash
# Run on Mac mini
brew install utm
# Download Ubuntu 24.04 noble server ISO
# UTM → Create VM → Linux → Noble → 8 GB RAM, 100 GB disk, 4 cores
# Install Ubuntu server, snapshot as "duckbotos-build-base"
```

### B2: Duckets Decisions (D1–D5)

| # | Decision | Default if no answer | Impact |
|---|----------|----------------------|--------|
| **D1** | GPU target for v1 ISO? | NVIDIA + CPU-only fallback | Affects which `nvidia-driver-*` packages get bundled |
| **D2** | Boot type? | Full install only (skip Live USB) | Subiquity behavior — autoinstall.yaml already targets full install |
| **D3** | License? BSL 1.1 (cx-distro inherited) | OK with BSL 1.1 + Apache 2.0 for our additions | License files |
| **D4** | Both-mode GDM session picker (Hermes / OpenClaw / Hybrid Workstation)? | OK | Phase 4 scope |
| **D5** | LM Studio local-model rule: HermesOS only or all projects? | HermesOS only (current default) | Doesn't block OS build, only our other workspaces |

**Action:** Send these 5 questions in a single Telegram message — single round-trip.

---

## 3. Once the VM Exists: First ISO Build

### 3.1 VM Provisioning (5 min)

```bash
# In Ubuntu 24.04 VM
sudo apt update && sudo apt upgrade -y
sudo apt install -y git gh make curl wget

# Authenticate GitHub CLI for later (fork + CI)
gh auth login
```

### 3.2 Fork + Clone (2 min)

```bash
# Fork cxlinux-ai/cx-distro to Franzferdinan51/duckbotos-distro
gh repo fork cxlinux-ai/cx-distro \
  --org Franzferdinan51 \
  --fork-name duckbotos-distro \
  --clone

cd duckbotos-distro
```

### 3.3 First Adaptation (15 min)

Just enough to verify the fork builds a stock Debian-style ISO before we mutate:

```bash
# Install build deps
sudo apt install -y \
  live-build debootstrap squashfs-tools xorriso \
  isolinux syslinux-efi grub-pc-bin grub-efi-amd64-bin \
  mtools dosfstools dpkg-dev devscripts debhelper \
  fakeroot gnupg syft cyclonedx-cli python3-pip

# Verify cx-distro's Makefile works
make deps
make iso
# Result: output/cx-linux-0.1.0-amd64-offline.iso (Debian Trixie, no DuckBotOS yet)
```

### 3.4 First DuckBotOS Mutation (30 min)

Change one thing at a time, rebuild between:

**Mutation 1: Distribution Trixie → Noble**
```bash
# In iso/live-build/auto/config
- lb config noauto \
-     --distribution trixie \
+     --distribution noble \
      --mode ubuntu \
      --binary-images iso-hybrid \
      ...
```

Rebuild: `make iso`. Verify ISO boots.

**Mutation 2: Replace cx-* packages with duckbotos-***

Create the 13 packages listed in `docs/cx-linux-fork.md` §5. Start with the simplest meta-packages first:

```bash
mkdir -p packages/duckbotos-keyring/debian
cat > packages/duckbotos-keyring/debian/control << 'EOF'
Source: duckbotos-keyring
Section: admin
Priority: optional
Maintainer: DuckBotOS <franzferdinan51@github>

Package: duckbotos-keyring
Architecture: all
Depends: ${misc:Depends}
Description: GPG keyring for DuckBotOS APT repository
EOF

cat > packages/duckbotos-keyring/debian/rules << 'EOF'
#!/usr/bin/make -f
%:
	dh $@
EOF
chmod +x packages/duckbotos-keyring/debian/rules
```

Build: `cd packages/duckbotos-keyring && dpkg-buildpackage -us -uc -b`

**Mutation 3: Add LM Studio + BrowserOS packages**

Per `docs/lm-studio.md` §3.3 and `docs/browseros.md` §4.4 — these packages `postinst` curls the upstream .deb/AppImage at install time. For offline ISOs, we'd bundle the binaries. For v1, online postinst is fine.

### 3.5 First "Hermes-Only" ISO (60 min)

Once the package skeleton builds, write the ISO configuration:

```bash
# iso/live-build/config/package-lists/duckbotos-hermes.list.chroot
duckbotos-keyring
duckbotos-base
duckbotos-hermes
duckbotos-lm-studio
duckbotos-browseros
duckbotos-computer-use
duckbotos-kiosk-hermes
duckbotos-meta-hermes
weston
network-manager
systemd
```

Rebuild: `make iso`

**Success criteria:** ISO boots in UTM, lands on Weston kiosk, BrowserOS loads `http://127.0.0.1:9119` (Hermes dashboard).

### 3.6 Then: OpenClaw-only + Both ISOs (each 30 min)

Reuse the same package set, swap in different meta-package + kiosk variant.

---

## 4. Total Time Estimate

| Phase | Wall-clock time | Sequential? |
|-------|-----------------|-------------|
| B1: VM setup | 30 min | Sequential |
| B2: Duckets answers | minutes to days | Async |
| 3.1: VM provisioning | 5 min | After B1 |
| 3.2: Fork + clone | 2 min | After B1 |
| 3.3: Verify cx-distro builds | 30 min | After 3.2 |
| 3.4: First mutations | 30 min | After 3.3 |
| 3.5: First Hermes-only ISO | 60 min | After 3.4 |
| 3.6: OpenClaw + Both ISOs | 60 min | After 3.5 |
| **Total (after blockers)** | **~3.5 hours** | Mostly sequential |

---

## 5. Parallel Work (Do While VM is Being Set Up)

The cron cycle can keep doing these in parallel — none of them need the Linux VM:

| Task | Doc | Why no VM needed |
|------|-----|------------------|
| Write `docs/first-boot-wizard.md` (Step 1–5 UX, screenshots, TUI flow) | New doc | Pure design |
| Write `docs/troubleshooting.md` (common boot failures, recovery mode, log locations) | New doc | Synthesis of existing info |
| Write `docs/security-model.md` (TPM-backed creds, AppArmor profiles, firejail sandboxing, key isolation) | New doc | Design + reference docs |
| Write `docs/roadmap.md` (v0.1 → v0.2 → v1.0 feature timeline) | New doc | Project planning |
| Continue `docs/dual-agent-ipc.md` — add session-locking semantics | Existing | Design |
| Sketch `packages/duckbotos-base/debian/control` (the first actual package file) | Code | Can write anywhere |

---

## 6. Single Best Next Step

**Send Duckets a Telegram asking for B1 (UTM available?) and D1–D5 in one message.**

Once those answers are in, the build is unblocked.

---

## 7. Open-Claw-OS Comparison Note

We initially considered forking `thesysdev/openclaw-os` as the foundation. After research, we chose `cxlinux-ai/cx-distro` instead because:
- cx-distro has a live-build pipeline (ISO output)
- openclaw-os is an installer post-script, not a buildable ISO

If Duckets later wants an "openclaw-os flavor" of DuckBotOS, it's a swap of meta-package names — no rebuild of the foundation needed.

---

## 8. Key Sources Referenced

- `docs/architecture.md` — full stack
- `docs/installer.md` — autoinstall.yaml design
- `docs/providers.md` — provider matrix
- `docs/lm-studio.md` — llmster integration
- `docs/browseros.md` — BrowserOS integration
- `docs/cx-linux-fork.md` — fork strategy + package list
- `docs/build-guide.md` — step-by-step build (the longest doc, 17.7KB)
- `docs/system-boot-flow.md` — service order + failure handling
- `docs/dual-agent-ipc.md` — agent bus + session picker
- `TODO.md` — task tracker
- `OPEN-ISSUES.md` — decision tracker

---

*Build Readiness v0.1 — 2026-06-29 06:59 EDT*
*Total research/documentation phase: COMPLETE.*
*Build phase: BLOCKED on Linux VM + Duckets decisions.*