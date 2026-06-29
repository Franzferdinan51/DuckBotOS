# DuckBotOS — Contributing Guide

> How to develop, build, and contribute to DuckBotOS.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Overview

DuckBotOS is built by **forking** `cxlinux-ai/cx-distro` and extending it with agent-native components. Development happens in three places:

| Repo | Purpose |
|------|---------|
| `Franzferdinan51/DuckBotOS` | Project overview, SPEC, docs, spec files, coordination |
| `Franzferdinan51/cx-distro` | ISO build pipeline (live-build, Debian packages, branding) |
| `Franzferdinan51/duckbot-memory` | DuckBot's brain (RAG memory, MCP server) — separate dependency |

---

## 2. Prerequisites

### 2.1 Build Machine (Linux VM Required)

live-build runs on Linux only. Use UTM (macOS) or QEMU to create a Ubuntu 24.04 VM:

```
- Ubuntu 24.04 LTS (Noble Numbat)
- 4+ CPU cores
- 8+ GB RAM
- 100+ GB disk
- Internet connection (for package downloads)
```

### 2.2 Dev Tools on Build Machine

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y \
  live-build debootstrap squashfs-tools xorriso \
  isolinux syslinux-efi grub-pc-bin grub-efi-amd64-bin \
  mtools dosfstools dpkg-dev devscripts debhelper fakeroot gnupg \
  git gh

# Clone the fork
git clone https://github.com/Franzferdinan51/cx-distro.git duckbotos/
cd duckbotos/
```

### 2.3 GitHub CLI

```bash
# Authenticate
gh auth login

# Fork cxlinux-ai/cx-distro (if not already done)
gh repo fork cxlinux-ai/cx-distro -- clone
```

---

## 3. Repository Structure

```
duckbotos/                          # Fork of cxlinux-ai/cx-distro
├── .github/
│   └── workflows/                  # CI: ISO build, SBOM, package publish
├── iso/
│   ├── live-build/                 # live-build config (auto/, config/)
│   │   ├── auto/
│   │   │   ├── clean
│   │   │   ├── config
│   │   │   └── build
│   │   └── config/
│   │       ├── package-lists/      # .base + .hermes + .openclaw + .both
│   │       ├── hooks/              # Shell hooks during build
│   │       └── includes/           # File injection into ISO
│   └── autoinstall/                # Subiquity autoinstall configs
│       ├── hermes.yaml             # Hermes-only installer config
│       ├── openclaw.yaml           # OpenClaw-only installer config
│       └── both.yaml               # Hybrid installer config
├── packages/
│   ├── duckbotos-base/             # Base system meta-package
│   ├── duckbotos-lm-studio/        # LM Studio headless (.deb)
│   ├── duckbotos-browseros/        # BrowserOS browser (.deb)
│   ├── duckbotos-hermes/          # Hermes agent + gateway
│   ├── duckbotos-openclaw/        # OpenClaw gateway
│   ├── duckbotos-computer-use/     # computer-use-linux MCP
│   ├── duckbotos-kiosk/           # Weston + BrowserOS kiosk
│   ├── hermesos-meta/              # Hermes-only meta-package
│   ├── openclawos-meta/            # OpenClaw-only meta-package
│   └── duckbotos-hybrid-meta/      # Both-mode meta-package
├── branding/
│   ├── plymouth/                   # DuckBotOS Plymouth theme
│   └── wallpapers/                 # DuckBotOS wallpapers
├── scripts/
│   └── build.sh                    # Master build orchestrator
├── repository/
│   └── scripts/
│       └── repo-manage.sh          # APT repo tooling
├── sbom/                           # CycloneDX + SPDX SBOM output
├── Makefile                        # make deps, make iso, make test
├── CONTRIBUTING.md                 # This file
└── README.md
```

---

## 4. Building ISOs

### 4.1 Full Build (All 3 Variants)

```bash
# Install deps first
sudo make deps

# Build Hermes-only ISO
sudo make profile=hermes iso

# Build OpenClaw-only ISO
sudo make profile=openclaw iso

# Build Both-mode ISO
sudo make profile=both iso

# Build everything
sudo make iso-all
```

### 4.2 Single Package Build

```bash
# Build one Debian package
sudo make package PKG=duckbotos-lm-studio

# Or build directly with dpkg-buildpackage
dpkg-buildpackage -us -uc -b
```

### 4.3 ISO Output

```
output/
├── duckbotos-hermes-0.1.0-amd64.iso
├── duckbotos-hermes-0.1.0-amd64.iso.sha256
├── duckbotos-openclaw-0.1.0-amd64.iso
├── duckbotos-openclaw-0.1.0-amd64.iso.sha256
├── duckbotos-both-0.1.0-amd64.iso
├── duckbotos-both-0.1.0-amd64.iso.sha256
└── sbom/
    ├── duckbotos-hermes-0.1.0.cdx.json
    └── duckbotos-hermes-0.1.0.spdx.json
```

---

## 5. Package Development

### 5.1 Creating a New Package

All DuckBotOS packages follow the standard Debian package layout:

```
packages/duckbotos-example/
├── DEBIAN/
│   ├── control          # Package metadata
│   ├── postinst         # Post-install script (runs after install)
│   ├── prerm            # Pre-removal script
│   └── copyright        # License file
└── usr/
    ├── lib/
    │   └── duckbotos/   # Binary files
    └── share/
        └── doc/
            └── duckbotos-example/  # Documentation
```

### 5.2 DEBIAN/control (Example)

```
Package: duckbotos-lm-studio
Version: 0.1.0-1
Section: AI
Priority: optional
Architecture: amd64
Depends: ${misc:Depends}, curl, libstdc++6
Maintainer: DuckBotOS Team <Franzferdinan51@github.com>
Description: LM Studio headless for DuckBotOS
 LLM inference server with OpenAI-compatible REST API.
 Installs llmster daemon and LMS CLI tool.
```

### 5.3 DEBIAN/postinst (Example)

```bash
#!/bin/bash
set -e

case "$1" in
    configure)
        # Enable and start llmster service
        systemctl daemon-reload
        systemctl enable llmster.service
        systemctl start llmster.service || true

        # Create LM Studio config directory
        mkdir -p /etc/duckbotos/lm-studio
        ;;
esac

#DEBIAN# exit 0
```

### 5.4 Package Publishing

```bash
# Add to local repository
./repository/scripts/repo-manage.sh add \
  packages/duckbotos-lm-studio_0.1.0-1_amd64.deb

# Publish repository
CX_GPG_KEY_ID=YOUR_KEY_ID ./repository/scripts/repo-manage.sh publish
```

---

## 6. ISO Build Profiles

DuckBotOS builds three separate ISOs. Profiles control which packages are included:

### 6.1 hermes Profile

Packages: `duckbotos-base`, `duckbotos-hermes`, `duckbotos-lm-studio`, `duckbotos-browseros`, `duckbotos-computer-use`, `duckbotos-kiosk`

Installs: Hermes gateway (port 9119), Weston kiosk → Hermes dashboard

### 6.2 openclaw Profile

Packages: `duckbotos-base`, `duckbotos-openclaw`, `duckbotos-lm-studio`, `duckbotos-browseros`, `duckbotos-computer-use`, `duckbotos-kiosk`

Installs: OpenClaw gateway (port 18797), Weston kiosk → OpenClaw workspace

### 6.3 both Profile

Packages: `duckbotos-base`, `duckbotos-hermes`, `duckbotos-openclaw`, `duckbotos-lm-studio`, `duckbotos-browseros`, `duckbotos-computer-use`, `duckbotos-kiosk`, `duckbotos-hybrid-meta`

Installs: Both agents + GDM session picker

---

## 7. Live-Build Hooks

Hooks run at specific points during the ISO build:

| Hook | Timing | Use Case |
|------|--------|---------|
| `auto/config` | Before `lb config` | Modify live-build config |
| `auto/build` | Before `lb build` | Inject generated files |
| `auto/clean` | Before `lb clean` | Cleanup generated artifacts |
| `chroot_local-prerm` | Before package removal | Clean up package state |
| `chroot_local-postinst` | After package install | Configure packages inside ISO |

---

## 8. Testing

### 8.1 Verify ISO

```bash
# Run all verification tests
sudo make test

# Verify ISO boots (requires VM)
./tests/verify-iso.sh output/duckbotos-hermes-0.1.0-amd64.iso

# Verify packages
./tests/verify-packages.sh

# Verify autoinstall configs
./tests/verify-autoinstall.sh
```

### 8.2 VM Testing (UTM/QEMU)

```bash
# Test ISO in VM (UTM on macOS, qemu-system-x86 on Linux)
# Mount ISO as boot device, verify:
# 1. Kiosk boots to agent dashboard
# 2. systemctl services start correctly
# 3. LM Studio API responds on port 1234
# 4. BrowserOS MCP accessible on port 9003
```

---

## 9. Git Workflow

### 9.1 Branch Strategy

```
main                    # Stable, builds ISOs
├── develop             # Integration branch
├── docs/...            # Documentation-only changes
├── pkg/duckbotos-*     # Package-specific work
└── iso/...             # Build system changes
```

### 9.2 Submitting Changes

```bash
# Create feature branch
git checkout -b pkg/duckbotos-lm-studio

# Make changes, commit
git add packages/duckbotos-lm-studio/
git commit -m "packages/duckbotos-lm-studio: add llmster systemd service"

# Push to fork
git push origin pkg/duckbotos-lm-studio

# Open PR via GitHub
gh pr create --repo Franzferdinan51/cx-distro \
  --title "packages/duckbotos-lm-studio: add llmster systemd service" \
  --body "Adds LM Studio headless (llmster) as a Debian package with systemd service"
```

### 9.3 Commit Message Format

```
<scope>: <short description>

<longer description if needed>

Closes: #<issue number>
See also: #<related issue>
```

Examples:
- `packages/duckbotos-hermes: add hermes-gateway.service`
- `iso/live-build: add hermes profile config`
- `docs: add LM Studio integration guide`

---

## 10. Code Standards

### 10.1 Shell Scripts

- Use `set -euo pipefail` in all scripts
- Use `#!/bin/bash` (not `#!/bin/sh`)
- Quote variables: `"$var"` not `$var`
- Use `$(command)` for command substitution (not backticks)

### 10.2 Debian Packages

- Always include `DEBIAN/copyright` with correct license
- Use `dh_missing --fail-missing` to catch missing files
- Test with `dpkg-deb -I pkg.deb` before publishing

### 10.3 YAML (autoinstall, config)

- 2-space indentation
- No tabs
- Validate with `yamllint` before committing

---

## 11. Documentation Standards

### 11.1 Doc Files

- All docs go in `docs/` directory
- Use Markdown format
- Include `Status:` header (Draft / Review / Final)
- Include `Last updated:` date

### 11.2 Doc Sections

Every doc should have:
```
# <Title>

> One-line description
> Status: Draft v0.1 — YYYY-MM-DD

## 1. Overview
## 2. ...
## N. ...
```

---

## 12. Security Guidelines

### 12.1 Package Signing

- All `.deb` packages must be signed with GPG before publishing
- Repository must use `Signed-By` in `sources.list.d`
- Never publish unsigned packages

### 12.2 SBOM

- Generate CycloneDX SBOM for every ISO build
- Run `make sbom` after each build
- Commit SBOM JSON to repo for traceability

### 12.3 Credentials

- Never commit API keys, tokens, or secrets to any repo
- Use environment variables or TPM-backed secret storage
- LM Studio API key is per-user, not system-wide

---

## 13. Getting Help

| Resource | Link |
|----------|------|
| DuckBotOS Issues | https://github.com/Franzferdinan51/DuckBotOS/issues |
| cx-distro Fork | https://github.com/Franzferdinan51/cx-distro |
| OpenClaw Docs | https://docs.openclaw.dev |
| Hermes Agent | https://github.com/nousresearch/hermes-agent |
| CX Linux | https://cxlinux.com/docs |

---

*Contributing Guide v0.1 — 2026-06-29*
