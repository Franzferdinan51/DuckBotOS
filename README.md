# DuckBotOS

> A Ubuntu-derived OS where an AI agent **is** the desktop environment — not an app you open, but the environment you live in.

[![Repo](https://img.shields.io/badge/GitHub-Franzferdinan51%2FDuckBotOS-blue)](https://github.com/Franzferdinan51/DuckBotOS)

**Inspiration:** NVIDIA DGX Spark / RTX Spark. We do for Hermes (NousResearch) + OpenClaw what DGX OS does for the AI dev stack — but **agent-first, Linux-native**.

---

## The Vision

Your computer has an intelligent butler who lives in every room of the house, knows how everything works, and can operate anything in it.

You boot your computer. The agent wakes up. Your entire desktop is a single chat surface that can:

- 🛠️ Install software by talking about it ("I need a Python web server")
- 📊 Show you what your computer is doing on an interactive graph
- 🔒 Stop apps from leaking your data before it leaves
- 🗣️ Listen and respond — voice-first when your hands are busy
- 🤝 Coordinate with other agents when tasks get complex
- 💾 Remember what you did yesterday, last week, last year

Not a chat sidebar. Not a "smart assistant" widget. **The whole OS.**

---

## What It Is

DuckBotOS is a custom Ubuntu-based distro that boots directly into an AI agent (Hermes or OpenClaw) running as a system service. The desktop is a fullscreen web kiosk pointing at the agent's dashboard. Every system operation — package install, firewall rule, process spawn, file move — can be expressed as natural language and the agent handles it.

---

## Install Modes

Pick at install time:

| Mode | Boots Into |
|------|-----------|
| **Hermes-only** | Hermes Web Dashboard + `computer-use-linux` for desktop control |
| **OpenClaw-only** | openclaw-os plugin + same computer-use-linux bridge |
| **Both** | GDM session picker: Hermes / OpenClaw / Hybrid Workstation (GNOME + both) |

---

## Cool AI Features (Tier 1 Flagships)

| Feature | Description |
|---------|-------------|
| 🗣️ **Natural Language Package Manager** | "I need to run a Python web server" → finds, installs, configures, explains |
| ⚙️ **Predictive Resource Orchestrator** | Watches patterns, proactively adjusts CPU/RAM/disk, explains every move |
| 🔗 **Multi-Agent Pipeline** | Both mode: agents coordinate via IPC, spawn specialists, show live DAG |
| 📊 **OS-Wide Activity Graph** | Everything happening on your system as a live interactive graph |
| 🎙️ **Voice-Native Interaction** | "Hey Duck, switch to the browser and open YouTube" — wake-word OS control |

Full list: [docs/features.md](docs/features.md)

---

## What's Built So Far

- ✅ Three install modes (Hermes-only / OpenClaw-only / Both)
- ✅ LM Studio as first-class provider (installed by default, URL input, model load/select from OS UI)
- ✅ All Hermes + OpenClaw providers (MiniMax, Grok, OpenAI, Anthropic, OpenRouter, etc.)
- ✅ BrowserOS as default browser
- ✅ `computer-use-linux` integration for desktop control
- ✅ Dual-agent IPC bus (`/run/hermes-claw/agent-bus.sock`)
- ✅ 5 flagship AI features designed

---

## What's Coming

- [ ] CX Linux ISO build pipeline (Ubuntu 24.04 + preseed + APT repo + SBOM)
- [ ] Subiquity OEM installer with agent-selection page
- [ ] GDM theme for Both mode session picker
- [ ] First bootable ISO
- [ ] docs/architecture.md, docs/installer.md, docs/providers.md

---

## Stack

- **Base:** Ubuntu 24.04 LTS Noble Numbat
- **ISO builder:** Fork of `cxlinux-ai/cx-distro` (live-build + preseed + Debian packages)
- **Compositor:** Weston kiosk + Chromium BrowserOS fullscreen
- **Agents:** Hermes (NousResearch) + OpenClaw
- **Desktop control:** `agent-sh/computer-use-linux` Rust MCP server
- **Voice:** openWakeWord + Whisper.cpp (LM Studio bundled) + Piper TTS
- **Activity graph:** netdata + custom `hermesos-graph` daemon

---

## Reference Projects

We inherit from:
- [cxlinux-ai/cx-distro](https://github.com/cxlinux-ai/cx-distro) — ISO build pipeline
- [cxlinux-ai/cx-core](https://github.com/cxlinux-ai/cx-core) — natural-language OS admin pattern
- [thesysdev/openclaw-os](https://github.com/thesysdev/openclaw-os) — OpenClaw web workspace
- [nousresearch/hermes-agent](https://github.com/nousresearch/hermes-agent) — agent core + Web Dashboard
- [agent-sh/computer-use-linux](https://github.com/agent-sh/computer-use-linux) — desktop control MCP
- [browseros-ai/BrowserOS](https://github.com/browseros-ai/BrowserOS) — default browser

---

## License

Apache 2.0 + attribution to NousResearch (Hermes), OpenClaw team, cxlinux-ai, agent-sh.

---

*Built by [Franzferdinan51/DuckBotOS](https://github.com/Franzferdinan51/DuckBotOS). For when an OS should be an intelligent butler, not a chat sidebar.*
