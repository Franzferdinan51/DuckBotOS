# DuckBotOS — CX Linux Fork Guide

> What we inherited from cxlinux-ai/cx-distro, what we changed, and why.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Overview

DuckBotOS is built by **forking** `cxlinux-ai/cx-distro` — the ISO build project for CX Linux. We do not import it as a submodule; we fork it and surgically replace pieces we don't need.

**Fork target:** `https://github.com/Franzferdinan51/DuckBotOS` (our account)
**Upstream:** `https://github.com/cxlinux-ai/cx-distro`

This document tracks every inheritance and every change.

---

## 2. What We Inherit (Confirmed from cx-distro README)

### 2.1 Build Pipeline

| Inherited | Purpose | Status |
|-----------|---------|--------|
| `iso/live-build/` | live-build config (package lists, hooks, includes) | ✅ Keep |
| `scripts/build.sh` | Master build orchestrator | ✅ Keep |
| `Makefile` | `make deps`, `make iso` targets | ✅ Keep |
| APT repo tooling (`repository/scripts/repo-manage.sh`) | Package publishing | ✅ Keep |
| SBOM generation (`sbom/`) | CycloneDX/SPDX supply-chain docs | ✅ Keep |
| Security defaults | Firejail, AppArmor profiles | ✅ Keep |

### 2.2 Package Patterns

| Inherited | Purpose | Status |
|-----------|---------|--------|
| `packages/cx-core/` | Minimal meta-package (Depends: base deps) | ✅ Reference + replace |
| `packages/cx-full/` | Full meta-package | ✅ Reference (likely remove) |
| `packages/cx-archive-keyring/` | GPG keyring package | ✅ Keep |
| `DEBIAN/control` pattern | Standard Debian package metadata | ✅ Copy pattern |
| `DEBIAN/postinst` pattern | Post-install hooks | ✅ Copy pattern |

### 2.3 Installer

| Inherited | Purpose | Status |
|-----------|---------|--------|
| `iso/preseed/` | Preseed automation (Debian installer) | ❌ Remove (use Subiquity) |
| `iso/live-build/` auto-install config | Configured via preseed | ❌ Replace with autoinstall.yaml |
| ISO labeling | `cxlinux-ai/distro` naming | ✅ Replace with DuckBotOS |

---

## 3. What We Replace

### 3.1 Packages (Full Replacement)

| Original | Replacement | Rationale |
|----------|-------------|-----------|
| *(none — cx-terminal is in cx-core, not cx-distro)* | `packages/duckbotos-base/` | DuckBotOS base system |
| *(none — LM Studio is runtime)* | `packages/duckbotos-lm-studio/` | LM Studio headless |
| *(none)* | `packages/duckbotos-browseros/` | BrowserOS (new) |
| *(none)* | `packages/duckbotos-hermes/` | Hermes agent |
| *(none)* | `packages/duckbotos-openclaw/` | OpenClaw gateway |
| *(none)* | `packages/duckbotos-computer-use/` | computer-use-linux MCP |
| *(none)* | `packages/duckbotos-kiosk/` | Weston + BrowserOS kiosk |
| *(none)* | `packages/duckbotos-hermes-meta/` | Hermes-only ISO meta-package |
| *(none)* | `packages/duckbotos-openclaw-meta/` | OpenClaw-only ISO meta-package |
| *(none)* | `packages/duckbotos-hybrid-meta/` | Both-mode ISO meta-package |
| `packages/cx-full/` | *(removed)* | Replaced by our meta-packages |
| `iso/preseed/` | *(removed)* | Replaced by Subiquity autoinstall |

### 3.2 Branding (Full Replacement)

| Original | Replacement |
|----------|-------------|
| `branding/plymouth/` | `branding/plymouth/` (DuckBotOS theme) |
| `branding/wallpapers/` | `branding/wallpapers/` (DuckBotOS theme) |
| ISO volume label: `CX-LINUX` | ISO volume label: `DUCKBOTOS` |
| Boot menu: CX Linux | Boot menu: DuckBotOS |

### 3.3 Installer Backend

CX Linux uses `preseed` (Debian's legacy installer). DuckBotOS uses **Subiquity** (Ubuntu's official installer):
- Ubuntu 24.04 base
- Better OEM mode support
- Active development
- Modern `autoinstall.yaml` API

**Translation table:**

| CX preseed concept | DuckBotOS equivalent |
|---|---|
| `preseed.cfg` | `autoinstall.yaml` |
| `d-i ...` statements | `autoinstall` sections |
| Late-commands | `late-commands` |
| Early commands | `early-commands` |

---

## 4. Actual cx-distro Directory Structure

```
cx-distro/                              # Confirmed from README
├── .github/workflows/                  # CI/CD pipelines
├── iso/
│   ├── live-build/                    # Debian live-build config
│   │   ├── auto/                     # Build automation scripts
│   │   └── config/                    # Package lists, hooks, includes
│   └── preseed/                       # Preseed files (REMOVE in DuckBotOS)
├── packages/
│   ├── cx-archive-keyring/           # GPG keyring package
│   ├── cx-core/                      # Minimal meta-package (REFERENCE)
│   └── cx-full/                      # Full meta-package (REMOVE)
├── repository/
│   └── scripts/
│       └── repo-manage.sh            # APT repo tooling
├── sbom/                             # CycloneDX + SPDX SBOM generation
├── branding/                         # Plymouth theme, wallpapers
├── scripts/
│   └── build.sh                      # Master build script
├── tests/
│   ├── verify-iso.sh
│   ├── verify-packages.sh
│   └── verify-preseed.sh
├── Makefile                          # make deps, make iso, make test
└── README.md
```

**Note:** `cx-terminal` is NOT in cx-distro — it lives in `cxlinux-ai/cx-core` (a separate repo). cx-distro's `cx-core` package depends on `cxlinux-ai/cx-core` as an external package. We do NOT need to remove `cx-terminal` from the fork.

---

## 5. Fork Process (Step-by-Step)

### 5.1 Fork on GitHub

1. Go to `https://github.com/cxlinux-ai/cx-distro`
2. Click **Fork** → to `Franzferdinan51/DuckBotOS`
3. Clone locally (in Linux VM — live-build requires Linux, not macOS)

### 5.2 Clone and Set Up Remotes

```bash
git clone https://github.com/Franzferdinan51/DuckBotOS.git duckbotos/
cd duckbotos/

# Track upstream for future sync
git remote add upstream https://github.com/cxlinux-ai/cx-distro.git
git fetch upstream
```

### 5.3 Replace All cx-linux References

```bash
# Preview what will change
grep -r "cx-linux\|cx_distro\|CX-LINUX\|cxlinux" . \
  --include="*.sh" --include="*.yaml" --include="*.list" \
  --include="Makefile" --include="*.desktop" --include="*.service" | wc -l

# Replace in all text files
find . -type f \
  \( -name "*.sh" -o -name "*.yaml" -o -name "*.list" \
     -o -name "Makefile" -o -name "*.desktop" -o -name "*.service" \
     -o -name "*.preseed" -o -name "*.md" \) \
  -exec sed -i \
    's/cx-linux/DuckBotOS/g; s/cx_distro/duckbotos/g;
     s/CX-LINUX/DUCKBOTOS/g; s/cxlinux/duckbotos/g' {} +

git add -A
git commit -m "docs: rename from cx-linux to DuckBotOS"
```

### 5.4 Remove cx-full + preseed

```bash
# Remove preseed (we use Subiquity autoinstall)
rm -rf iso/preseed/

# Remove cx-full (replaced by our meta-packages)
rm -rf packages/cx-full/
```

### 5.5 Create DuckBotOS Packages

```bash
mkdir -p packages/duckbotos-base/
mkdir -p packages/duckbotos-lm-studio/
mkdir -p packages/duckbotos-browseros/
mkdir -p packages/duckbotos-hermes/
mkdir -p packages/duckbotos-openclaw/
mkdir -p packages/duckbotos-computer-use/
mkdir -p packages/duckbotos-kiosk/
mkdir -p packages/duckbotos-hermes-meta/
mkdir -p packages/duckbotos-openclaw-meta/
mkdir -p packages/duckbotos-hybrid-meta/
```

### 5.6 Update live-build Package Lists

In `iso/live-build/config/package-lists/`, edit the package list files to:
- Add: `duckbotos-base duckbotos-lm-studio duckbotos-browseros duckbotos-hermes duckbotos-openclaw duckbotos-computer-use duckbotos-kiosk duckbotos-hermes-meta` (for Hermes ISO)
- Remove or comment out: `cx-full cx-cli cx-llm` (if present)

### 5.7 Add Subiquity Autoinstall Config

```bash
mkdir -p iso/subiquity/
# Copy autoinstall.yaml from docs/installer.md into iso/subiquity/
cp ~/Desktop/DuckBotOS/docs/autoinstall.yaml iso/subiquity/
```

### 5.8 Build and Test

```bash
# Install build deps
sudo apt-get install -y live-build debootstrap squashfs-tools xorriso \
  isolinux syslinux-efi grub-pc-bin grub-efi-amd64-bin \
  mtools dosfstools dpkg-dev devscripts debhelper fakeroot gnupg

make deps
make iso    # Produces DuckBotOS-0.1.0-amd64-offline.iso
make test   # Run verification tests
```

---

## 6. File Map: cx-distro → DuckBotOS

```
cx-distro/                             →  duckbotos/
├── .github/workflows/                →  ✅ Keep (update for DuckBotOS repo)
├── iso/
│   ├── live-build/                   →  ✅ Keep (update package lists)
│   └── preseed/                      →  ❌ Remove (use Subiquity)
├── packages/
│   ├── cx-archive-keyring/          →  ✅ Keep (update naming)
│   ├── cx-core/                      →  ✅ Reference (replace with duckbotos-base)
│   └── cx-full/                      →  ❌ Remove (replaced by meta-packages)
├── repository/                        →  ✅ Keep
├── sbom/                             →  ✅ Keep (update name)
├── branding/                         →  ✅ Keep (replace assets only)
├── scripts/
│   └── build.sh                     →  ✅ Keep (update package refs)
├── tests/                            →  ✅ Keep (update paths)
├── Makefile                          →  ✅ Keep (update targets)
└── README.md                         →  ✅ Replace with DuckBotOS-specific
```

---

## 7. Meta-Package Design (for 3 ISO Variants)

Each DuckBotOS ISO is defined by its meta-package:

### `packages/duckbotos-hermes-meta/DEBIAN/control`
```
Package: duckbotos-hermes-meta
Version: 0.1.0
Section: ai
Priority: optional
Depends: duckbotos-base, duckbotos-hermes, duckbotos-lm-studio,
         duckbotos-browseros, duckbotos-computer-use, duckbotos-kiosk
Architecture: amd64
Description: Hermes-only DuckBotOS (default mode)
```

### `packages/duckbotos-openclaw-meta/DEBIAN/control`
```
Package: duckbotos-openclaw-meta
Version: 0.1.0
Section: ai
Priority: optional
Depends: duckbotos-base, duckbotos-openclaw, duckbotos-lm-studio,
         duckbotos-browseros, duckbotos-computer-use, duckbotos-kiosk
Architecture: amd64
Description: OpenClaw-only DuckBotOS
```

### `packages/duckbotos-hybrid-meta/DEBIAN/control`
```
Package: duckbotos-hybrid-meta
Version: 0.1.0
Section: ai
Priority: optional
Depends: duckbotos-base, duckbotos-hermes, duckbotos-openclaw,
         duckbotos-lm-studio, duckbotos-browseros,
         duckbotos-computer-use, duckbotos-kiosk
Architecture: amd64
Description: Both-mode DuckBotOS (Hermes + OpenClaw)
```

---

## 8. CLAUDE.md Update

```markdown
# DuckBotOS — CX-Distro Fork

ISO builder for DuckBotOS — an agent-first OS built on Ubuntu 24.04 LTS.

## Key Directories
```
duckbotos/
├── packages/        # Debian packages (duckbotos-*, duckbotos-*-meta/)
├── iso/
│   ├── live-build/  # live-build config for ISO generation
│   └── subiquity/   # Subiquity autoinstall config (replaces preseed/)
├── branding/        # Plymouth theme, wallpapers (DuckBotOS branded)
└── scripts/         # Build scripts
```

## Build Commands
```bash
make deps   # Install build dependencies
make iso   # Build DuckBotOS ISO
make test  # Run verification tests
```

## Key Differences from cx-distro
- Uses Subiquity autoinstall (not preseed) — Ubuntu 24.04 base
- No embedded LLM (LM Studio is a runtime provider)
- 3 separate ISO variants via meta-packages
- BrowserOS as default browser (not stock Chromium)
- Hermes + OpenClaw as agent systems
- cx-terminal NOT included (no custom terminal — browser IS the interface)
```

---

## 9. Build Checklist

- [ ] Fork cxlinux-ai/cx-distro to Franzferdinan51/DuckBotOS on GitHub
- [ ] Clone fork to Linux VM (Ubuntu 24.04)
- [ ] Run sed replacement (cx-linux → DuckBotOS)
- [ ] Remove `iso/preseed/` (use Subiquity)
- [ ] Remove `packages/cx-full/`
- [ ] Create `packages/duckbotos-base/`
- [ ] Create `packages/duckbotos-lm-studio/` (see docs/lm-studio.md)
- [ ] Create `packages/duckbotos-browseros/` (see docs/browseros.md)
- [ ] Create `packages/duckbotos-hermes/`
- [ ] Create `packages/duckbotos-openclaw/`
- [ ] Create `packages/duckbotos-computer-use/`
- [ ] Create `packages/duckbotos-kiosk/`
- [ ] Create `packages/duckbotos-hermes-meta/`
- [ ] Create `packages/duckbotos-openclaw-meta/`
- [ ] Create `packages/duckbotos-hybrid-meta/`
- [ ] Update live-build package lists for each ISO variant
- [ ] Add `iso/subiquity/autoinstall.yaml`
- [ ] Replace branding assets (Plymouth, wallpapers, ISO label)
- [ ] Update CLAUDE.md
- [ ] `make deps && make iso` — build first DuckBotOS ISO in VM
- [ ] Verify ISO boots to DuckBotOS splash screen

---

*CX Linux Fork Guide v0.1 — 2026-06-29*
