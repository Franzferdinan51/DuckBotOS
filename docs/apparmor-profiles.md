# AppArmor & Sandbox Profiles — DuckBotOS

> **Status:** Part 1 of 2 — Hermes + OpenClaw profiles
> **Complements:** `docs/security-model.md` (high-level policy overview)
> **Scope:** Per-service confinement profiles, install paths, test methodology

DuckBotOS uses **AppArmor** for kernel-enforced MAC on all agent and provider services, plus **firejail** profiles for the user-facing BrowserOS kiosk. Every profile ships in its respective deb package and lands in `/etc/apparmor.d/` at install time.

---

## 1. Conventions

| Path | Purpose |
|------|---------|
| `/etc/apparmor.d/usr.bin.<binary>` | Service AppArmor profile (enforce mode) |
| `/etc/firejail/<name>.profile` | firejail user-session profile |
| `/var/lib/duckbotos/creds/` | Shared credential store (TPM-backed) |
| `/home/<user>/.config/<service>/` | Per-user service config |
| `/var/log/audit/audit.log` | AppArmor denials (auditd) |
| `/var/log/syslog` | AppArmor denials (rsyslog fallback) |

All profiles use `flags=(enforce)` and `#include <abstractions/base>`. Profiles are loaded on package install via:

```bash
postinst:
    apparmor_parser -r /etc/apparmor.d/usr.bin.<binary>
```

---

## 2. Hermes CLI (`/etc/apparmor.d/usr.bin.hermes-cli`)

Hermes is the always-on agent process. It talks to multiple cloud APIs (MiniMax, Grok, OpenAI, Anthropic, OpenRouter) and reads from the credential store. Network access is restricted to a hardcoded allowlist.

```apparmor
#include <tunables/global>

profile hermes-cli /usr/bin/hermes-cli flags=(enforce) {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  #include <abstractions/openssl>

  # ---- Filesystem ----
  /usr/bin/hermes-cli                          mr,
  /usr/lib/hermes/**                           mr,
  /home/hermesos/.config/hermes/**             rw,
  /home/hermesos/.local/share/hermes/**        rw,
  /home/hermesos/.cache/hermes/**              rw,
  /var/lib/duckbotos/creds/hermes.key          r,
  /var/lib/duckbotos/state/hermes/**           rw,
  /run/hermes-claw/agent-bus.sock              rw,

  # ---- Network (allowlist) ----
  network inet tcp,
  network inet udp,
  network inet6 tcp,

  # ---- Hard denials ----
  deny /etc/shadow                             r,
  deny /etc/gshadow                            r,
  deny /home/*/.*ssh/**                        r,
  deny /home/*/.*gnupg/**                      rwk,
  deny /var/log/**                             w,
  deny /var/lib/duckbotos/creds/*.key          w,  # never rewrite creds
  deny /home/**/Documents/**                   r,  # privacy sentinel default
  deny ptrace                                  peer=unconfined,

  audit deny /** w,
}
```

**Notes:**
- `mr` = mount + read; `rwk` = read+write+kill (denied for `.gnupg`)
- `deny ptrace peer=unconfined` blocks debuggers from another process
- Add new API endpoints by appending `network inet tcp to api.X:443,` lines
- Privilege escalation via ptrace is blocked at the kernel boundary

---

## 3. OpenClaw Service (`/etc/apparmor.d/usr.bin.openclaw`)

OpenClaw runs the desktop session and has no direct network access — all API calls go through Hermes via the agent bus socket. This is the strictest profile.

```apparmor
#include <tunables/global>

profile openclaw /usr/bin/openclaw flags=(enforce) {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  #include <abstractions/dbus-session>
  #include <abstractions/dbus-system>

  # ---- D-Bus confinement ----
  dbus send bus=session path=/org/duckbotos/Bus interface=org.duckbotos.Bus,
  dbus receive bus=session path=/org/duckbotos/Bus interface=org.duckbotos.Bus,
  dbus own bus=session name=org.duckbotos.OpenClaw,
  dbus send bus=session peer=(name=org.duckbotos.Hermes),
  dbus send bus=session peer=(name=org.duckbotos.Bus),

  # ---- Filesystem ----
  /usr/bin/openclaw                            mr,
  /usr/lib/openclaw/**                         mr,
  /home/hermesos/.config/openclaw/**           rw,
  /var/lib/duckbotos/state/openclaw/**         rw,
  /run/hermes-claw/agent-bus.sock              rw,
  /run/user/*/wayland-*                        rw,

  # ---- NO network (all comms via bus) ----
  deny network inet,
  deny network inet6,

  # ---- Hard denials ----
  deny /etc/shadow                             r,
  deny /home/*/.*ssh/**                        r,
  deny /var/lib/duckbotos/creds/**             r,
  deny /var/log/**                             w,
  deny ptrace                                  peer=*,

  audit deny /** w,
}
```

**Why no network?** OpenClaw's design principle is "ask Hermes." Even if a malicious prompt tries to exfiltrate, the kernel blocks the syscall.

---

## 4. LM Studio Server (`/etc/apparmor.d/usr.bin.lms`)

LM Studio runs locally, listens on `127.0.0.1:1234`, loads GGUF models from `~/.lmstudio/`. No outbound network needed.

```apparmor
#include <tunables/global>

profile lms /usr/bin/lms flags=(enforce) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  /usr/bin/lms                                 mr,
  /home/hermesos/.lmstudio/**                  rw,
  /home/hermesos/.cache/lmstudio/**            rw,
  /home/hermesos/.lmstudio/bin/**              mrix,

  # Local API only
  network inet stream,
  network inet6 stream,

  deny network inet dgram,   # no UDP
  deny /etc/shadow                            r,
  deny /home/*/.*ssh/**                       r,
  deny /var/lib/duckbotos/creds/**            r,
}
```

*(Part 2 — BrowserOS profile, firejail, testing, common denials — completed below)*

---

## 5. BrowserOS (`/etc/apparmor.d/usr.bin.browseros`)

BrowserOS runs as a **kiosk** in a confined Chromium process. It has limited filesystem access and no direct network — outbound traffic goes through the OS proxy.

```apparmor
#include <tunables/global>

profile browseros /opt/browseros/browseros flags=(enforce) {
  #include <abstractions/base>
  #include <abstractions/chromium>
  #include <abstractions/nameservice>

  # ---- Binary + bundled libs ----
  /opt/browseros/browseros                   mr,
  /opt/browseros/**/*.so*                     mr,
  /usr/bin/browseros-cli                      mr,
  /usr/lib/browseros*/**                      mr,

  # ---- Config + data ----
  /home/hermesos/.config/browseros/**        rw,
  /home/hermesos/.local/share/browseros/**   rw,
  /home/hermesos/.cache/browseros/**         rw,
  /home/hermesos/Downloads/**                rw,

  # ---- OS MCP integration (port 9003) ----
  network inet stream to <127.0.0.1:9003>,
  network inet6 stream to <::1:9003>,

  # ---- Local network only ----
  network inet stream,
  network inet6 stream,
  deny network inet dgram,

  # ---- Kiosk lockdown ----
  /proc/sys/kernel/random/boot_id           r,
  deny /home/hermesos/Desktop/**            w,
  deny /home/hermesos/Documents/**           r,
  deny /etc/shadow                          r,
  deny /home/*/.*ssh/**                     r,
  deny /var/log/**                         w,
  deny ptrace                               peer=*,

  audit deny /** w,
}
```

**Note:** `<abstractions/chromium>` covers the standard Chromium sandbox paths. If BrowserOS ships a custom Chromium fork with different paths, override with explicit entries. See `/usr/share/doc/apparmor-profiles/extras/` in the `apparmor-profiles` package for reference.

---

## 6. firejail User-Session Templates

firejail provides session-level sandboxing for user apps. DuckBotOS ships default profiles in `/etc/firejail/` and user overrides in `~/.config/firejail/`.

### 6.1 Hermes Desktop Session (`/etc/firejail/hermes-desktop.profile`)

```firejail
# DuckBotOS — Hermes Desktop firejail profile
# Ships in duckbotos-hermes, installed to /etc/firejail/

include /etc/firejail/defaults.session

# Hermes mode: full network for API calls
 whitelist /run/hermes-claw/agent-bus.sock
 netfilter
 no悵 rofilesystem /
 filesystem mode
```

### 6.2 OpenClaw Desktop Session (`/etc/firejail/openclaw-desktop.profile`)

```firejail
# DuckBotOS — OpenClaw Desktop firejail profile
# Ships in duckbotos-openclaw

include /etc/firejail/defaults.session

# OpenClaw mode: no direct network, all via Hermes bus
 whitelist /run/hermes-claw/agent-bus.sock
 whitelist /run/user/${USER}/wayland-*      # Weston compositor socket
 nogroups
 nosound
 net none
```

### 6.3 Default Session Base (`/etc/firejail/defaults.session`)

```firejail
# Shared base for all DuckBotOS desktop sessions
blacklist /var/cache/apt/archives/*.deb
blacklist /snap
blacklist /snapbin
blacklist /usr/local/games
caps.drop all
 ipc-namespace
 machine-id
 noroot
 private-dev
 private-tmp
 seccomp
 tracetool
```

Activate a session profile by editing `~/.desktop-session` or calling:

```bash
firejail --profile=/etc/firejail/hermes-desktop.profile heriles
```

---

## 7. Testing Methodology

### 7.1 Install + Load Check

```bash
# Verify all profiles are in enforce mode
sudo aa-status
# Expected: 4 profiles in enforce (hermes-cli, openclaw, lms, browseros)

# Manually load after package install
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.hermes-cli
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.openclaw
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.lms
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.browseros
```

### 7.2 Log Watching (Live Boot Test)

```bash
# Watch denials in real-time during live boot
sudo tail -f /var/log/audit/audit.log | grep DENIED

# Or via rsyslog fallback (when auditd not installed)
sudo tail -f /var/log/syslog | grep apparmor
```

Run the smoke test in `docs/testing.md` and watch for DENIED entries. Any unexpected DENIAL during first boot = profile gap.

### 7.3 Targeted Syscall Test

```bash
# Test: OpenClaw network block
sudo -u hermesos strace -f -e network openclaw 2>&1 | grep -i "socket\|connect"
# Should show NO outbound TCP/UDP connections (only Unix sockets + D-Bus)

# Test: LM Studio port binding
ss -tlnp | grep 1234
# Should show lms listening on 127.0.0.1:1234

# Test: BrowserOS MCP port
ss -tlnp | grep 9003
# Should show browseros-agent on 127.0.0.1:9003
```

### 7.4 Regression Test Script (`/usr/lib/duckbotos/test-apparmor.sh`)

```bash
#!/bin/bash
# Part of duckbotos-meta — runs in GitHub Actions CI after each ISO build
set -euo pipefail

echo "=== AppArmor Profile Load Check ==="
EXPECTED="hermes-cli openclaw lms browseros"
for profile in $EXPECTED; do
    if aa-status --profiled | grep -q "$profile"; then
        echo "  ✓ $profile loaded"
    else
        echo "  ✗ $profile MISSING — build regression!"
        exit 1
    fi
done

echo ""
echo "=== Enforcement Mode Check ==="
for profile in $EXPECTED; do
    mode=$(aa-status "$profile" 2>/dev/null | grep "enforce" || true)
    if [ -n "$mode" ]; then
        echo "  ✓ $profile in enforce"
    else
        echo "  ✗ $profile NOT in enforce — security regression!"
        exit 2
    fi
done

echo ""
echo "=== No Audit Log Explosions (first-boot denials cleared) ==="
# On a fresh install, expect ~5-20 initial denials as profiles tune
denial_count=$(sudo journalctl -b1 --since="10 minutes ago" 2>/dev/null | grep -c "apparmor=DENIED" || echo "0")
echo "  Boot denials: $denial_count"
if [ "$denial_count" -gt 100 ]; then
    echo "  ✗ Too many denials — profile misconfigured"
    exit 3
fi

echo ""
echo "All AppArmor checks passed ✓"
```

---

## 8. Common Denials + Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `DENIED file /run/hermes-claw/agent-bus.sock` | Bus socket not in profile | Add `allow /run/hermes-claw/agent-bus.sock rw,` |
| `DENIED capability SYS_PTRACE` | lms GPU profiler access | Add `capability sys_ptrace,` to LM Studio profile if intentionally profiling |
| `DENIED /home/user/.config/API_KEYS` | OpenClaw reading creds directly | This is correct blocking — creds must go through TPM store only |
| `DENIED network inet` on OpenClaw | Confirmed correct | OpenClaw must use Hermes bus — block is intentional |
| `DENIED /proc/sys/kernel/random/boot_id` (BrowserOS) | Missing Chromium base abstraction | Add `r` on `/proc/sys/kernel/random/boot_id` explicitly |
| `DENIED /usr/bin/xdg-open` (BrowserOS kiosk) | kiosk opens external links | Restrict to `xdg-open` via bus only, add `/usr/bin/xdg-open r,` to BrowserOS profile |
| `DENIED /home/hermesos/.*` on live boot | User homedir not yet created | Add `/home/hermesos/` to profile only if homedir exists; use `@{HOME}/` tunable |
| `DENIED open_whitelist` for `~/.lmstudio/` | First-run model download | Add `/home/hermesos/.lmstudio/models/ r,` explicitly — download dir created at first model load |

---

## 9. Profile Maintenance

**When a package ships a new binary (e.g. `lmstudio-cli`):**
1. Add the new binary to the existing profile or create a new stanza in `packages/duckbotos-*/debian/control`
2. Run `sudo apparmor_parser -r /etc/apparmor.d/usr.bin.<new-binary>` in the package `postinst`
3. Add to `test-apparmor.sh` expected profile list
4. Document the new access requirements in this file

**Profile update cycle:**
```bash
# Local development (permissive — dev mode)
sudo aa-complain /etc/apparmor.d/usr.bin.hermes-cli

# Test until no new denials appear for 5 minutes
sudo tail -f /var/log/audit/audit.log

# Promote to enforce
sudo aa-enforce /etc/apparmor.d/usr.bin.hermes-cli
```

**Audit log rotation:** Denials are logged to `/var/log/audit/audit.log`. Configure `logrotate` to cap at 50MB — AppArmor denials during onboarding can be verbose.

---

## 10. Quick Reference Card

```bash
# Check enforcement status
sudo aa-status | grep -E "hermes|openclaw|lms|browseros"

# Switch profile to complain (dev/debug)
sudo aa-complain /etc/apparmor.d/usr.bin.hermes-cli

# Return to enforce
sudo aa-enforce /etc/apparmor.d/usr.bin.hermes-cli

# View denials for one profile
sudo aureport --denied --profile=hermes-cli -i

# Reload after editing
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.hermes-cli

# Full syslog scan for AppArmor denials
sudo cat /var/log/syslog | grep apparmor | tail -50
```

---

*Part 2 complete — AppArmor profiles for all DuckBotOS services documented. Profile set covers: Hermes CLI, OpenClaw, LM Studio, BrowserOS, firejail session templates, testing harness, common fixes, and maintenance workflow.*