# DuckBotOS — Desktop Control Architecture

> Updated 2026-06-29 14:24 EDT — Duckets confirmed `agent-sh/computer-use-linux` should be replaced with their own Lobster Edition; `trycua/cua` added as the VM orchestration layer.

---

## What lives where

```
DuckBotOS Kiosk Session (Weston, Wayland)
    │
    ├─ ~/.hermes/mcp.json              ← Hermes MCP server registry
    │   └─ mcpServers:
    │       ├─ newest-desktop-control  ← Duckets' local Lobster Edition (PRIMARY)
    │       └─ cua-driver (optional)   ← trycua/cua (Linux pre-release backend)
    │
    ├─ ~/.openclaw/mcp.json            ← OpenClaw MCP server registry (same format)
    │   └─ mcpServers:
    │       ├─ newest-desktop-control  ← same server, shared with Hermes
    │       └─ cua-driver (optional)
    │
    └─ /opt/duckbotos/desktop-control/ ← Installed source tree
        ├─ src/server.js               ← MCP stdio server entrypoint
        ├─ backends/desktop.js         ← PyAutoGUI + AT-SPI2 (Linux/macOS/Win)
        ├─ backends/android.js         ← ADB-based Android control
        ├─ backends/codex.js           ← Codex Computer Use detection (macOS)
        ├─ scripts/install.sh          ← Original Duckets installer (idempotent)
        └─ scripts/setup-config.js     ← Generates MCP server configs (canonical)

duckbotos-computer-use.service          ← systemd service, runs as kiosk user
    └─ /usr/bin/node /opt/duckbotos/desktop-control/src/server.js
```

---

## Why Newest Desktop Control, not agent-sh/computer-use-linux

| Aspect | Newest Desktop Control (Lobster Edition) | agent-sh/computer-use-linux |
|--------|------------------------------------------|------------------------------|
| License | MIT (Duckets' own code) | (external) |
| Tests | 38 passing | minimal |
| Install | `npm run setup:hermes` / `setup:openclaw` | Rust build from source |
| Setup matches our framework | YES — direct installer for Hermes AND OpenClaw | NO — manual JSON wiring |
| Number of tools | 20+ (mouse, keyboard, screenshot, clipboard, apps, windows, files, terminal, Android) | limited |
| Setup:openclaw one-liner | ✅ | ❌ |
| Setup:hermes one-liner | ✅ | ❌ |
| Setup:cua integration | ✅ built-in | ❌ |
| CHANGELOG | ✅ | minimal |
| Active maintainer | Duckets (Franzferdinan51) | third-party |

**Decision**: Lobster Edition is Duckets' own polished tool — pick it, wire it, ship it.

---

## Integration points — how agents talk to the desktop

### Hermes
Config file: `~/hermes-config.json` (the only Hermes config file). 

Format: `mcp_servers.{name}` where each value is a **JSON-STRINGIFIED** inner config object (NOT a nested object). Example from a real Hermes install:

```json
"mcp_servers": {
  "newest-desktop-control": "{"command":"node","args":["/opt/duckbotos/desktop-control/src/server.js"],"env":{},"transport":"stdio","startup_timeout_sec":20,"tool_timeout_sec":60}",
  "cua-driver": "...stringified..."  // optional
}
```

### OpenClaw
Config file: `~/.openclaw/openclaw.json` (default per `openclaw/src/config/paths.ts:resolveCanonicalConfigPath`).

Format: `mcp.servers.{name}` (nested under `mcp`, NOT top-level). Inner object is a NESTED object (NOT stringified). From `openclaw/src/config/schema.base.generated.ts`:

```json
"mcp": {
  "servers": {
    "newest-desktop-control": {
      "command": "node",
      "args": ["/opt/duckbotos/desktop-control/src/server.js"],
      "env": {}
    },
    "cua-driver": { ... }  // optional
    // strip transport + startup_timeout_sec + tool_timeout_sec (Claude Desktop fields, not OpenClaw schema)
  }
}
```

For OpenClaw EXTENSIONS (not MCP servers), use the separate `plugins.entries.{id}.enabled` + `config` block — also in `openclaw.json`.

### Two different concepts in OpenClaw
| Concept | Path | Format |
|---------|------|--------|
| MCP server process | `mcp.servers.{name}` | nested object |
| Extension/plugin | `plugins.entries.{name}` | enabled + config |

Brain plugin = extension (`plugins.entries.duckbot-memory`). Newest Desktop Control = MCP server (`mcp.servers.newest-desktop-control`).

### Configuration source of truth
Duckets' own `setup-config.js` script (`node scripts/setup-config.js openclaw`) generates the canonical config block. The postinst runs this script and uses its output verbatim. SETUP_OUT drives both Hermes and OpenClaw registrations, but **the format is transformed** for each:
- Hermes: JSON-stringify the inner object before writing to `mcp_servers.{name}`
- OpenClaw: strip `transport`/`startup_timeout_sec`/`tool_timeout_sec` fields, write nested object to `mcp.servers.{name}`

### Path summary (no longer use these wrong paths)
| Wrong (was) | Correct |
|-------------|---------|
| `~/.openclaw/openclaw.json` | `~/.openclaw/openclaw.json` |
| `~/.openclaw/mcp.json` (separate file) | `mcp.servers` block in openclaw.json |
| `~/.hermes/mcp-servers.json` | `~/hermes-config.json` |
| `~/.hermes/mcp.json` | `~/hermes-config.json` |

These wrong paths were a major bug class in v0.2.0 — fixed in v0.2.1.

---

## Tools exposed (20+)

| Group | Tools |
|-------|-------|
| Screenshots | `desktop_screenshot`, `desktop_get_pixel_color` |
| Mouse | `desktop_mouse_move`, `desktop_mouse_click`, `desktop_mouse_scroll`, `desktop_cursor_position` |
| Keyboard | `desktop_keyboard_type`, `desktop_keyboard_press`, `desktop_keyboard_hotkey` |
| Screen info | `desktop_get_screen_size`, `desktop_screen_info` |
| Clipboard | `desktop_clipboard_read`, `desktop_clipboard_write` |
| Apps/Windows | `desktop_launch_app`, `desktop_window_list`, `desktop_window_activate` |
| Files / Terminal | `desktop_file_read`, `desktop_file_write`, `desktop_run_script`, `desktop_terminal` |
| Lookup | `desktop_rs_lookup` (game lookup) |
| Android (ADB) | `android_*` (if adb installed) |

---

## trycua/cua — VM orchestration layer

DuckBotOS optionally ships `duckbotos-cua-bridge` which adds the trycua/cua stack:

- **`pip install cua cua-driver cua-sandbox`**
- **`/usr/local/bin/cua`** CLI wrapper for the Python SDK
- **`cua-driver mcp`** — second computer-use MCP server (alternative to Newest Desktop Control)
- **`cua-sandbox`** — programmatic VMs (QEMU, Apple Virtualization, Docker)

Use cases:

| Use case | Tool |
|----------|------|
| Spin up a Linux build VM in CI | `cua-sandbox`: `Sandbox.ephemeral(Image.linux())` |
| Run the built ISO headlessly to test | same |
| Use cua-driven computer-use instead of PyAutoGUI | `cua-driver mcp` |
| Cross-OS agent testing (Linux/macOS/Windows/Android) | `Sandbox.ephemeral(Image.macos())` etc. |

Reference: <https://github.com/trycua/cua>

---

## Setup ordering (chroot build)

```
1. debootstrap Ubuntu 24.04 → /tmp/duckbotos-chroot
2. mount -o bind /dev /proc /sys /tmp/duckbotos-chroot/{dev,proc,sys}
3. chroot /tmp/duckbotos-chroot /bin/bash
4. apt install -y nodejs python3.12 python3-pip git ...
5. install -d /opt/duckbotos/desktop-control
   git clone https://github.com/Franzferdinan51/desktop-control-lobster-edition-skill
6. pip3 install -r /opt/duckbotos/desktop-control/requirements.txt
7. bash /opt/duckbotos/desktop-control/scripts/install.sh --no-tests --no-config
8. /usr/bin/node /opt/duckbotos/desktop-control/src/server.js (smoke test)
9. dpkg-buildpackage for duckbotos-computer-use → deb installed → postinst runs
```

In CI: GitHub Actions runs this with `ubuntu-24.04` runner, installs all deps, and verifies the deb builds with `lintian`.

---

## Health checks

```bash
# Is the MCP server running?
systemctl status duckbotos-desktop-control

# Can agents see it?
cat ~/.hermes/mcp.json
cat ~/.openclaw/mcp.json

# Smoke test the MCP server directly
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  node /opt/duckbotos/desktop-control/src/server.js
# should print: 20+ tool definitions

# Test from an agent
hermes --new "list all MCP tools"   # should include newest-desktop-control
openclaw mcp list                    # should include newest-desktop-control
```

---

## Future enhancements (not v1.0)

- **AT-SPI2 acceleration** — currently PyAutoGUI does pixel-based clicks; AT-SPI2 would let us drive accessibility-named widgets directly (faster, more reliable)
- **Vision fallback** — when pixel-based clicks fail, screenshot + Vision LLM decides where to click
- **Voice control** — add `hey-duck` wake word + Whisper.cpp for hands-free commands
- **Multi-monitor** — `desktop_get_screen_info` already returns monitor count; expose `desktop_window_to_monitor`
- **Sandboxed execution** — currently the desktop server runs as the kiosk user; for untrusted agents add a per-session jail

---

*Last updated: 2026-06-29 14:24 EDT by OpenClaw (DuckBot)*