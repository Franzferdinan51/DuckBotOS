# DuckBotOS — Agent Handoff

> For the agent continuing this build. Everything is on GitHub. Clone and go.

---

## What This Is

**DuckBotOS** — a custom Ubuntu 24.04 LTS-based agent-first operating system where Hermes and/or OpenClaw IS the desktop environment. Not an app you open, but the environment you boot into.

**Two repos:**
- `Franzferdinan51/DuckBotOS` — project docs + this handoff
- `Franzferdinan51/cx-distro` (branch: `duckbotos`) — ISO build pipeline

**Clone everything:**
```bash
git clone --recurse-submodules https://github.com/Franzferdinan51/DuckBotOS
cd DuckBotOS
git clone https://github.com/Franzferdinan51/cx-distro -b duckbotos cx-distro
```

---

## The Build (do this first)

```bash
cd DuckBotOS/cx-distro

# Read the build config
cat src/args.sh | grep -E "^export TARGET_|^export DUCKBOTOS"

# Set mode (hermes | openclaw | both)
export DUCKBOTOS_MODE=hermes

# Install deps
sudo apt update && sudo apt install -y \
  live-build debootstrap squashfs-tools xorriso \
  isolinux syslinux-efi grub-pc-bin grub-efi-amd64-bin \
  mtools dosfstools dpkg-dev devscripts debhelper \
  fakeroot gnupg python3-pip wget curl git rsync \
  uuid-runtime cpio gzip xz-utils

# Build!
./src/build.sh
```

**Output:** `*.iso` in the current directory after ~30-60 min.

---

## Key Files to Know

### Build System
- `cx-distro/src/args.sh` — Ubuntu 24.04 config, DuckBotOS identity, mode selection
- `cx-distro/src/build.sh` — main build entry point (debootstrap → chroot → mods → iso)
- `cx-distro/Makefile` — `make deps`, `make iso` wrappers
- `cx-distro/src/mods/50-duckbotos-meta-mod/install.sh` — reads DUCKBOTOS_MODE, selects packages
- `cx-distro/src/mods/51-duckbotos-install-mod/install.sh` — clones fork, builds packages, installs by mode

### Packages (12 total — all have `debian/control` + `debian/rules`)
| Package | Purpose | Key File |
|---------|---------|----------|
| `duckbotos-base` | Core OS: Python + Node + Weston | Essential |
| `duckbotos-hermes` | Hermes v0.17 agent at :9119 | `debian/postinst` (git clone + pip install) |
| `duckbotos-brain` | **DuckBot RAG memory brain** — 4-tier CoALA, 67 MCP tools, FSRS, Wing/Room/Drawer palace | `debian/postinst` (git clone + venv + LM Studio config + plugin registration) |
| `duckbotos-openclaw` | OpenClaw gateway at :18789 + brain plugin wired in | `debian/postinst` (git clone + npm install + brain plugin JSON) |
| `duckbotos-lm-studio` | LM Studio API at :1234 | `debian/lm-studio-api.service` |
| `duckbotos-browseros` | BrowserOS default browser | `debian/postinst` (sets xdg default) |
| `duckbotos-computer-use` | AT-SPI2 + Wayland MCP server :9600 | `debian/computer-use-linux.service` |
| `duckbotos-kiosk` | Weston + Chromium kiosk (the OS surface) | `debian/duckbotos-kiosk-launch.sh` |
| `duckbotos-kiosk-hermes` | Pre-configures kiosk for Hermes :9119 | `debian/postinst` |
| `duckbotos-session-picker` | Both-mode UI at :8080 | `session-picker.py` + `index.html` |
| `duckbotos-hybrid` | Meta: both agents + session picker | Depends on all above |
| `duckbotos-meta` | Default meta-packages | hermes/openclaw/hybrid selects |
| `duckbotos-branding` | Plymouth + GDM + MOTD | Architecture: all |

### The Kiosk Architecture (how it works)
```
duckbotos-kiosk-launch.sh:
  1. weston --backend=drm-backend.so --shell=kiosk --idle-time=0
  2. chromium --kiosk --app=<URL from /etc/duckbotos/kiosk-mode>

/etc/duckbotos/kiosk-mode contains the URL:
  - Hermes mode:     http://localhost:9119
  - OpenClaw mode:   http://localhost:18789/plugins/openclawos
  - Hybrid mode:     http://localhost:8080 (session picker)
```

### Session Picker (Both mode)
- `duckbotos-session-picker/index.html` — dark-themed web UI, keyboard nav (1/2/3 + Enter)
- `duckbotos-session-picker/session-picker.py` — Python HTTP server on :8080
- Auto-selects Hermes after 3 seconds

---

## Known Issues / To Fix

1. **First CI build will fail** — GitHub Actions will surface errors. Common issues:
   - `debootstrap` needs root — CI uses `sudo`
   - Build deps may be missing some package
   - The mods assume internet access in the chroot — might need `lb config --apt-http-proxy` or offline mode

2. **HERMES_URL variable in postinst** — the `REAL_HOME` detection (`getent passwd | awk -F: '$3 >= 1000 {print $6; exit}'`) works in the chroot but might get the wrong user. The chroot runs as root; the real user is created by the Ubuntu installer later. May need to use `/home/ubuntu` or a known username.

3. **No `changelog` files** — each package needs a `debian/changelog` for `dpkg-buildpackage`. These are auto-generated with `dch -i` but haven't been created yet.

4. **cxlinux-ai/cx-distro upstream** — the fork still has `upstream` remote pointing to cxlinux-ai/cx-distro. Can merge upstream changes with `git fetch upstream && git merge upstream/main`.

5. **LM Studio install** — the `duckbotos-lm-studio` package doesn't actually install LM Studio. It needs to:
   - Add the LM Studio APT repo key + sources.list
   - `apt install lm-studio` (they have an official .deb)
   - Or download the AppImage and convert to deb with `appimage2deb`
   - Current postinst only writes the config file — doesn't install LM Studio itself

6. **BrowserOS install** — same issue. `duckbotos-browseros` postinst sets it as default browser but doesn't actually install BrowserOS. Need to:
   - Download from `https://github.com/browseros-ai/BrowserOS/releases`
   - Install the `.AppImage` or `.deb`
   - Add to PATH

7. **computer-use-linux** — needs to be built from source (Rust/cargo). The package `debian/control` lists `cargo` as a Build-Depends but the actual build from source isn't in the postinst. Could use pre-built binaries from their releases instead.

---

## Next Steps in Order

1. **Run `./src/build.sh` in a Linux VM** — first build will fail, but the error logs tell you what's broken
2. **Fix the failing package(s)** based on build output
3. **Iterate** — repeat until ISO builds successfully
4. **Test the ISO** in UTM or real hardware:
   - Boot from ISO
   - Install DuckBotOS
   - Verify services start: `systemctl --user status hermes-gateway`, `systemctl status lm-studio-api`, `systemctl --user status duckbotos-brain-watcher`
   - Verify kiosk loads the correct URL
   - Verify brain: `openclaw plugins list | grep duckbot-memory`
5. **Push fixes** to the `duckbotos` branch — CI auto-builds on every push

---

## Important Context

**Why separate repos?** The `cx-distro/` folder is a fork of `cxlinux-ai/cx-distro`. It has its own git history. We keep it as a subdirectory of the main repo so one `git clone` gets everything.

**License:** Apache 2.0 (our code), BSL 1.1 (cxlinux-ai inherited build pipeline), MIT (Hermes + OpenClaw)

**D1-D5 all confirmed:**
- GPU: NVIDIA (keep cx-gpu-nvidia package)
- Boot: Both (Live USB + full install)
- License: Apache 2.0 with CX Linux attribution
- Both mode GDM picker: Yes
- LM Studio scope: DuckBotOS only (local models in OS, cloud-only stays for other projects)

**Ubuntu version:** 24.04 LTS Noble Numbat

**Build machine specs needed:** Ubuntu 24.04 Server, 4+ cores, 8GB+ RAM, 64GB+ disk

---

## Quick Commands Reference

```bash
# Full build
cd cx-distro && ./src/build.sh

# Build just one package (for debugging)
cd cx-distro/packages/duckbotos-hermes && dpkg-buildpackage -us -uc -b

# View package contents without installing
dpkg-deb -c ../duckbotos-hermes_*.deb

# Check package dependencies
dpkg-checkbuilddeps   # must be run in package dir

# Generate changelog entry
cd cx-distro/packages/duckbotos-hermes && dch -i "Initial DuckBotOS package"
```

---

*Last updated: 2026-06-29 12:25 EDT by OpenClaw (DuckBot)*
*Push any fixes to `duckbotos` branch — CI auto-builds on every push*