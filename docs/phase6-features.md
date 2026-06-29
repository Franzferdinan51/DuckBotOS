# DuckBotOS — Phase 6 Feature Specifications

> Detailed specs for Tier 1 flagship features. These are design docs, not implementation guides.
> Status: Draft v0.1 — 2026-06-29

---

## F1: Natural Language Package Manager

**"I need a Python web server" → installs Flask + uv + creates project scaffold**

### Concept
Users express intent in natural language. The system resolves intent to packages across apt, snap, flatpak, pip, npm, cargo, and system configuration. Not a chat interface — a direct NL→action resolver that asks clarifying questions only when ambiguous.

### Architecture
```
User input: "I need a Python web server"
       │
       ▼
┌─────────────────┐
│ NL Package      │
│ Intent Parser   │  ← classify: package_install, service_create, config_set, file_create
│                 │
│ Resolver        │  ← match against known package taxonomies
│                 │
│ Executor        │  ← apt/snap/flatpak/pip/npm/cargo/systemd
│                 │
│ Verifier        │  ← confirm install succeeded, test basic function
└─────────────────┘
```

### Intent Taxonomy

| Intent | Example | Resolution |
|--------|---------|------------|
| `package_install` | "I need nginx" | apt install nginx, enable, start |
| `service_create` | "run a database" | apt install postgresql, enable, configure |
| `config_set` | "make it start on boot" | systemd enable {service} |
| `file_create` | "create a web project" | pip install flask, create app.py + requirements.txt |
| `developer_env` | "I want to code Python" | apt python3-dev, pip install uv black ruff mypy |
| `web_stack` | "full LAMP stack" | apt install apache2 mysql-server php, configure |
| `container` | "run this in docker" | docker build + docker run |
| `reverse_proxy` | "expose this to the internet" | apt install nginx, configure proxy_pass |

### Package Resolution Priority
1. apt (system packages) — highest priority, best integration
2. snap (sandboxed system apps)
3. flatpak (sandboxed desktop apps)
4. pip (Python packages)
5. npm (Node packages)
6. cargo (Rust packages)
7. compile from source (last resort)

### Design Decisions
- **No sudo escalation in kiosk mode** — assumes agent runs as privileged user OR uses PolicyKit
- **Dry-run first** — always show what would be installed before doing it
- **Rollback** — keep previous state so "undo that" works
- **Clarification only when genuinely ambiguous** — "did you mean nginx or apache2?"

### CLI Interface
```bash
# Direct NL
duckpkg "I need a Python web server"
duckpkg --dry-run "run postgres"
duckpkg --undo

# Interactive (asks questions)
duckpkg -i

# Confirm before action
duckpkg --confirm "make nginx start on boot"
```

### API for Agents
```python
# Hermes/OpenClaw tool call
{
  "tool": "nl_package_manager",
  "params": {
    "intent": "I need a Python web server with async support",
    "dry_run": false,
    "constraints": {"python_version": "3.11+", "async": true}
  }
}
```

### Dependencies
- hermesos-nlpm daemon (Python)
- apt, snap, flatpak, pip, npm, cargo (system)
- PolicyKit for privilege escalation

---

## F2: Predictive Resource Orchestrator

**Watches usage patterns, pre-starts services, pre-loads models**

### Concept
Not reactive resource management ("OOM happened, kill something") but predictive ("user usually opens the browser around 9am, model load takes 30s, start loading now"). Builds a usage profile over 7 days and acts on predictions.

### What It Predicts
- **Model usage** — which model will be needed at what time, pre-load it
- **Service need** — which services are typically started together, pre-warm them
- **Network** — VPN connects at 8am, disconnect at 6pm
- **Power** — switch to powersave at 10pm, performance at 8am
- **Disk** — clean /tmp when <2GB free predicted

### Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                    hermesos-watchdog                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Event       │  │ Predictor   │  │ Action Engine       │ │
│  │ Collector   │→ │ (7-day ML)  │→ │ (pre-start/stop)    │ │
│  │             │  │             │  │                     │ │
│  │ - Cron      │  │ - Time      │  │ - lms load model   │ │
│  │ - SystemD   │  │   patterns  │  │ - systemctl start  │ │
│  │ - LM Studio │  │ - Usage     │  │ - systemctl stop   │ │
│  │   API       │  │   sequences │  │ - Pre-warm caches  │ │
│  │ - Network   │  │ - Resource  │  │                     │ │
│  └─────────────┘  │   trends    │  └─────────────────────┘ │
│                   └─────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

### Data Collected (local only)
- Timestamps of service starts/stops
- CPU/memory/disk usage over time
- Network connection patterns
- LM Studio model load times
- User interaction events (from GNOME activity)

### Prediction Windows
| Prediction | Horizon | Confidence threshold |
|------------|---------|---------------------|
| Model pre-load | 5 min | 70% |
| Service pre-warm | 10 min | 75% |
| VPN connect | 30 min | 80% |
| Disk cleanup | when predicted | 90% |
| Sleep/hibernate | 15 min | 85% |

### LM Studio Integration
```python
# When predicted model is needed:
lms load llama-3.3-70b-instruct --gpu=max -y &
# Parallel load while user is still thinking
```

### SystemD Integration
```bash
# When predicted service cluster is needed:
systemctl start postgresql.service
systemctl start redis.service
systemctl start nginx.service
# All pre-warmed before user explicitly asks
```

### Web Dashboard
- `/opt/hermesos/dashboard/predictive.html` — visualize predicted vs actual
- Shows: usage heatmap, current predictions, confidence scores

---

## F3: Multi-Agent Pipeline

**DAG visualization of agent coordination, live status, streaming output**

### Concept
When a task requires multiple agents working together, DuckBotOS shows the live DAG: which agent is running, what's its output, how data flows between agents. Think GitHub Actions workflow visualization but for live agent pipelines.

### Pipeline Types
- **Sequential** — A → B → C (B waits for A, C waits for B)
- **Parallel** — A, B, C run simultaneously (fan-out)
- **Merge** — A, B, C results merge into D (fan-in)
- **Conditional** — A → [B if X, C if Y]
- **Loop** — A → B → A until condition met

### IPC Bus Integration
The agent bus (`/run/hermes-claw/agent-bus.sock`) carries pipeline events:
```json
// Pipeline start
{"type": "pipeline_start", "id": "pipe-abc123", "dag": {...}}
// Node state changes
{"type": "node_state", "pipe": "pipe-abc123", "node": "researcher", "state": "running"}
{"type": "node_output", "pipe": "pipe-abc123", "node": "researcher", "chunk": "..."}
// Pipeline end
{"type": "pipeline_end", "id": "pipe-abc123", "result": {...}}
```

### Web UI
- `/opt/hermesos/dashboard/pipeline.html` — live DAG view
- Nodes show: agent name, status (⏳ pending / 🔄 running / ✅ done / ❌ failed), output preview
- Edges show data flow direction and type (text/image/tool_call/file)
- Click node → expand full output log
- Click edge → see data passed between agents

### CLI
```bash
# Start a pipeline
duckpipe "research the latest AI news then summarize it"

# List running pipelines
duckpipe list

# Follow output of a pipeline
duckpipe follow pipe-abc123

# Stop a pipeline
duckpipe stop pipe-abc123
```

### OpenClaw Integration
OpenClaw's existing streaming + sub-agent spawning hooks into the pipeline DAG:
- Each spawned sub-agent = one DAG node
- Streaming chunks = edge data flowing through the DAG
- Final result = pipeline output

---

## F4: OS-Wide Activity Graph

**Interactive real-time observability: processes, agents, resources, network — all in one graph**

### Concept
A live knowledge graph of everything happening on the system: processes, network connections, agent thoughts, file operations, API calls. Inspired by Datadog/Netdata but with a knowledge graph twist — nodes are entities (processes, files, URLs, agents) and edges are relationships (reads, writes, spawns, calls).

### Graph Entities
| Entity | Properties |
|--------|------------|
| Process | PID, name, CPU%, MEM%, user, parent_pid |
| File | path, size, permissions, last_access |
| Network connection | local:port ↔ remote:port, state |
| Agent | name, model, current_task, tokens_used |
| API call | provider, endpoint, status, latency_ms |
| URL | domain, path, content_type, size |
| GPU process | PID, VRAM%, model_loaded |

### Graph Edges
| Relationship | Direction |
|-------------|-----------|
| `spawned_by` | agent → process |
| `reads` | process → file |
| `writes` | process → file |
| `connects_to` | process → network_connection |
| `calls` | agent → API_endpoint |
| `loads` | process → model |
| `child_of` | process → process |
| `uses_port` | process → network_connection |

### Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                hermesos-graph-daemon                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Collectors   │  │ Graph Store  │  │ Query API        │ │
│  │              │→ │              │→ │                  │ │
│  │ - procfs     │  │ (SQLite +    │  │ - REST API       │ │
│  │ - netlink    │  │  adjacency   │  │ - WebSocket      │ │
│  │ - eBPF       │  │  lists)      │  │   (live push)    │ │
│  │ - systemd    │  │              │  │                  │ │
│  │ - LM Studio  │  │              │  │                  │ │
│  │ - OpenClaw   │  └──────────────┘  └──────────────────┘ │
│  └──────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────────┐
              │   /opt/hermesos/dashboard/  │
              │   activity-graph.html        │
              │   (interactive D3.js viz)    │
              └──────────────────────────────┘
```

### Web UI Features
- **Force-directed graph** — nodes repel, edges attract
- **Filter by entity type** — show only agents + processes
- **Filter by time window** — last 5m, 1h, 24h, all
- **Search** — find entity by name/path/PID
- **Inspect** — click node → side panel with all properties
- **Timeline** — scrub through historical graph states
- **Live mode** — WebSocket push, new nodes animate in

### CLI
```bash
# Query the graph
duckgraph "show processes using more than 1GB RAM"
duckgraph "show all files written by hermes-agent in the last hour"
duckgraph "show network connections made by openclaw"

# Real-time stream
duckgraph stream --entity=agent --follow

# Export
duckgraph export --format=json --since=1h > activity.json
```

### Netdata Integration
For raw metric collection (CPU, RAM, disk, network), integrate with netdata:
```bash
# netdata exports metrics via:
# - REST API (localhost:19999)
# - WebSocket streaming
# hermesos-graph reads netdata API → converts to graph entities
```

---

## F5: Voice-Native Interaction

**Wake word → speech-to-text → agent → text-to-speech → voice response**

### Concept
You don't need to type. "Hey DuckBot, what's my disk usage?" → agent responds with voice. Wake word detection runs as a system service, always listening locally (no cloud). Whisper.cpp for STT (runs locally). Piper for TTS (runs locally, neural voices).

### Pipeline
```
Wake word detected ("Hey DuckBot")
         │
         ▼
   ┌─────────────┐
   │ openWakeWord │  ← local wake word, CPU-based, ~50MB RAM
   └─────────────┘
         │ (triggers recording)
         ▼
   ┌─────────────┐
   │ Whisper.cpp │  ← STT, local, model: tiny.en or base.en
   └─────────────┘
         │ (text)
         ▼
   ┌─────────────┐
   │  Hermes /   │  ← agent processes intent
   │  OpenClaw   │
   └─────────────┘
         │ (text response)
         ▼
   ┌─────────────┐
   │   Piper     │  ← TTS, local, neural voice
   │  (TTS)      │
   └─────────────┘
         │ (audio)
         ▼
   ┌─────────────┐
   │   speaker   │  ← pulseaudio / pipewire
   └─────────────┘
```

### Key Properties
- **Always-on wake word** — openWakeWord daemon runs at boot
- **No internet required** — all inference local (whisper.cpp + piper)
- **Wake word models** — `hey_duckbot` (trained) or `ok_nemo` (generic)
- **TTS voices** — multiple voices available, configurable in settings
- **Interruptible** — say "stop" or "cancel" to abort current response

### Configuration
```yaml
# /etc/hermesos/voice.yaml
wake_word:
  model: hey_duckbot          # or: ok_nemo, alexa, etc.
  sensitivity: 0.5            # 0.0 (very sensitive) to 1.0 (very strict)
  audio_gain: 2.0

stt:
  model: whisper-base-en       # tiny / base / small / medium
  language: en
  prompt: ""                  # context prompt for better accuracy

tts:
  voice: en_US-libritts-high  #piper voice name
  rate: 1.0                   # playback speed
  volume: 1.0

audio:
  input_device: default        # microphone
  output_device: default        # speakers
  sample_rate: 16000
```

### CLI
```bash
# Voice mode (continuous listening)
duckvoice

# Single command
duckvoice "what's my IP address"

# Configure wake word
duckvoice --train              # train custom wake word
duckvoice --test               # test microphone + wake detection
```

### SystemD Services
```bash
# Always-on wake word listener
hermesos-wakeword.service

# STT server (whisper.cpp HTTP API)
hermesos-stt.service

# TTS server (piper HTTP API)
hermesos-tts.service
```

### Privacy
- Audio never leaves the device
- Wake word detection is purely local signal processing
- STT model runs entirely on CPU/GPU locally
- TTS synthesis is entirely local
- User can disable wake word listening at any time (hardware mic mute)

---

## Implementation Priority

| Feature | Complexity | Dependencies | Priority |
|---------|------------|--------------|----------|
| F5 Voice | Medium | whisper.cpp, piper, openWakeWord | 1 — standalone service |
| F4 Activity Graph | High | eBPF/netlink, SQLite, D3.js | 2 — observability |
| F2 Resource Orchestrator | Medium | systemd, LM Studio API, Python | 3 — predictive |
| F1 NL Package Manager | High | apt/snap/flatpak/pip APIs | 4 — complex parsing |
| F3 Multi-Agent Pipeline | Medium | agent bus, WebSocket, DAG lib | 5 — visualization |

---

*Phase 6 Feature Specs v0.1 — 2026-06-29*
