# Python SDK Guide

## Installation

```bash
pip install akasha-sdk
# Or from source:
cd sdks/python && pip install -e .
```

## Client Comparison

| Client | Transport | Best For | Async |
|--------|-----------|----------|-------|
| `AkashaClient` | gRPC | Agents (high throughput) | ❌ |
| `AsyncAkashaClient` | gRPC | Async agents (asyncio) | ✅ |
| `AkashaHttpClient` | HTTP/REST | Scripts, notebooks | ❌ |
| `AsyncAkashaHttpClient` | HTTP/REST | Async scripts | ✅ |

## Quick Start

```python
from akasha import AkashaHttpClient

# Connect (use verify=False for self-signed certs)
client = AkashaHttpClient("https://localhost:7777")

# Write a record
record = client.put("agents/planner/state", {
    "status": "active",
    "current_task": "analyze-report"
})
print(f"Created: {record.path} (v{record.version})")

# Read it back
state = client.get("agents/planner/state")
print(f"Status: {state.value['status']}")

# Query with glob patterns
all_agents = client.query("agents/*/state")
for agent in all_agents:
    print(f"  {agent.path}: {agent.value}")

# Delete
client.delete("agents/planner/state")
client.close()
```

## Authentication

### With API Key (recommended for agents)

```python
from akasha import AkashaHttpClient

client = AkashaHttpClient(
    "https://localhost:7777",
    headers={"Authorization": "Bearer ak_your-api-key-here"}
)
```

### With JWT (for scripts)

```python
import httpx

# Login first
resp = httpx.post("https://localhost:7777/api/v1/auth/login",
                  json={"username": "akasha", "password": "your-password"},
                  verify=False)
token = resp.json()["token"]

# Use token
from akasha import AkashaHttpClient
client = AkashaHttpClient(
    "https://localhost:7777",
    headers={"Authorization": f"Bearer {token}"}
)
```

## gRPC Client (High Performance)

```python
from akasha import AkashaClient

# Connect via gRPC
client = AkashaClient("localhost:50051")

# Write (same API as HTTP)
client.put("agents/worker/state", {"status": "working", "progress": 0.45})

# Read
record = client.get("agents/worker/state")
print(record.value)

# Query
results = client.query("agents/**")

# Subscribe to real-time events
for event in client.subscribe(pattern="agents/*"):
    print(f"Event: {event.kind} on {event.path}")
    if event.kind == EventKind.PUT:
        print(f"  New value: {event.record.value}")

client.close()
```

## Async Client (asyncio)

```python
import asyncio
from akasha import AsyncAkashaClient

async def main():
    async with AsyncAkashaClient("localhost:50051") as client:
        # All operations are async
        await client.put("agents/async-agent/state", {"status": "running"})
        record = await client.get("agents/async-agent/state")
        results = await client.query("agents/**")

        # Async event subscription
        async for event in client.subscribe("agents/*"):
            print(f"Event: {event}")

asyncio.run(main())
```

## Working with Memory Layers

```python
from akasha import AkashaHttpClient, MemoryLayer

client = AkashaHttpClient("https://localhost:7777")

# Write to Working Memory (short-lived scratchpad)
client.put("memory/working/planner/current-context", {
    "task": "analyze Q3 report",
    "sources": ["report.pdf", "financials.xlsx"],
    "started_at": "2024-01-15T10:00:00Z"
}, ttl_seconds=3600)  # Expires in 1 hour

# Write to Episodic Memory (what happened)
client.put("memory/episodic/planner/analysis-complete", {
    "task": "analyze Q3 report",
    "result": "revenue up 12%, margins stable",
    "decision": "recommend hold",
    "confidence": 0.85
}, tags={"topic": "Q3-analysis", "agent": "planner"})

# Write to Semantic Memory (what we know — permanent)
client.put("memory/semantic/finance/Q3-insights", {
    "insight": "Revenue growth driven by enterprise segment",
    "evidence_count": 3,
    "last_updated": "2024-01-15"
})

# Query all memories for a topic
q3_memories = client.query("memory/*/planner/*Q3*")
for m in q3_memories:
    print(f"  [{m.path}]: {m.value}")
```

## Working with Pheromones

```python
import httpx

base = "https://localhost:7777"
headers = {"Authorization": "Bearer ak_your-key"}

# Deposit a pheromone trail
httpx.post(f"{base}/api/v1/pheromones",
    json={
        "path": "signals/task-complete/Q3-analysis",
        "signal_type": "success",
        "intensity": 0.9,
        "emitter": "planner-agent",
        "metadata": {
            "task_id": "analyze-Q3",
            "duration_ms": 45000,
            "result_path": "memory/episodic/planner/analysis-complete"
        },
        "half_life_secs": 3600
    },
    headers=headers, verify=False
)

# Read active pheromone trails
resp = httpx.get(f"{base}/api/v1/pheromones", headers=headers, verify=False)
trails = resp.json()
for trail in trails:
    print(f"  {trail['path']}: intensity={trail['value'].get('intensity', 0)}")
```

## Building an Agent (Complete Example)

```python
"""
Planner Agent — demonstrates the full Akasha agent lifecycle:
1. Register in the store
2. Read tasks from working memory
3. Deposit pheromone trails for coordination
4. Write results to episodic memory
"""

import time
import json
from akasha import AkashaHttpClient

AGENT_ID = "planner"
BASE_PATH = f"agents/{AGENT_ID}"

def run_agent():
    client = AkashaHttpClient(
        "https://localhost:7777",
        headers={"Authorization": "Bearer ak_your-key"}
    )

    # 1. Register agent
    client.put(f"{BASE_PATH}/state", {
        "status": "active",
        "started_at": time.time(),
        "capabilities": ["planning", "analysis"],
        "version": "1.0.0"
    })
    print(f"✅ Agent {AGENT_ID} registered")

    # 2. Main loop
    try:
        while True:
            # Check for tasks in working memory
            tasks = client.query(f"memory/working/{AGENT_ID}/tasks/*")

            for task in tasks:
                task_id = task.path.split("/")[-1]
                print(f"📋 Processing task: {task_id}")

                # Update status
                client.put(f"{BASE_PATH}/state", {
                    "status": "working",
                    "current_task": task_id
                })

                # ... do the actual work here ...
                result = {"analysis": "complete", "confidence": 0.92}

                # Write result to episodic memory
                client.put(f"memory/episodic/{AGENT_ID}/{task_id}", {
                    "task": task.value,
                    "result": result,
                    "completed_at": time.time()
                })

                # Leave a pheromone trail for other agents
                import httpx
                httpx.post("https://localhost:7777/api/v1/pheromones",
                    json={
                        "path": f"signals/task-complete/{task_id}",
                        "signal_type": "success",
                        "intensity": 0.9,
                        "emitter": AGENT_ID,
                        "half_life_secs": 7200
                    },
                    headers={"Authorization": "Bearer ak_your-key"},
                    verify=False
                )

                # Clean up working memory
                client.delete(task.path)
                print(f"  ✅ Task {task_id} complete")

            # Update heartbeat
            client.put(f"{BASE_PATH}/state", {
                "status": "idle",
                "last_heartbeat": time.time()
            })

            time.sleep(5)  # Poll interval

    except KeyboardInterrupt:
        client.put(f"{BASE_PATH}/state", {"status": "stopped"})
        client.close()
        print(f"Agent {AGENT_ID} stopped")

if __name__ == "__main__":
    run_agent()
```

## Data Model

### Record

| Field | Type | Description |
|-------|------|-------------|
| `path` | `str` | Hierarchical path (e.g., `agents/planner/state`) |
| `value` | `Any` | JSON-serializable value |
| `version` | `int` | Auto-incrementing version number |
| `created_at` | `str` | ISO 8601 creation timestamp |
| `updated_at` | `str` | ISO 8601 last update timestamp |
| `tags` | `dict[str,str]` | Key-value metadata tags |
| `ttl_seconds` | `float` | Time-to-live (None = permanent) |
| `content_type` | `str` | Content type hint (e.g., `"json"`) |

### Path Conventions

| Pattern | Use |
|---------|-----|
| `agents/{id}/state` | Agent registration and heartbeat |
| `agents/{id}/config` | Agent configuration |
| `memory/working/{agent}/*` | Short-lived task context |
| `memory/episodic/{agent}/*` | What happened (decisions, outcomes) |
| `memory/semantic/{topic}/*` | What we know (facts, patterns) |
| `memory/procedural/{name}/*` | How to do things (workflows) |
| `pheromones/{signal}/*` | Stigmergic signals between agents |

### Glob Patterns

| Pattern | Matches |
|---------|---------|
| `agents/planner/state` | Exact path |
| `agents/*/state` | All agent states (1 level) |
| `agents/**` | All records under `agents/` (recursive) |
| `memory/working/planner/*` | All working memory for planner |
| `**` | All records in the store |
