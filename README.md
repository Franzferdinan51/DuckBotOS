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
- 💾 Remember what you did yesterday, last week, last year — **across every reboot**

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

## 🧠 Memory & Brain — Ships by Default (NEW!)

DuckBotOS comes with the [DuckBot RAG Memory System](https://github.com/Franzferdinan51/duckbot-rag-memory) **pre-installed in every mode** (Hermes, OpenClaw, Both). The agent never forgets.

**What you get:**

| Capability | Description |
|------------|-------------|
| 📦 **4-tier CoALA memory** | working → episodic → semantic → procedural (the canonical memory taxonomy from the CoALA paper) |
| 🔍 **67 MCP tools** | `brain_wake_up`, `brain_recall`, `brain_remember`, `brain_palace`, `brain_skills_*`, `brain_nudge`, `brain_forget_by_query`, `brain_decay_*`, `brain_graph_*`, ... |
| 🔁 **FSRS-6 spaced repetition** | Self-tuning forgetting curve — daily review queue (`brain_fsrs_review`) keeps important memories alive |
| 🏛️ **Wing/Room/Drawer 2D palace** | MemPalace-inspired `brain_palace` MCP tool — navigate by project (wing) × time (room) × memory (drawer) |
| 📑 **AAAK corpus index** | Scan the whole brain in <500 tokens via `brain_index` |
| 🤝 **Multi-agent skill pipeline** | Agents stamp `skill_candidate` chunks → promote to agentskills.io `SKILL.md` for repeated use |
| 🧬 **Honcho-style user model** | `brain_user_model` aggregates Duckets facts into a single memory block, updated daily |
| ⏰ **autoWakeUp + autoSync hooks** | `brain_wake_up` fires on every `session_start`, `brain_sync` on every `session_end` |
| 💾 **Local-first embeddings** | LM Studio at `127.0.0.1:1234` (GPU-accelerated, zero API cost) — OpenAI-compatible fallback |
| 📂 **OpenClaw native plugin** | Auto-registered in `openclaw.json` — `duckbot-memory` plugin shim proxying 67 tools + session hooks |
| 🔄 **Watcher daemon** | Polls the workspace every 5 min, content-hash dedup, auto-ingests new edits |

**Installed at:** `/opt/duckbotos/brain/` (cloned from `Franzferdinan51/duckbot-rag-memory`)
**Config:** `/etc/duckbotos/brain.env` (LM Studio pre-wired, OpenAI-compatible fallback)
**MCP wrapper:** `/usr/bin/duckbotos-brain-mcp`
**OpenClaw plugin:** `~/.openclaw/extensions/duckbot-memory/` (auto-registered in `openclaw.json`)
**Package:** `duckbotos-brain` — installed in **all three install modes**

The brain is wired into **every install mode** — Hermes, OpenClaw, and Both. It survives reboots, accumulates facts across sessions, and actively prevents the agent from forgetting important decisions (D1-D5 brain rules, the cloud-only directive, Duckets' preferences, project context).

> **"Identity, not a feature."** — the brain is part of what makes DuckBotOS *DuckBotOS*. Without it, the agent is a chat sidebar. With it, the agent has continuity.

Docs: [docs/lm-studio.md](docs/lm-studio.md) | Source: [duckbot-rag-memory](https://github.com/Franzferdinan51/duckbot-rag-memory)

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

## Status (2026-06-29)

**DuckBotOS is ready to build.** All parallel-safe work is complete. The first ISO build is the next milestone — runs in CI automatically on the next push to `duckbotos` branch, or `./src/build.sh` in a Linux VM.

| Area | Status |
|------|--------|
| 📚 Docs (22 total) | ✅ Complete |
| 📦 Packages (13/13 with debian/control + debian/rules + debian/changelog) | ✅ Complete |
| 🧠 **DuckBot brain** (duckbot-rag-memory, 67 MCP tools, FSRS, skill pipeline) | ✅ **Ships by default in all modes** — wired via OpenClaw plugin |
| 🔧 All service files (hermes, openclaw, lm-studio, desktop-control, cua-driver, brain, kiosk, session-picker) | ✅ Written |
| 🖱️ Newest Desktop Control (Lobster Edition) + trycua/cua bridge | ✅ **Newest Desktop Control rewrites computer-use package** — replaces agent-sh with Duckets' local tool |
| 🎨 Session picker UI for Both mode (8080) | ✅ Complete |
| 🏗️ ISO build pipeline (cx-distro fork, Ubuntu 24.04 Noble) | ✅ Ready — `./src/build.sh` |
| 🤖 GitHub Actions CI auto-builds ISO | ✅ Configured |
| 📋 HANDOFF.md for other agents | ✅ Complete |
| 💿 First bootable ISO | ⏳ Awaiting CI run / Linux VM |

The ISO build is the only remaining milestone. See [HANDOFF.md](HANDOFF.md) for the build guide and known issues.

---

## Stack

- **Base:** Ubuntu 24.04 LTS Noble Numbat
- **ISO builder:** Fork of `cxlinux-ai/cx-distro` (live-build + preseed + Debian packages)
- **Compositor:** Weston kiosk + Chromium BrowserOS fullscreen
- **Agents:** Hermes (NousResearch) + OpenClaw
- **Memory & brain:** `duckbot-rag-memory` (4-tier CoALA, 67 MCP tools, FSRS, OpenClaw plugin shim)
- **Local LLM:** LM Studio headless (llmster daemon) at `localhost:1234`
- **Desktop control:** Duckets' Newest Desktop Control (Lobster Edition, MIT, 38 tests, 20+ tools) — wires into Hermes AND OpenClaw automatically. Optional trycua/cua bridge (`duckbotos-cua-bridge`) for VM orchestration and an alternative computer-use backend.
- **Voice:** openWakeWord + Whisper.cpp (LM Studio bundled) + Piper TTS
- **Activity graph:** netdata + custom `hermesos-graph` daemon

---

## Reference Projects

We inherit from:
- [cxlinux-ai/cx-distro](https://github.com/cxlinux-ai/cx-distro) — ISO build pipeline
- [cxlinux-ai/cx-core](https://github.com/cxlinux-ai/cx-core) — natural-language OS admin pattern
- [thesysdev/openclaw-os](https://github.com/thesysdev/openclaw-os) — OpenClaw web workspace
- [nousresearch/hermes-agent](https://github.com/nousresearch/hermes-agent) — agent core + Web Dashboard
- [Franzferdinan51/duckbot-rag-memory](https://github.com/Franzferdinan51/duckbot-rag-memory) — **the brain (ships by default in all DuckBotOS modes)**
- [Franzferdinan51/desktop-control-lobster-edition-skill](https://github.com/Franzferdinan51/desktop-control-lobster-edition-skill) — **the desktop control MCP (Duckets' local tool, MIT, 38 tests)**
- [trycua/cua](https://github.com/trycua/cua) — VM orchestration + optional Linux computer-use backend
- [browseros-ai/BrowserOS](https://github.com/browseros-ai/BrowserOS) — default browser

---

## License

Apache 2.0 + attribution to NousResearch (Hermes), OpenClaw team, cxlinux-ai, agent-sh, Franzferdinan51 (duckbot-rag-memory).

---

*Built by [Franzferdinan51/DuckBotOS](https://github.com/Franzferdinan51/DuckBotOS). For when an OS should be an intelligent butler that remembers, not a chat sidebar that forgets. Built on Duckets' own tools — desktop control, computer-use, and the brain all ship as first-class MIT-licensed components.*