# Akasha Python SDK

[![Version](https://img.shields.io/badge/version-1.0.0-purple.svg)](https://github.com/ocuil/akasha-public)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-ASL--1.0-blue.svg)](../../LICENSE)

Production-ready Python client for [Akasha](https://github.com/ocuil/akasha-public) — The Shared Cognitive Fabric for Intelligent Agent Systems.

## Features

- **gRPC Client** — High-performance, connection-pooled, with automatic retry and exponential backoff
- **Async Client** — Full asyncio support for LangGraph, FastAPI, and other async frameworks
- **HTTP Client** — Lightweight alternative using `httpx` for simple scripts
- **Stigmergy** — Deposit, sense, and reinforce pheromone trails
- **Cognitive Fabric** — Read/write across the 4-layer memory hierarchy
- **Type-safe** — Dataclass models with full type annotations
- **Thread-safe** — Safe for multi-threaded agent systems

## Installation

```bash
# From source (development)
pip install -e sdks/python

# Or install dependencies manually
pip install grpcio grpcio-tools protobuf msgpack httpx
```

## Quick Start

```python
from akasha import AkashaClient

# Connect to Akasha
with AkashaClient("localhost:50051") as client:
    # Write agent state
    client.put("agents/my-agent/state", {
        "status": "processing",
        "task": "data-pipeline",
        "progress": 0.42,
    })

    # Read another agent's state
    record = client.get("agents/other-agent/state")
    if record:
        print(f"Other agent status: {record.value['status']}")

    # Query all agents
    agents = client.query("agents/*/state")
    for agent in agents:
        print(f"{agent.path}: {agent.value}")
```

## Core API

### CRUD Operations

```python
from akasha import AkashaClient

client = AkashaClient("localhost:50051")

# Write with TTL and tags
record = client.put(
    "sensors/temperature/lab-01",
    {"celsius": 22.5, "humidity": 0.65},
    ttl_seconds=300,          # expires in 5 minutes
    tags={"type": "sensor", "location": "lab"},
    source="sensor-collector",
)

# Read
record = client.get("sensors/temperature/lab-01")
print(record.value)        # {"celsius": 22.5, "humidity": 0.65}
print(record.version)      # monotonic version counter
print(record.tags)         # {"type": "sensor", "location": "lab"}

# Delete
deleted = client.delete("sensors/temperature/lab-01")

# Query with glob patterns
all_sensors = client.query("sensors/*/lab-*")
all_agents = client.query("agents/**")        # recursive

# List paths
paths = client.list_paths("agents/")
```

### Agent Lifecycle

```python
# Register an agent
path = client.register_agent(
    "planner-01",
    agent_type="planner",
    metadata={"model": "gpt-4", "version": "2.1"},
)
# Returns: "agents/planner-01"

# Send periodic heartbeats
client.heartbeat("planner-01", status={"task": "active"})
```

### Stigmergy — Pheromone System

```python
from akasha import AkashaClient, SignalType

with AkashaClient("localhost:50051") as client:
    # Deposit a pheromone after completing work
    result = client.deposit_pheromone(
        trail="pipelines/data-enrichment",
        signal_type=SignalType.SUCCESS,
        emitter="agent-alpha",
        intensity=1.0,
        half_life_secs=3600,
        payload={"duration_ms": 320, "quality_score": 0.95},
    )
    print(f"Intensity: {result['current_intensity']}")
    print(f"Reinforced: {result['reinforced']}")

    # Sense active pheromones
    trails = client.sense_pheromones("pipelines/*")
    for trail in trails:
        print(f"  {trail['trail']}: intensity={trail['current_intensity']:.2f}")

    # Reinforce a trail (intensities sum)
    client.reinforce_pheromone(
        "pipelines/data-enrichment",
        additional_intensity=0.5,
        emitter="agent-beta",
    )

    # Warning pheromone (others learn to avoid)
    client.deposit_pheromone(
        trail="pipelines/legacy-etl",
        signal_type=SignalType.WARNING,
        emitter="agent-gamma",
        payload={"error": "timeout", "retry_count": 3},
    )
```

### Cognitive Fabric — Memory Layers

```python
from akasha import AkashaClient, MemoryLayer

with AkashaClient("localhost:50051") as client:
    # Working Memory — scratchpad (auto-expires)
    client.write_memory(
        MemoryLayer.WORKING,
        namespace="planner-01",
        key="current-context",
        value={"task": "analyze-report", "step": 3},
    )

    # Episodic Memory — what happened
    client.write_memory(
        MemoryLayer.EPISODIC,
        namespace="data-pipeline",
        key="run-2024-01-15",
        value={
            "outcome": "success",
            "duration_ms": 4520,
            "records_processed": 15000,
        },
    )

    # Semantic Memory — distilled knowledge
    client.write_memory(
        MemoryLayer.SEMANTIC,
        namespace="enrichment-patterns",
        key="batch-vs-stream",
        value={
            "insight": "Batch enrichment is 3x faster for datasets > 10K records",
            "confidence": 0.87,
        },
    )

    # Procedural Memory — proven workflows
    client.write_memory(
        MemoryLayer.PROCEDURAL,
        namespace="data-pipeline",
        key="standard-etl",
        value={
            "steps": ["extract", "validate", "transform", "load", "verify"],
            "timeout_per_step_ms": 5000,
        },
    )

    # Query all semantic knowledge
    knowledge = client.query_memory(MemoryLayer.SEMANTIC)
    for record in knowledge:
        print(f"  {record.path}: {record.value}")

    # Read specific memory
    ctx = client.read_memory(MemoryLayer.WORKING, "planner-01", "current-context")
```

### Real-Time Subscriptions

```python
# Blocking iterator — use in a dedicated thread
for event in client.subscribe("agents/**"):
    print(f"[{event.kind}] {event.path}")
    if event.record:
        print(f"  Value: {event.record.value}")
```

### Async Client (asyncio)

```python
import asyncio
from akasha import AsyncAkashaClient

async def main():
    async with AsyncAkashaClient("localhost:50051") as client:
        await client.put("agents/async-agent/state", {"status": "running"})

        record = await client.get("agents/async-agent/state")
        print(record.value)

        records = await client.query("agents/*/state")
        for r in records:
            print(f"{r.path}: {r.value}")

asyncio.run(main())
```

### HTTP Client

```python
from akasha import AkashaHttpClient

# For scripts that don't need gRPC
client = AkashaHttpClient("https://localhost:7777", verify_ssl=False)

# Login (if auth is enabled)
client.login("akasha", "akasha")

# Same API surface
client.put("agents/script/state", {"status": "running"})
record = client.get("agents/script/state")
records = client.query("agents/*/state")
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `address` | `localhost:50051` | gRPC server address |
| `timeout` | `10.0` | Default timeout in seconds |
| `max_retries` | `3` | Max retries for transient failures |
| `retry_backoff` | `0.5` | Initial backoff (doubles per retry) |
| `max_message_size` | `64MB` | Max gRPC message size |

## Signal Types

| Type | Use Case |
|------|----------|
| `SignalType.SUCCESS` | Task completed successfully |
| `SignalType.WARNING` | Issue detected, others should avoid |
| `SignalType.RESOURCE` | Resource availability signal |
| `SignalType.DISCOVERY` | New information found |
| `SignalType.CLAIM` | "I'm working on this" lock signal |

## License

[Akasha Source License 1.0 (ASL-1.0)](../../LICENSE)
