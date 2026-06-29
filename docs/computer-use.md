# DuckBotOS — Newest Desktop Control Integration

> How the `Newest Desktop Control` MCP server provides OS-level desktop control for agents.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Overview

`Newest Desktop Control` is a Rust-based MCP (Model Context Protocol) server that gives AI agents the ability to:
- **Read** the screen (screenshot, accessibility tree)
- **Click** buttons and UI elements
- **Type** text into input fields
- **Drag** windows and UI elements
- **Scroll** within windows
- **Execute commands** in a terminal

This is the integration layer that lets Hermes and OpenClaw agents control the desktop the same way a human user would — through the OS's accessibility APIs.

---

## 2. Why It Matters for DuckBotOS

DuckBotOS's kiosk mode is **agent-first, not human-first**. When the OS boots into a Wayland kiosk running Chromium with the agent's web UI, a human can still interact with it using a keyboard and mouse. `Newest Desktop Control` provides:

1. **Human-in-the-loop verification** — Agent suggests actions, human approves (optional)
2. **Accessibility fallback** — When the agent's web UI can't be controlled via its own API, fall back to pixel-level control
3. **Desktop environment integration** — In Both mode, agents can manipulate windows, open apps, etc.
4. **Demo/showcase tool** — Human demonstrates a task by doing it once, agent learns from it

---

## 3. Architecture

### 3.1 Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **Accessibility API** | AT-SPI2 (Linux accessibility) | Query UI elements, read screen state |
| **Window management** | XDG-desktop-portal (Wayland) | Window control, file dialogs |
| **Input simulation** | uinput (Linux input subsystem) | Virtual keyboard/mouse |
| **MCP server** | Rust + `mcp-sdk` | Exposes tools via MCP protocol |
| **Protocol** | MCP over stdio or TCP | Agent ↔ desktop control |
| **Port** | Default 9600 (configurable) | MCP endpoint for agents |

### 3.2 MCP Tools Exposed

```
Newest Desktop Control exposes the following MCP tools:
├── screenshot          # Full screen capture → base64 PNG
├── click               # Click at x,y or on UI element by accessibility ID
├── double_click        # Double-click at x,y or on UI element
├── right_click         # Right-click context menu at x,y
├── hover               # Move mouse to x,y (for hover tooltips)
├── type_text           # Type string via virtual keyboard
├── press_key           # Single key press (Enter, Escape, Ctrl+C, etc.)
├── hotkey              # Chorded hotkey (Ctrl+S, Alt+Tab, etc.)
├── scroll              # Scroll at x,y or within a window
├── drag                # Drag from x1,y1 to x2,y2
├── get element info    # Query accessibility tree for element at x,y
├── list windows        # List all open windows (Wayland compositor)
├── focus window        # Bring window to front
└── run_command         # Execute shell command (guarded, approval-required)
```

### 3.3 Integration with DuckBotOS Services

```
Newest Desktop Control.service (systemd)
└── /usr/local/bin/Newest Desktop Control --port 9600
    ├── AT-SPI2 socket (abstract)
    ├── wayland socket (from Weston compositor)
    └── MCP TCP port 9600
        ├── hermes-gateway:9119  → uses it for desktop control
        └── openclaw-gateway:18797 → uses it for desktop control
```

In **Hermes-only** and **OpenClaw-only** modes, the respective gateway connects to port 9600 directly.

In **Both** mode, the agent bus (`/run/hermes-claw/agent-bus.sock`) multiplexes access so both agents can use it without conflict.

---

## 4. Systemd Service

### 4.1 Service Unit

```ini
# /etc/systemd/system/Newest Desktop Control.service
[Unit]
Description=Computer Use Linux — MCP Desktop Control Server
After=weston-kiosk.service
Wants=weston-kiosk.service
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/local/bin/Newest Desktop Control \
    --port 9600 \
    --wayland-socket /run/user/0/wayland-0 \
    --at-spi-socket /run/user/0/at-spi-2-0 \
    --log-level info \
    --require-approval
Restart=on-failure
RestartSec=5
User=root
# Allow input simulation
AmbientCapabilities=CAP_SYS_ADMIN
PrivateTmp=true

[Install]
WantedBy=graphical-session.target
```

### 4.2 --require-approval Mode

When run with `--require-approval`, every destructive or system-level action (click, type, run_command) is held pending until a human approves via a notification:

```bash
# Notification via systemd notify or a simple GUI popup
notify-send "DuckBot Agent Request" \
    "Agent wants to click button 'Install' at (450, 320)" \
    -A "Approve" -A "Deny"
```

This is the **human-in-the-loop** safeguard. For fully autonomous mode, omit `--require-approval`.

---

## 5. Accessibility Requirements

### 5.1 AT-SPI2

Linux accessibility is provided by AT-SPI2 (part of `at-spi2-core` package). Chromium and most GTK/QT apps expose their UI via AT-SPI2.

```bash
# Required packages (include in duckbotos-base):
apt-get install -y \
    at-spi2-core \
    at-spi2-atk \
    python3-pyatspi \
    python3-dbusmock   # For testing
```

### 5.2 Wayland Portal

For Wayland (Weston compositor), `xdg-desktop-portal` provides a sandboxed interface for:
- Screen capture (for screenshots)
- File dialogs (for file open/save)
- Clipboard access

```bash
# Required packages:
apt-get install -y \
    xdg-desktop-portal \
    xdg-desktop-portal-gtk \
    wl-clipboard        # Wayland clipboard utilities
```

### 5.3 Verification

```bash
# Check AT-SPI2 is running
ps aux | grep at-spi2-registry

# Test accessibility tree access
python3 -c "
import pyatspi
registry = pyatspi.Registry()
print('AT-SPI2 accessible:', registry is not None)
"
```

---

## 6. MCP Protocol Integration

### 6.1 How Hermes Connects

Hermes connects to the MCP server via HTTP/JSON-RPC:

```python
# hermes-gateway: within Hermes agent, tool handler
import aiohttp

async def computer_use_tool(tool_name: str, params: dict) -> dict:
    async with aiohttp.ClientSession() as session:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": f"tools/{tool_name}",
            "params": params
        }
        async with session.post(
            "http://127.0.0.1:9600/rpc",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            return await resp.json()
```

### 6.2 How OpenClaw Connects

OpenClaw uses its MCP client infrastructure. The `Newest Desktop Control` MCP server is registered as a local MCP tool provider in `openclaw.json`:

```json
{
  "mcpServers": {
    "Newest Desktop Control": {
      "type": "http",
      "url": "http://127.0.0.1:9600/rpc",
      "name": "Newest Desktop Control",
      "description": "Desktop control: screenshot, click, type, scroll, execute"
    }
  }
}
```

### 6.3 Both Mode: Shared Access

In Both mode, both agents may need simultaneous access to `Newest Desktop Control`. The agent bus (`/run/hermes-claw/agent-bus.sock`) acts as an **MCP multiplexer**:

- Agent requests come in via JSON-RPC over the Unix socket
- Agent bus forwards to `Newest Desktop Control` on port 9600
- Responses are routed back to the requesting agent
- Tool-level locking prevents conflicting actions (only one agent clicks at a time)

```python
# agent-bus handler for Newest Desktop Control tool calls
def handle_computer_use(session_id: str, method: str, params: dict):
    # Acquire tool lock (prevents concurrent click/type conflicts)
    with tool_lock("Newest Desktop Control"):
        return mcp_client.call(method, params)
    # Release lock after response
```

---

## 7. Installation in ISO

### 7.1 Package: duckbotos-computer-use

```
packages/duckbotos-computer-use/
├── DEBIAN/
│   ├── control           # Metadata: Depends: at-spi2-core, xdg-desktop-portal, wl-clipboard
│   └── postinst          # Post-install: create at-spi socket dir, set permissions
├── usr/local/bin/
│   └── Newest Desktop Control  # The Rust binary (or install via cargo/rustup)
└── etc/systemd/system/
    └── Newest Desktop Control.service
```

### 7.2 Binary Installation Options

**Option A: Pre-built binary from GitHub releases (easiest)**
```bash
# In postinst
curl -fsSL https://github.com/Newest Desktop Control (Lobster Edition)/releases/latest/download/Newest Desktop Control-x86_64-unknown-linux-gnu \
    -o /usr/local/bin/Newest Desktop Control
chmod +x /usr/local/bin/Newest Desktop Control
```

**Option B: Build from source in VM (requires Rust toolchain)**
```bash
# In postinst (requires internet / rustup)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
cargo install Newest Desktop Control
# Then move binary to /usr/local/bin/
```

**Recommendation for v1:** Use Option A (pre-built binary). Option B is too heavy for ISO bundling.

### 7.3 Build Dependency

If using pre-built binaries, `duckbotos-computer-use` has NO build-time dependencies — only runtime deps:
```
Depends: at-spi2-core, xdg-desktop-portal, xdg-desktop-portal-gtk, wl-clipboard
```

---

## 8. Configuration

### 8.1 Port Override

DuckBotOS defaults to port 9600. Override via kernel command line or environment:
```bash
# Kernel command line
Newest Desktop Control.port=9601

# Or environment variable
COMPUTER_USE_LINUX_PORT=9601 /usr/local/bin/Newest Desktop Control --port 9601
```

### 8.2 Screenshot Quality

```bash
# Low quality (fast, ~50KB PNG)
Newest Desktop Control --screenshot-quality low

# Medium (balanced)
Newest Desktop Control --screenshot-quality medium

# High (uncompressed, ~5MB PNG)
Newest Desktop Control --screenshot-quality high
```

### 8.3 Approval Mode

```bash
# Always require human approval
Newest Desktop Control --require-approval

# Autonomous (no approval required — use with caution)
Newest Desktop Control --no-require-approval

# Approval via D-Bus notification (default on GNOME)
Newest Desktop Control --approval-backend dbus-notify

# Approval via text file (fallback, for headless)
Newest Desktop Control --approval-backend file:/run/hermes-claw/approvals/
```

---

## 9. Troubleshooting

### 9.1 AT-SPI2 Not Available
```bash
# Check at-spi2-registry is running
ps aux | grep at-spi2-registry
# If not running, start it
/usr/libexec/at-spi2-registryd &
```

### 9.2 Screenshot Returns Black Screen
Usually means the Wayland compositor hasn't exposed the screen. Check:
```bash
# Verify wayland socket is accessible
ls -la /run/user/0/wayland-0
# Or check the WAYLAND_DISPLAY env var
echo $WAYLAND_DISPLAY
```

### 9.3 Click Doesn't Work in Chromium
Chromium needs the `--accessibility-reader` flag for full AT-SPI2 support. The kiosk launch script should include:
```bash
chromium-browser \
    --kiosk \
    --accessibility-reader \
    --enable-features=AccessiblityTreeDi
```

### 9.4 Permission Denied on Input Devices
```bash
# Check user is in input group
groups $USER
# If not:
sudo usermod -aG input $USER
```

---

## 10. GitHub Repository

**Repository:** `https://github.com/Newest Desktop Control (Lobster Edition)`
**License:** Apache 2.0 (verify before bundling)
**Language:** Rust
**Status in DuckBotOS:** Required, must be bundled in all ISO variants

---

## 11. Future Enhancements

| Feature | Priority | Notes |
|---|---|---|
| Multi-monitor support | High | MCP tool to query and control monitors |
| Wayland native screenshot | High | Replace `grim` with portal API |
| Accessibility annotation overlay | Medium | Highlight clicked element for transparency |
| TUI approval interface | Medium | For headless/server deployments |
| Agent action history | Medium | Store action log for audit/replay |
| Gesture support (pinch/zoom) | Low | Requires libinput improvements |
