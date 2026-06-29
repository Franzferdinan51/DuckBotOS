# DuckBotOS — Dual-Agent IPC Bus

> How Hermes and OpenClaw communicate in Both mode: the Unix socket IPC bus, D-Bus integration, and shared credential store.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Design Goals

In **Both mode** (the Hybrid Workstation install), both Hermes and OpenClaw run simultaneously. They need to:

1. **Coordinate** — Agree on shared state (active provider, current model, API keys loaded)
2. **Delegate** — Hermes can ask OpenClaw to verify/refine its work, and vice versa
3. **Share tools** — `Newest Desktop Control` MCP server is shared with tool-level locking
4. **Share credentials** — API keys stored once, accessible to both (TPM-backed when available)
5. **Resolve conflicts** — If both agents want to do contradictory actions, resolve gracefully

The IPC bus is the core of this coordination.

---

## 2. Architecture Overview

```
Dual-Agent IPC Architecture (Both Mode)
========================================

/run/hermes-claw/
├── agent-bus.sock          # JSON-RPC 2.0 Unix socket — main bus
├── hermes.sock             # Hermes gateway Unix socket (internal)
├── openclaw.sock           # OpenClaw gateway Unix socket (internal)
├── computer-use.sock       # Newest Desktop Control tool lock socket
└── credentials/            # Shared credential store (0600, owned by hermes-claw group)

/etc/hermes-claw/
├── agent-bus.yaml          # Bus configuration (providers, policies)
├── hermes/                 # Hermes agent config (symlinked)
└── openclaw/               # OpenClaw agent config (symlinked)
```

---

## 3. Agent Bus Socket

### 3.1 Protocol: JSON-RPC 2.0 over Unix Socket

The agent bus is a **Unix domain socket** (`/run/hermes-claw/agent-bus.sock`) that speaks JSON-RPC 2.0. Both Hermes and OpenClaw connect as clients. A small daemon (`hermes-claw-bus`) mediates all communication.

**Why Unix socket (not TCP):**
- No network exposure — entirely local
- Standard POSIX — works across containers, VMs, systemd scopes
- Fast — zero-copy on local machine
- Standard permissions — chmod + ACLs

### 3.2 Message Types

**Request** (client → bus → target agent):
```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "hermes.delegate",
  "params": {
    "session_id": "sess-abc123",
    "prompt": "Review this Python code for bugs:\n\ndef add(a, b):\n    return a - b",
    "context": {
      "source": "openclaw",
      "reply_to": "sess-xyz789",
      "priority": "normal",
      "tool_access": ["screenshot", "read_file"]
    }
  }
}
```

**Response** (target agent → bus → client):
```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "status": "complete",
    "output": "The add() function has a bug: it subtracts instead of adding. The fix is:\n\ndef add(a, b):\n    return a + b",
    "confidence": 0.95
  }
}
```

**Notification** (fire-and-forget, no response expected):**
```json
{
  "jsonrpc": "2.0",
  "method": "hermes-claw.provider_changed",
  "params": {
    "agent": "hermes",
    "provider": "lm-studio",
    "model": "qwen3.5-2b"
  }
}
```

### 3.3 Supported Methods

| Method | Direction | Description |
|---|---|---|
| `hermes.delegate` | OpenClaw → Hermes | Delegate task to Hermes agent |
| `openclaw.delegate` | Hermes → OpenClaw | Delegate task to OpenClaw agent |
| `hermes-claw.status` | Either → bus | Get bus status, list connected agents |
| `hermes-claw.provider_changed` | Either → both | Notification: active provider changed |
| `hermes-claw.model_loaded` | Either → both | Notification: LM Studio model loaded |
| `hermes-claw.credential_access` | Either → bus | Request credential (API key) lookup |
| `computer-use.lock` | Either → bus | Acquire exclusive tool lock |
| `computer-use.unlock` | Either → bus | Release exclusive tool lock |
| `hermes-claw.ping` | Either → bus | Health check / presence announcement |

### 3.4 Bus Daemon: hermes-claw-bus

```python
# hermes-claw-bus — simplified structure
import asyncio
import json
import os
import socket
from typing import Dict

AGENT_SOCKETS = {
    "hermes": "/run/hermes-claw/hermes.sock",
    "openclaw": "/run/hermes-claw/openclaw.sock",
}
BUS_SOCKET = "/run/hermes-claw/agent-bus.sock"

class AgentBusProtocol(asyncio.Protocol):
    def __init__(self):
        self.clients: Dict[str, asyncio.Protocol] = {}  # agent_name → protocol
        self.pending_locks: Dict[str, str] = {}  # tool_name → holder_session_id

    def connection_made(self, transport):
        # First message must be: { "type": "register", "agent": "hermes" }
        self.transport = transport

    def data_received(self, data):
        msg = json.loads(data.decode())
        msg_type = msg.get("type")

        if msg_type == "register":
            self.clients[msg["agent"]] = self
            return

        if msg_type == "delegate":
            target = msg["target"]  # "hermes" or "openclaw"
            asyncio.create_task(self.forward_to(target, msg))

        elif msg_type == "notification":
            asyncio.create_task(self.broadcast(msg))

        elif msg_type == "tool_lock":
            tool = msg["tool"]
            session = msg["session_id"]
            if tool not in self.pending_locks:
                self.pending_locks[tool] = session
                self.respond({"status": "granted", "tool": tool})
            else:
                self.respond({"status": "held", "holder": self.pending_locks[tool]})

        elif msg_type == "tool_unlock":
            tool = msg["tool"]
            if self.pending_locks.get(tool) == msg["session_id"]:
                del self.pending_locks[tool]

    async def forward_to(self, target, msg):
        target_transport = self.clients.get(target)
        if target_transport:
            target_transport.write(json.dumps(msg).encode())

    async def broadcast(self, msg):
        for client in self.clients.values():
            client.write(json.dumps(msg).encode())
```

---

## 4. D-Bus Integration

### 4.1 Why D-Bus?

D-Bus is the Linux desktop standard for inter-process communication. We use it for:

1. **Session notifications** — "Provider changed to LM Studio"
2. **System-wide signals** — "Agent started/stopped"
3. **Policy enforcement** — Controlling which agent can access which resources
4. **Logind integration** — Detecting user session state (active/idle/locked)

### 4.2 Bus Names

| Bus | Name | Purpose |
|---|---|---|
| **System bus** | `org.duckbotos.DuckBotOS` | System-wide agent status |
| **Session bus** | `org.duckbotos.Agent.{hermes,openclaw}` | Per-agent interface |

### 4.3 D-Bus Service Definitions

```xml
<!-- /usr/share/dbus-1/interfaces/org.duckbotos.DuckBotOS.Agent.xml -->
<node name="/org/duckbotos/DuckBotOS/Agent">
  <interface name="org.duckbotos.DuckBotOS.Agent">
    <method name="Status">
      <arg name="status" type="s" direction="out"/>
    </method>
    <method name="Delegate">
      <arg name="prompt" type="s" direction="in"/>
      <arg name="result" type="s" direction="out"/>
    </method>
    <method name="SetProvider">
      <arg name="provider" type="s" direction="in"/>
    </method>
    <signal name="ProviderChanged">
      <arg name="provider" type="s"/>
      <arg name="model" type="s"/>
    </signal>
    <signal name="ModelLoaded">
      <arg name="model" type="s"/>
      <arg name="memory_estimate_gb" type="d"/>
    </signal>
  </interface>
</node>
```

### 4.4 Logind Integration

```python
# hermes-claw-bus: detect session state changes
import dbus

system_bus = dbus.SystemBus()
logind = system_bus.get_object(
    "org.freedesktop.login1",
    "/org/freedesktop/login1"
)

# Listen for PrepareForSleep signal (system going to sleep)
logind.connect_to_signal(
    "PrepareForSleep",
    lambda on: pause_agents() if on else resume_agents()
)

# Listen for Session paused/resumed
logind.connect_to_signal(
    "SessionPaused",
    lambda session_id: pause_agents()
)
logind.connect_to_signal(
    "SessionResumed",
    lambda session_id: resume_agents()
)
```

---

## 5. Shared Credential Store

### 5.1 Design

API keys are stored once and shared between Hermes and OpenClaw via a **secret store** backed by `libsecret` (Linux keyring) when available, or by files with restricted permissions as a fallback.

```bash
# Directory structure (owned by hermes-claw group)
drwx------ 2 root root 4096 Jun 29 /run/hermes-claw/credentials/
-rw-r----- 1 root hermes-claw hermes-claw  4096 Jun 29 /run/hermes-claw/credentials/minimax.key
-rw-r----- 1 root hermes-claw hermes-claw  4096 Jun 29 /run/hermes-claw/credentials/openai.key
-rw-r----- 1 root hermes-claw hermes-claw  4096 Jun 29 /run/hermes-claw/credentials/anthropic.key
```

### 5.2 TPM-Backed Storage (Future)

When DuckBotOS runs on hardware with a TPM 2.0 chip:
- Keys are sealed to the TPM
- Only the OS kernel can unseal them
- Agents request unsealed keys via the agent bus
- Keys never appear in plaintext on disk

```bash
# TPM-backed key creation
tpm2_createprimary -C o -c primary.ctx
tpm2_create -G rsa -u key.pub -r key.priv -C primary.ctx
tpm2_evictcontrol -c key.pub 0x81000000

# Agent requests unsealed key (via bus)
dbus-send --system --dest=org.duckbotos.DuckBotOS \
    /org/duckbotos/DuckBotOS/Secrets \
    org.duckbotos.DuckBotOS.Secrets.GetKey \
    string:"openai" → returns decrypted API key
```

### 5.3 Agent Bus Credential Access

```json
// Request (agent → bus)
{
  "jsonrpc": "2.0",
  "method": "hermes-claw.credential_access",
  "params": {
    "session_id": "sess-abc",
    "provider": "openai"
  }
}

// Response (bus → agent)
{
  "jsonrpc": "2.0",
  "id": "...",
  "result": {
    "provider": "openai",
    "api_key": "sk-..."   // Decrypted value (only if authorized)
  }
}
```

Authorization rules in `/etc/hermes-claw/agent-bus.yaml`:
```yaml
credential_policy:
  hermes:
    allowed_providers: [minimax, openai, anthropic, grok, deepseek]
    require_approval: true  # Prompt user before giving key
  openclaw:
    allowed_providers: [minimax, openai, anthropic, grok, deepseek, lm-studio]
    require_approval: false  # OpenClaw can auto-access all
```

---

## 6. Tool Sharing — Newest Desktop Control

### 6.1 The Problem

Both Hermes and OpenClaw may want to use `Newest Desktop Control` simultaneously. If both agents click the same button at the same time, chaos ensues.

### 6.2 Solution: Tool-Level Locking via Agent Bus

```json
// Agent requests lock before any tool call
{
  "jsonrpc": "2.0",
  "method": "computer-use.lock",
  "params": {
    "tool": "click",
    "session_id": "sess-hermes-001",
    "timeout_ms": 30000
  }
}

// Response: granted or held
{ "status": "granted" }  // → proceed with tool call
{ "status": "held", "holder": "sess-openclaw-042" }  // → wait or skip

// After tool call completes, release lock
{
  "jsonrpc": "2.0",
  "method": "computer-use.unlock",
  "params": {
    "tool": "click",
    "session_id": "sess-hermes-001"
  }
}
```

### 6.3 Lock Timeout

Locks auto-expire after `timeout_ms` (default: 30000ms). If an agent crashes while holding a lock, the lock is released after the timeout so the other agent isn't permanently blocked.

---

## 7. GDM Session Picker

### 7.1 Session Files

In Both mode, GDM shows three session options:

```bash
# /usr/share/xsessions/duckbotos-hermes.desktop
[Desktop Entry]
Name=DuckBotOS — Hermes Desktop
Comment=Agent-first kiosk with Hermes AI
Exec=/usr/local/bin/duckbotos-launch hermes
Icon=/usr/share/pixmaps/duckbotos-hermes.png
Type=Application

# /usr/share/xsessions/duckbotos-openclaw.desktop
[Desktop Entry]
Name=DuckBotOS — OpenClaw Desktop
Comment=Agent-first kiosk with OpenClaw AI
Exec=/usr/local/bin/duckbotos-launch openclaw
Icon=/usr/share/pixmaps/duckbotos-openclaw.png
Type=Application

# /usr/share/xsessions/duckbotos-hybrid.desktop
[Desktop Entry]
Name=DuckBotOS — Hybrid Workstation
Comment=Both agents running with GNOME Shell
Exec=/usr/local/bin/duckbotos-launch hybrid
Icon=/usr/share/pixmaps/duckbotos-hybrid.png
Type=Application
```

### 7.2 Launch Script

```bash
#!/usr/local/bin/duckbotos-launch
# /usr/local/bin/duckbotos-launch
MODE="$1"  # hermes | openclaw | hybrid

case "$MODE" in
    hermes)
        systemctl start hermes-gateway.service
        systemctl start weston-kiosk.service
        systemctl start chromium-kiosk.service  # → --app=http://127.0.0.1:9119
        systemctl start Newest Desktop Control.service
        ;;
    openclaw)
        systemctl start openclaw-gateway.service
        systemctl start weston-kiosk.service
        systemctl start chromium-kiosk.service  # → --app=http://127.0.0.1:18789/plugins/openclawos
        systemctl start Newest Desktop Control.service
        ;;
    hybrid)
        systemctl start hermes-gateway.service
        systemctl start openclaw-gateway.service
        systemctl start hermes-claw-bus.service
        systemctl start Newest Desktop Control.service
        systemctl start gnome-session.service  # Full GNOME Shell with both agents
        ;;
esac
```

---

## 8. Conflict Resolution

### 8.1 Rule: Last Write Wins (for state)

For provider/model selection, the last agent to call `SetProvider` wins. Both agents receive the `ProviderChanged` notification.

### 8.2 Rule: Locked Tools (for actions)

`Newest Desktop Control` tool calls are serialized via locks. One agent acts at a time.

### 8.3 Rule: Explicit Delegation (for reasoning)

If Hermes needs OpenClaw's reasoning capability (e.g., complex code review), it explicitly delegates via `hermes.delegate` with `reply_to` set. The result comes back to Hermes for synthesis.

---

## 9. Security Model

| Risk | Mitigation |
|---|---|
| Agent A steals Agent B's API keys | Credentials stored with hermes-claw group; agent must be in group |
| Agent bypasses lock and clicks simultaneously | Kernel-level file locks on the tool socket |
| Malicious agent connects to bus | UDS permissions: `chmod 0770 /run/hermes-claw/agent-bus.sock` owned by `hermes-claw:hermes-claw` |
| Rogue D-Bus service impersonates agent | D-Bus policy: only `hermes` and `openclaw` can own bus names |
| Key material in memory after crash | Agents zero-fill key memory after use (best effort) |

---

## 10. systemd Service Units

### 10.1 hermes-claw-bus.service

```ini
# /etc/systemd/system/hermes-claw-bus.service
[Unit]
Description=DuckBotOS Agent Bus — Hermes/OpenClaw IPC
After=network.target
Wants=hermes-gateway.service openclaw-gateway.service

[Service]
Type=simple
ExecStart=/usr/local/bin/hermes-claw-bus
Restart=on-failure
RestartSec=5
User=root
Group=hermes-claw
SupplementaryGroups=hermes-claw

# Socket permissions
SocketMode=0770
DirectoryMode=0750
RuntimeDirectory=hermes-claw
RuntimeDirectoryPreserve=preserve

# Security hardening
NoNewPrivileges=false
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/run/hermes-claw/credentials
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 10.2 hermes-claw-credentials.service

```ini
# /etc/systemd/system/hermes-claw-credentials.service
[Unit]
Description=DuckBotOS Credential Store Init
Before=hermes-gateway.service openclaw-gateway.service hermes-claw-bus.service
After=systemd-logind.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/hermes-claw-credentials-init
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```
