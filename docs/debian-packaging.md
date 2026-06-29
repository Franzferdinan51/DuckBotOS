# Debian Packaging Guide for DuckBotOS

> How to write `debian/control` files and related packaging artifacts for DuckBotOS packages.
> Assumes Ubuntu 24.04 (Noble) base, debhelper compat 13, and `debhelper-compat` build system.
> Read `docs/cx-linux-fork.md` first for how the cx-distro fork is structured.

---

## 1. Overview

Every Debian package has a **`debian/control`** file that declares:
- **Source package** — the recipe name, build dependencies, and upstream metadata
- **Binary package(s)** — one or more stanza(s) describing what gets installed

Each `.deb` binary package = one stanza under the source stanza.

```
Source: foo
Section: utils
Priority: optional
Maintainer: My Name <me@example.com>
Build-Depends: debhelper-compat (= 13)
Standards-Version: 4.7.0

Package: foo
Architecture: any
Depends: ${misc:Depends}, bar (>= 1.0)
Description: does foo things
```

---

## 2. Source Stanza Fields

| Field | Required | Notes |
|-------|----------|-------|
| `Source` | ✅ | Package name (kebab-case, unique in archive) |
| `Section` | ✅ | `admin`, `utils`, `net`, `python`, etc. |
| `Priority` | ✅ | `optional` for all DuckBotOS packages |
| `Maintainer` | ✅ | `Name <email>` format |
| `Build-Depends` | ✅ | Comma-separated build deps; `debhelper-compat (= 13)` is standard |
| `Standards-Version` | | Latest stable is `4.7.0` (update periodically) |
| `Homepage` | | URL to project |
| `Vcs-Browser` | | GitHub/GitLab web URL |
| `Vcs-Git` | | `https://...git` URL |
| `Rules-Requires-Root` | | `no` = no root needed at build time |

---

## 3. Binary Stanza Fields

| Field | Required | Notes |
|-------|----------|-------|
| `Package` | ✅ | Unique binary package name |
| `Architecture` | ✅ | `all` (no arch), `any` (compile for host), `amd64`, `arm64`, etc. |
| `Depends` | ✅ | Runtime deps; `${misc:Depends}` is mandatory first |
| `Pre-Depends` | | Like Depends but must be installed BEFORE this package unpacks |
| `Recommends` | | Strong suggestions (installed by default) |
| `Suggests` | | Weak suggestions (user-initiated) |
| `Conflicts` | | Packages that cannot be co-installed |
| `Replaces` | | Files this package takes over |
| `Description` | ✅ | Two-line format: short summary on line 1, blank line, long description |

### Description Field Format

```
Description: Short summary (≤60 chars)
 Longer description here. Lines are wrapped at ~76 chars.
 Can have multiple paragraphs separated by a blank line.
 .
 Each dot+space (". ") starts a new paragraph.
```

---

## 4. Architecture Values

| Value | Meaning |
|-------|---------|
| `all` | No compiled code — pure scripts, configs, docs. Most DuckBotOS packages use this. |
| `any` | Compiled C/Rust/Go — built for the build machine's architecture |
| `amd64` | Intel/AMD 64-bit only |
| `arm64` | ARM 64-bit only |
| `anyamd64` | Any arch, but only built on amd64 |

---

## 5. Dependency Syntax

```
Depends: ${misc:Depends}                        ← always include first
Depends: foo (>= 1.0), bar (<= 2.0)             ← version constraints
Depends: foo | bar                               ← alternative (foo OR bar)
Depends: ${python3:Depends}                      ← Python3 sysdeps via helpers
Recommends: weston                               ← installed by default, not mandatory
Suggests: lm-studio-server                      ← optional add-on
Conflicts: hermesos-base (< 1.0)                ← cannot co-install
Breaks: old-package (< 2.0)                     ← breaks upgrades from old version
```

---

## 6. DuckBotOS Package Conventions

### Meta Packages (Architecture: all)

Meta packages have no files of their own — they only declare `Depends` on other packages. Always `Architecture: all`.

```
Package: duckbotos-meta
Architecture: all
Depends: ${misc:Depends},
 duckbotos-base,
 duckbotos-hermes,
 duckbotos-openclaw
Description: ...
```

### Base Packages

```
Package: duckbotos-base
Architecture: all
Depends: ${misc:Depends},
 ubuntu-desktop-minimal,
 weston,
 xdg-desktop-portal,
 ...
Description: ...
```

### CLI Tool Packages

```
Package: duckbotos-lm-studio
Architecture: all
Depends: ${misc:Depends},
 lm-studio-server           ← pre-built .deb or external package
Description: LM Studio headless model server
```

### Python Packages

For packages that install Python tools via pip:

```
Package: duckbotos-nlpkg
Architecture: all
Depends: ${misc:Depends}, ${python3:Depends}
Build-Depends: debhelper-compat (= 13), python3-all-dev, python3-pip
Description: Natural language package manager for DuckBotOS
```

---

## 7. Complete Minimal Example

```
Source: duckbotos-example
Section: admin
Priority: optional
Maintainer: DuckBotOS Team <team@duckbotos.ai>
Build-Depends: debhelper-compat (= 13)
Standards-Version: 4.7.0
Homepage: https://github.com/Franzferdinan51/DuckBotOS
Rules-Requires-Root: no

Package: duckbotos-example
Architecture: all
Depends: ${misc:Depends},
 curl,
 wget,
 git,
 htop
Description: Example DuckBotOS package
 A minimal example showing the debian/control format.
 .
 This package installs basic shell utilities used by all
 DuckBotOS modes. It is a dependency of duckbotos-base.
```

---

## 8. Full Debian Package Build

A complete package directory looks like:

```
packages/duckbotos-example/
├── debian/
│   ├── control          ← THIS FILE
│   ├── copyright        ← License file (Apache 2.0 for DuckBotOS packages)
│   ├── rules            ← Build script (usually just "include /usr/share/dh-sequence/dh_python3")
│   ├── install          ← List of files to install (e.g., "etc/ usr/bin/")
│   └── postinst         ← Optional: commands run after install (e.g., update-alternatives)
└── files to package/
    ├── etc/
    └── usr/
```

### debian/rules (standard Python/standalone package)

```makefile
#!/usr/bin/make -f

%:
    dh $@

override_dh_auto_install:
    dh_auto_install --destdir=debian/duckbotos-example
```

### debian/install (what gets packaged)

```
etc/duckbotos/        etc/
usr/bin/duckbotos    usr/bin/
```

---

## 9. Version Numbering

DuckBotOS packages follow Debian versioning:

```
<upstream_version>-<debian_revision>
```

Examples:
- `0.1.0-1` — First Debian revision of upstream 0.1.0
- `0.1.0-2duckbotos1` — Second revision, DuckBotOS-specific patch

---

## 10. Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing `${misc:Depends}` in `Depends` | Always add `${misc:Depends},` as the first item |
| Description without blank line separator | Use `. ` on its own line to separate paragraphs |
| Binary stanza before source stanza | Source stanza MUST come first |
| `Architecture: any` for pure-script packages | Use `all` — `any` is for compiled code only |
| Non-ASCII in Maintainer field | Use ASCII name and angle-bracket email |
| Missing `Build-Depends` on build-essential | `debhelper-compat (= 13)` pulls in the essentials |

---

## 11. Useful Commands

```bash
# Check control file syntax (no package build needed)
dpkg-checkbuilddeps          # exits 0 if build deps satisfied

# Build a package (from package parent dir)
dpkg-buildpackage -us -uc   # -us = no signing, -uc = no changes file

# Install locally built .deb
sudo dpkg -i duckbotos-example_0.1.0-1_amd64.deb
sudo apt --fix-broken install   # fix any dependency issues

# List contents of a .deb
dpkg-deb -I duckbotos-example_0.1.0-1_amd64.deb

# Extract control info
dpkg-deb --field duckbotos-example_0.1.0-1_amd64.deb Package Version Architecture
```

---

## 12. External Packages (No Rebuild Needed)

For packages that exist as `.deb` upstream (LM Studio, BrowserOS, Hermes, OpenClaw):

- Do NOT rebuild them — reference the upstream `.deb` or external install script
- Use a **wrapper package** that declares the external dep:

```
Package: duckbotos-lm-studio
Architecture: all
Depends: ${misc:Depends}, lm-studio-server
Description: DuckBotOS LM Studio integration
```

- Document the install method in `debian/postinst` (curl|bash for unofficial .debs)

---

## 13. Related Docs

- `packages/duckbotos-meta/debian/control` — Reference for all 7 DuckBotOS package control stanzas
- `docs/cx-linux-fork.md` — How the cx-distro fork is structured
- `docs/build-guide.md` — Full ISO build step-by-step
- `docs/contributing.md` — How to add new packages to the ISO build

---

*This doc covers debian/control authoring. For the full Debian build system (rules, patches, signing), see the Debian New Maintainer's Guide.*

---

## 14. Pre-Build Audit (REQUIRED before committing changes)

**Always run `scripts/audit-debian-packages.py` before committing any `debian/control` or `debian/postinst` change.** The audit catches:

1. **Missing required files** — `control`, `rules`, `changelog` per source package
2. **Binary package name collisions** — two source packages generating the same binary name (would fail at dpkg install)
3. **Internal Depends violations** — `Depends:` entries pointing to non-existent DuckBotOS packages

```bash
$ python3 scripts/audit-debian-packages.py
PACKAGE                             CTRL  CHANGELOG  RULES  POSTINST  SERVICES   GIT OK
------------------------------------------------------------------------------------------
duckbotos-base                      ✅     ✅          ✅      ✅         —          ✅
...
============================================================
PACKAGE COLLISION CHECK
============================================================
✅ All 18 binary package names are unique across 15 source packages
============================================================
SUMMARY
============================================================
✅ READY for dpkg-buildpackage
```

### What bit us in v0.2.0 → v0.2.2

- `duckbotos-meta` was generating binaries `duckbotos-{hermes,openclaw,hybrid}` that collided with the standalone source packages of the same names. Renamed to `duckbotos-mode-{hermes,openclaw,hybrid}`.
- `duckbotos-kiosk` was also generating `duckbotos-kiosk-hermes` (collision). Removed the colliding binary stanza — that package belongs to the standalone `duckbotos-kiosk-hermes` source.
- `Conflicts: duckbotos-kiosk-openclaw` in `duckbotos-kiosk-hermes/debian/control` pointed at a phantom package. Created the full `duckbotos-kiosk-openclaw/` source package.

**Lesson:** Use unique names for binary packages that come from different source packages. Either give each source its own binary name, or have ONE source package generate multiple binaries (and have the other source packages NOT generate the same binary).

### Naming convention for DuckBotOS

| Pattern | Usage |
|---------|-------|
| `duckbotos-<role>` | Service packages: `duckbotos-kiosk`, `duckbotos-brain`, `duckbotos-hermes` |
| `duckbotos-kiosk-<mode>` | Kiosk mode URLs: `duckbotos-kiosk-hermes`, `duckbotos-kiosk-openclaw` |
| `duckbotos-mode-<mode>` | Install mode meta-packages: `duckbotos-mode-hermes`, `duckbotos-mode-openclaw`, `duckbotos-mode-hybrid` |
| `duckbotos-meta` | Catch-all default meta |

