# DuckBotOS — First-Boot Wizard

> Post-OEM-install configuration wizard for DuckBotOS. Runs once, before the
> first GDM login, to set up agent mode, provider keys, local models, and
> session defaults.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Overview

DuckBotOS ships in three ISO variants (Hermes-only, OpenClaw-only, Both). All
three end up at the same place after OEM install: a configured agent OS ready
for first login. The **First-Boot Wizard** is the bridge between "OEM install
complete" and "GDM session picker."

It is **not** part of the autoinstall flow — `autoinstall.yaml` handles the
base install unattended, and the wizard handles *what makes this DuckBotOS
instead of plain Ubuntu*:

- Which agent(s) to enable (Hermes, OpenClaw, or both)
- Which LLM provider to use (cloud key entry, or local LM Studio)
- Which models to prefer (cascading dropdowns, with cost/VRAM hints)
- Accessibility and desktop-shortcut defaults
- A confirmation summary, then hand-off to GDM

### When it runs

```
OEM install (autoinstall.yaml)
        │
        ▼
First reboot → display-manager.service
        │
        ▼
duckbotos-first-boot-wizard.service   ← runs ONCE
        │
        ▼
GDM session picker (Hermes / OpenClaw / Hybrid)
        │
        ▼
User's chosen session
```

The wizard runs **before** the user picks a session at GDM. It blocks GDM
until complete (via `Before=gdm.service`) so users can't accidentally skip
straight to a desktop without configuring their agent.

### How to skip

Three legitimate escape hatches:

| Method | When to use |
|--------|-------------|
| Click "Advanced → Skip wizard" in the UI | Power users who'll configure by hand |
| `sudo duckbotos-first-boot-wizard --skip` from a TTY | Headless / remote installs |
| `sudo touch /var/lib/duckbotos/.wizard-complete` | Pre-staged deployments, OEM factories, CI |

When skipped, agents read defaults from `/etc/duckbotos/defaults.yaml` (the
minimal Hermes/OpenClaw-only "no API keys, local models only" baseline).

---

## 2. Wizard Steps

The wizard is **5 steps + welcome**, with a progress indicator (5 dots) along
the top. A `← Back` button is available on every step except the welcome
screen. A `Cancel → Skip wizard` link is always visible in the footer.

```
● ● ● ● ● ● ●
W  1  2  3  4  5  Done
```

---

### Step 0 — Welcome

Centered hero with the duck logo (128px SVG), subtitle "The agent-first
operating system," a primary **Get Started** button, and a secondary
**Advanced** link that reveals a menu:

- *Skip wizard and use defaults*
- *Open D-Bus configuration API* (shows the `com.duckbotos.FirstBootWizard`
  interface path so power users can `busctl` it)
- *Open documentation in BrowserOS*

No back button — this is the first step.

---

### Step 1 — Mode Selection

Three side-by-side cards. The selected card glows with a 2px primary-color
border; the others desaturate slightly.

**🤖 Hermes Agent** — Nous Research's autonomous agent runtime. Long-running
tasks, deep reasoning, tool-calling, fine-tune friendly.
*Recommended for: solo research, coding workflows, automation pipelines.*

**🦆 OpenClaw Agent** — Multi-provider gateway with mesh networking.
Multi-model routing, sub-agent spawning, cross-agent coordination.
*Recommended for: multi-agent setups, hybrid cloud+local, telemetry.*

**🔗 Both (Hybrid)** — Hermes and OpenClaw run side-by-side. Pick either from
a session-picker at GDM. They share credentials but keep separate session state.
*Recommended for: power users, developers, agent experimentation.*

The chosen mode is shown as a chip in the wizard header.

---

### Step 2 — Provider Setup

Contents depend on the mode selected in Step 1.

**If mode = Hermes:** Three API key fields — MiniMax (default, required),
Grok (optional), OpenAI (optional). Each has a password-style input with 👁
toggle, a "Test" button that hits a cheap endpoint (`GET /v1/models` for
OpenAI-compatible, `/api-key` for MiniMax), and a green ✓ or red ✗ indicator
after validation.

**If mode = OpenClaw:** Single primary MiniMax API key field. "Add secondary
provider…" link reveals optional Grok/OpenAI fields.

**If mode = Both:** Two side-by-side panels ("Hermes credentials" / "OpenClaw
credentials") with shared `Use same key for both?` toggle. When ON, only one
set of fields is shown and is written to both agents' config.

**All modes — Local Models toggle:** A prominent toggle at the bottom that,
when ON, adds Step 4 to the flow. LM Studio is pre-installed and listens on
port 1234.

**Security note (always visible at bottom):**

```
🔒 API keys are stored in /var/lib/duckbotos/creds (mode 0600, root only).
   When TPM 2.0 is available, keys are sealed to PCR values 0+7 and
   decrypted on demand — never written to disk in plaintext.
```

Continue is disabled until at least one valid key OR local models is enabled.

---

### Step 3 — Channel & Model Selection

Shown when cloud providers are in play. **Cascading dropdowns:**

```
Provider:  [ MiniMax        ▾ ]
Channel:   [ Production     ▾ ]
Model:     [ MiniMax-M2.7    ▾ ]   ← "⭐ Recommended" badge
```

When the user picks a model, a metadata panel updates with context window,
recommended VRAM, per-token cost, latency p50, vision/tool support, and a
"Recommended for" tag.

Below the metadata is a **Preview Chat** mini-test: a single text input +
Send button that runs a single non-streaming completion
(`max_tokens=128`, ~$0.0001) so users can sanity-check the model.

A "Show all models" link expands the dropdown to show every available model
in the channel (otherwise it shows the top 5).

---

### Step 4 — LM Studio Configuration

Shown only when "Use Local Models" is toggled ON.

**Server URL** (default `http://127.0.0.1:1234`) with a "Test" button that
hits `GET /v1/models` and shows a count + first 3 model IDs. The dropdown
stores the last 5 successful URLs.

**Model browser** — if the test succeeds, a model list panel appears with
selectable rows showing GGUF filename, size, context length, quant type,
and a warning icon when the model exceeds available VRAM (queried via
`nvidia-smi` or `/sys/class/drm/card*/device/mem_info_vram_total`).

**GPU offload** — radio buttons (Auto / Max / Custom) with a 0.00–1.00 slider
for Custom mode.

**Context length** — dropdown with options 2048, 4096, 8192, 16384, 32768,
65536, 131072. Default is 8192. Warning shown above 32768 on <16GB VRAM.

**Test Local Model** button at the bottom runs a single completion against
the selected model and shows the response + token count + latency.

---

### Step 5 — Finishing Touches

Three toggles + a summary screen:

- 🌐 **Network access** — Allow outbound API calls? (yes = cloud works,
  no = local only)
- ♿ **Accessibility** — Enable voice input via openWakeWord?
  ("Hey DuckBot" wake word activates microphone when ON)
- 🖥 **Desktop shortcuts** — Create Hermes/OpenClaw launcher shortcuts on
  the Activities overview?

**Summary panel:**

```
✅ Ready to start DuckBotOS

Mode:            Hybrid Workstation
Agents:          Hermes + OpenClaw
Providers:       MiniMax (Hermes + OpenClaw)
Default model:   MiniMax-M2.7
Local models:    LM Studio @ 127.0.0.1:1234 (qwen2.5-coder-32b)
Network:         Enabled
Voice:           Disabled
Shortcuts:       Enabled

Credentials stored: /var/lib/duckbotos/creds (TPM-sealed)

[ ← Back ]              [ Start DuckBotOS → ]
```

The **Start DuckBotOS** button writes `first-boot.yaml` and `.wizard-complete`,
reloads systemd, triggers `systemctl start gdm.service`, and closes with a
600ms fade-out.

---

## 3. Technical Implementation

### Frontend

The wizard ships as **two interchangeable frontends** sharing one config
schema and one D-Bus interface:

| Frontend | Use case | Package |
|----------|----------|---------|
| **GTK4 native app** | Default on `*-both*.iso` and full-disk installs | `duckbotos-wizard-gtk` |
| **Web app in Chromium kiosk** | Live USB sessions, lower-spec hardware | `duckbotos-wizard-web` |

Both are pure consumers of the D-Bus API — all config logic lives in the
`duckbotos-first-boot-wizardd` systemd service.

### Config schema

Written to `/var/lib/duckbotos/first-boot.yaml`:

```yaml
# /var/lib/duckbotos/first-boot.yaml
# Generated by first-boot-wizard on 2026-06-29
# DO NOT EDIT — re-run wizard or use 'duckbotos config set'

version: 1
mode: hybrid                    # hermes | openclaw | hybrid
completed_at: 2026-06-29T07:41:23Z

providers:
  minimax:
    api_key: ${DUCKBOTOS_MINIMAX_KEY}    # resolved from creds store
    default_channel: production
    default_model: MiniMax-M2.7
  xai:
    enabled: false
    api_key: ${DUCKBOTOS_GROK_KEY}
  openai:
    enabled: false
    api_key: ${DUCKBOTOS_OPENAI_KEY}

local_models:
  enabled: true
  server_url: http://127.0.0.1:1234
  default_model: qwen2.5-coder-32b-instruct-q4_k_m.gguf
  gpu_offload: 0.85
  context_length: 8192

preferences:
  outbound_network: true
  voice_input: false
  desktop_shortcuts: true
```

### D-Bus API

The wizard daemon exposes `com.duckbotos.FirstBootWizard` at
`/com/duckbotos/FirstBootWizard`:

```
Properties:
  s Mode                          # "hermes" | "openclaw" | "hybrid"
  s State                         # "WELCOME" | "MODE_SELECT" | ...
  b Completed
  a{sv} CurrentConfig             # dict of current wizard state

Methods:
  SetMode(s mode) → b
  SetProvider(s provider, s api_key) → b
  TestProvider(s provider, s api_key) → s status
  SetLocalConfig(s server_url, s model, d gpu_offload, i ctx) → b
  TestLocalModel() → s status
  SetPreference(s key, v value) → b
  GetConfig() → s yaml
  Complete() → b                  # writes files, returns true
  Skip() → b                      # writes marker file only

Signals:
  StateChanged(s old, s new)
  ConfigChanged(a{sv} diff)
```

Power users / scripts can drive the wizard without a UI:

```bash
busctl --user call com.duckbotos.FirstBootWizard \
    /com/duckbotos/FirstBootWizard \
    com.duckbotos.FirstBootWizard SetMode s hybrid

busctl --user call com.duckbotos.FirstBootWizard \
    /com/duckbotos/FirstBootWizard \
    com.duckbotos.FirstBootWizard SetProvider s minimax "sk-..."
```

### systemd unit

`/etc/systemd/system/duckbotos-first-boot-wizard.service`:

```ini
[Unit]
Description=DuckBotOS First-Boot Configuration Wizard
Documentation=man:duckbotos-first-boot-wizard(8)
After=display-manager.service network-online.target
Before=gdm.service
ConditionPathExists=!/var/lib/duckbotos/.wizard-complete
ConditionFirstBoot=yes

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/duckbotos-first-boot-wizardd --ui=auto
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

# Hard timeout — wizard must finish in 15 minutes
TimeoutStartSec=900

[Install]
WantedBy=graphical.target
```

`Type=oneshot` + `RemainAfterExit=yes` means the unit "completes" once the
wizard exits, allowing GDM to start. The 15-minute timeout prevents users
from being stuck on the wizard forever (after which it auto-completes with
defaults and logs a warning).

### Skipping

```bash
# CLI skip
sudo duckbotos-first-boot-wizard --skip

# Manual skip (e.g. in preseed/post-install scripts)
sudo install -m 0644 /dev/null /var/lib/duckbotos/.wizard-complete
sudo systemctl start gdm.service

# Re-run wizard (e.g. support engineers)
sudo rm /var/lib/duckbotos/.wizard-complete
sudo systemctl start duckbotos-first-boot-wizard.service
```

---

## 4. State Machine

```
                          ┌─────────────┐
                          │   WELCOME   │ (terminal entry)
                          └──────┬──────┘
                                 │ "Get Started"
                                 ▼
                          ┌─────────────┐
              ┌──────────│ MODE_SELECT │
              │          └──────┬──────┘
              │ "Advanced"     │ mode chosen
              ▼                ▼
        ┌──────────┐    ┌──────────────┐
        │ SKIPPED  │    │ PROVIDER_SETUP│
        └──────────┘    └──────┬───────┘
                               │ at least 1 valid key OR local=on
                               ▼
                       ┌───────────────┐
                       │  MODEL_SELECT │ (cloud providers only)
                       └──────┬────────┘
                              │ model chosen
                              ▼
                       ┌───────────────┐
                       │  LOCAL_MODEL  │ (only if local=on)
                       └──────┬────────┘
                              │ local model configured OR skipped
                              ▼
                       ┌───────────────┐
                       │   FINISHING   │
                       └──────┬────────┘
                              │ "Start DuckBotOS"
                              ▼
                       ┌───────────────┐
                       │   COMPLETE    │ ──→ writes config, starts GDM
                       └───────────────┘
```

- **`← Back`** is available on every state except `WELCOME` (nothing before it)
  and `COMPLETE` (terminal state)
- **`Cancel`** is always available → confirmation dialog → `SKIPPED`
- **`Skip wizard`** link in the footer → `SKIPPED`
- State transitions emit `StateChanged` on D-Bus for monitoring/automation

The wizard writes its current state to `/var/lib/duckbotos/wizard-state.json`
on every transition. If interrupted (crash, power loss), it resumes from
the last persisted state on next boot. The persisted file is removed when
state reaches `COMPLETE` or `SKIPPED`.

---

## 5. Error Handling

### API key validation

For each provider, the wizard issues a cheap read-only request after the user
pastes a key:

| Provider | Validation endpoint | Cost |
|----------|--------------------|------|
| MiniMax | `GET /v1/models` (OpenAI-compatible) | Free |
| xAI Grok | `GET /v1/models` | Free |
| OpenAI | `GET /v1/models` | Free |

Responses are matched against the schema. UI shows:

- ✓ **Valid** — green check, model count, "Continue" enabled
- ✗ **Invalid** — red X, error excerpt, "Try again" + "Skip this provider"
- ⚠ **Network error** — yellow warning, "Retry" + "Skip this provider"

Keys are stored **only after successful validation** — failed attempts leave
the field empty and emit a `ConfigChanged` signal so audit logs can see the
attempt.

### LM Studio connection

`GET <server_url>/v1/models` is called when the user clicks "Test" on Step 4:

- **200 + models list** → green ✓, populates the model browser
- **Connection refused** → "Can't reach LM Studio at <url>. Is the server
  running? Try `systemctl --user status lmstudio`." with an "Open terminal"
  button
- **404 / unexpected response** → "LM Studio responded but doesn't look
  like an OpenAI-compatible server. Check the URL."
- **Timeout (>3s)** → "LM Studio is slow to respond. Try increasing the
  timeout in LM Studio settings."

If `lmstudiod` isn't running, the wizard offers a "Start LM Studio" button
that runs `systemctl --user start lmstudiod.service` and re-tests after 2s.

### Offline mode

If `network-online.target` hasn't been reached by the time the wizard hits
Step 3, it shows a banner:

```
⚠ No network detected. Cloud provider testing is disabled.
   You can still complete the wizard using local models only.
```

When the user finishes without any cloud provider configured and
`outbound_network: false` is set, the summary screen shows a final warning
that voice transcription and web search features will be unavailable.

### Crash recovery

If the wizard daemon dies mid-flow, `wizard-state.json` lets it resume on
next boot. If resume fails (corrupt file, schema mismatch), the wizard
falls back to `WELCOME` and logs the recovery.

The systemd unit has `Restart=on-failure` with a 30s delay and max 3
restarts — beyond that, the wizard self-skips and writes
`.wizard-complete` with an error marker so support can diagnose.

### Field-level validation

Happens client-side (no round-trip):

- API key length: must be ≥ 20 chars (catches pasted placeholders)
- LM Studio URL: must parse as a valid HTTP/HTTPS URL with a hostname
- Context length: must be a power of 2 between 512 and 1,048,576
- GPU offload: must be 0.0–1.0

Invalid fields show inline red text + disable Continue until corrected.

---

## 6. References

- `docs/architecture.md` — overall DuckBotOS architecture
- `docs/system-boot-flow.md` — boot sequence (wizard sits between
  display-manager and GDM)
- `docs/providers.md` — provider list and channel/model metadata schema
- `docs/lm-studio.md` — LM Studio integration details (port 1234, model
  discovery, GPU offload defaults)
- `docs/installer.md` — autoinstall.yaml flow (wizard is the post-install
  step, not part of autoinstall)
- `docs/dual-agent-ipc.md` — how Hermes and OpenClaw share credentials
  in Hybrid mode