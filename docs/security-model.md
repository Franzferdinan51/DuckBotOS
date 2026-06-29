# DuckBotOS Security Model

**Version:** 1.0  
**Date:** 2026-06-29  
**Base OS:** Ubuntu 24.04 Noble Numbat  
**Primary Agent:** Hermes (hermesos user)  
**Secondary Agent:** OpenClaw (openclaw user)  
**Local LLM Provider:** LM Studio (lmstudio user)  
**Default Browser:** BrowserOS (Chromium fork)

---

## 1. Threat Model

### Primary Threats
- **Stolen API keys**: Extraction of `minimax.key`, `openai.key`, `grok.key`, `openrouter.key` from credential storage or process memory.
- **Local model data exfiltration**: Theft of GGUF weights or embeddings from `~/.lmstudio/models/` or LM Studio runtime directories.
- **Malicious websites in BrowserOS**: Drive-by downloads, XSS, or browser sandbox escapes targeting the agent desktop session.
- **Rogue agent actions**: Hermes or OpenClaw executing unauthorized shell commands, D-Bus calls, or network requests outside whitelisted domains.
- **Supply chain attacks during ISO build**: Compromised `.deb` packages, unsigned kernels, or malicious assets injected into the live-build process.

### Assets Protected
- API keys and authentication tokens
- Conversation history and session transcripts (stored in DuckBot Brain)
- Local model weights and LoRA adapters
- System filesystem integrity (`/etc`, `/usr`, `/var/lib/duckbotos`)
- User home directories (`/home/hermesos`, `/home/openclaw`)

### Out-of-Scope Protections
- Physical access attacks beyond full-disk encryption (LUKS2 + TPM)
- Nation-state level attackers with hardware implants
- Compromised build infrastructure or signing key theft
- Side-channel attacks (Spectre, Rowhammer, etc.)

### Trust Boundaries
| Boundary | Trust Level | Rationale |
|----------|-------------|-----------|
| User space (hermesos, openclaw) | Untrusted | Receives untrusted input from BrowserOS, tools, and D-Bus |
| System services (LM Studio, Weston, BrowserOS) | Trusted | Run under dedicated service accounts with strict sandboxing |
| Kernel + initramfs | Trusted | Signed kernel, verified boot chain |
| Build infrastructure | Semi-trusted | Reproducible builds + SBOM required; public key embedded in ISO |

---

## 2. User/Group Model

### Dedicated Service Accounts

| User | UID Range | Primary Groups | Purpose | Shell | Login |
|------|-----------|----------------|---------|-------|-------|
| `hermesos` | 97801 | `audio`, `video`, `network`, `duckbotos` | Primary agent runtime | `/bin/bash` | No direct login |
| `openclaw` | 97802 | `audio`, `video`, `duckbotos` | Secondary agent runtime | `/bin/bash` | No direct login |
| `lmstudio` | 97803 | `audio`, `video` | LM Studio inference service | `/usr/sbin/nologin` | No |
| `duckbotos` | 97800 (GID) | — | Shared IPC group | — | — |

### UID/GID Allocation
- Reserved block: `97801–97899` (from `systemd.DynamicUser` range)
- `duckbotos` group GID: 97800
- No passwordless `sudo` for any account
- Root SSH login disabled (`PermitRootLogin no`)
- Sudo requires password + `tty` requirement

### Group Membership Rules
- `hermesos` gets `network` group (direct outbound allowed)
- `openclaw` deliberately **excludes** `network` group — all outbound traffic must route through Hermes IPC bus
- Both users share `duckbotos` group for `/var/lib/duckbotos/creds/` access and D-Bus IPC socket

---

## 3. Credential Storage

### Directory Layout
```
/var/lib/duckbotos/creds/
├── minimax.key          # 0600, hermesos:duckbotos
├── openai.key
├── grok.key
├── openrouter.key
├── lmstudio.url         # localhost endpoint only
└── age-recipients.txt   # public keys for AGE encryption
```

### Permissions
- Directory: `0700 root:root`
- Files: `0600 root:duckbotos` (group-readable by service accounts)
- Never world-readable

### TPM2-Backed Storage (Preferred)
When TPM2 device is present (`/dev/tpmrm0`):
- Keys sealed to PCR 0+7 (Secure Boot + OS state)
- Unseal only succeeds on verified boot chain
- Keys never exist in plaintext at rest
- Tooling: `tpm2_createprimary`, `tpm2_create`, `tpm2_unseal`

### AGE Fallback (No TPM)
- Credentials encrypted with AGE using passphrase stored in TPM (or removable YubiKey/TPM dongle)
- Decryption happens at service startup via `age -d`
- Passphrase never written to disk in plaintext

### Environment Variable Injection
Services use a small wrapper (`/usr/lib/duckbotos/bin/inject-creds`) that:
1. Reads appropriate `.key` file
2. Exports `MINIMAX_API_KEY`, `OPENAI_API_KEY`, etc.
3. `exec`s the real binary
- Never stored in `/etc/environment` or systemd unit `Environment=`

### LM Studio Auth Token
- Path: `/home/hermesos/.lmstudio/settings.json`
- Mode: `0600 hermesos:hermesos`
- Contains local server bearer token for `http://127.0.0.1:1234`

### SSH Keys
- `~/.ssh/id_ed25519` and `id_rsa` owned by respective user, mode `0600`
- `hermesos` and `openclaw` cannot read each other's SSH directories

---

## 4. Process Sandboxing

### BrowserOS (firejail)
```bash
firejail --profile=/etc/firejail/browseros.profile \
  --net=none \
  --read-only=/home \
  --read-write=/tmp \
  --noroot \
  --nosound \
  --caps.drop=all \
  browseros --kiosk --disable-gpu
```

**Profile highlights** (`/etc/firejail/browseros.profile`):
- `net none` (toggleable via settings → re-exec with `--net=eth0`)
- `read-only /home`
- `read-write /tmp,/var/tmp`
- `blacklist /home/*/.*ssh`
- `blacklist /var/lib/duckbotos/creds`
- No `sudo` or `su` allowed inside jail

### Hermes CLI (firejail)
```bash
firejail --profile=/etc/firejail/hermes.profile \
  --net=eth0 \
  --whitelist=/var/lib/duckbotos/creds \
  --whitelist=/home/hermesos/.config/hermes \
  --whitelist=/home/hermesos/.lmstudio \
  --read-only=/etc \
  hermes-cli
```

### AppArmor — Hermes Service
Profile: `/etc/apparmor.d/usr.bin.hermes-cli`

```apparmor
#include <tunables/global>
profile hermes-cli /usr/bin/hermes-cli flags=(enforce) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  /home/hermesos/.config/hermes/** rw,
  /home/hermesos/.lmstudio/** rw,
  /var/lib/duckbotos/creds/ r,
  /var/lib/duckbotos/creds/*.key r,

  network inet tcp,
  network inet udp,

  # Explicitly allowed API domains only (enforced by nftables too)
  network inet tcp to api.minimax.chat:443,
  network inet tcp to api.grok.com:443,
  network inet tcp to api.openai.com:443,
  network inet tcp to api.openrouter.ai:443,

  deny /etc/shadow r,
  deny /home/*/.*ssh/** r,
  deny /var/log/** w,

  audit deny /** w,   # catch-all write denial
}
```

All denials logged to `/var/log/syslog` with `apparmor="DENIED"`.

### AppArmor — OpenClaw Service
Profile: `/etc/apparmor.d/usr.bin.openclaw`

- Same file restrictions as Hermes
- D-Bus rule: can own `org.duckbotos.OpenClaw` but cannot send to other bus names except `org.duckbotos.Bus`
- No network abstractions allowed (OpenClaw has no `network` group)

---

## 5. D-Bus Access Control

### Bus Architecture
- **System bus**: No DuckBotOS services registered (explicit policy denial)
- **Session bus**: Per-login-session bus
  - `org.duckbotos.Hermes`
  - `org.duckbotos.OpenClaw`
  - `org.duckbotos.Bus` (shared IPC bus)

### Policy File
`/etc/dbus-1/duckbotos.conf`:

```xml
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy context="user">
    <allow send_destination="org.duckbotos.*"/>
    <allow receive_sender="org.duckbotos.*"/>
    <!-- Block all system bus relay attempts -->
    <deny send_destination="org.freedesktop.*"/>
    <deny send_destination="org.freedesktop.systemd1"/>
  </policy>
</busconfig>
```

### IPC Rules
- Hermes ↔ OpenClaw communication occurs **only** via Unix socket at `/run/duckbotos/ipc.sock` (0600, duckbotos:duckbotos)
- No direct D-Bus method calls between the two agent users

---

## 6. Network Security

### nftables Outbound Policy (`/etc/nftables.conf`)
```nftables
table inet duckbotos {
  chain output {
    type filter hook output priority 0; policy drop;

    # Hermes (hermesos user)
    meta skuid hermesos tcp dport {80,443} ip daddr {api.minimax.chat, api.grok.com, api.openai.com, api.openrouter.ai} accept
    meta skuid hermesos udp dport 53 accept

    # OpenClaw (openclaw user) — limited
    meta skuid openclaw tcp dport {80,443} ip daddr {api.minimax.chat, api.openrouter.ai} accept
    meta skuid openclaw udp dport 53 accept

    # LM Studio — localhost only
    meta skuid lmstudio ip daddr 127.0.0.1 tcp dport 1234 accept

    # BrowserOS — none by default (user must explicitly enable)
    meta skuid browseros drop
  }
}
```

### Inbound Policy
- Default: `DROP` all
- No listening sockets exposed on any interface except loopback for LM Studio

### DNS
- `systemd-resolved` primary
- `dnsmasq` for local `.local` and DuckBotOS service discovery
- DNS-over-HTTPS disabled by default (can be enabled via settings)

### Optional VPN
- WireGuard interface `wg0` for `gitlawb` DID operations
- Activated only when `duckbotos-vpn` service is started

---

## 7. ISO Build Security

### Build Process Hardening
- All `.deb` packages verified against SHA256 sums in `Packages` manifest before inclusion
- No `curl`/`wget` allowed during `lb build` — all assets pre-bundled in `assets/`
- Reproducible builds: `lb build --reproducible`
- ISO SHA256 recorded in build log and embedded in `/boot/grub/grub.cfg`
- Signing: DuckBotOS release key signs the ISO; public key shipped at `/usr/share/keyrings/duckbotos-archive-keyring.gpg`

### Telemetry & Consent
- Zero network calls on first boot or during install without explicit user consent stored in `/etc/duckbotos/consent.json`

### SBOM
- SPDX 2.3 document generated at build time
- Location: `/usr/share/doc/duckbotos/sbom.spdx`
- Includes all packages, kernel modules, and firmware blobs

---

## 8. Kernel Hardening

### Secure Boot
- Kernel and initramfs signed with canonical Microsoft UEFI CA (via `shim-signed`)
- Custom DuckBotOS kernel modules must be signed with build-time key

### Sysctl Hardening (`/etc/sysctl.d/99-duckbotos.conf`)
```sysctl
kernel.kptr_restrict=2
kernel.dmesg_restrict=1
kernel.yama.ptrace_scope=1
fs.protected_hardlinks=1
fs.protected_symlinks=1
fs.protected_fifos=2
fs.protected_regular=2
net.ipv4.icmp_echo_ignore_all=0
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.default.rp_filter=1
net.ipv6.conf.all.disable_ipv6=0   # allowed for modern stacks
```

### Module Loading
- `modprobe.blacklist=off` is **not** set
- Unsigned modules rejected at load time

---

## 9. File Access Control

| Path | Mode | Owner | Notes |
|------|------|-------|-------|
| `/etc/shadow` | 0400 | root:root | No access from agent users |
| `/var/log/` | 0755 | root:syslog | Agents can read (journald writes) |
| `/var/lib/duckbotos/creds/` | 0700 | root:duckbotos | Group read for service accounts only |
| `/home/*/.*ssh/` | 0700 | respective user | Cross-user isolation enforced |
| `/proc/` | — | — | seccomp filter blocks `pidfd_open` on foreign PIDs |
| `/run/duckbotos/` | 0755 | root:duckbotos | IPC socket lives here |

---

## 10. User Data Encryption

### Home Directory Encryption
- `/home` partition uses LUKS2 with TPM2 sealing (PCR 0+7)
- Recovery key: sealed to TPM + optional printed QR code stored offline

### Swap & Hibernate
- Encrypted swap required (`/etc/crypttab` entry)
- `systemctl hibernate` blocked if swap is not encrypted (`ConditionPathIsMountPoint=/dev/mapper/swap_crypt`)

### Removable Media
- LUKS containers auto-unlocked via TPM when inserted (policy in `/etc/udev/rules.d/99-duckbotos-luks.rules`)

---

## 11. Compliance & Audit

### Audit Log Location
- `/var/log/duckbotos/audit.log` (0600 root:duckbotos)

### Logged Events
- Credential file reads (`cred.read`)
- Model weight downloads (`model.download`)
- Tool execution (`tool.exec`)
- D-Bus method calls (`dbus.call`)
- firejail/AppArmor denials (via syslog → audit forwarder)

### Log Rotation
- Audit logs: 7 days, compressed
- System logs: 30 days via `logrotate`

### Query Tool
```bash
duckbotos-audit --from=2026-06-01 --to=2026-06-07 \
  --event=cred.read --user=hermesos
```

---

## 12. Security Update Process

### Automatic Updates
- `unattended-upgrades` enabled, limited to `security` pocket only
- `APT::Periodic::Update-Package-Lists "1";`

### Kernel Updates
- Require re-verification of Secure Boot signature
- New kernel installed as `linux-image-*-duckbotos` package

### LM Studio
- Manual updates only (reproducibility requirement)
- Version pinned in ISO manifest

### BrowserOS
- `.deb` updates must be signed with DuckBotOS key
- Signature verified before `dpkg -i`

---

**End of Security Model Document**

*This document is the authoritative reference for all DuckBotOS security controls. Changes require security review and version bump.*