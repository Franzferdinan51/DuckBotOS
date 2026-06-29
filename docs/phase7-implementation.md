# DuckBotOS — Phase 7 Implementation Specs
# Tier 1 Feature Implementation: F1–F5

> How to build the 5 flagship AI features: detailed architecture, CLI contracts, data flows, systemd integration, and implementation order.
> Status: Draft v0.1 — 2026-06-29

---

## Overview

Phase 7 implements the 5 Tier 1 flagship features from `docs/features.md`. Each feature is a first-class OS component with:
- A **systemd service** (or user-level daemon)
- A **Hermes/OpenClaw tool** exposed to the agent layer
- A **CLI / API** exposed to the user
- A **D-Bus bus name** for inter-feature coordination

### Implementation Order (recommended)

```
F2 → F4 → F1 → F3 → F5
```
- **F2 (Resource Orchestrator)** — lowest risk, no new ports, just reads /proc
- **F4 (Activity Graph)** — netdata-based, well-understood stack
- **F1 (NL Package Manager)** — Hermes tool, straightforward to implement on top of apt/snap/flatpak
- **F3 (Multi-Agent Pipeline)** — needs IPC bus (P4-1) to be ready first
- **F5 (Voice)** — audio stack dependency, complex; implement last

---

## F1: Natural Language Package Manager

### Goal
> *"I need a Python web server"* → daemon checks pip/apt/snap/flatpak, presents ranked choices, installs on confirmation.

### Architecture

```
User NL intent
      ↓
hermes-nlpkg daemon (Python)
      ↓
Intent Resolver (rule-based + LM Studio fallback)
      ↓
Multi-backend resolver:
  ├── apt cache search   (subprocess: apt-cache)
  ├── snap search        (subprocess: snap find)
  ├── flatpak search      (subprocess: flatpak search)
  ├── pip search         (HTTP: PyPI JSON API)
  └── brew search        (subprocess: brew search)
      ↓
Ranked results → Hermes tool response
      ↓
User confirms install
      ↓
 privileged/apt/snap/flatpak/pip install
```

### Hermes Tool Contract

```python
# Tool: nlpkg_resolve
# Description: "Resolve a natural language software request to installable packages"
# Arguments:
#   intent: str              # e.g. "a Python web server"
#   max_results: int = 5
# Returns:
#   results: List[dict]:
#     - name: str
#     - backend: "apt" | "snap" | "flatpak" | "pip" | "brew"
#     - description: str
#     - version: str
#     - relevance_score: float
#     - install_cmd: str
#     - already_installed: bool

# Tool: nlpkg_install
# Arguments:
#   backend: str
#   package: str
#   sudo: bool = False  # ask for privilege if needed
# Returns:
#   success: bool
#   output: str
```

### CLI Interface

```bash
# User-facing
duckpkg "a Python web server"
duckpkg install pip tornado  # direct
duckpkg search "web framework"

# Agent-facing (Hermes tool)
hermes-nlpkg resolve "REST API server for Node"
hermes-nlpkg install --backend pip "fastapi uvicorn"
```

### Intent Resolver Logic

**Step 1 — Keyword extraction:**
- "web server" → ["http", "server", "web", "httpd", "serve"]
- "Python" → ["python", "pip", "py"]
- "database" → ["sql", "db", "postgres", "mysql"]
- "API" → ["rest", "api", "json", "graphql"]

**Step 2 — Backend-specific search:**
- apt: `apt-cache search --names-only 'python.*web.*server'`
- snap: `snap find 'http server'`
- flatpak: `flatpak search 'web server'`
- pip: `curl -s https://pypi.org/search/?q=web+server | extract`

**Step 3 — LLM ranking (fallback when keywords ambiguous):**
- Send top 3 from each backend to LM Studio
- Prompt: "Rank these packages by how well they satisfy the user intent: {intent}\nPackages: {list}"
- Use `minimax-portal/MiniMax-M2.5` (cheaper than M2.7 for ranking)

**Step 4 — Filter already-installed:**
- apt: `dpkg -l | grep ^ii | awk '{print $2}'`
- snap: `snap list`
- flatpak: `flatpak list`
- pip: `pip list`

### Systemd Integration

```ini
# /etc/systemd/system/hermes-nlpkg.service
[Unit]
Description=HermesOS Natural Language Package Manager
PartOf=hermes.target

[Service]
Type=dbus
BusName=ai.hermesos.nlpkg
ExecStart=/usr/bin/python3 /usr/lib/hermesos/nlpkg daemon
Restart=on-failure
Environment=LM_STUDIO_URL=http://127.0.0.1:1234/v1

[Install]
WantedBy=hermes.target
```

### D-Bus Interface

```python
# Bus name: ai.hermesos.nlpkg
# Object path: /ai/hermesos/nlpkg

interface ai.hermesos.nlpkg {
    Resolve(instructor: s, max_results: u) -> (results: a{s});
    Install(backend: s, package: s, sudo: b) -> (success: b, output: s);
    Search(backend: s | "", query: s) -> (results: a{s});
}
```

### Dependencies
- `python3-dbus` (D-Bus Python bindings)
- `python3-apt` (APT Python bindings)
- `lmstudio` running locally (optional, fallback ranker)
- Subprocess access to: `apt-cache`, `snap`, `flatpak`, `pip`

---

## F2: Predictive Resource Orchestrator

### Goal
> Watch system resource patterns over time. Predict when RAM will be exhausted, CPU will spike, or disk will fill. Preemptively adjust LM Studio model loading or warn the agent before OOM.

### Architecture

```
hermesos-watchdog daemon (Python)
  ├── Reads /proc/{meminfo,loadavg,cpuinfo,diskstats}
  ├── Reads /sys/class/power_supply/* (battery)
  ├── Polls LM Studio API (/v1/models, /v1/loaded)
  ├── Maintains 24h rolling window of readings (SQLite)
  │
  ├── Anomaly Detector (simple threshold + Holt-Winters)
  │     ↓
  ├── Resource Forecaster (predicts 15min ahead)
  │     ↓
  └── Action Dispatcher (D-Bus + Hermes tool)
        ├── "OOM预警: free RAM < 2GB, unloading gemma..."
        ├── "Agent notified: CPU loadavg 4.2, deferring background tasks"
        └── "Disk warning: /home at 92%, triggering cleanup"
```

### Hermes Tool Contract

```python
# Tool: resource_status
# Description: "Get current system resource summary"
# Returns:
#   cpu: dict (loadavg_1m, loadavg_5m, loadavg_15m, cores)
#   memory: dict (total_gb, available_gb, used_gb, percent, swap_gb)
#   disk: dict (mount, total_gb, used_gb, available_gb, percent)
#   gpu: dict (name, memory_used_gb, memory_total_gb, util_percent) | null
#   lm_studio: dict (loaded_models: list, available_memory_gb: float)

# Tool: resource_forecast
# Arguments:
#   metric: "cpu" | "memory" | "disk"
#   horizon_minutes: int = 15
# Returns:
#   metric: str
#   current: float
#   predicted_15m: float
#   confidence: float
#   alert: bool
#   recommendation: str

# Tool: resource_adjust
# Arguments:
#   action: "unload_model" | "reduce_context" | "clear_cache" | "alert_agent"
#   target: str | null  # model name if action=unload_model
# Returns:
#   success: bool
#   before: dict
#   after: dict
```

### Data Collection

```python
# heremesos-watchdog collection loop (every 30s)
COLLECTION_INTERVAL = 30  # seconds

def collect_snapshot():
    return {
        "timestamp": time.time(),
        "loadavg": os.getloadavg(),          # (1m, 5m, 15m)
        "meminfo": parse_meminfo(),           # /proc/meminfo
        "disk": parse_df(),                   # df -h parsed
        "cpu_percent": psutil.cpu_percent(interval=1),
        "lm_studio": query_lm_studio(),       # GET http://127.0.0.1:1234/v1/models
    }
```

### Prediction Algorithm

**Simple exponential smoothing (Holt-Winters lightweight):**
- Maintain 48 data points (24h at 30min intervals) per metric
- `forecast = α * last_value + (1-α) * last_forecast` where α=0.3
- Alert threshold: `predicted > current * 1.5` OR `predicted > threshold_abs`

**OOM prediction:**
```python
def predict_oom():
    mem_history = get_history("memory_available_gb", hours=2)
    trend = linear_fit(mem_history)  # simple least squares
    minutes_to_zero = abs(mem_history[-1] / slope) if slope < 0 else float('inf')
    if minutes_to_zero < 30:
        trigger_oom_warning(minutes_to_zero)
```

### LM Studio Coordination

```python
def query_lm_studio():
    """Query LM Studio API for loaded models and memory."""
    try:
        resp = requests.get("http://127.0.0.1:1234/v1/models", timeout=2)
        loaded = resp.json().get("data", [])
        # Estimate memory: each 1B param model ~2GB in Q4
        total_mem = sum(model["params"] * 2 for model in loaded)
        return {
            "loaded_models": [m["id"] for m in loaded],
            "estimated_mem_gb": total_mem,
            "available": len(loaded) == 0
        }
    except requests.RequestException:
        return {"loaded_models": [], "available": True}
```

### Systemd Integration

```ini
# /etc/systemd/system/hermesos-watchdog.service
[Unit]
Description=HermesOS Predictive Resource Orchestrator
After=network.target lmstudio.service
Wants=lmstudio.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/lib/hermesos/watchdog daemon
Restart=always
RestartSec=10
WatchdogSec=60

# Resource limits — watchdog itself shouldn't cause OOM
MemoryMax=100M
MemoryHigh=80M

[Install]
WantedBy=hermes.target
```

### Alert Actions (via D-Bus)

```python
# /ai/hermesos/watchdog org.hermesos.watchdog.alert
D_BUS_ALERT = {
    "oom_warning": {
        "severity": "critical",
        "action": "unload_lm_studio_model",
        "message": "RAM predicted to exhaust in {minutes}min"
    },
    "cpu_spike": {
        "severity": "warning",
        "action": "defer_background_tasks",
        "message": "Load avg {load} exceeds threshold"
    },
    "disk_full": {
        "severity": "warning",
        "action": "trigger_cleanup",
        "message": "/home at {percent}% — cleanup recommended"
    }
}
```

---

## F3: Multi-Agent Pipeline (Both Mode)

### Goal
> When both Hermes and OpenClaw are running, coordinate them as a pipeline. Agent A thinks, Agent B reviews, result synthesizes. Live DAG visualization in the kiosk dashboard.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Pipeline Orchestrator              │
│                 /run/hermes-claw/pipeline.sock              │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
   ┌──────▼──────┐                  ┌───────▼──────┐
   │   Hermes    │                  │   OpenClaw   │
   │  (Primary)  │◄─────────────────►│  (Reviewer)  │
   └─────────────┘   IPC bus         └─────────────┘
          │                                 │
          └──────────────┬──────────────────┘
                         │
              ┌──────────▼──────────┐
              │   Synthesizer       │
              │  (shared context)    │
              └─────────────────────┘
```

### Pipeline Modes

**1. Hermes → OpenClaw (H→O)**
- Hermes drafts response/action
- OpenClaw reviews and critiques
- Hermes revises based on critique
- Final output synthesized

**2. OpenClaw → Hermes (O→H)**
- OpenClaw drafts primary plan
- Hermes provides domain knowledge
- OpenClaw finalizes

**3. Parallel (Both)**
- Both agents work simultaneously on same task
- Results merged by synthesizer
- Best-effort: take longer, more detailed response

### IPC Bus Protocol

```json
// All messages are JSON-RPC 2.0 over Unix socket
// Socket: /run/hermes-claw/pipeline.sock

// Pipeline initiation
{"jsonrpc": "2.0", "method": "pipeline.start", "params": {
  "mode": "hermes_to_openclaw" | "openclaw_to_hermes" | "parallel",
  "task": "Build a REST API for my task manager",
  "context": {"cwd": "/home/user/project", "language": "python"},
  "trace_id": "uuid-v4"
}, "id": 1}

// Progress update (Hermes → Dashboard)
{"jsonrpc": "2.0", "method": "pipeline.progress", "params": {
  "trace_id": "uuid-v4",
  "agent": "hermes",
  "step": "planning",
  "message": "Analyzing requirements..."
}}

// Review request (Hermes → OpenClaw)
{"jsonrpc": "2.0", "method": "review.request", "params": {
  "trace_id": "uuid-v4",
  "draft": "Here is my draft response...",
  "criteria": ["accuracy", "safety", "completeness"]
}}

// Review response (OpenClaw → Hermes)
{"jsonrpc": "2.0", "method": "review.response", "params": {
  "trace_id": "uuid-v4",
  "verdict": "needs_revision",
  "issues": [
    {"criterion": "safety", "severity": "high", "description": "SQL injection risk in query"},
    {"criterion": "completeness", "severity": "medium", "description": "Missing DELETE endpoint"}
  ],
  "suggestions": ["Use parameterized queries", "Add /tasks/{id} DELETE handler"]
}}

// Pipeline completion
{"jsonrpc": "2.0", "method": "pipeline.complete", "params": {
  "trace_id": "uuid-v4",
  "output": "Final synthesized response...",
  "hermes_revision": 2,
  "openclaw_reviews": 1,
  "total_time_ms": 4523
}}
```

### DAG Visualization

```javascript
// Dashboard frontend (React component in kiosk web UI)
// Reads from: /run/hermes-claw/pipeline-events.sock (append-only event log)

// DAG node types
const NodeType = {
  THINK: "hermes_think",
  REVIEW: "openclaw_review",
  REVISE: "hermes_revise",
  SYNTHESIZE: "synthesize",
  TOOL_CALL: "tool_call",
  RESULT: "result"
};

// DAG state
{
  nodes: [
    { id: "n1", type: "THINK", label: "Hermes: Plan approach", status: "done", duration_ms: 1200 },
    { id: "n2", type: "REVIEW", label: "OpenClaw: Review draft", status: "running" },
    { id: "n3", type: "REVISE", label: "Hermes: Revise based on review", status: "pending" },
    { id: "n4", type: "RESULT", label: "Final response", status: "pending" }
  ],
  edges: [
    { from: "n1", to: "n2", label: "draft" },
    { from: "n2", to: "n3", label: "issues" },
    { from: "n3", to: "n4", label: "revised" }
  ]
}
```

### Hermes Tool Contract

```python
# Tool: pipeline_start
# Arguments:
#   mode: str              # "hermes_to_openclaw" | "openclaw_to_hermes" | "parallel"
#   task: str              # Natural language task description
#   context: dict | null   # Optional context (cwd, language, etc.)
# Returns:
#   trace_id: str
#   pipeline_socket: str
#   dashboard_url: str     # "http://127.0.0.1:9119/pipeline/{trace_id}"

# Tool: pipeline_status
# Arguments:
#   trace_id: str
# Returns:
#   status: "running" | "complete" | "failed"
#   current_step: str
#   dag: dict              # Current DAG state

# Tool: pipeline_stream
# Arguments:
#   trace_id: str
# Yields: real-time SSE events from pipeline
```

### Systemd Integration

```ini
# /etc/systemd/system/hermesos-pipeline.service
[Unit]
Description=HermesOS Multi-Agent Pipeline Orchestrator
After=hermes.target openclaw-gateway.service
Requires=hermes.socket openclaw-gateway.socket

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/lib/hermesos/pipeline daemon
Restart=on-failure
RestartSec=5
RuntimeDirectory=hermes-claw
SocketMode=0660
# Allow both hermes and openclaw users to access
SupplementaryGroups=hermes openclaw

[Install]
WantedBy=multi-user.target
```

---

## F4: OS-Wide Activity Graph

### Goal
> Real-time interactive visualization of all OS and agent activity as a live graph. Shows processes, network connections, agent thoughts, tool calls, file operations — everything in one graph.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Activity Graph Daemon                      │
│              /usr/lib/hermesos/activity-graph.py              │
│                                                                  │
│  Sources:                                                         │
│  ├── /proc/* (process tree, network connections)                  │
│  ├── auditd (file access, exec events)                            │
│  ├── D-Bus (session bus messages)                                 │
│  ├── Hermes bus (/run/hermes/events)                              │
│  └── OpenClaw bus (MCP messages)                                  │
│           ↓                                                        │
│  Graph Engine (networkx + custom layout)                          │
│  └── In-memory directed graph (nodes = entities, edges = events)  │
│           ↓                                                        │
│  HTTP Server (:9120) → React Dashboard                            │
│  └── /api/graph — current graph state (JSON)                      │
│  └── /api/events — SSE stream of new edges                        │
└──────────────────────────────────────────────────────────────┘
```

### Graph Data Model

```python
# Node types
class NodeType(Enum):
    PROCESS = "process"           # /proc entries
    FILE = "file"                 # file operations
    NETWORK = "network"           # sockets, connections
    AGENT = "agent"               # Hermes / OpenClaw
    TOOL = "tool"                 # tool executions
    THOUGHT = "thought"           # agent reasoning
    INTENT = "intent"             # user intents
    PACKAGE = "package"           # installed packages
    DEVICE = "device"             # hardware

# Edge types
class EdgeType(Enum):
    SPAWNED = "spawned"           # process fork/exec
    READ = "read"                 # file read
    Wrote = "wrote"               # file write
    CONNECTED_TO = "connected_to" # network connection
    CALLED = "called"             # tool called by agent
    THINKING = "thinking"          # agent reasoning chain
    RESULT_OF = "result_of"       # tool result
    TRUSTS = "trusts"             # credential relationship

@dataclass
class GraphNode:
    id: str           # "proc:1234" or "file:/etc/passwd" or "agent:hermes"
    type: NodeType
    label: str       # human-readable: "python3 (pid 1234)"
    properties: dict  # metadata (user, timestamp, etc.)
    first_seen: float
    last_seen: float

@dataclass
class GraphEdge:
    source: str       # node id
    target: str       # node id
    type: EdgeType
    weight: float    # 0.0–1.0 (frequency / importance)
    timestamp: float
    properties: dict  # metadata
```

### Data Collection Sources

**1. Process tree (`/proc`):**
```python
def walk_process_tree():
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            with open(f"/proc/{pid}/stat") as f:
                stat = f.read().split()
            with open(f"/proc/{pid}/cmdline") as f:
                cmdline = f.read().replace("\x00", " ").strip()
            yield {
                "pid": int(pid),
                "name": stat[1],
                "cmdline": cmdline,
                "parent_pid": int(stat[3]),
                "state": stat[2]
            }
```

**2. Network connections (`/proc/net/*`):**
```python
def get_network_connections():
    # Parse /proc/net/tcp, /proc/net/tcp6, /proc/net/udp
    connections = []
    with open("/proc/net/tcp") as f:
        for line in f.readlines()[1:]:  # skip header
            parts = line.split()
            local_addr, local_port = parts[1].split(":")
            remote_addr, remote_port = parts[2].split(":")
            state = parts[3]
            connections.append({
                "protocol": "tcp",
                "local": f"{ipv4(local_addr)}:{int(local_port, 16)}",
                "remote": f"{ipv4(remote_addr)}:{int(remote_port, 16)}",
                "state": tcp_state(int(state))
            })
    return connections
```

**3. Hermes/OpenClaw events (via IPC bus):**
```python
# Subscribe to Hermes event bus
def on_hermes_event(event):
    add_edge(
        source=f"agent:hermes",
        target=f"tool:{event['tool']}",
        type=EdgeType.CALLED,
        weight=1.0,
        properties={"trace_id": event.get("trace_id")}
    )

# Subscribe to OpenClaw MCP messages
def on_openclaw_message(msg):
    add_edge(
        source=f"agent:openclaw",
        target=f"tool:{msg['tool']}",
        type=EdgeType.CALLED,
        weight=1.0
    )
```

### HTTP API (Port 9120)

```python
# GET /api/graph
# Returns current full graph state
{
  "nodes": [...],
  "edges": [...],
  "stats": {
    "total_nodes": 1234,
    "total_edges": 5678,
    "by_type": {"process": 200, "file": 800, "network": 50, "agent": 2}
  }
}

# GET /api/events
# SSE stream of new edges (last 1000 events)
event: new_edge
data: {"source": "proc:1234", "target": "file:/etc/shadow", "type": "read", "ts": 1751234567.890}

# GET /api/search?q=python&type=process
# Search nodes by label or type
{"results": [{"id": "proc:5678", "label": "python3 -m uvicorn", "score": 0.95}]}

# WebSocket /ws/graph
# Real-time graph updates pushed to dashboard
```

### Dashboard (React + D3.js)

```
URL: http://127.0.0.1:9120/
or:  http://127.0.0.1:9119/activity (embedded in kiosk)
```

**Features:**
- Force-directed graph layout (D3.js force simulation)
- Filter by node type (checkboxes)
- Zoom/pan with mouse
- Click node → side panel with details
- Timeline slider (replay last N minutes)
- Search bar (highlight matching nodes)
- Auto-layout with manual override
- Dark mode (matches kiosk theme)

### Systemd Integration

```ini
# /etc/systemd/system/hermesos-activity-graph.service
[Unit]
Description=HermesOS OS-Wide Activity Graph
After=network.target
Wants=auditd.service  # if available

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/lib/hermesos/activity-graph daemon
Restart=on-failure
RestartSec=10
RuntimeDirectory=hermesos
# Access to /proc and /proc/net
PrivateTmp=no
ProtectSystem=off

# Rate limit: max 100 events/sec to prevent DoS
ExecStartPost=/usr/sbin/auditd -f 2>/dev/null || true

[Install]
WantedBy=hermes.target
```

---

## F5: Voice-Native Interaction

### Goal
> *"Hey DuckBot, restart the nginx service"* — wake word detection, speech-to-text, natural language command execution, text-to-speech response. Full voice loop as an alternative to the kiosk UI.

### Architecture

```
Microphone (default device)
      ↓
openWakeWord (wake word detection)
      ↓  (wake word detected)
Whisper.cpp (speech-to-text)
      ↓  (transcribed text)
Hermes/OpenClaw (NL command understanding)
      ↓  (response text)
Piper TTS (text-to-speech)
      ↓  (audio)
Speaker (default device)
```

### Wake Word

**Engine:** openWakeWord (TensorFlow Lite models)
- Models: "hey_hermes", "okay_nvidia", "alexa" (community)
- Custom wake word training: record 100 samples, train with openWakeWord CLI
- Sensitivity configurable via config file

```python
# /etc/hermesos/voice/wakeword.toml
[wake_word]
model = "/usr/share/hermesos/wakeword/hey_hermes.tflite"
sensitivity = 0.5  # 0.0–1.0
trigger_phrases = ["hey hermes", "hermes", "duck bot", "hey duck"]
```

### Speech-to-Text

**Engine:** whisper.cpp (C++, fast, local)
- Model: `ggml-medium.bin` (~1.5GB) or `ggml-small.bin` (~488MB)
- Language: auto-detect or forced via config
- Realtime: continuous listening with VAD (voice activity detection)

```python
# Whisper inference (whisper.cpp Python bindings)
from whisper import Whisper

model = Whisper("/usr/share/hermesos/voice/ggml-small.bin")
audio = pyaudio_stream.read(CHUNK)  # 30ms chunks
frames = voice_activity_detector(audio)  # silero-vad
if is_speech(frames):
    result = model.transcribe(frames)
    text = result["text"].strip()
    if text:
        dispatch_to_hermes(text)
```

### Text-to-Speech

**Engine:** Piper (ONNX-based, fast, local)
- Default voice: `en_US-lessac-medium.onnx` (~46MB)
- Fast voice: `en_US-amy-medium.onnx` (~43MB)
- Latency target: <200ms from response text to audio

```python
# Piper TTS
from piper import Piper

tts = Piper(
    model="/usr/share/hermesos/voice/en_US-lessac-medium.onnx",
    config="/usr/share/hermesos/voice/en_US-lessac-medium.onnx.json"
)
audio = tts.synthesize(response_text)
play_audio(audio)
```

### Voice Command Handler (Hermes Tool)

```python
# Tool: voice_listen
# Description: "Listen for a voice command (uses wake word or forced)"
# Arguments:
#   wait: bool = True  # wait for wake word, or immediate listen
#   timeout_seconds: int = 10
# Returns:
#   text: str         # transcribed command
#   confidence: float # 0.0–1.0
#   language: str      # detected language

# Tool: voice_respond
# Description: "Speak text aloud using TTS"
# Arguments:
#   text: str
#   voice: str = "default"  # voice ID from available voices
#   speed: float = 1.0      # 0.5–2.0 playback speed
# Returns:
#   duration_seconds: float

# Tool: voice_status
# Returns:
#   listening: bool
#   wake_word_active: bool
#   last_command: str | null
#   available_voices: list[str]
```

### Command Routing

```python
COMMAND_INTENTS = {
    "service_restart": r"restart\s+(\w+[\w-]*)",
    "service_stop": r"stop\s+(\w+[\w-]*)",
    "service_start": r"start\s+(\w+[\w-]*)",
    "file_find": r"find\s+(?:file\s+)?(.+)",
    "package_install": r"install\s+(.+)",
    "system_info": r"(?:what|show).*(?:system|cpu|ram|disk|memory)",
    "agent_query": r"(?:ask|tell|have)\s+(hermes|openclaw)\s+(.+)",
}

def route_voice_command(text: str):
    for intent, pattern in COMMAND_INTENTS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return execute_intent(intent, match.groups())
    # Fallback: send full text to Hermes for NL understanding
    return hermes.handle(text)
```

### Audio Pipeline

```python
# Full voice loop (runs in hermesos-voice daemon)
async def voice_loop():
    vad_model = load_vad("silero-vad")  # voice activity detection
    whisper = load_whisper("ggml-small.bin")
    tts = load_piper("en_US-lessac-medium.onnx")
    ww = load_wakeword("/usr/share/hermesos/wakeword/hey_hermes.tflite")

    mic = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=16000, input=True)

    while True:
        audio_chunk = mic.read(480)  # 30ms at 16kHz

        # Wake word check (runs continuously)
        if ww.process(audio_chunk):
            logger.info("Wake word detected!")
            await play_beep("awake")  # confirmation tone
            continue  # start recording

        # VAD check
        if vad_model.is_speech(audio_chunk):
            frames.append(audio_chunk)
            if silence_detected(frames, threshold=1.0):  # 1s silence = done
                audio = b"".join(frames)
                text = whisper.transcribe(audio)
                if text:
                    response = await hermes.handle(text)
                    audio_out = tts.synthesize(response["text"])
                    play_audio(audio_out)
                frames = []
```

### Systemd Integration

```ini
# /etc/systemd/system/hermesos-voice.service
[Unit]
Description=HermesOS Voice-Native Interaction Daemon
PartOf=hermes.target
After=audio.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/lib/hermesos/voice daemon
Restart=on-failure
RestartSec=5
# Audio access
SupplementaryGroups=audio

# Resource: whisper and piper models stay in RAM
MemoryMin=500M
MemoryLow=400M

# Environment
Environment=LD_LIBRARY_PATH=/usr/lib/hermesos/voice
Environment=AUDIO_DEVICE=default

[Install]
WantedBy=hermes.target
```

### Wake Word Custom Training (Future)

```bash
# Train custom wake word with openWakeWord
openwakeword train \
  --audio_dir ~/wakeword-recordings/ \
  --keyword "hey_duck" \
  --output_dir /usr/share/hermesos/wakeword/ \
  --epochs 100
```

### Dependencies

| Component | Package | Size | Source |
|-----------|---------|------|--------|
| Wake word | openWakeWord TFLite model | ~2MB | openwakeword.io |
| STT | whisper.cpp + ggml-small.bin | ~488MB | whisper.cpp |
| VAD | silero-vad | ~1MB | snakers4/silero-vad |
| TTS | Piper + en_US-lessac-medium.onnx | ~46MB | rhasspy/piper |
| PyAudio | python3-pyaudio | system | apt |

---

## Cross-Feature Integration

### Shared D-Bus Bus Names

| Bus Name | Owner | Purpose |
|----------|-------|---------|
| `ai.hermesos.nlpkg` | F1 | NL Package manager |
| `ai.hermesos.watchdog` | F2 | Resource orchestrator |
| `ai.hermesos.pipeline` | F3 | Multi-agent pipeline |
| `ai.hermesos.activity` | F4 | Activity graph |
| `ai.hermesos.voice` | F5 | Voice interaction |

### Feature-to-Feature Calls

```
F5 (Voice) → F2 (Watchdog): "What's system memory?" → returns voice TTS response
F5 (Voice) → F1 (NL Pkg): "Install nginx" → confirmation beep → install
F1 (NL Pkg) → F2 (Watchdog): Check available disk before install
F3 (Pipeline) → F4 (Graph): Publish DAG nodes to activity graph
F2 (Watchdog) → F5 (Voice): OOM alert spoken aloud
F4 (Graph) ← All features: receive events, render in real-time
```

### Installation Order (Package Dependencies)

```
Stage 1 (Base packages):
  → hermesos-base (F2 dependency)
  → hermesos-watchdog (F2)
  → hermesos-nlpkg (F1, needs apt/snap/flatpak tools)

Stage 2 (UI):
  → hermesos-activity-graph (F4)
  → hermesos-web-dashboard (kiosk, hosts F4 UI)

Stage 3 (Coordination):
  → hermesos-pipeline (F3, needs hermes + openclaw both installed)

Stage 4 (Voice):
  → hermesos-voice (F5, needs audio.target)
```

---

## Implementation Checklist

### F1 — NL Package Manager
- [ ] Write `hermes-nlpkg` daemon (`/usr/lib/hermesos/nlpkg/`)
- [ ] Implement intent resolver (keyword + LM Studio fallback)
- [ ] Implement multi-backend search (apt, snap, flatpak, pip)
- [ ] Register Hermes tools: `nlpkg_resolve`, `nlpkg_install`
- [ ] Create D-Bus service file
- [ ] Write systemd unit
- [ ] Write shell CLI wrapper: `duckpkg`
- [ ] Test: "I need a Python web server" → returns ranked pip/apt options

### F2 — Predictive Resource Orchestrator
- [ ] Write `hermesos-watchdog` daemon
- [ ] Implement `/proc` reader (CPU, RAM, disk)
- [ ] Implement LM Studio API polling
- [ ] Implement Holt-Winters predictor
- [ ] Implement action dispatcher (unload model, alert)
- [ ] Register Hermes tools: `resource_status`, `resource_forecast`, `resource_adjust`
- [ ] Write systemd unit with `WatchdogSec=60`
- [ ] Test: predict memory exhaustion under load

### F3 — Multi-Agent Pipeline
- [ ] Implement pipeline orchestrator (JSON-RPC 2.0 over Unix socket)
- [ ] Implement Hermes → OpenClaw review flow
- [ ] Implement OpenClaw → Hermes review flow
- [ ] Implement parallel mode (both agents, merge results)
- [ ] Register Hermes tools: `pipeline_start`, `pipeline_status`, `pipeline_stream`
- [ ] Write systemd unit with `SupplementaryGroups=hermes openclaw`
- [ ] Write React DAG component for dashboard
- [ ] Test: "Build a REST API" → H→O→H pipeline with visualization

### F4 — OS-Wide Activity Graph
- [ ] Write `activity-graph` daemon
- [ ] Implement `/proc` process tree walker
- [ ] Implement `/proc/net` connection tracker
- [ ] Implement Hermes/OpenClaw event subscribers
- [ ] Implement in-memory NetworkX graph
- [ ] Implement HTTP API server (port 9120)
- [ ] Write React dashboard with D3.js force graph
- [ ] Write systemd unit
- [ ] Test: real-time graph of `python3 -c "import os; os.system('ls')"`

### F5 — Voice-Native Interaction
- [ ] Write `hermesos-voice` daemon
- [ ] Integrate openWakeWord (wake word detection)
- [ ] Integrate whisper.cpp (STT)
- [ ] Integrate Piper (TTS)
- [ ] Implement voice command router
- [ ] Register Hermes tools: `voice_listen`, `voice_respond`, `voice_status`
- [ ] Write systemd unit with `SupplementaryGroups=audio`
- [ ] Test: "Hey Hermes, what's my CPU usage?" → spoken response

---

*Next: Phase 8 — Tier 2 feature specs + cx-distro fork execution (pending Linux VM + Duckets decisions)*
