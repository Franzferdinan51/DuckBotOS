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

*(Part 2 will cover BrowserOS profile, firejail templates, testing methodology, common denials + fixes)*