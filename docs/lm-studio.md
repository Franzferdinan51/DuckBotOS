# DuckBotOS — LM Studio Integration

> How LM Studio is installed, configured, and integrated as a first-class provider in DuckBotOS.
> Status: Updated v0.2 — 2026-06-29 (research-verified)

---

## 1. Overview

LM Studio is a **first-class provider** in DuckBotOS — installed by default on all three ISO variants (Hermes-only, OpenClaw-only, Both). Users can download models, configure the local server, and use it as their primary AI inference backend at zero API cost.

LM Studio runs as a **headless system service** (`llmster` daemon) bound to `localhost:1234`. The full OpenAI-compatible REST API lets both Hermes and OpenClaw use it as a drop-in provider with no code changes.

---

## 2. The Three LM Studio Components

| Component | Description | In DuckBotOS |
|-----------|-------------|--------------|
| **`lmstudio.ai`** | The desktop GUI app (Electron). Ships with bundled model downloader + inference UI. | ❌ Not used — no GUI in kiosk OS |
| **`llmster`** | The **headless daemon** — LM Studio core repackaged server-native, no Electron, no GUI. Installed via `curl -fsSL https://lmstudio.ai/install.sh \| bash`. | ✅ **Use this** |
| **`lms`** | The **CLI tool** — talks to both the desktop app and `llmster`. Auto-installed with `llmster`. Commands: `lms get`, `lms load`, `lms ls`, `lms ps`, `lms server start/stop`. | ✅ Used for model management |

`llmster` is the correct choice for a kiosk OS where the browser IS the interface.

---

## 3. Headless Installation

### 3.1 One-liner Install

```bash
curl -fsSL https://lmstudio.ai/install.sh | bash
```

This installs to `~/.lmstudio/bin/`:
- `lms` — CLI tool
- `llmster` — headless daemon binary

**Note:** Binary installs to `~/.lmstudio/bin/` (NOT `~/.local/bin/`). Add `~/.lmstudio/bin/` to PATH, or call via `~/.lmstudio/bin/lms`.

### 3.2 Install Script Breakdown

The install script (`https://lmstudio.ai/install.sh`) performs:
1. Detects OS (Linux/macOS/Windows)
2. Downloads the `llmster` binary for the platform
3. Installs `lms` CLI wrapper to `~/.lmstudio/bin/`
4. Creates `~/.lmstudio/` config directory
5. Creates `~/.cache/lm-studio/` model cache directory

No root required for installation — everything goes under `$HOME`.

### 3.3 DuckBotOS Package: `duckbotos-lm-studio`

For ISO bundling, wrap the install in a Debian package:

```
packages/duckbotos-lm-studio/
├── DEBIAN/
│   ├── control          # Package metadata + depends
│   └── postinst         # Post-install: run install.sh, enable service
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
if ! grep -q 'lmstudio/bin' /etc/environment 2>/dev/null; then
  echo 'export PATH="$HOME/.lmstudio/bin:$PATH"' >> /etc/bash.bashrc
fi
# Enable the systemd service
systemctl daemon-reload
systemctl enable lmstudio
echo "[DuckBotOS] LM Studio (llmster) installed and service enabled."
```

### 3.4 Offline Bundle (Future)

For air-gapped ISO builds, pre-download the `llmster` binary and bundle it:

```bash
# On a machine with internet:
curl -fsSL https://lmstudio.ai/install.sh | bash
# Then copy the ~/.lmstudio directory into the package rootfs:
cp -r ~/.lmstudio packages/duckbotos-lm-studio/rootfs/root/.lmstudio
```

---

## 4. Daemon Lifecycle

The `llmster` daemon is the core runtime. `lms` CLI communicates with it.

```
lms daemon up    → starts llmster as background daemon
lms daemon down  → stops the daemon
```

The daemon must be running before `lms server start` works.

---

## 5. Model Management

### 5.1 Download Models

```bash
# Download a model from HuggingFace
lms get openai/gpt-oss-20b
lms get lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF
lms get lmstudio-community/Qwen2.5-7B-Instruct-GGUF
lms get lmstudio-community/gemma-2-9b-it-GGUF

# List downloaded models
lms ls

# Show currently loaded models in memory
lms ps
```

### 5.2 Load Models

```bash
# Load a specific model (use model ID from lms ls)
lms load lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF --yes

# Load with GPU offload control
lms load lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF \
  --gpu=max       # maximum GPU offload
  --gpu=auto      # automatic GPU detection
  --gpu=0.5       # 50% GPU offload (half on GPU, half on CPU)

# Load with context length control
lms load lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF \
  --context-length=4096

# Unload a model (free VRAM)
lms unload lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF

# Unload all models
lms unload --all
```

**GPU layer flag:** `--gpu=max` attempts to offload 100% of computation to GPU. For models with N transformer layers, `--gpu=<N>` offloads that many layers. `-1` means all layers.

### 5.3 Model Identifiers

LM Studio uses HuggingFace model IDs. The model must be downloadable via HuggingFace. Example IDs:
- `lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF`
- `lmstudio-community/Qwen2.5-7B-Instruct-GGUF`
- `lmstudio-community/gemma-2-9b-it-GGUF`
- `openai/gpt-oss-20b`

---

## 6. REST API Endpoints

`llmster` exposes a **full OpenAI-compatible API** on `http://127.0.0.1:1234/v1`:

### 6.1 Start the Server

```bash
lms server start
# Server binds to http://127.0.0.1:1234/v1
# Default port: 1234. Use --port N to override.
```

### 6.2 Key Endpoints

```
GET  /v1/models                        — list available/loaded models
POST /v1/chat/completions             — chat completions (OpenAI format)
POST /v1/completions                  — text completions
POST /v1/embeddings                   — embedding vectors
POST /v1/models/{id}/load             — JIT load a model (JIT mode only)
POST /v1/models/{id}/unload           — unload a model
```

### 6.3 Example: Chat Completions

```bash
curl http://127.0.0.1:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
    "messages": [
      {"role": "system", "content": "You are DuckBot."},
      {"role": "user", "content": "Hello"}
    ],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

### 6.4 Example: Model List

```bash
curl http://127.0.0.1:1234/v1/models
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

---

## 7. Just-In-Time (JIT) Model Loading

JIT loading controls when models are loaded into memory:

| Mode | `/v1/models` returns | Inference behavior |
|------|---------------------|-------------------|
| **JIT ON** (default) | All downloaded models | Auto-loads model on first API call |
| **JIT OFF** | Only loaded models | Must call `POST /v1/models/{id}/load` first |

**Recommended for DuckBotOS:** JIT ON (default) — models load on first use, no explicit `lms load` needed in the systemd unit.

### Auto-Unload

JIT-loaded models auto-unload after a period of inactivity (configurable via TTL/auto-evict settings in `lms`).

---

## 8. systemd Service (Recommended)

**Correct binary path:** `~/.lmstudio/bin/lms` (NOT `/usr/local/bin/lms`)

### 8.1 Service Unit

```ini
# /etc/systemd/system/lmstudio.service

[Unit]
Description=LM Studio Server (llmster)
After=network.target
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
Environment="HOME=/root"
ExecStartPre=/root/.lmstudio/bin/lms daemon up
# JIT loading: models load on first API call, no pre-loading needed
ExecStart=/root/.lmstudio/bin/lms server start --port 1234
ExecStop=/root/.lmstudio/bin/lms daemon down
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 8.2 Alternative: Pre-load a Model

To pre-load a model on boot (no JIT):

```ini
[Service]
ExecStartPre=/root/.lmstudio/bin/lms daemon up
ExecStartPre=/root/.lmstudio/bin/lms load lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF --yes
ExecStart=/root/.lmstudio/bin/lms server start --port 1234
```

### 8.3 Install and Enable

```bash
sudo cp lmstudio.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lmstudio
sudo systemctl start lmstudio
```

### 8.4 Verification

```bash
# Check service status
systemctl status lmstudio

# Check API is responding
curl http://127.0.0.1:1234/v1/models

# Check loaded models
lms ps

# Check downloaded models
lms ls
```

---

## 9. Provider Configuration

### 9.1 Hermes Provider Config

In `/etc/hermes/providers.yaml`:

```yaml
providers:
  lm-studio:
    type: openai-compatible
    name: "LM Studio (Local)"
    base_url: "http://127.0.0.1:1234/v1"
    api_key: "lm-studio-local"    # Dummy — LM Studio needs no key
    default_models:
      - "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF"
    description: "Local GPU-accelerated inference. Zero API cost."
    capabilities: ["chat", "completion", "embedding"]
    hardware: local
```

### 9.2 OpenClaw Provider Config

In `openclaw.json` provider chain:

```json
{
  "providers": {
    "lm-studio": {
      "type": "openai-compatible",
      "name": "LM Studio",
      "base_url": "http://127.0.0.1:1234/v1",
      "api_key": "lm-studio-local",
      "models": ["lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF"]
    }
  }
}
```

### 9.3 Environment Variables

```bash
# /etc/duckbotos/kiosk-env.sh (sourced by kiosk services)
export LM_STUDIO_URL="http://127.0.0.1:1234/v1"
export LM_STUDIO_API_KEY="lm-studio-local"
```

---

## 10. First-Boot Wizard: Model Download

During first-boot (Step 2/5: Local Model Setup):

1. Start the `lmstudio` service if not running
2. Call `GET http://127.0.0.1:1234/v1/models` to get available models
3. Display a searchable model picker (HuggingFace search)
4. User selects a model → `lms get <model-id>` downloads it
5. Model appears in `lms ls`

**Recommended v1 models to suggest:**

| Model | Size | VRAM | Quality |
|-------|------|------|---------|
| `lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF` | ~4.7GB | 6GB | Excellent |
| `lmstudio-community/Qwen2.5-7B-Instruct-GGUF` | ~4.2GB | 5GB | Excellent |
| `lmstudio-community/gemma-2-9b-it-GGUF` | ~5GB | 6GB | Good |

---

## 11. Security

```bash
# API bound to localhost only — not network-exposed
# Port: 1234 (localhost only)

# Service runs as root (needed for GPU access)
# Future: firejail sandbox for lmstudio.service

# Config files
chmod 600 /etc/duckbotos/providers.yaml
```

**Network risk:** If `--bind 0.0.0.0` is used, the API is network-exposed. Always keep it on `127.0.0.1`.

---

## 12. Key Differences: llmster vs Desktop App

| | llmster (headless) | Desktop App |
|---|---|---|
| **GUI required** | No | Yes |
| **Memory footprint** | ~200 MB | ~500 MB+ |
| **Startup** | systemd service | Manual / tray |
| **API endpoint** | `http://127.0.0.1:1234/v1` | Same |
| **Model loading** | CLI or API | GUI |
| **Use case** | Server/headless/cockpit | Interactive |
| **DuckBotOS fit** | ✅ Perfect | ❌ Wasteful |

---

## 13. Build Checklist

- [ ] Create `packages/duckbotos-lm-studio/DEBIAN/control`
- [ ] Create `packages/duckbotos-lm-studio/DEBIAN/postinst`
- [ ] Create `packages/duckbotos-lm-studio/usr/lib/systemd/system/lmstudio.service`
- [ ] Add `duckbotos-lm-studio` to all three ISO package lists
- [ ] Verify `curl http://127.0.0.1:1234/v1/models` returns 200 in live ISO
- [ ] Verify `lms get <model>` downloads a model
- [ ] Verify chat completions work end-to-end

---

## 14. Key Sources

- [LM Studio headless docs](https://lmstudio.ai/docs/developer/core/headless) — official
- [llmster systemd setup](https://lmstudio.ai/docs/developer/core/headless_llmster) — official
- [lms CLI reference](https://lmstudio.ai/docs/cli) — official
- [LM Studio 0.4.0 release](https://lmstudio.ai/blog/0.4.0) — llmster introduction
- [llmster vs lms vs desktop](https://lmstudio.ai/docs/app/basics/lmstudio-vs-llmster-vs-lms) — official comparison

*LM Studio integration v0.2 — 2026-06-29 (research-verified)*
