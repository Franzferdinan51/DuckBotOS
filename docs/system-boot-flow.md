# DuckBotOS — System Boot Flow

> Complete boot sequence: from UEFI/BIOS to agent-ready kiosk display.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Overview

DuckBotOS has three distinct boot paths depending on which ISO variant was installed:

| ISO Variant | Boot Path | Display Manager |
|-------------|-----------|-----------------|
| `duckbotos-hermes-x86_64.iso` | Auto-kiosk | Weston (no GDM) |
| `duckbotos-openclaw-x86_64.iso` | Auto-kiosk | Weston (no GDM) |
| `duckbotos-both-x86_64.iso` | GDM session picker | GDM3 |

All three paths reach the same outcome: a **Wayland kiosk compositor** running the agent's web dashboard in fullscreen Chromium.

---

## 2. Boot Phase Timeline

```
T+0s    UEFI/BIOS → bootloader (GRUB)
T+3s    Kernel boot → initramfs → systemd (PID 1)
T+8s    multi-user.target reached
T+10s   DuckBotOS services start (see Section 3)
T+15s   Weston compositor starts on tty1
T+18s   Chromium kiosk launches (browser loads agent URL)
T+20s   Agent gateway ready (port 9119 or 18797)
T+22s   Agent web dashboard fully loaded in Chromium
T+25s   User can interact with agent
```

---

## 3. Service Startup Order

All services are `systemd` units. Startup order is enforced via `After=` dependencies.

### Phase A: Base System (runs as `root`)

```
local-fs.target
  └─ system-modules.target
      └─ sockets.target
          ├─ dbus.socket           (D-Bus session bus)
          └─ dbus-daemon.service

multi-user.target
  ├─ network-online.target
  │   └─ NetworkManager.service   (WiFi, Ethernet, VPN)
  │
  ├─ local-fs.target
  │   └─ various mount units (/home, /tmp, /var/log)
  │
  └─time-set.target
```

### Phase B: Agent Gateways (runs as `root` or `hermes`/`openclaw` user)

```
# Hermes-only or Both ISO:
hermes-gateway.service
  ExecStart=/usr/bin/hermes gateway start
  ListenStream=127.0.0.1:9119
  After=network-online.target
  WantedBy=multi-user.target

# OpenClaw-only or Both ISO:
openclaw-gateway.service
  ExecStart=/opt/openclaw/bin/openclaw gateway start
  ListenStream=127.0.0.1:18797
  After=network-online.target
  WantedBy=multi-user.target
```

### Phase C: Computer-Use MCP Server (all ISOs)

```
computer-use-linux.service          (all ISOs)
  ExecStart=/usr/bin/computer-use-linux --port 9600
  ListenStream=127.0.0.1:9600
  After=hermes-gateway.service openclaw-gateway.service
  WantedBy=multi-user.target
```

### Phase D: LM Studio (all ISOs, optional — user can disable)

```
lmstudio.service                    (user service, all ISOs)
  Type=notify
  ExecStart=%h/.local/bin/lms daemon up
  Environment="LMSTUDIO_API_KEY="
  After=network-online.target
  WantedBy=default.target
```

### Phase E: Kiosk Compositor (Hermes-only and OpenClaw-only)

```
weston-kiosk.service               (hermes/openclaw ISOs — no GDM)
  Type=idle
  ExecStart=/usr/local/bin/weston-kiosk-launch.sh
  After=local-fs.target
  RequiredBy=multi-user.target

  # weston-kiosk-launch.sh:
  #!/bin/bash
  # Starts Weston on tty1 as DRM compositor
  # No login screen — auto-starts kiosk session
  exec weston --shell=kiosk.so --tty=1 \
    --idle-time=0 \
    --backend=drm-backend.so
```

### Phase F: Browser Kiosk (Hermes-only and OpenClaw-only)

```
chromium-kiosk.service             (hermes/openclaw ISOs)
  After=weston-kiosk.service
  ExecStartPre=/bin/sleep 3        # wait for Weston to initialize
  ExecStart=/usr/local/bin/chromium-kiosk-launch.sh

  # chromium-kiosk-launch.sh:
  #!/bin/bash
  # Reads /etc/duckbotos/agent-url to determine which agent to load
  AGENT_URL=$(cat /etc/duckbotos/agent-url)
  exec /usr/bin/chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-features=Translate \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --start-fullscreen \
    --app="$AGENT_URL"
```

**`/etc/duckbotos/agent-url`** (written by first-boot wizard):
```bash
# Hermes-only ISO:
echo "http://127.0.0.1:9119" > /etc/duckbotos/agent-url

# OpenClaw-only ISO:
echo "http://127.0.0.1:18789/plugins/openclawos" > /etc/duckbotos/agent-url
```

### Phase G: Both Mode — GDM Session Picker (Both ISO only)

```
gdm3.service                       (both ISO only)
  After=hermes-gateway.service openclaw-gateway.service
  WantedBy=graphical.target

# GDM shows three session entries:
# 1. "DuckBotOS (Hermes)"     → starts weston-kiosk + chromium → Hermes
# 2. "DuckBotOS (OpenClaw)"   → starts weston-kiosk + chromium → OpenClaw
# 3. "DuckBotOS (Hybrid)"     → starts GNOME Shell + both agents + sidebar

# Session .desktop files in /usr/share/xsessions/:
# - duckbotos-hermes.desktop
# - duckbotos-openclaw.desktop
# - duckbotos-hybrid.desktop
```

---

## 4. First-Boot Wizard Flow

On a **fresh install** (OEM mode), the first-boot wizard runs after the autoinstall completes:

```
[System boots after install]
  → systemd runs duckbotos-firstboot.service

[duckbotos-firstboot.service]
  1. Check if /var/lib/duckbotos/firstboot-done exists
     → If yes: exit (already ran)
     → If no: continue

  2. Launch firstboot-wizard in Chromium (maximized, not kiosk):
     URL: http://127.0.0.1:9000/firstboot

  3. Wizard steps:
     Step 1: Welcome → select mode (Hermes / OpenClaw / Both)
       → Writes /etc/duckbotos/mode
       → Writes /etc/duckbotos/agent-url

     Step 2: Network → connect WiFi / Ethernet (via NM)

     Step 3: Provider config
       For each enabled provider:
         - LM Studio: "Download a model?" → calls lms download <model>
         - Cloud providers: enter API key
       → Writes /etc/duckbotos/providers.yaml

     Step 4: Model selection
       - GET http://127.0.0.1:1234/v1/models (LM Studio)
       - User picks default model
       → Writes ~/.hermes/config.yaml or /var/lib/openclaw/config.yaml

     Step 5: Create user account
       → Standard user creation (name, username, password)

     Step 6: Done → "Restart to begin using DuckBotOS"

  4. On "Restart":
     - Touch /var/lib/duckbotos/firstboot-done
     - systemctl reboot
```

**Firstboot wizard service:**

```ini
# /etc/systemd/system/duckbotos-firstboot.service
[Unit]
Description=DuckBotOS First-Boot Wizard
After=network-online.target hermes-gateway.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/lib/duckbotos/firstboot-wizard.py
User=root
Restart=no

[Install]
WantedBy=multi-user.target
```

---

## 5. Service Failure Handling

### If Hermes gateway fails to start:
```
weston-kiosk.service fails (After=hermes-gateway.service)
→ Fallback: show error screen in Chromium
  URL: http://127.0.0.1:9000/error?service=hermes
→ Error message: "Hermes gateway failed to start. Check logs: journalctl -u hermes-gateway"
→ Options: [Retry] [Use OpenClaw instead] [View Logs]
```

### If LM Studio not running:
```
Agent detects /v1/models returns empty or connection refused
→ Informational banner: "LM Studio not running. Install models at http://127.0.0.1:1234"
→ Cloud providers used as fallback
```

### If network is offline:
```
Agent detects no internet connectivity
→ Banner: "Offline mode — using local models only"
→ LM Studio becomes primary provider
```

---

## 6. Shutdown Flow

```
[User clicks "Shut Down" in kiosk UI]
  → Browser sends POST to /api/shutdown on localhost
  → hermes-claw-ctrl service receives request
  → SIGTERM sent to all agent processes
  → systemctl poweroff
```

---

## 7. Emergency Recovery

### Boot to Recovery Shell
On boot, hold **Esc** or press **F4** during GRUB to enter recovery mode:
- Root shell
- Logs at `/var/log/`
- Service status: `systemctl status`
- Manual start: `systemctl start hermes-gateway.service`

### Re-run First-Boot Wizard
```bash
sudo rm /var/lib/duckbotos/firstboot-done
sudo systemctl start duckbotos-firstboot.service
```

### Reset Agent Config
```bash
sudo rm /etc/duckbotos/agent-url
sudo systemctl restart hermes-gateway.service openclaw-gateway.service
```

---

## 8. Port Map (All Services)

| Port | Service | Interface | Purpose |
|------|---------|-----------|---------|
| 22 | sshd | 0.0.0.0 | Remote SSH access |
| 53 | dnsmasq | 127.0.0.1 | Local DNS (kiosk) |
| 1234 | lmstudio (llmster) | 127.0.0.1 | LM Studio API |
| 3000 | firstboot-wizard | 127.0.0.1 | First-boot UI (pre-kiosk) |
| 6000 | wayland (Weston) | unix socket | Wayland compositor |
| 9003 | browseros-mcp | 127.0.0.1 | BrowserOS MCP server |
| 9119 | hermes-gateway | 127.0.0.1 | Hermes Web Dashboard |
| 9600 | computer-use-linux | 127.0.0.1 | AT-SPI2 MCP server |
| 18789 | openclaw-gateway | 127.0.0.1 | OpenClaw Web UI |
| 18797 | openclaw-gateway | 127.0.0.1 | OpenClaw gateway (internal) |
| 19289 | openclaw-mcp | 127.0.0.1 | OpenClaw MCP server |

---

*System Boot Flow v0.1 — 2026-06-29*
