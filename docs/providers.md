# DuckBotOS — Provider Aggregation

> All AI providers available in DuckBotOS: cloud APIs, local LM Studio, OpenRouter, and OpenAI-compatible endpoints.
> Status: Draft v0.1 — 2026-06-29

---

## 1. Philosophy

DuckBotOS is provider-agnostic. The OS ships with every provider that both Hermes and OpenClaw support, giving users maximum flexibility:
- **Cloud-first** users bring their own API keys
- **Privacy-first** users use LM Studio for fully local inference
- **Hybrid** users use LM Studio for everyday tasks and cloud for heavy lifting

Providers are configured in a unified `providers.yaml` that both agent systems can read.

---

## 2. Provider Matrix

| Provider | Type | API Key Env | Base URL | Default Model | Status |
|----------|------|-------------|----------|---------------|--------|
| **MiniMax** | OpenAI-compatible | `MINIMAX_API_KEY` | `https://api.minimaxi.chat/v1` | `minimax-portal/MiniMax-M2.7` | ✅ Available |
| **OpenAI** | OpenAI-compatible | `OPENAI_API_KEY` | `https://api.openai.com/v1` | `gpt-4o` | ✅ Available |
| **Anthropic** | Anthropic-native | `ANTHROPIC_API_KEY` | `https://api.anthropic.com` | `claude-sonnet-4-20250514` | ✅ Available |
| **Grok/xAI** | OpenAI-compatible | `XAI_API_KEY` | `https://api.x.ai/v1` | `xai/grok-4.3` | ✅ Available |
| **OpenRouter** | OpenAI-compatible | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` | `google/gemini-2.0-flash-exp` | ✅ Available |
| **LM Studio** | OpenAI-compatible | `local` (no key) | `http://127.0.0.1:1234/v1` | user-selected | ✅ First-class |
| **Free GLM** | OpenAI-compatible | none (free tier) | `https://open.bigmodel.cn/api/paas/v4` | `zai/glm-4.7-flash` | ✅ Free tier |
| **DeepSeek** | OpenAI-compatible | `DEEPSEEK_API_KEY` | `https://api.deepseek.com/v1` | `deepseek-chat` | ⏳ Future |
| **Ollama** | OpenAI-compatible | none (local) | `http://localhost:11434/v1` | user-selected | ⏳ Future |

---

## 3. LM Studio (First-Class, Local)

LM Studio is a **first-class provider** in DuckBotOS — installed by default, with a dedicated setup step in the first-boot wizard.

### 3.1 Why LM Studio

- **Zero API cost** — runs models locally on the user's GPU
- **Privacy** — no data leaves the machine
- **OpenAI-compatible API** — drop-in replacement for any OpenAI-compatible client
- **Model portability** — HuggingFace GGUF models, easily downloaded
- **Cross-vendor** — works with NVIDIA, AMD, Intel GPUs via llama.cpp

### 3.2 Configuration

```yaml
# Provider entry for LM Studio
- name: lm-studio
  type: openai-compatible
  api_key: local  # no auth needed for localhost
  base_url: http://127.0.0.1:1234/v1
  default_model: null  # user selects at first-boot wizard
  required_capabilities:
    - chat
    - completion
    - embeddings
  # JIT loading: model auto-loaded on first inference call
  # Configurable via lms config set server.jit.enabled true
```

### 3.3 OS-Level Integration

- **Installed by default** in all three ISOs
- **llmster daemon** (`lms daemon up`) runs as a systemd user service
- **API port 1234** bound to localhost only (not exposed externally)
- **Model download** via first-boot wizard or `lms download` CLI
- **Model selection** UI in first-boot wizard: calls `GET /v1/models`, shows downloaded models

### 3.4 LM Studio Headless Install

```bash
# Official headless install script (installs llmster)
curl -fsSL https://lmstudio.ai/install.sh | bash

# This installs:
#   ~/.local/bin/lms              # CLI
#   ~/.local/share/lm-studio/     # models, config, cache

# llmster runs without GUI:
lms daemon up

# CLI examples:
lms models list              # show downloaded models
lms models available         # search HuggingFace
lms download Llama-3.1-8B    # download a model
lms server start             # start REST API (if daemon not running)

# REST API available at http://127.0.0.1:1234
```

### 3.5 Systemd User Service for llmster

```ini
# ~/.config/systemd/user/lmstudio.service
[Unit]
Description=LM Studio llmster daemon
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=%h/.local/bin/lms daemon up
Restart=always
RestartSec=10
Environment=LMSTUDIO_API_KEY=
# If LM Studio has API auth configured:
# Environment=LMSTUDIO_API_KEY=your-key-here

[Install]
WantedBy=default.target
```

Enable with:
```bash
systemctl --user enable lmstudio.service
systemctl --user start lmstudio.service
```

### 3.6 lm-studio .deb Packaging for ISO

To bundle llmster in the ISO, create a `packages/lm-studio/` deb:

```
packages/lm-studio/
├── DEBIAN/
│   ├── control        # Depends: curl, ca-certificates
│   ├── postinst       # runs: curl -fsSL https://lmstudio.ai/install.sh | bash
│   └── prerm          # cleanup if needed
└── usr/
    └── share/
        └── doc/
            └── lm-studio/
                └── README.install  # explains how to use lms CLI
```

Or better: download the AppImage in the live-build hook and install it:

```bash
# config/hooks/live/chroot-early/10-lm-studio.chroot
cd /tmp
curl -fsSL -o lm-studio-appimage \
  https://lmstudio.ai/download/linux/latest/LM_Studio-*.AppImage
chmod +x lm-studio-appimage
mv lm-studio-appimage /usr/local/bin/lm-studio-headless
# Register lms bootstrap
su -c '/usr/local/bin/lm-studio-headless --help' || true
```

---

## 4. MiniMax

Primary cloud provider for DuckBotOS.

### 4.1 API Details

- **API endpoint:** `https://api.minimaxi.chat/v1`
- **Models:** MiniMax-M3, MiniMax-M2.7, MiniMax-M2.5
- **Context:** 1M tokens (M3), 256K (M2.7)
- **API key:** `MINIMAX_API_KEY`

### 4.2 Provider Config

```yaml
- name: minimax
  type: openai-compatible
  api_key_env: MINIMAX_API_KEY
  base_url: https://api.minimaxi.chat/v1
  default_model: minimax-portal/MiniMax-M2.7
  max_tokens: 8192
  required_capabilities:
    - chat
    - completion
    - streaming
```

---

## 5. OpenAI

Standard OpenAI API provider.

### 5.1 API Details

- **API endpoint:** `https://api.openai.com/v1`
- **Models:** GPT-4o, GPT-4o-mini, o3, o4-mini, GPT-4.1, etc.
- **API key:** `OPENAI_API_KEY`

### 5.2 Provider Config

```yaml
- name: openai
  type: openai-compatible
  api_key_env: OPENAI_API_KEY
  base_url: https://api.openai.com/v1
  default_model: gpt-4o
  max_tokens: 16384
  required_capabilities:
    - chat
    - completion
    - streaming
    - embeddings
    - function-calling
```

---

## 6. Anthropic

Anthropic Claude models via native API.

### 6.1 API Details

- **API endpoint:** `https://api.anthropic.com`
- **Models:** claude-opus-4-5, claude-sonnet-4-5, claude-3-5-haiku, etc.
- **API key:** `ANTHROPIC_API_KEY`

### 6.2 Provider Config

```yaml
- name: anthropic
  type: anthropic
  api_key_env: ANTHROPIC_API_KEY
  default_model: claude-sonnet-4-20250514
  max_tokens: 8192
  required_capabilities:
    - chat
    - streaming
    - tool-use
```

---

## 7. Grok / xAI

xAI's Grok models via the xAI API.

### 7.1 API Details

- **API endpoint:** `https://api.x.ai/v1`
- **Models:** `xai/grok-4.3` (2M context), `xai/grok-4.20-beta` (2M context)
- **API key:** `XAI_API_KEY`
- **Note:** Grok models are reasoning-focused; good for complex multi-step tasks

### 7.2 Provider Config

```yaml
- name: grok
  type: openai-compatible
  api_key_env: XAI_API_KEY
  base_url: https://api.x.ai/v1
  default_model: xai/grok-4.3
  max_tokens: 65536
  required_capabilities:
    - chat
    - completion
    - streaming
```

---

## 8. OpenRouter

Aggregated gateway for many models (Google, Meta, Mistral, etc.).

### 8.1 API Details

- **API endpoint:** `https://openrouter.ai/api/v1`
- **Models:** 100+ models, free and paid tiers
- **API key:** `OPENROUTER_API_KEY`
- **Key advantage:** Single API key for many model providers; unified billing

### 8.2 Provider Config

```yaml
- name: openrouter
  type: openai-compatible
  api_key_env: OPENROUTER_API_KEY
  base_url: https://openrouter.ai/api/v1
  default_model: google/gemini-2.0-flash-exp  # free tier default
  max_tokens: 32768
  required_capabilities:
    - chat
    - completion
    - streaming
```

### 8.3 Recommended Free Models on OpenRouter

| Model | Context | Quality |
|-------|---------|---------|
| `google/gemini-2.0-flash-exp` | 1M | Excellent, fast |
| `deepseek/deepseek-chat-v3-0324` | 128K | Great reasoning |
| `mistralai/mistral-nemo` | 128K | Good all-around |
| `meta-llama/llama-3.1-8b-instruct` | 128K | Solid local-class |

---

## 9. Free GLM (Budget — No Cost)

Zhipu AI's free tier models via their API.

### 9.1 API Details

- **API endpoint:** `https://open.bigmodel.cn/api/paas/v4`
- **Models:** `zai/glm-4.7-flash` (reasoning, 200K ctx), `zai/glm-4.6v-flash` (vision, 200K ctx)
- **API key:** free tier available, no cost
- **Note:** Use for simpler sub-agent tasks where MiniMax-tier isn't needed

### 9.2 Provider Config

```yaml
- name: free-glm
  type: openai-compatible
  api_key_env: ZHIPU_API_KEY
  base_url: https://open.bigmodel.cn/api/paas/v4
  default_model: zai/glm-4.7-flash
  max_tokens: 8192
  required_capabilities:
    - chat
    - completion
```

---

## 10. Unified Provider Config File

DuckBotOS stores all provider configuration in `/etc/duckbotos/providers.yaml`:

```yaml
# /etc/duckbotos/providers.yaml
# Unified provider config for DuckBotOS
# Read by both Hermes and OpenClaw

version: 1

# Cloud providers (keys entered in first-boot wizard)
providers:
  minimax:
    enabled: true
    api_key: "${MINIMAX_API_KEY}"
    default_model: minimax-portal/MiniMax-M2.7
    base_url: https://api.minimaxi.chat/v1

  openai:
    enabled: false
    api_key: "${OPENAI_API_KEY}"
    default_model: gpt-4o
    base_url: https://api.openai.com/v1

  anthropic:
    enabled: false
    api_key: "${ANTHROPIC_API_KEY}"
    default_model: claude-sonnet-4-20250514
    base_url: https://api.anthropic.com

  grok:
    enabled: false
    api_key: "${XAI_API_KEY}"
    default_model: xai/grok-4.3
    base_url: https://api.x.ai/v1

  openrouter:
    enabled: false
    api_key: "${OPENROUTER_API_KEY}"
    default_model: google/gemini-2.0-flash-exp
    base_url: https://openrouter.ai/api/v1

  free-glm:
    enabled: false
    api_key: "${ZHIPU_API_KEY}"
    default_model: zai/glm-4.7-flash
    base_url: https://open.bigmodel.cn/api/paas/v4

# Local provider (installed by default)
  lm-studio:
    enabled: true
    api_key: local
    base_url: http://127.0.0.1:1234/v1
    default_model: null  # set by user in first-boot wizard

# Provider priority (fallback order)
priority:
  - lm-studio        # local first (fast, free, private)
  - minimax          # then MiniMax (primary cloud)
  - openrouter       # then OpenRouter (variety)
  - grok             # then Grok (reasoning)
  - free-glm         # free GLM as last resort

# Model selection per task type
task_defaults:
  coding: minimax        # MiniMax for coding tasks
  reasoning: grok        # Grok for deep reasoning
  quick: lm-studio       # LM Studio for quick local tasks
  creative: openai       # OpenAI for creative tasks
  budget: free-glm       # Free GLM for cost-sensitive tasks
```

---

## 11. How Providers Are Used

### 11.1 Provider Selection Logic

1. **User task →** agent scores complexity (1–10)
2. **Complexity 1–3:** use LM Studio (local, fast, free)
3. **Complexity 4–6:** use MiniMax (cloud, good quality)
4. **Complexity 7–10:** use Grok or OpenAI (high quality for hard tasks)
5. **If LM Studio unavailable:** fall back to cloud providers in priority order

### 11.2 Multi-Provider Fallback

Both Hermes and OpenClaw support automatic fallback. If one provider fails (rate limit, error), the next in priority chain is tried:

```yaml
# In agent config:
fallback_chain:
  - lm-studio
  - minimax
  - openrouter
  - grok
```

---

## 12. API Key Management

### 12.1 First-Boot Entry

API keys are entered in the first-boot wizard (Step 3/5: Cloud Providers) and stored in:

- **Hermes mode:** `~/.hermes/config.yaml`
- **OpenClaw mode:** `/var/lib/openclaw/config.yaml`
- **Both modes also write:** `/etc/duckbotos/providers.yaml`

### 12.2 Environment Variable Injection

DuckBotOS generates a `~/.duckbotos/env` file that gets sourced on kiosk startup:

```bash
# ~/.duckbotos/env — sourced by kiosk services
export MINIMAX_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export OPENROUTER_API_KEY="sk-or-..."
```

This keeps keys out of config files (which might be in git) and into the OS-managed environment.

### 12.3 Permissions

```bash
# Config files with API keys
chmod 600 ~/.hermes/config.yaml
chmod 600 /var/lib/openclaw/config.yaml
chmod 600 /etc/duckbotos/providers.yaml
chmod 600 ~/.duckbotos/env

# env file not in git
echo "~/.duckbotos/env" >> ~/.gitignore
```

---

## 13. Future Providers

Planned additions:
- **Ollama** — local models via Ollama API (`http://localhost:11434`)
- **DeepSeek** — `https://api.deepseek.com/v1`
- **Groq** — ultra-fast inference API
- ** Cerebras** — fast inference on custom silicon

---

## 14. Related Documentation

| Doc | What It Covers |
|-----|---------------|
| `docs/lm-studio.md` | Full llmster headless install, systemd service, JIT loading, model management, debian packaging, API endpoint reference |
| `docs/architecture.md` §6 | LM Studio in the kiosk stack: provider config, model selection UI, OS-level integration |
| `docs/architecture.md` §12 | Unified provider config: full `providers.yaml` with priority chain and task defaults |
| `docs/installer.md` §4 | First-boot wizard: provider step (Step 3/5: Cloud Providers) and LM Studio step (Step 2/5) |
| `docs/phase7-implementation.md` | How agents actually route between providers using complexity scoring — the decision logic behind the priority chain |
| `docs/computer-use.md` | computer-use-linux MCP server — not a language model provider, but a desktop control provider the agent uses |

---

*Providers v0.2 — 2026-06-29. All providers confirmed from Hermes + OpenClaw source configs.*