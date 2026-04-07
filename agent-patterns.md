# Agent Patterns — How to Build AI Agents with Akasha

This guide covers the core patterns for building multi-agent systems with Akasha. Each pattern is independent — use what you need.

## Pattern 1: Agent Registration & Heartbeat

Every agent should register itself and maintain a heartbeat:

```python
from akasha import AkashaHttpClient
import time

AGENT_ID = "planner"
client = AkashaHttpClient("https://localhost:7777",
    headers={"Authorization": "Bearer ak_your-key"})

# Register
client.put(f"agents/{AGENT_ID}/state", {
    "status": "active",
    "capabilities": ["planning", "analysis"],
    "version": "1.0.0",
    "started_at": time.time()
})

# Heartbeat loop (in a background thread or event loop)
while running:
    client.put(f"agents/{AGENT_ID}/state", {
        "status": current_status,
        "last_heartbeat": time.time()
    })
    time.sleep(10)
```

Other agents or the dashboard can discover all agents:
```python
agents = client.query("agents/*/state")
for a in agents:
    print(f"Agent {a.path}: status={a.value['status']}")
```

## Pattern 2: Task Queue via Working Memory

Use working memory as a lightweight task queue:

```python
# Producer: Submit a task
client.put("memory/working/executor/tasks/analyze-Q3", {
    "type": "analysis",
    "input": {"report": "s3://reports/Q3.pdf"},
    "priority": "high",
    "submitted_by": "planner",
    "submitted_at": time.time()
}, ttl_seconds=3600)  # Task expires if not picked up in 1h

# Consumer: Poll for tasks
tasks = client.query("memory/working/executor/tasks/*")
for task in tasks:
    task_id = task.path.split("/")[-1]

    # Claim it (optimistic — check version)
    client.put(task.path, {**task.value, "claimed_by": AGENT_ID})

    # Process...
    result = process(task.value)

    # Write result to episodic memory
    client.put(f"memory/episodic/{AGENT_ID}/{task_id}", {
        "task": task.value,
        "result": result,
        "duration_ms": elapsed
    })

    # Clean up working memory
    client.delete(task.path)
```

## Pattern 3: Stigmergy (Pheromone Coordination)

Agents coordinate indirectly through pheromone signals, like ant colonies:

```python
import httpx

base = "https://localhost:7777"
auth = {"Authorization": "Bearer ak_your-key"}

# === Agent A: "I found something useful" ===
httpx.post(f"{base}/api/v1/pheromones", json={
    "path": "signals/data-available/customer-segmentation",
    "signal_type": "success",
    "intensity": 0.95,      # Strength of the signal
    "emitter": "data-miner",
    "metadata": {
        "data_path": "memory/semantic/customers/segments-v3",
        "record_count": 15000,
        "quality_score": 0.92
    },
    "half_life_secs": 7200   # Signal decays over 2 hours
}, headers=auth, verify=False)

# === Agent B: "I sense a strong signal, let me use it" ===
trails = httpx.get(f"{base}/api/v1/pheromones",
                   headers=auth, verify=False).json()

for trail in trails:
    if trail["value"]["signal_type"] == "success" and \
       trail["value"]["intensity"] > 0.5:
        # Follow the trail — read the data it points to
        data_path = trail["value"]["metadata"]["data_path"]
        data = client.get(data_path)
        print(f"Found data via pheromone: {data.value}")

        # Reinforce the trail (others will see it's valuable)
        httpx.post(f"{base}/api/v1/pheromones", json={
            "path": trail["path"],
            "signal_type": "success",
            "intensity": 0.85,  # Slightly lower — decay is natural
            "emitter": "analyst",
            "half_life_secs": 3600
        }, headers=auth, verify=False)
```

### Pheromone Signal Types

| Signal | Use When | Example |
|--------|----------|---------|
| `success` | Task completed successfully | "Analysis done, results at path X" |
| `warning` | Anomaly or concern detected | "Data quality below threshold" |
| `progress` | Long-running task update | "Processing 45% complete" |
| `request` | Requesting help from swarm | "Need analysis expertise" |

### Key Insight: Emergent Coordination

Pheromones decay naturally over time (via `half_life_secs`). This means:
- **Recent signals** are strong → agents prioritize fresh information
- **Reinforced signals** persist → important data stays discoverable
- **Ignored signals** evaporate → noise self-cleans
- **No central coordinator needed** → coordination emerges from individual behavior

## Pattern 4: Cognitive Memory Hierarchy

Structure agent knowledge using the 4-layer memory system:

```
memory/
├── working/           # Minutes — current task context
│   └── planner/
│       ├── current-task    → "analyzing Q3 report"
│       └── scratch-data    → {intermediate calculations}
│
├── episodic/          # Hours/Days — what happened
│   └── planner/
│       ├── task-001-result → {input, output, duration}
│       └── task-002-result → {input, output, duration}
│
├── semantic/          # Permanent — what we know
│   └── finance/
│       ├── Q3-insights     → "Revenue driven by enterprise"
│       └── market-trends   → {patterns, correlations}
│
└── procedural/        # Permanent — how to do things
    └── analysis/
        ├── report-template → {steps, prompts, validation}
        └── best-practices  → {guidelines, anti-patterns}
```

### Memory Promotion (Nidra)

Akasha automatically promotes memories through the hierarchy:

1. **Working → Episodic**: When `nidra` runs, working memories with enough
   "rehearsals" (reads/writes) get promoted to episodic
2. **Episodic → Semantic**: With LLM consolidation enabled, episodic memories
   are distilled into semantic insights

You can also promote manually:
```python
# Manually promote a working insight to semantic
client.put("memory/semantic/finance/Q3-pattern", {
    "insight": "Enterprise segment drives 80% of growth",
    "evidence": ["episodic/planner/task-001", "episodic/planner/task-005"],
    "confidence": 0.92,
    "promoted_at": time.time()
})
```

## Pattern 5: Multi-Agent Swarm

A complete swarm with 3 agents coordinating through Akasha:

```python
# === Agent 1: Planner ===
# Reads tasks from external source, breaks into subtasks
client.put("memory/working/executor/tasks/subtask-1", {...})
client.put("memory/working/executor/tasks/subtask-2", {...})
# Deposits pheromone: "tasks available"
deposit_pheromone("signals/tasks-ready/batch-42", intensity=0.9)

# === Agent 2: Executor ===
# Senses "tasks-ready" pheromone
# Picks up subtasks from working memory
# Executes and writes results to episodic memory
# Deposits pheromone: "results-ready"

# === Agent 3: Reviewer ===
# Senses "results-ready" pheromone
# Reads results from episodic memory
# Validates quality, writes final output to semantic memory
# If quality is low, deposits "warning" pheromone
```

### Coordination Flow
```
Planner → [working memory] → Executor → [episodic memory] → Reviewer → [semantic memory]
    ↓                              ↓                              ↓
  pheromone:               pheromone:                   pheromone:
  "tasks-ready"            "results-ready"              "review-done"
```

## Pattern 6: Event-Driven Architecture

Use gRPC subscriptions for real-time reactions:

```python
from akasha import AkashaClient, EventKind

client = AkashaClient("localhost:50051")

# Subscribe to all changes under agents/
for event in client.subscribe("agents/**"):
    if event.kind == EventKind.PUT:
        agent_id = event.path.split("/")[1]
        status = event.record.value.get("status")
        print(f"Agent {agent_id} is now: {status}")

        if status == "error":
            # Auto-heal: restart the agent
            client.put(f"memory/working/supervisor/restart/{agent_id}", {
                "reason": "error detected",
                "triggered_at": time.time()
            })
```

## Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|--------------|
| Store large files in records | Store file paths/URLs, keep data in object storage |
| Poll every 100ms | Use gRPC `subscribe()` for real-time events |
| Use deeply nested paths (>5 levels) | Keep paths flat: `agents/{id}/state` |
| Store secrets in records | Use environment variables or a secrets manager |
| Create one agent per task | Reuse agents with a task queue pattern |
| Ignore pheromone decay | Choose meaningful `half_life_secs` for your use case |
