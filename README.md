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
[![Version](https://img.shields.io/badge/Version-1.0.3-purple.svg)](CHANGELOG.md)
[![Cluster](https://img.shields.io/badge/Cluster-3_node_HA-brightgreen.svg)](#-architecture)
[![Tests](https://img.shields.io/badge/Tests-148_passing-success.svg)](#-project-status)
[![Auth](https://img.shields.io/badge/Auth-JWT_%2B_API_Keys-orange.svg)](#-security)
[![Rust](https://img.shields.io/badge/Engine-Rust-orange.svg)](https://www.rust-lang.org/)
[![gRPC](https://img.shields.io/badge/Protocol-gRPC-green.svg)](https://grpc.io/)

[Quick Start](#-quick-start) · [Documentation](#-documentation) · [Architecture](#-architecture) · [Why Akasha?](#-why-akasha) · [Community](#-community)

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

| Layer | Purpose | Lifespan |
|-------|---------|----------|
| **Working** | Current task context — the agent's scratchpad | Minutes |
| **Episodic** | What happened — decisions, outcomes, timelines | Hours → Days |
| **Semantic** | What we know — facts, patterns, learned insights | Days → Permanent |
| **Procedural** | How to do things — proven playbooks, workflows | Permanent |

Records naturally flow upward through Nidra consolidation:

```
Working → (persists) → Episodic → (Nidra consolidates) → Semantic → (distills) → Procedural
```

### 🧘 Nidra — The Dreaming Engine

Named after *Yoga Nidra* (yogic sleep), Nidra is a background process that mimics the consolidation function of human sleep. While you sleep, your brain replays experiences, prunes irrelevant connections, and consolidates important memories into long-term storage. Nidra does the same for Akasha.

**Three sleep stages:**

1. **Light Sleep (Sweep)** — Every 5 minutes: evaporates decayed pheromones, expires stale working memory
2. **Deep Sleep (Consolidate)** — Every ~1 hour: scans episodic memory, extracts patterns into semantic knowledge
3. **REM (Optimize)** — On-demand: identifies redundant records, merges trails into procedural memory

---

## 💡 Why Akasha?

In complex multi-agent systems — RAG pipelines, automation workflows, LLM orchestrators — agents need to know what other agents are doing, **without asking them**.

| Problem | Akasha Solution |
|---------|----------------|
| Agent A needs Agent B's status | B writes to `agents/b/state`, A reads instantly |
| Dashboard needs real-time view | WebSocket subscription to `**` — all events live |
| Detecting stale agents | TTL + automatic reaper removes expired state |
| Querying "all agents of type X" | Glob pattern `agents/*/state` with tag filters |
| Knowledge persists between sessions | Semantic + Procedural memory survive restarts |
| Avoiding duplicate work | `claim` pheromones signal "I'm working on this" |
| Learning from collective experience | Nidra distills episodic outcomes into wisdom |

---

## 🚀 Quick Start

### Install (Linux / macOS)

```bash
curl -fsSL https://akasha-installer.akasha.workers.dev/install | bash
```

### Docker

```bash
# Single node
docker run -d --name akasha \
  -p 7777:7777 -p 50051:50051 \
  -v akasha-data:/akasha-data \
  ghcr.io/ocuil/akasha:latest

# Verify
curl -sk https://localhost:7777/api/v1/health
```

### 3-Node Cluster (Enterprise)

```bash
docker compose up -d   # 3 nodes with SWIM gossip + CRDT replication

# Write on node-01, read from node-02 (replicated!)
curl -sk -X POST https://localhost:7771/api/v1/records/agents/test/state \
  -H "Content-Type: application/json" \
  -d '{"value": {"status": "active"}}'
curl -sk https://localhost:7772/api/v1/records/agents/test/state
```

### Python SDK

```python
from akasha import AkashaClient, MemoryLayer, SignalType

with AkashaClient("localhost:50051") as client:
    # Write state — inscribe into the Records
    client.put("agents/planner/state", {
        "status": "processing",
        "task": "generate-report",
    })

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

    # Real-time subscriptions — the fabric speaks
    for event in client.subscribe("agents/**"):
        print(f"[{event.kind}] {event.path}")
```

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         A K A S H A                              │
│                    Shared Cognitive Fabric                        │
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

### Enterprise Clustering

```
┌─────────────────────────────────────────────────────────────────┐
│                    AKASHA CLUSTER (Enterprise)                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐        │
│  │          Control Plane (GossipRaft · 3 nodes)        │        │
│  │                                                      │        │
│  │  Node 1 (Leader)    Node 2         Node 3            │        │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │        │
│  │  │ Raft Log   │  │ (Follower) │  │ (Follower) │     │        │
│  │  │ Nidra Lead │  │            │  │            │     │        │
│  │  └────────────┘  └────────────┘  └────────────┘     │        │
│  └──────────────────────────────────────────────────────┘        │
│                          │                                       │
│                SWIM Gossip (UDP :7946)                            │
│             HMAC-SHA256 authenticated                            │
│                          │                                       │
│  ┌──────────────────────────────────────────────────────┐        │
│  │           Data Plane (CRDT · all nodes)              │        │
│  │                                                      │        │
│  │  • HLC + LWW registers (conflict resolution)        │        │
│  │  • Delta gossip (sub-10ms LAN convergence)           │        │
│  │  • Anti-entropy (15s full-state reconciliation)      │        │
│  └──────────────────────────────────────────────────────┘        │
│                                                                  │
│  Agents connect to ANY node — zero routing complexity            │
│  🔐 mTLS inter-node · 🔑 License-bound cluster ID               │
└─────────────────────────────────────────────────────────────────┘
```

**Upgrade Mode (v1.0.2)**: For zero-downtime rolling upgrades, enable upgrade mode via `POST /api/v1/cluster/upgrade`. The cluster temporarily accepts +1 node beyond the license limit with a configurable grace period (default: 1 hour). After the grace period, the extra node is automatically evicted.

**License Expiration Watchdog (v1.0.3)**: Paid licenses (Basic/Enterprise) now enforce expiration with a background watchdog. The system warns at 30, 7, and 1 day before expiration, enters a 48-hour read-only grace period after expiry (writes return 503), and shuts down after the grace period ends. Monitor status via `GET /api/v1/license/status`. Community tier licenses remain perpetual.

---

## 🔒 Security

- **TLS everywhere** — Auto-generated certificates on first boot
- **Authentication** — JWT tokens + API keys with Argon2id password hashing
- **RBAC** — Admin, User, and ReadOnly roles
- **mTLS** — Mutual TLS for inter-node cluster communication
- **HMAC-SHA256** — Authenticated gossip protocol

---

## ⚡ Performance

- **Sub-millisecond** state access via DashMap (lock-free concurrent reads)
- **MessagePack** serialization (30-50% smaller than JSON)
- **Zero-copy** gRPC for binary data
- **RocksDB** WAL with LZ4 compression for durable persistence
- **Exponential decay** pheromones computed on-read (no background timer per pheromone)

---

## 📦 Downloads

| Platform | Architecture | |
|----------|-------------|---|
| Linux | x86_64 (amd64) | `akasha-v1.0.3-linux-amd64.tar.gz` |
| Linux | aarch64 (arm64) | `akasha-v1.0.3-linux-arm64.tar.gz` |
| macOS | Apple Silicon | `akasha-v1.0.3-darwin-arm64.tar.gz` |
| Docker | Multi-arch | `ghcr.io/ocuil/akasha:1.0.3` |

See [Releases](https://github.com/ocuil/akasha-public/releases) for downloads.

---

## 📊 Project Status

| Component | Status |
|-----------|--------|
| Core Engine (CRUD, Query, Subscribe) | ✅ Production |
| Stigmergy (Pheromones) | ✅ Production |
| Cognitive Fabric (4-layer memory) | ✅ Production |
| Nidra Consolidation Engine | ✅ Production |
| Python & Node.js SDKs | ✅ Production |
| Authentication (JWT + API Keys) | ✅ Production |
| Dashboard SPA (React) | ✅ Embedded in binary |
| CRDT Replication (HLC + LWW) | ✅ 29/29 E2E tests |
| SWIM Gossip + Raft Consensus | ✅ 3-node HA |
| mTLS + HMAC Inter-Node | ✅ Encrypted |
| Test Suite | ✅ 148 tests passing |

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](installation.md) | Standalone, cluster, Docker, and Kubernetes deployment |
| [Configuration Reference](configuration.md) | Complete TOML configuration reference |
| [Authentication & Security](authentication.md) | Users, JWT tokens, API keys, and RBAC |
| [Python SDK Guide](sdk-python.md) | Full Python SDK tutorial with examples |
| [Node.js SDK Guide](sdk-nodejs.md) | Full Node.js/TypeScript SDK tutorial |
| [Agent Patterns](agent-patterns.md) | Stigmergy, memory fabric, and pheromone patterns |
| [Cluster Operations](cluster-operations.md) | Scaling, failover, monitoring, and anti-entropy |
| [REST API Reference](api-reference.md) | Complete HTTP/WebSocket API reference |
| [Dashboard Guide](dashboard.md) | Web dashboard usage and features |

---

## 💰 License Tiers

| Feature | Community | Enterprise |
|---------|:---------:|:----------:|
| Core Engine + Stigmergy + Cognitive Fabric | ✅ | ✅ |
| Python & Node.js SDKs | ✅ | ✅ |
| Nidra Basic (rule-based) | ✅ | ✅ |
| Web Dashboard | — | ✅ |
| Clustering (3+ node HA) | — | ✅ |
| Elasticsearch Forwarder | — | ✅ |
| LLM Consolidation Hooks | — | ✅ |
| Priority Support | — | ✅ |

Licenses are **cryptographically signed (Ed25519)** and validated **entirely offline** — zero phone-home, zero telemetry, zero tracking.

### How to Get a License

**Community** — no license needed. Install and run, features are available immediately.

**Enterprise** — follow these steps:

```
1. Install Akasha and start the server
   → A unique installation fingerprint is generated automatically

2. Retrieve your fingerprint:
   curl -sk https://your-server:7777/api/v1/license/fingerprint

3. Send your fingerprint to the Akasha team
   → Contact: dev@alejandrosl.com

4. Receive your license.json file

5. Place it in your config directory and restart:
   cp license.json /path/to/akasha/
   # Update akasha.toml: license_path = "license.json"
   akasha akasha.toml
   # → 🔑 License validated ✓
```

Each license is **bound to your specific installation** — it cannot be transferred to a different server. Licenses are validated offline with no network dependency.

---

## 🤝 Community

- **Issues**: [Report bugs and request features](https://github.com/ocuil/akasha-public/issues)
- **Releases**: [Download latest binaries](https://github.com/ocuil/akasha-public/releases)
- **Author**: [Alejandro Sánchez Losa](https://alejandrosl.com) · [LinkedIn](https://www.linkedin.com/in/alejandrosl/)

---

## 📄 License

**[Akasha Source License 1.0 (ASL-1.0)](LICENSE)**

- ✅ You **may** use, copy, distribute, and modify freely
- ✅ You **may** use it in your own products and services
- ❌ You may **not** offer as a hosted/managed service
- ❌ You may **not** circumvent license key mechanisms

---

<div align="center">

*"In the Akashic field, there is no distance between knowing and being known. Every agent that writes to the fabric enriches it. Every agent that reads from it gains awareness. The whole becomes greater than the sum of its parts — not through command, but through connection."*

**Built with 🦀 Rust · Powered by ⚡ Tokio · Dreaming through 🧘 Nidra**

</div>
