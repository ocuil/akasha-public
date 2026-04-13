<div align="center">

```
░█████╗░██╗░░██╗░█████╗░░██████╗██╗░░██╗░█████╗
██╔══██╗██║░██╔╝██╔══██╗██╔════╝██║░░██║██╔══██╗
███████║█████╔╝░███████║╚█████╗░███████║███████║
██╔══██║██╔═██╗░██╔══██║░╚═══██╗██╔══██║██╔══██║
██║░░██║██║░╚██╗██║░░██║██████╔╝██║░░██║██║░░██║
╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚═╝░░╚═╝╚═╝░░╚═╝
```

**The Shared Cognitive Fabric for Intelligent Agent Systems**

[![License: ASL-1.0](https://img.shields.io/badge/License-ASL--1.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.1.2-purple.svg)](CHANGELOG.md)
[![Docker](https://img.shields.io/docker/v/alejandrosl/akasha?label=Docker%20Hub&color=2496ED)](https://hub.docker.com/r/alejandrosl/akasha)
[![PyPI](https://img.shields.io/pypi/v/akasha-client?color=blue&label=PyPI)](https://pypi.org/project/akasha-client/)
[![npm](https://img.shields.io/npm/v/akasha-memory?color=CB3837&label=npm)](https://www.npmjs.com/package/akasha-memory)
[![Cluster](https://img.shields.io/badge/Cluster-3_node_HA-brightgreen.svg)](#enterprise-clustering)
[![Tests](https://img.shields.io/badge/QA-41%2F41_passing-success.svg)](#project-status)
[![Auth](https://img.shields.io/badge/Auth-JWT_%2B_API_Keys-orange.svg)](#authentication)
[![MCP](https://img.shields.io/badge/MCP-Server_v1.2-blueviolet.svg)](#mcp-protocol)
[![Encryption](https://img.shields.io/badge/Encryption-AES--256--GCM_BYOK-critical.svg)](#-security)
[![Rust](https://img.shields.io/badge/Engine-Rust-orange.svg)](https://www.rust-lang.org/)
[![gRPC](https://img.shields.io/badge/Protocol-gRPC-green.svg)](https://grpc.io/)

</div>

---

## The Soul of Akasha

> *"In Vedic philosophy, **Akasha** (आकाश) is the fifth element — the ethereal substrate that pervades all of existence. It is not merely space; it is the **medium through which all things connect**. The Akashic Records are said to contain every thought, word, and deed of every being that has ever lived — an infinite, omnipresent memory woven into the fabric of reality."*

Akasha brings this ancient principle to the world of software.

It is **not** a database. It is **not** a message queue. Akasha is a **living cognitive substrate** — a shared memory space where autonomous agents read, write, and sense the world around them without ever needing to ask each other directly.

When Agent A writes its state to Akasha, Agent B doesn't need to poll, request, or negotiate. It simply *knows* — because the knowledge is already inscribed in the shared fabric, instantly accessible to all.

This is **stigmergy**: the same mechanism that allows millions of termites to build cathedral-like structures without a blueprint. Each agent leaves traces in the environment, and the environment itself becomes the communication medium.

---

## The Three Pillars

### 🐜 Stigmergy — Coordination Without Communication

Inspired by how ant colonies solve complex optimization problems through pheromone trails:

- Agents leave **pheromone traces** in the shared memory (`_pheromones/tasks/optimization`)
- Pheromones have **intensity** that decays exponentially over time (configurable half-life)
- When multiple agents reinforce the same trail, intensity **sums** — popular paths get stronger signals
- Failed approaches leave `warning` pheromones — others learn to avoid them without being told
- **Emergence** happens naturally: no master plan, no central coordinator, just traces in the environment

```python
from akasha import AkashaClient, SignalType

with AkashaClient("localhost:50051") as client:
    # Agent deposits a success pheromone after completing a task
    client.deposit_pheromone(
        trail="pipelines/data-enrichment",
        signal_type=SignalType.SUCCESS,
        emitter="agent-alpha",
        intensity=1.0,
        half_life_secs=3600,
        payload={"duration_ms": 320, "quality_score": 0.95},
    )

    # Another agent senses active pheromones — follows strongest trail
    trails = client.sense_pheromones("pipelines/*")
    strongest = max(trails, key=lambda r: r.value.get("intensity", 0))
```

### 🧠 Shared Cognitive Fabric — Four Layers of Memory

Modeled after the human memory hierarchy from cognitive science:

| Layer | Path | Purpose | Lifespan |
|-------|------|---------|----------|
| **Working** | `memory/working/{agent}/` | Current task context — the agent's scratchpad | Minutes |
| **Episodic** | `memory/episodic/{topic}/` | What happened — decisions, outcomes, timelines | Hours → Days |
| **Semantic** | `memory/semantic/{domain}/` | What we know — facts, patterns, learned insights | Days → Permanent |
| **Procedural** | `memory/procedural/{workflow}/` | How to do things — proven playbooks, workflows | Permanent |

Records naturally flow upward through Nidra consolidation:

```
Working → (persists) → Episodic → (Nidra consolidates) → Semantic → (distills) → Procedural
```

### 🧘 Nidra — The Dreaming Engine

Named after *Yoga Nidra* (yogic sleep), Nidra is a background process that mimics the consolidation function of human sleep. While you sleep, your brain replays experiences, prunes irrelevant connections, and consolidates important memories into long-term storage. Nidra does the same for Akasha.

**Three sleep stages:**

1. **Light Sleep (Sweep)** — Every 5 minutes
   - Evaporates decayed pheromones below threshold
   - Expires stale working memory
   - Counts records per memory layer → emits metrics

2. **Deep Sleep (Consolidate)** — Every ~1 hour
   - Scans episodic memory for high-activity topics
   - Extracts patterns into semantic knowledge
   - **Archives source records to `_consolidated/`** with full audit tags (`_nidra_archived`, `_nidra_cycle`, `_archived_at`)
   - Zero data loss — originals are never deleted

3. **REM (Optimize)** — On-demand
   - Identifies redundant records
   - Merges pheromone trails into procedural memory
   - Reports housekeeping stats to `system/nidra/last-cycle`

Nidra supports **two consolidation modes**:
- **Rule-based** (default, LLM-free) — counting, thresholds, dedup
- **LLM-powered** (opt-in) — pluggable `ConsolidationHook` trait with built-in Ollama/OpenAI support. **Configurable from the admin Dashboard** with one-click connection testing and automatic model discovery.

---

## Why Akasha?

In complex multi-agent systems (RAG pipelines, automation workflows, LLM orchestrators), agents need to know what other agents are doing — **without asking them**.

| Problem | Akasha Solution |
|---------|----------------|
| Agent A needs Agent B's status | Agent B writes to `agents/b/state`, A reads instantly |
| Dashboard needs real-time view | WebSocket subscription to `**` — all events live |
| Detecting stale agents | TTL + automatic reaper removes expired state |
| Querying "all agents of type X" | Glob pattern `agents/*/state` with tag filters |
| Knowledge persists between sessions | Semantic + Procedural memory survive restarts |
| Avoiding duplicate work | `claim` pheromones signal "I'm working on this" |
| Learning from collective experience | Nidra distills episodic outcomes into wisdom |

## Architecture

### Standalone Mode (Community / Basic)

```
┌──────────────────────────────────────────────────────────────────┐
│                         A K A S H A                             │
│                  Shared Cognitive Fabric                         │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  ┌──────────┐ │
│  │   DashMap   │  │  Event Bus  │  │ TTL Reaper │  │  Nidra   │ │
│  │ (in-memory) │  │ (broadcast) │  │ (entropy)  │  │ (sleep)  │ │
│  └──────┬──────┘  └──────┬──────┘  └────────────┘  └──────────┘ │
│         │                │                                       │
│  ┌──────┴────────────────┴───────────────────────────────┐       │
│  │                   AkashaStore                         │       │
│  │         CRUD + Query + Subscribe + Pheromones          │       │
│  └──────┬────────────────────────────────────────────────┘       │
│         │                                                        │
│  ┌──────┴──────┐  ┌──────────────┐  ┌──────────────────┐        │
│  │  RocksDB    │  │ Memory Fabric│  │  Auth Guard      │        │
│  │  (persist)  │  │ W→E→S→P     │  │  JWT + API Keys  │        │
│  └─────────────┘  └──────────────┘  └──────────────────┘        │
│                                                                  │
│  ┌────────────────────────┬────────────────────────────┐         │
│  │  gRPC :50051 (tonic)   │  HTTPS/WS :7777 (axum)    │         │
│  └────────────────────────┴────────────────────────────┘         │
│  🔐 TLS · 🔑 Auth · 📊 Dashboard SPA · 📡 Telemetry            │
└──────────────────────────────────────────────────────────────────┘
```

### Enterprise Clustering (3+ Nodes)

```
┌─────────────────────────────────────────────────────────────────┐
│                    AKASHA CLUSTER (Enterprise)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐        │
│  │          Control Plane (GossipRaft · 3 nodes)        │        │
│  │                                                      │        │
│  │  Node 1 (Leader)    Node 2         Node 3            │        │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐      │        │
│  │  │ Raft Log   │  │ (Follower) │  │ (Follower) │      │        │
│  │  │ Nidra Lead │  │            │  │            │      │        │
│  │  └────────────┘  └────────────┘  └────────────┘      │        │
│  └──────────────────────────────────────────────────────┘        │
│                          │                                       │
│                SWIM Gossip (UDP :7946)                            │
│             HMAC-SHA256 authenticated                             │
│                          │                                       │
│  ┌──────────────────────────────────────────────────────┐        │
│  │           Data Plane (CRDT · all nodes)              │        │
│  │                                                      │        │
│  │  Each node:                                          │        │
│  │  • DashMap + RocksDB (local state)                   │        │
│  │  • HLC + LWW registers (conflict resolution)        │        │
│  │  • Delta gossip (sub-10ms LAN convergence)           │        │
│  │  • Anti-entropy (rate-limited, 500 paths/tick)       │        │
│  │  • Sync backpressure (send-with-timeout, no drops)   │        │
│  │  • MTU-safe batch chunking (UDP-friendly)            │        │
│  └──────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐        │
│  │  Gateway (every node — agents connect to ANY node)   │        │
│  │  gRPC :50051  │  HTTPS :7777  │  Gossip :7946        │        │
│  └──────────────────────────────────────────────────────┘        │
│  🔐 mTLS inter-node · 🔑 License-bound cluster ID               │
└─────────────────────────────────────────────────────────────────┘
```

**Key operational properties:**
- Agents connect to **any node** — no routing complexity
- Writes are applied **locally first**, then propagated via CRDT delta gossip (<10ms LAN convergence)
- If a node dies, the other 2 continue serving; rejoining nodes recover via **anti-entropy**
- Nidra consolidation runs **only on the elected leader** to avoid duplicate work
- Adding/removing nodes: automatic SWIM discovery + CRDT sync — **zero configuration**

#### Cluster Upgrade Mode (Grow & Shrink) — v1.0.9

For zero-downtime rolling upgrades, the cluster supports a **temporary +1 node grace period**:

```bash
# 1. Enable upgrade mode (default: 1 hour grace period)
curl -sk -X POST https://node-01:7777/api/v1/cluster/upgrade \
  -H "Content-Type: application/json" \
  -d '{"activated_by": "admin", "grace_period_secs": 3600}'

# 2. Add new node to the cluster (joins via SWIM gossip)
#    The cluster now accepts max_nodes + 1 temporarily

# 3. Migrate workload / data to new node

# 4. Remove the old node (shrink back to max_nodes)
#    OR the grace period expires and the upgrade node is auto-evicted

# Check status
curl -sk https://node-01:7777/api/v1/cluster/upgrade

# Manually disable and evict
curl -sk -X DELETE https://node-01:7777/api/v1/cluster/upgrade
```

| State | Max Nodes | Duration |
|-------|:---------:|:--------:|
| Normal | license limit (e.g. 3) | Permanent |
| Upgrade mode | license limit + 1 | Grace period (default 1h) |
| After grace expires | license limit | Auto-evicts last node |

#### License Expiration Watchdog — v1.0.9

Paid licenses (Basic/Enterprise) now enforce expiration with a background watchdog:

```
  ┌──────────┐  30d  ┌──────────┐  7d  ┌──────────┐  1d  ┌──────────┐
  │  Valid    │ ───→  │ Warning  │ ──→  │ Warning  │ ──→  │ Warning  │
  │ (normal) │       │ (30 day) │      │ (7 day)  │      │ (1 day)  │
  └──────────┘       └──────────┘      └──────────┘      └────┬─────┘
                                                              │ 0d
                                                              ▼
                                                      ┌──────────────┐
                                                      │ Grace Period │
                                                      │ (read-only)  │
                                                      │  48 hours    │
                                                      └──────┬───────┘
                                                             │ -48h
                                                             ▼
                                                      ┌──────────────┐
                                                      │   Expired    │
                                                      │  exit(1)     │
                                                      └──────────────┘
```

| Phase | Behavior |
|-------|----------|
| **Valid** | Normal operation |
| **Warning** (30/7/1d) | Warning in logs every hour |
| **Grace period** (0–48h after expiry) | READ-ONLY mode — reads work, writes return `503` |
| **Expired** (>48h after expiry) | Server exits with code 1 |

Monitor via API:
```bash
curl -sk https://localhost:7777/api/v1/license/status
# {"status": "warning", "days_left": 7, "read_only": false, "tier": "Enterprise"}
```

Community tier licenses are **perpetual** — no expiration.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Pull from Docker Hub
docker pull alejandrosl/akasha:latest

# Run Akasha with a single command
docker run -d --name akasha \
  -p 7777:7777 -p 50051:50051 \
  -v akasha-data:/akasha-data \
  alejandrosl/akasha:latest

# TLS certificates are auto-generated on first boot
# Trust the CA for green-lock HTTPS:
docker cp akasha:/akasha-data/tls/ca.pem ./akasha-ca.pem
```

### Option 2: One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/ocuil/akasha-public/main/deploy/get-akasha.sh | bash
```

Detects your OS/arch, downloads the correct binary, and installs to `/usr/local/bin/`.

### Option 3: Build from Source

```bash
git clone https://github.com/ocuil/akasha.git
cd akasha
cargo build --release

# Run (auto-generates TLS certs on first boot)
cargo run --release

# Or with a custom config
cargo run --release -- akasha.toml
```

### Option 4: 3-Node Enterprise Cluster

```bash
# Requires Enterprise license
docker compose up -d   # Starts 3 nodes with SWIM gossip + CRDT replication

# Check cluster health (3 nodes, all alive)
curl -sk https://localhost:7771/api/v1/cluster/nodes | jq

# Write on node-01, read from node-02 (CRDT replication)
curl -sk -X POST https://localhost:7771/api/v1/records/agents/test/state \
  -H "Content-Type: application/json" \
  -d '{"value": {"status": "active"}}'
curl -sk https://localhost:7772/api/v1/records/agents/test/state  # ← replicated!

# Run the full QA suite (41 tests)
python3 tools/akasha-qa.py
```

### Try It

```bash
# Health check (TLS enabled by default)
curl -sk https://localhost:7777/api/v1/health

# Or trust the auto-generated CA for verified HTTPS:
curl --cacert akasha-data/tls/ca.pem https://localhost:7777/api/v1/health

# Write agent state
curl -sk -X POST https://localhost:7777/api/v1/records/agents/planner-01/state \
  -H "Content-Type: application/json" \
  -d '{"value": {"status": "processing", "task": "data-pipeline"}}'

# Read it back
curl -sk https://localhost:7777/api/v1/records/agents/planner-01/state

# Query all agents
curl -sk "https://localhost:7777/api/v1/query?pattern=agents/*/state"

# Deposit a pheromone (stigmergy)
curl -sk -X POST https://localhost:7777/api/v1/pheromones \
  -H "Content-Type: application/json" \
  -d '{"trail": "tasks/enrichment", "signal_type": "success", "emitter": "agent-01", "intensity": 1.0}'

# Full system tree
curl -sk https://localhost:7777/api/v1/tree

# Prometheus metrics
curl -sk https://localhost:7777/metrics

# Cognitive Fabric endpoints
curl -sk https://localhost:7777/api/v1/nidra/status
curl -sk https://localhost:7777/api/v1/pheromones
curl -sk https://localhost:7777/api/v1/memory/layers

# Dashboard (open in browser)
open https://localhost:7777/dashboard
```

## SDKs

### Python SDK

```bash
pip install akasha-client
```

```python
from akasha import AkashaClient, MemoryLayer, SignalType

with AkashaClient("localhost:50051") as client:
    # Write state — inscribe into the Records
    client.put("agents/planner/state", {
        "status": "processing",
        "task": "generate-report",
        "progress": 0.6,
    })

    # Read another agent's state — instant awareness
    worker = client.get("agents/worker-01/state")

    # Stigmergy — deposit and sense pheromones
    client.deposit_pheromone(
        "pipelines/data-enrichment",
        signal_type=SignalType.DISCOVERY,
        emitter="planner-01",
    )

    # Cognitive Fabric — write to memory layers
    client.write_memory(
        MemoryLayer.SEMANTIC,
        "workflows/enrichment-patterns",
        {"pattern": "batch_enrichment", "confidence": 0.78},
    )

    # Query all agents — stigmergic sensing
    for record in client.query("agents/*/state"):
        print(f"{record.path}: {record.value}")

    # Real-time subscriptions — the fabric speaks
    for event in client.subscribe("agents/**"):
        print(f"[{event.kind}] {event.path}")
```

Also includes **async client** (asyncio/LangGraph), **HTTP client**, and **high-level convenience methods**.
See [Python SDK docs](sdks/python/README.md) | [PyPI](https://pypi.org/project/akasha-client/).

### Node.js SDK

```bash
npm install akasha-memory
```

```typescript
import { AkashaHttpClient } from 'akasha-memory';

const client = new AkashaHttpClient({
  baseUrl: 'https://localhost:7777',
  token: 'your-jwt-token',
  rejectUnauthorized: false,  // for self-signed certs
});

await client.put('agents/orchestrator/state', {
  status: 'coordinating',
  task: 'pipeline-execution',
});

const worker = await client.get('agents/worker-01/state');

// CAS (optimistic concurrency)
const record = await client.get('agents/counter');
await client.putCas('agents/counter', { count: 2 }, record!.version);

// gRPC client also available:
import { AkashaClient } from 'akasha-memory';
const grpc = new AkashaClient({ address: 'localhost:50051' });
for await (const event of grpc.subscribe('agents/**')) {
  console.log(`[${event.kind}] ${event.path}`);
}
```

Also includes **HTTP client** with WebSocket subscriptions. See [Node.js SDK docs](sdks/node/README.md) | [npm](https://www.npmjs.com/package/akasha-memory).

## Configuration

Create an `akasha.toml` file (optional — sensible defaults used otherwise):

```toml
[server]
grpc_addr = "0.0.0.0:50051"
http_addr = "0.0.0.0:7777"
name = "akasha"

[persistence]
enabled = true
data_dir = "./akasha-data"

[ttl]
sweep_interval_secs = 10

[nidra]
enabled = true
sweep_interval_secs = 300          # 5 min between sweeps
consolidation_every_n_sweeps = 12  # Deep consolidation every ~1 hour
evaporation_threshold = 0.01      # Pheromone evaporation threshold
max_episodic_per_topic = 100       # Max episodic records before consolidation

[elasticsearch]
enabled = false
url = "http://localhost:9200"
index_prefix = "akasha"
batch_size = 1000
flush_interval_secs = 5

[llm]
enabled = false                          # Set true to enable LLM-powered consolidation
provider = "ollama"                      # "ollama" or "openai" (OpenAI-compatible)
endpoint = "http://localhost:11434/api/generate"  # Your Ollama server URL
model = "llama3.2"                       # Model to use (auto-discoverable from Dashboard)
system_prompt = "You are Nidra, the consolidation engine of Akasha..."
max_tokens = 1024
# 💡 LLM config can also be managed at runtime from the admin Dashboard:
#    Administration > LLM / Nidra tab > Test Connection / Discover Models

[auth]
enabled = true                       # Require authentication for all API requests
# jwt_secret = ""                    # Auto-generated if empty
# jwt_lifetime_hours = 24            # JWT session lifetime
# Default user: akasha/akasha (created on first boot — change immediately!)

# license_path = "license.json"
```

### Enterprise Cluster Configuration

Each node in the cluster needs a `[cluster]` section:

```toml
[cluster]
enabled = true
node_id = "akasha-01"              # Unique per node
bind_addr = "0.0.0.0:7946"         # SWIM gossip port (UDP)
advertise_addr = "akasha-01:7946"  # Reachable address for peers
seeds = ["akasha-02:7946", "akasha-03:7946"]  # Bootstrap peers
cluster_id = "akasha-enterprise"   # Shared cluster identifier

[auth]
enabled = true                     # Recommended for production clusters

[tls]
enabled = true                     # mTLS for inter-node + client
dns_suffix = "sslip.io"            # Auto-cert domain suffix
```

## API Reference

### REST Endpoints (HTTP :7777)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/records/{path}` | Write a record |
| `GET` | `/api/v1/records/{path}` | Read a record |
| `DELETE` | `/api/v1/records/{path}` | Delete a record |
| `GET` | `/api/v1/query?pattern=...` | Glob query |
| `GET` | `/api/v1/agents` | List registered agents |
| `GET` | `/api/v1/tree` | Full state tree |
| `GET` | `/api/v1/metrics` | Server metrics |
| `GET` | `/api/v1/nidra/status` | Last Nidra consolidation report |
| `GET` | `/api/v1/pheromones` | Active pheromone trails |
| `GET` | `/api/v1/memory/layers` | Memory layer record counts |
| `GET` | `/api/v1/cluster/nodes` | Cluster node topology |
| `GET` | `/api/v1/cluster/sync` | CRDT sync status |
| `GET` | `/api/v1/cluster/raft` | Raft consensus status |
| `GET` | `/api/v1/diag/report` | 🔍 Cluster diagnostic report (admin) |
| `GET` | `/api/v1/audit?category=...` | 📋 Security audit trail |
| `GET` | `/dashboard/` | 📊 Enterprise Dashboard SPA |
| `WS` | `/api/v1/stream?pattern=...` | WebSocket event stream |
| `SSE` | `/api/v1/events?pattern=...` | Server-Sent Events stream |
| | | |
| **Auth** | | *Public (no auth required)* |
| `POST` | `/api/v1/auth/login` | Login → JWT token |
| `GET` | `/api/v1/auth/status` | Check if auth is enabled |
| `GET` | `/api/v1/auth/me` | Current user identity |
| `POST` | `/api/v1/auth/change-password` | Change own password |
| | | |
| **Admin** | | *Requires Admin role* |
| `GET` | `/api/v1/admin/users` | List users |
| `POST` | `/api/v1/admin/users` | Create user |
| `PUT` | `/api/v1/admin/users/:username` | Update user (role/password) |
| `DELETE` | `/api/v1/admin/users/:username` | Delete user |
| `GET` | `/api/v1/admin/keys` | List API keys |
| `POST` | `/api/v1/admin/keys` | Create API key (returns key once) |
| `DELETE` | `/api/v1/admin/keys/:id` | Revoke API key |
| | | |
| **LLM Config** | | *Requires Admin role* |
| `GET` | `/api/v1/admin/llm/config` | Get current LLM/Nidra config |
| `POST` | `/api/v1/admin/llm/config` | Update LLM config at runtime |
| `POST` | `/api/v1/admin/llm/test` | Test connection to LLM endpoint |
| `GET` | `/api/v1/admin/llm/models` | Discover available Ollama models |

### gRPC Service (Port :50051)

| RPC | Description |
|-----|-------------|
| `Put` | Write a record |
| `Get` | Read a record |
| `Delete` | Delete a record |
| `Query` | Glob pattern query with tag filters |
| `ListPaths` | List paths under prefix |
| `Subscribe` | Server-streaming event subscription |
| `RegisterAgent` | Register an agent |
| `Heartbeat` | Agent heartbeat |
| `GetMetrics` | Server metrics |

## Performance

- **Sub-millisecond** state access via DashMap (lock-free concurrent reads)
- **MessagePack** internal serialization (30-50% smaller than JSON)
- **Zero-copy** gRPC for binary data
- **Broadcast channels** for fan-out event delivery (no per-subscriber overhead)
- **RocksDB** WAL with LZ4 compression for durable persistence
- **AES-256-GCM** encryption at-rest with **~3% overhead** (AES-NI hardware acceleration)
- **Exponential decay** pheromones computed on-read (no background timer per pheromone)

## 🔒 Security

Akasha is built with defense-in-depth — every layer of the stack is secured:

| Layer | Mechanism | Details |
|-------|-----------|--------|
| **Transport** | TLS 1.3 | Auto-generated certificates on first boot |
| **Authentication** | JWT + API Keys | Argon2id password hashing, configurable expiry |
| **Authorization** | RBAC | Admin, User, and ReadOnly roles |
| **Inter-node** | mTLS | Mutual TLS for all cluster communication |
| **Gossip** | HMAC-SHA256 | Authenticated protocol messages |
| **Rate Limiting** | Per-user | 5 failed attempts / 60s lockout |
| **Data at Rest** | **AES-256-GCM** | **BYOK — Bring Your Own Key** |
| **Audit Trail** | Immutable log | Auth, admin, policy events with 90-day retention |

### Encryption At-Rest (BYOK)

All record values are encrypted before hitting disk using **AES-256-GCM** (authenticated encryption). The operator provides their own 256-bit master key — Akasha never generates or stores keys for you.

**Key provisioning modes:**

| Mode | Configuration | Use Case |
|------|---------------|----------|
| **File** | `key_file = "/secrets/akasha.key"` | Kubernetes Secret, Docker secret |
| **Env var** | `key_env = "AKASHA_ENCRYPTION_KEY"` | CI/CD, Docker Compose |

```toml
# akasha.toml
[encryption]
enabled = true
algorithm = "aes-256-gcm"
key_file = "/secrets/akasha.key"    # Hex-encoded 256-bit key (64 chars)
```

```bash
# Generate a key
python3 -c "import secrets; print(secrets.token_hex(32))" > encryption.key
```

**Key properties:**
- **Wire format**: `[version(1)][nonce(12)][ciphertext+tag]` — versioned for future algorithm rotation
- **Nonces**: 96-bit random per operation — cryptographically guaranteed unique
- **Memory safety**: Keys are zeroized from memory after use (`zeroize` crate)
- **Migration**: The system auto-detects unencrypted records and reads them transparently (enable encryption on existing deployments without data loss)
- **Performance**: ~3% overhead with AES-NI (P50: 14.6ms encrypted vs 16.5ms unencrypted)

### Audit Trail

Every security-relevant event is recorded as an **immutable record** in the `audit/` namespace (enforced `append_only` policy — records cannot be modified or deleted):

| Category | Events Tracked |
|----------|---------------|
| `auth` | Login success/failure, rate limiting triggered |
| `admin` | User created/updated/deleted, API key issued/revoked |
| `policy` | Namespace policy violations (403 Forbidden) |
| `system` | Encryption key loaded, Nidra consolidation, node join/leave |

```bash
# Query the audit trail
curl -sk -H "Authorization: Bearer $TOKEN" \
  "https://your-server:7777/api/v1/audit?category=auth&limit=50"
```

Audit records have a 90-day TTL by default and are automatically cleaned up.

---

## Project Status

| Component | Status |
|-----------|--------|
| Core Engine (`akasha-core`) | ✅ Production-ready |
| Stigmergy / Pheromones | ✅ Production-ready |
| Cognitive Fabric (4-layer memory) | ✅ Production-ready |
| Nidra Consolidation Engine | ✅ Production-ready |
| gRPC Server | ✅ Production-ready |
| REST/WebSocket Server | ✅ Production-ready |
| Python SDK | ✅ Production-ready |
| Node.js SDK | ✅ Production-ready |
| Elasticsearch Forwarder | ✅ Implemented (Enterprise) |
| LLM Consolidation Hooks | ✅ Production-ready (Ollama / OpenAI-compatible) |
| LLM Dashboard Config | ✅ **Runtime config, test connection, model discovery** |
| License Key System | ✅ Ed25519 cryptographic |
| **Authentication (JWT + API Keys)** | ✅ **Argon2id + HMAC-SHA256** |
| **Dashboard SPA (React)** | ✅ **Embedded in binary (rust-embed)** |
| **CLI Key Generation** | ✅ **`akasha-license api-key`** |
| **CRDT Replication (HLC + LWW)** | ✅ **29/29 E2E tests** |
| **SWIM Gossip Discovery** | ✅ **3-node cluster** |
| **Anti-Entropy Reconciliation** | ✅ **Rate-limited, backpressure-safe** |
| **GossipRaft Consensus** | ✅ **Leader election + failover** |
| **mTLS + HMAC Inter-Node** | ✅ **Encrypted cluster** |
| **Distributed Nidra** | ✅ **Single-leader consolidation** |
| **Encryption At-Rest (BYOK)** | ✅ **AES-256-GCM, Bring Your Own Key** |
| **Immutable Audit Trail** | ✅ **Auth, admin, policy, system events** |
| **Namespace Write Policies** | ✅ **LWW, CAS-only, append-only, immutable** |
| **SSE Event Streaming** | ✅ **Real-time filtered event stream** |
| **Batch Read API** | ✅ **Up to 1000 paths/request** |
| **Diagnostic Report API** | ✅ **Health score, topology, security posture** |
| **MCP Server** | ✅ **Claude/Gemini agent integration** |
| **Sync Backpressure** | ✅ **Rate-limited anti-entropy, zero data loss** |
| **Namespace Isolation** | ✅ **Per-API-key path filtering** |
| QA Suite | ✅ **41/41 tests (100%)** |

## How Akasha Compares

Akasha, [Mem0](https://github.com/mem0ai/mem0), and [Letta](https://github.com/letta-ai/letta) all solve **agent memory** — but with fundamentally different approaches:

| | **Akasha** | **Mem0** | **Letta (MemGPT)** |
|:---|:---:|:---:|:---:|
| **Philosophy** | Memory as infrastructure | Memory as a service | Memory as OS |
| **Core idea** | Shared cognitive fabric — agents coordinate through persistent stigmergy | Pluggable memory layer — add recall to any agent | Agent runtime — the agent manages its own memory |
| | | | |
| **Write latency** | **< 1 ms** (direct data op) | ~1,400 ms (requires LLM) | ~500–2,000 ms (LLM tool call) |
| **Read latency** | **< 1 ms** | ~200–500 ms (vector search) | ~200–500 ms (vector search) |
| **LLM calls per memory op** | **0** | 2 (extract + dedup) | 1+ (agent tool call) |
| **Throughput** | **2,237 ops/sec** | ~1–5 ops/sec (LLM-bound) | ~1–5 ops/sec (LLM-bound) |
| | | | |
| **Multi-agent coordination** | ✅ Native (stigmergy) | ❌ Single-agent | ❌ Single-agent |
| **Memory tiers** | ✅ Working → Episodic → Semantic → Procedural | ⚠️ Flat | ✅ Core → Recall → Archival |
| **Auto-consolidation** | ✅ Nidra (time-based, configurable) | ✅ LLM-driven (on every write) | ⚠️ Agent-driven (unreliable) |
| **Memory decay** | ✅ Pheromone evaporation | ❌ Manual deletion | ❌ Manual |
| **Cross-agent memory** | ✅ Shared paths + pheromones | ❌ Per-user isolation | ❌ Per-agent isolation |
| **Self-organizing** | ✅ Stigmergy (emergent) | ❌ Static structure | ⚠️ Agent decides |
| | | | |
| **Clustering / HA** | ✅ 3+ node CRDT (Enterprise) | ❌ | ❌ |
| **Auth** | ✅ JWT + API Keys + RBAC | ⚠️ API key only | ⚠️ Basic |
| **Dashboard** | ✅ React SPA with CRUD | ❌ | ⚠️ Basic UI |
| **gRPC** | ✅ | ❌ | ❌ |
| **Encryption at rest** | ✅ AES-256-GCM (BYOK) | ❌ | ❌ |
| **Audit trail** | ✅ Immutable log | ❌ | ❌ |
| **Persistence** | ✅ RocksDB (WAL, LSM, encrypted) | External (Qdrant, etc.) | Postgres |
| **LLM dependency** | **Optional** | **Critical** | **Critical** |
| | | | |
| **Best for** | Multi-agent coordination at scale | Single-user personalization | Stateful single-agent reasoning |
| **License** | ASL-1.0 (source-available) | Apache-2.0 | Apache-2.0 |

**The key insight:**
- **Mem0** asks: *"What facts should I remember about this user?"*
- **Letta** asks: *"How should the agent manage its own context window?"*
- **Akasha** asks: *"How should a community of agents share and build knowledge?"*

> These systems can also be **complementary**: Akasha serves as the coordination backbone while Mem0 handles user-facing personalization and Letta manages complex single-agent reasoning.

---

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](USER_GUIDE.md) | Complete guide: installation, memory architecture, API, system prompts |
| [**Agent Integrations**](INTEGRATIONS.md) | **Connect Pi, LangGraph, CrewAI, AutoGen, OpenAI SDK, Google ADK, and more** |
| [Agent Skills](skills/) | Pre-built skills (agentskills.io standard) for agent onboarding |
| [Python SDK](sdks/python/README.md) | Python SDK with gRPC + HTTP + async support |
| [Node.js SDK](sdks/node/README.md) | TypeScript SDK with gRPC + HTTP + WebSocket |

## License Tiers

| Feature | Community | Basic | Enterprise |
|---------|:---------:|:-----:|:----------:|
| Core Engine (CRUD, Query, Subscribe) | ✅ | ✅ | ✅ |
| Agent Registration & Heartbeat | ✅ | ✅ | ✅ |
| Stigmergy (Pheromones) | ✅ | ✅ | ✅ |
| Cognitive Fabric (4 layers) | ✅ | ✅ | ✅ |
| Nidra Basic (rule-based) | ✅ | ✅ | ✅ |
| Python & Node.js SDKs | ✅ | ✅ | ✅ |
| Web Dashboard | ❌ | ✅ | ✅ |
| Clustering (HA / FT / DR) | ❌ | ❌ | ✅ (3+ nodes) |
| Elasticsearch Forwarder | ❌ | ❌ | ✅ |
| Nidra LLM Hooks | ❌ | ❌ | ✅ |
| Custom Consolidation Hooks | ❌ | ❌ | ✅ |
| Max Agents | 5 | 100 | ♾️ |
| Max Records | 10K | 1M | ♾️ |
| Max Pheromone Trails | 100 | 10K | ♾️ |
| Max Nodes | 1 | 1 | Licensed (3+) |
| License Required | No (auto-demo) | Yes (registered) | Yes (registered) |
| Cluster Binding | None | Installation fingerprint | Installation fingerprint |
| Priority Support | ❌ | ❌ | ✅ |

---

## Licensing Operations — Full Guide

### Security Model

Licenses are **Ed25519 cryptographically signed** and validated **offline** (zero phone-home).

Since v2, licenses are bound to a **installation-specific fingerprint** composed of:

```
fingerprint = SHA-256(cluster_id + installation_id + install_timestamp)
                 ↑                    ↑                    ↑
           user-defined       UUID v4 (auto)         first boot epoch
```

- `cluster_id`: Defined in `akasha.toml` by the user
- `installation_id`: Random UUID generated once on first boot, saved to `data/cluster.identity`
- `install_timestamp`: Unix epoch of first boot

This ensures the **same cluster_id on a different server produces a different fingerprint**.

### Step 0: Generate Keypair (one-time)

```bash
akasha-license keygen --output keys/
# → keys/akasha.key  (PRIVATE — never share)
# → keys/akasha.pub  (PUBLIC  — embedded in binary)
```

### Step 1: Client Installs & Gets Fingerprint

The client installs Akasha and starts the server. On first boot, a `cluster.identity` file is generated:

```bash
# Client runs:
akasha akasha.toml
# 🔑 New cluster identity generated — share this fingerprint for licensing
# → data/cluster.identity created

# Client retrieves fingerprint:
curl -sk https://localhost:7777/api/v1/license/fingerprint
```

Response:
```json
{
  "fingerprint": "a7f3b2e1d4c5f6a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2",
  "cluster_id": "acme-production",
  "installation_id": "e9c14a2b-7f3d-4e5a-8b1c-9d0e2f3a4b5c",
  "installed_at": 1712345678,
  "license_tier": "Community",
  "license_valid": true
}
```

The client sends you the `fingerprint` value.

### Step 2: Issue License (Admin)

```bash
# Enterprise license (recommended: use --fingerprint from server)
akasha-license issue \
  --customer "Acme Corp" \
  --tier enterprise \
  --fingerprint "a7f3b2e1d4c5f6a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2" \
  --max-nodes 5 \
  --days 365 \
  --private-key keys/akasha.key \
  --output acme-license.json

# Basic license
akasha-license issue \
  --customer "Startup Inc" \
  --tier basic \
  --fingerprint "<fingerprint>" \
  --days 365 \
  --private-key keys/akasha.key \
  --output startup-license.json

# Legacy mode (v1 — cluster-id only, NOT recommended)
akasha-license issue \
  --customer "Legacy Corp" \
  --tier basic \
  --cluster-id "legacy-prod" \
  --private-key keys/akasha.key \
  --output legacy-license.json
```

### Step 3: Client Activates License

```bash
# Client copies license.json to their server
cp license.json /path/to/akasha/license.json

# Updates akasha.toml:
# [auth]
# license_path = "license.json"

# Restarts:
akasha akasha.toml
# 🔑 License validated: Enterprise (Acme Corp, 5 nodes)
```

### Step 4: Verify License (Admin)

```bash
akasha-license verify \
  --license acme-license.json \
  --public-key keys/akasha.pub
# ✅ License is VALID
```

### Full Flow Diagram

```
CLIENT                                     ADMIN (you)
──────                                     ───────────
1. Install Akasha
2. akasha akasha.toml (first boot)
   → generates data/cluster.identity
   → prints fingerprint
   
3. curl .../api/v1/license/fingerprint
   → gets fingerprint JSON
   
4. Sends fingerprint to admin ─────────── 5. akasha-license issue \
                                              --fingerprint "..." \
                                              --customer "..." \
                                              --tier enterprise \
                                              --max-nodes 5 \
                                              --private-key keys/akasha.key
                                              
6. Receives license.json ◄──────────────── 7. Sends license.json

8. cp license.json → config dir
9. Restart: 🔑 License validated ✓

DONE — zero phone-home, fully offline
```

### Key Paths

| File | Purpose |
|------|---------|
| `keys/akasha.key` | Ed25519 private signing key (**NEVER SHARE**) |
| `keys/akasha.pub` | Ed25519 public verification key (embedded in binary) |
| `data/cluster.identity` | Installation fingerprint (auto-generated, immutable) |
| `license.json` | Signed license file (given to client) |
| API: `/api/v1/license/status` | Live expiry status (JSON) |
| API: `/api/v1/license/fingerprint` | Installation fingerprint (JSON) |

## License

**[Akasha Source License 1.0 (ASL-1.0)](LICENSE)**

Copyright © 2026 [Alejandro Sánchez Losa](https://alejandrosl.com) · [GitHub](https://github.com/ocuil) · [LinkedIn](https://www.linkedin.com/in/alejandrosl/)

You may use, copy, distribute, and modify this software freely, subject to the following limitations:

- ❌ You may **not** offer Akasha as a hosted/managed service
- ❌ You may **not** circumvent license key mechanisms
- ✅ You **may** use it in your own products and services
- ✅ You **may** modify and create derivative works
- ✅ You **may** distribute copies (with license)

---

<div align="center">

*"In the Akashic field, there is no distance between knowing and being known. Every agent that writes to the fabric enriches it. Every agent that reads from it gains awareness. The whole becomes greater than the sum of its parts — not through command, but through connection."*

**Built with 🦀 Rust · Powered by ⚡ Tokio · Dreaming through 🧘 Nidra**

</div>
