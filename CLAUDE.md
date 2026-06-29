# DuckBotOS — Agent Context

> This file is for Claude/agent context when working in this repository.

## Two-Repo Architecture

DuckBotOS uses **two separate GitHub repos**:

| Repo | URL | Branch | Role |
|------|-----|--------|------|
| **DuckBotOS** (this repo) | github.com/Franzferdinan51/DuckBotOS | `main` | Docs, specs, source packages, CI |
| **cx-distro** | github.com/Franzferdinan51/cx-distro | `duckbotos` | ISO build pipeline (sibling subdirectory) |

```
~/Desktop/DuckBotOS/           ← this repo (main)
├── CLAUDE.md                  ← you are here
├── packages/                  ← Debian source packages (15 duckbotos-* packages)
├── docs/                      ← Architecture, installer, provider, build docs
├── scripts/                   ← audit-debian-packages.py, verify-config-formats.py
├── cx-distro/                 ← cx-distro fork (sibling subdirectory)
│   ├── packages/              ← Debian packages for ISO (also duckbotos-*)
│   ├── src/                  ← Build scripts, mods
│   ├── iso/                  ← live-build config
│   └── scripts/              ← Build helpers
└── .github/workflows/         ← GitHub Actions CI
```

**Clone together:**
```bash
git clone https://github.com/Franzferdinan51/DuckBotOS
cd DuckBotOS
git clone https://github.com/Franzferdinan51/cx-distro -b duckbotos cx-distro
```

## Key Commands

```bash
# Audit all packages (runs against cx-distro/packages/)
python3 scripts/audit-debian-packages.py

# Verify config formats
python3 scripts/verify-config-formats.py

# Trigger ISO build (push to main or duckbotos branch)
git push origin main
```

## Package Structure

- **This repo (`packages/`)** — source package specs, referenced by docs
- **cx-distro (`cx-distro/packages/`)** — actual buildable Debian packages with `debian/control`, `debian/rules`, `debian/changelog`, `debian/postinst`

Both directories have the same `duckbotos-*` package names. Use the cx-distro versions for building.

## Newest Desktop Control

The desktop automation system is **clawdwatch-lobster-edition** (MIT):
- GitHub: `Franzferdinan51/clawdwatch-lobster-edition`
- Package: `duckbotos-computer-use`

## Build Workflow

ISO builds run via `.github/workflows/build-iso.yml` on GitHub Actions:
1. Checks out DuckBotOS (this repo)
2. Clones cx-distro fork fresh into `duckbot-os-repo/cx-distro/`
3. Installs build deps (`live-build`, `debootstrap`, etc.)
4. Runs `./src/build.sh` in `cx-distro/`
5. Uploads `.iso` artifact + SHA256 checksum

## Important Notes

- **DO NOT** hardcode usernames like `duckets` in systemd service files — use `%h` for the installing user's home
- **DO NOT** commit to `duckbotos` branch directly in cx-distro — that branch is owned by the DuckBotOS sync workflow
- **Audit before committing** any package changes: `python3 scripts/audit-debian-packages.py`
