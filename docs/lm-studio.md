# DuckBotOS — LM Studio Integration

> How LM Studio is installed, configured, and integrated as a first-class provider in DuckBotOS.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Overview

LM Studio is a **first-class provider** in DuckBotOS — installed by default on all three ISO variants (Hermes-only, OpenClaw-only, Both). Users can download models, configure the local server, and use it as their primary AI inference backend at zero API cost.

LM Studio runs as a **headless system service** (`llmster` daemon) bound to `localhost:1234`. The full OpenAI-compatible REST API lets both Hermes and OpenClaw use it as a drop-in provider with no code changes.

---

## 2. Why llmster (Not the Desktop App)

| | llmster (headless) | Desktop App |
|---|---|---|
| **GUI required** | No | Yes |
| **Memory footprint** | ~200 MB | ~500 MB+ |
| **Startup** | systemd service | Manual / tray |
| **API endpoint** | `http://127.0.0.1:1234/v1` | Same |
| **Model loading** | CLI or API | GUI |
| **Use case** | Server/headless/cockpit | Interactive |
| **DuckBotOS fit** | ✅ Perfect | ❌ Wasteful |

`llmster` is the core inference runtime of LM Studio, packaged without the Electron GUI. It is the correct choice for a kiosk OS where the browser IS the interface.

---

## 3. Headless Installation

### 3.1 Install Script (One-liner)

```bash
curl -fsSL https://lmstudio.ai/install.sh | bash
```

This installs:
- `lms` CLI tool → `~/.local/bin/lms`
- `llmster` daemon binary (internal)
- Model cache directory → `~/.cache/lm-studio/`
- Config directory → `~/.lmstudio/`

**Note:** The binary installs to `~/.lmstudio/bin/` (NOT `~/.local/bin/`). Add `~/.lmstudio/bin/` to PATH, or call via `~/.lmstudio/bin/lms`.

### 3.2 DuckBotOS Package: `duckbotos-lm-studio`

For ISO bundling, we wrap this in a Debian package:

```
packages/duckbotos-lm-studio/
├── DEBIAN/
│   ├── control          # Package metadata + depends
│   └── postinst         # Post-install: run install.sh, enable service
├── opt/lmstudio/        # Binary staging (if offline bundle needed)
└── usr/lib/systemd/system/
    └── lmstudio.service # systemd unit
```

**`DEBIAN/control`:**
```
Package: duckbotos-lm-studio
Version: 0.4.0
Section: ai
Priority: optional
Depends: curl, libc6 (>= 2.34)
Maintainer: DuckBotOS <franzferdinan51@github>
Architecture: amd64
Description: LM Studio headless inference server (llmster)
 Installs llmster daemon + lms CLI for local LLM inference.
 Provides OpenAI-compatible REST API on port 1234.
```

**`DEBIAN/postinst`:**
```bash
#!/bin/bash
set -e
# Run LM Studio headless install script
curl -fsSL https://lmstudio.ai/install.sh | bash
# Add to PATH if not already
if ! grep -q 'lmstudio/bin' /etc/environment; then
  echo 'export PATH="$HOME/.lmstudio/bin:$PATH"' >> /etc/bash.bashrc
fi
# Enable the systemd service
systemctl daemon-reload
systemctl enable lmstudio
echo "[DuckBotOS] LM Studio (llmster) installed and service enabled."
```

### 3.3 Offline Bundle (Future)

For air-gapped ISO builds, bundle the `lms` CLI + models directory directly. The install script downloads the llmster binary on first run — for offline ISO, pre-bundle:

```bash
# On a machine with internet, download once:
curl -fsSL https://lmstudio.ai/install.sh | bash
# Then copy the ~/.lmstudio directory into the package:
cp -r ~/.lmstudio packages/duckbotos-lm-studio/rootfs/root/.lmstudio
```

---

## 4. systemd Service

### 4.1 Service Unit: `lmstudio.service`

**Correct path:** `~/.lmstudio/bin/lms` (from official LM Studio docs).

```ini
[Unit]
Description=LM Studio Server
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
Environment="HOME=/root"
ExecStartPre=/root/.lmstudio/bin/lms daemon up
ExecStartPre=/root/.lmstudio/bin/lms load lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF --yes
ExecStart=/root/.lmstudio/bin/lms server start
ExecStop=/root/.lmstudio/bin/lms daemon down
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Alternative (JIT loading — no pre-loaded model):**
Omit the `ExecStartPre` lines. The server starts and loads models on first API call.

Install to `/etc/systemd/system/lmstudio.service`, then:

```bash
systemctl daemon-reload
systemctl enable lmstudio
systemctl start lmstudio
```

### 4.2 Verification

```bash
# Check service status
systemctl status lmstudio

# Check API is responding
curl http://127.0.0.1:1234/v1/models
# Expected: JSON with list of available models

# Check lms CLI
lms ps   # Show loaded models
lms ls   # List downloaded models
```

---

## 5. REST API Endpoints

llmster exposes a **full OpenAI-compatible API** on `http://127.0.0.1:1234/v1`:

### 5.1 Model List

```
GET /v1/models
```

```json
{
  "object": "list",
  "data": [
    {
      "id": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
      "object": "model",
      "created": 1717200000,
      "owned_by": "lmstudio-community",
      "permission": [],
      "root": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
      "parent": null
    }
  ]
}
```

### 5.2 Chat Completions

```
POST /v1/chat/completions
```

```json
{
  "model": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
  "messages": [
    {"role": "system", "content": "You are DuckBot."},
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7,
  "max_tokens": 512
}
```

### 5.3 Completions

```
POST /v1/completions
```

```json
{
  "model": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
  "prompt": "The capital of France is",
  "max_tokens": 50
}
```

### 5.4 Embeddings

```
POST /v1/embeddings
```

```json
{
  "model": "lmstudio-community/bert-bge-base-en-v1.5-GGUF",
  "input": "Hello world"
}
```

### 5.5 Model Loading (JIT)

When JIT loading is enabled (default), a model is loaded automatically on first API call. Explicit load via CLI:

```bash
# Load a specific model (use model ID from lms ls)
lms load lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF

# Load with options
lms load lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF \
  --context-length 4096 \
  --gpu off

# Show downloaded models
lms ls

# Show what's currently loaded
lms ps

# Unload to free VRAM
lms unload lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF

# Stop the server
lms server stop

# Start the server
lms server start

# Daemon control
lms daemon up    # Start the daemon
lms daemon down  # Stop the daemon
```

---

## 6. OS Integration

### 6.1 Provider Configuration

LM Studio is pre-configured in `/etc/duckbotos/providers.yaml` as:

```yaml
providers:
  lm-studio:
    type: openai-compatible
    name: "LM Studio (Local)"
    base_url: "http://127.0.0.1:1234/v1"
    api_key: "lm-studio-local"        # Dummy: LM Studio needs no key
    default_models:
      - "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF"
    description: "Local GPU-accelerated inference. Zero API cost."
    capabilities: ["chat", "completion", "embedding"]
    hardware: "local"                 # Tags for UI display
```

### 6.2 First-Boot Wizard: Model Download

During first-boot (Step 2/5: Local Model Setup), the wizard:

1. Starts the `lmstudio` service if not running
2. Calls `GET http://127.0.0.1:1234/v1/models` to get available models
3. Displays a model picker (searchable list from HuggingFace)
4. User selects a model → `lms get <model-id>` downloads it
5. Model appears in `lms ls` output

**Recommended v1 models to suggest:**
| Model | Size | VRAM | Quality |
|-------|------|------|---------|
| `lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF` | ~4.7GB | 6GB | Excellent |
| `lmstudio-community/Qwen2.5-7B-Instruct-GGUF` | ~4.2GB | 5GB | Excellent |
| `lmstudio-community/gemma-2-9b-it-GGUF` | ~5GB | 6GB | Good |

### 6.3 Kiosk Environment Variables

The kiosk startup script exports:

```bash
# /etc/duckbotos/kiosk-env.sh (sourced by kiosk services)
export LM_STUDIO_URL="http://127.0.0.1:1234/v1"
export LM_STUDIO_API_KEY="lm-studio-local"
```

Both Hermes and OpenClaw read these to auto-configure LM Studio as a provider.

### 6.4 LM Studio UI (Optional)

DuckBotOS is a kiosk (no desktop), but for development/debugging, LM Studio's GUI can be installed as a snap:

```bash
snap install lm-studio --classic  # If/when available as snap
```

Or accessed via BrowserOS at `http://127.0.0.1:1234` (LM Studio serves a local web UI at port 1234 by default when the desktop app is running — llmster does NOT serve a web UI, only the REST API).

---

## 7. Security

```bash
# API bound to localhost only — not network-exposed
# Port: 1234 (localhost)

# Service runs as root (GPU access) — llmster needs GPU
# Config files
chmod 600 /etc/duckbotos/providers.yaml

# Model files in user dir — standard DAC
# Future: consider firejail sandbox for lmstudio.service
```

---

## 8. Build Checklist

- [ ] Create `packages/duckbotos-lm-studio/DEBIAN/control`
- [ ] Create `packages/duckbotos-lm-studio/DEBIAN/postinst`
- [ ] Create `packages/duckbotos-lm-studio/usr/lib/systemd/system/lmstudio.service`
- [ ] Add `duckbotos-lm-studio` to all three ISO package lists
- [ ] Verify `curl http://127.0.0.1:1234/v1/models` returns 200 in live ISO
- [ ] Verify `lms get <model>` downloads a model
- [ ] Verify chat completions work end-to-end

---

*LM Studio integration v0.1 — 2026-06-29*