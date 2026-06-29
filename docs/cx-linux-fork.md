# DuckBotOS — CX Linux Fork Strategy

> How DuckBotOS forks cxlinux-ai/cx-distro: what to keep, what to replace, and the exact fork workflow.
> Status: Updated v0.2 — 2026-06-29

---

## 1. Critical Discovery: live-build Is NOT in Git

**Important:** The `iso/` directory **IS committed to git** — including `iso/live-build/` (Debian live-build config) and `iso/preseed/` (preseed files). Both are part of the versioned source. The Makefile runs `lb config` to initialize live-build, but the actual config files in `iso/live-build/config/` are versioned.

```
cx-distro/ (confirmed from git tree)
├── .github/workflows/      # CI/CD
├── apt/                    # APT repo tooling (deb822 format, signed)
├── config/                 # Build config JSON (release-amd64.json, etc.)
├── iso/                    # ISO build configuration
│   ├── live-build/         # Debian live-build config (versioned!)
│   │   ├── auto/          # Build automation scripts (auto/config, auto/clean, auto/build)
│   │   └── config/        # Package lists, hooks, includes
│   └── preseed/           # Automated installation preseeds
├── packages/               # Debian meta-packages (cx-archive-keyring, cx-core, cx-full)
├── repository/             # APT repository tooling + scripts/
├── sbom/                   # SBOM generation
├── branding/               # Plymouth theme, wallpapers
├── scripts/                # Build automation scripts/
│   └── build.sh           # Master build script
├── tests/                  # Verification tests (verify-iso.sh, verify-packages.sh, etc.)
├── Makefile               # Build orchestrator — runs lb config + lb build
├── README.md
├── CLAUDE.md
└── LICENSE (BSL 1.1)
```

```
cx-distro/ (what's actually in git)
├── .github/workflows/      # CI/CD
├── apt/                    # APT repo tooling (deb822 format, signed)
├── config/                 # Build config JSON (release-amd64.json, etc.)
├── packages/               # Debian meta-packages (cx-archive-keyring, cx-core, cx-full)
├── Makefile               # Build orchestrator — runs lb config + lb build
├── README.md
├── CLAUDE.md
└── LICENSE (BSL 1.1)
```

The **Debian base system** comes from live-build's debootstrap of Debian Trixie (13), NOT Ubuntu. This is a meaningful difference — we may need to change the base to Ubuntu 24.04.

---

## 2. What We Inherit vs. Replace

### Inherit (keep exactly)
- **Makefile build system** — `make deps`, `make iso`, `make package` targets
- **APT repo tooling** — `apt/sign-release.sh`, deb822 format, GPG signing workflow
- **Package skeleton pattern** — `packages/cx-archive-keyring/`, `packages/cx-core/` debian/ structure
- **CI/CD workflows** — `.github/workflows/build-iso.yml`, `installation-tests.yml`
- **SBOM generation** — syft + cyclonedx-cli in Makefile
- **ISO output layout** — `output/*.iso`, `output/*.sha256`, `output/sbom/`

### Replace wholesale
- **All packages** — `cx-archive-keyring`, `cx-core`, `cx-full` → `duckbotos-*`
- **APT repo URL** — `repo.cxlinux.com` → `repo.duckbotos.com` (or keep configurable)
- **ISO labels + branding** — "CX Linux" → "DuckBotOS"
- **Distribution codename** — Debian Trixie → Ubuntu Noble (or stay Debian-based)
- **Package dependencies** — cx-* packages → duckbotos-* packages

### Replace partially
- **`config/release-amd64.json`** — version, codename, architectures, ISO label
- **CI/CD workflows** — change repo name, artifact upload paths

---

## 3. Package Structure Pattern

cx-distro packages follow standard Debian meta-package structure:

```
packages/cx-archive-keyring/
├── debian/
│   ├── changelog
│   ├── compat        # debhelper compat level (9)
│   ├── control       # Package metadata + Depends
│   ├── rules         # Build rules (usually trivial for meta-packages)
│   └── source/
│       └── format   # "3.0 (quilt)"
└── (no source files — pure meta-package)
```

Example `debian/control`:
```
Source: cx-archive-keyring
Section: admin
Priority: optional
Maintainer: CX Linux Team <team@cxlinux.com>

Package: cx-archive-keyring
Architecture: all
Depends: ${misc:Depends}
Description: GPG keyring for CX Linux APT repository
 Installs the GPG public key used to verify packages from the
 CX Linux APT repository.
```

Example `debian/rules` (trivial meta-package):
```makefile
#!/usr/bin/make -f

%:
	dh $@

override_dh_systemd_enable:
	# No systemd services for keyring package
```

Build command: `dpkg-buildpackage -us -uc -b` from within `packages/{pkg}/`

---

## 4. DuckBotOS Package Plan

All DuckBotOS packages live in `packages/`:

| Package | Role | Depends |
|---------|------|---------|
| `duckbotos-keyring` | GPG keyring for DuckBotOS APT repo | — |
| `duckbotos-base` | Core OS (Weston, Chromium, network, systemd) | weston, network-manager, systemd |
| `duckbotos-hermes` | Hermes agent + dashboard | duckbotos-base, hermes-agent |
| `duckbotos-openclaw` | OpenClaw gateway + plugin | duckbotos-base, openclaw |
| `duckbotos-lm-studio` | LM Studio headless + systemd service | duckbotos-base |
| `duckbotos-browseros` | BrowserOS + kiosk launcher | duckbotos-base, weston |
| `duckbotos-computer-use` | AT-SPI2 + Wayland portal MCP | duckbotos-base |
| `duckbotos-kiosk-hermes` | Weston kiosk + Chromium pointing at Hermes | duckbotos-hermes, duckbotos-browseros |
| `duckbotos-kiosk-openclaw` | Weston kiosk + Chromium pointing at OpenClaw | duckbotos-openclaw, duckbotos-browseros |
| `duckbotos-kiosk-hybrid` | GDM + session picker | duckbotos-hermes, duckbotos-openclaw |
| `duckbotos-meta-hermes` | Full Hermes ISO meta-package | duckbotos-kiosk-hermes, duckbotos-lm-studio |
| `duckbotos-meta-openclaw` | Full OpenClaw ISO meta-package | duckbotos-kiosk-openclaw, duckbotos-lm-studio |
| `duckbotos-meta-hybrid` | Full Both-mode ISO meta-package | duckbotos-kiosk-hybrid, duckbotos-lm-studio |

---

## 5. Three-ISO Build Strategy

Rather than one ISO with complex installer branching, build three separate ISOs:

```
# Herms-only ISO
duckbotos-hermes-x86_64.iso
  duckbotos-meta-hermes
  duckbotos-keyring
  duckbotos-base
  duckbotos-hermes
  duckbotos-lm-studio
  duckbotos-browseros
  duckbotos-computer-use
  duckbotos-kiosk-hermes

# OpenClaw-only ISO
duckbotos-openclaw-x86_64.iso
  duckbotos-meta-openclaw
  duckbotos-keyring
  duckbotos-base
  duckbotos-openclaw
  duckbotos-lm-studio
  duckbotos-browseros
  duckbotos-computer-use
  duckbotos-kiosk-openclaw

# Both-mode ISO (with GDM session picker)
duckbotos-both-x86_64.iso
  duckbotos-meta-hybrid
  duckbotos-keyring
  duckbotos-base
  duckbotos-hermes
  duckbotos-openclaw
  duckbotos-lm-studio
  duckbotos-browseros
  duckbotos-computer-use
  duckbotos-kiosk-hybrid
```

Each ISO has its own `Makefile` target and package list.

---

## 6. Base OS: Debian Trixie vs Ubuntu Noble

**Current cx-distro:** Debian 13 "Trixie" (debootstrap minbase)

**DuckBotOS decision:** Use **Ubuntu 24.04 LTS "Noble Numbat"** for these reasons:
- More familiar to desktop users
- Subiquity installer (better than Debian's debian-installer)
- Larger community + driver support
- Matches our research on Subiquity OEM autoinstall

**What changes:** Replace `lb config --distribution trixie` with `lb config --distribution noble` in the Makefile, and change debootstrap options accordingly.

Note: live-build works with Ubuntu base images too — it's not Debian-specific.

---

## 7. APT Repository Integration

DuckBotOS packages are built and stored in a local APT repository embedded in the ISO (offline mode):

```
output/
├── duckbotos-hermes-x86_64.iso
└── repo/                          # Embedded APT repo in ISO
    ├── pool/
    │   └── main/
    │       └── d/
    │           └── duckbotos-*/
    ├── dists/
    │   └── noble/
    │       ├── Release
    │       └── main/
    │           ├── binary-amd64/
    │           │   ├── Packages.gz
    │           │   └── Release
    └── db/
        └── packages.db
```

The `apt/` tooling in cx-distro handles signing and repo metadata generation.

---

## 8. Build Environment Requirements

From cx-distro Makefile deps target (unchanged for DuckBotOS):

```bash
# Build dependencies for live-build
sudo apt-get install -y \
    live-build \
    debootstrap \
    squashfs-tools \
    xorriso \
    isolinux \
    syslinux-efi \
    grub-pc-bin \
    grub-efi-amd64-bin \
    mtools \
    dosfstools \
    dpkg-dev \
    devscripts \
    debhelper \
    fakeroot \
    gnupg \
    syft \
    cyclonedx-cli \
    python3-pip
```

**Note:** live-build requires a **Linux host** — cannot build on macOS. This is why P2-1 (Linux VM) is a blocker.

---

## 9. CI/CD Build Pipeline

cx-distro has GitHub Actions workflows we can adapt:

- `build-iso.yml` — triggers on push to main, builds ISO, uploads as artifact
- `installation-tests.yml` — runs VMs to test the ISO installs correctly

For DuckBotOS, we'd add:
- Build all 3 ISO variants
- Run verification tests (ISO boots, services start, browser loads)
- Upload artifacts to GitHub Releases

---

## 10. Preseed/Autoinstall Files

cx-distro stores preseed files at `preseed/cx.preseed`. DuckBotOS will use Subiquity's `autoinstall.yaml` format (Ubuntu native) instead of Debian preseed:

```
iso/
├── live-build/          # Generated by lb config
│   └── config/
│       └── package-lists/
│           ├── duckbotos-hermes.list         # Package list for hermes ISO
│           ├── duckbotos-openclaw.list       # Package list for openclaw ISO
│           └── duckbotos-both.list           # Package list for both ISO
└── autoinstall/
    ├── autoinstall-hermes.yaml
    ├── autoinstall-openclaw.yaml
    └── autoinstall-both.yaml
```

---

## 11. Build Checklist

- [ ] Fork cxlinux-ai/cx-distro → Franzferdinan51/duckbotos-distro
- [ ] Change distribution in Makefile: `trixie` → `noble` (Ubuntu 24.04)
- [ ] Create `packages/duckbotos-keyring/` (GPG keyring)
- [ ] Create `packages/duckbotos-base/`
- [ ] Create `packages/duckbotos-hermes/`
- [ ] Create `packages/duckbotos-openclaw/`
- [ ] Create `packages/duckbotos-lm-studio/` (see docs/lm-studio.md)
- [ ] Create `packages/duckbotos-browseros/` (see docs/browseros.md)
- [ ] Create `packages/duckbotos-computer-use/` (see docs/computer-use.md)
- [ ] Create `packages/duckbotos-kiosk-hermes/`
- [ ] Create `packages/duckbotos-kiosk-openclaw/`
- [ ] Create `packages/duckbotos-kiosk-hybrid/`
- [ ] Create meta-packages (`duckbotos-meta-hermes`, `duckbotos-meta-openclaw`, `duckbotos-meta-hybrid`)
- [ ] Update Makefile with three ISO build targets
- [ ] Create `iso/autoinstall/autoinstall-*.yaml` for each variant
- [ ] Replace branding (Plymouth theme, wallpapers, ISO label, GDM theme)
- [ ] Update CI/CD workflows for DuckBotOS
- [ ] Run `make deps && make iso` in Linux VM — verify ISO boots
- [ ] Verify ISO boots to DuckBotOS splash screen
- [ ] Publish to GitHub Releases

---

*CX Linux Fork Guide v0.2 — 2026-06-29*
