# Akasha — Persistent Memory for AI Agents

> *"What if your AI agents could remember, learn, and coordinate — without you wiring every connection?"*

---

## The Problem

Every organization deploying AI agents in 2026 hits the same wall:

**Agents are individually smart but collectively amnesiac.** A planner schedules tasks. A researcher retrieves documents. A coder writes software. A monitor watches production. Each one is intelligent in isolation — but none of them remember what the others learned.

### Three Broken Promises of Multi-Agent Systems

#### 1. Agents Forget Everything
When Agent A discovers "the client prefers summaries under 200 words", that knowledge dies with the session. Next time Agent B serves the same client, it starts from scratch. **There is no shared learning.**

#### 2. Coordination Requires Custom Plumbing
If Agent A needs to pass context to Agent B, you build a pipeline. If Agent C needs to know what Agent A learned, you build another. For N agents, you need N² connections. **This doesn't scale.**

#### 3. Infrastructure Wasn't Designed For This
Traditional databases store data. Vector databases store embeddings. Neither stores *knowledge* — the structured, evolving understanding that agents build over time.

---

## The Solution: Akasha

Akasha is a **persistent memory system** for AI agents. It sits behind your agents — it doesn't replace them, it **gives them a shared space to store knowledge, recall experiences, and coordinate without explicit wiring.**

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Agent A │  │ Agent B │  │ Agent C │
│ Planner │  │ Coder   │  │ Monitor │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┼────────────┘
                  │
          ┌───────▼───────┐
          │    AKASHA     │
          │               │
          │  Working ─────│── What they're doing now
          │  Episodic ────│── What happened (history)
          │  Semantic ────│── What they've learned
          │  Procedural ──│── How to do things
          │               │
          │  Pheromones ──│── Coordination signals
          │               │
          └───────────────┘
```

Any agent can **write** what it learns. Any agent can **read** what others know. No pipelines. No message queues. No orchestrator deciding who talks to whom.

---

## Key Design Principles

### Four Memory Layers (Inspired by Cognitive Science)

Modeled after the human memory hierarchy:

| Layer | Purpose | Lifespan | Analogy |
|-------|---------|----------|---------|
| **Working** | Current task scratchpad | Minutes | Your desk notepad |
| **Episodic** | Events, outcomes, decisions | Hours → Days | Your journal |
| **Semantic** | Facts, patterns, learned insights | Days → Permanent | Your knowledge base |
| **Procedural** | Proven workflows, playbooks | Permanent | Your muscle memory |

### Nidra — Automatic Memory Consolidation

Named after *Yoga Nidra* (yogic sleep), Nidra is a background process that organizes memory — like how your brain consolidates experiences during sleep.

> [!IMPORTANT]
> **What Nidra actually does (implementation reality):**
> - **Default mode (rule-based, no LLM):** Counts records per topic, identifies high-activity areas, creates summary records in the semantic layer. **Original records are tagged as consolidated — never deleted.**
> - **LLM mode (Enterprise, opt-in):** If explicitly configured, uses an LLM to extract patterns. Prompts are deterministic and auditable.
> - **Pheromone evaporation:** Only affects pheromone signals (coordination hints). Never touches records, never deletes data.
>
> Nidra is NOT lossy compression. It's additive — it creates new knowledge without destroying sources.

### Stigmergy — Coordination Without Communication

Inspired by how ant colonies coordinate through environmental signals:

- Agents emit **pheromone signals** (lightweight metadata with intensity and half-life)
- Other agents sense these signals and respond accordingly
- Signals naturally decay over time — old coordination cues fade, current ones stay strong

> [!IMPORTANT]
> **What pheromones actually are (implementation reality):**
> - Pheromones are **coordination hints**, not message queues. They signal "discovery", "success", "warning", "claim" on a topic.
> - They are NOT for guaranteed task delivery. For that, use regular records with no TTL.
> - Think of them as "team status board" — not "work ticket queue".
> - Akasha provides both models: durable records for data, ephemeral pheromones for coordination.

---

## What Akasha Is NOT

To prevent misunderstanding, let's be explicit:

| Akasha is... | Akasha is NOT... |
|-------------|-----------------|
| A persistent memory store | A message queue (use Kafka/RabbitMQ for guaranteed delivery) |
| A coordination layer via stigmergy | A task orchestrator (use LangGraph/Temporal for DAGs) |
| A path-based key-value system with glob queries | A vector database (use Qdrant/Pinecone for semantic search) |
| Zero-LLM by default — sub-ms operations | LLM-dependent like Mem0 (which calls LLMs on every write) |
| Infrastructure — it works with any agent framework | A framework — it doesn't replace LangGraph, CrewAI, etc. |

---

## What Exists Today (v1.1.2)

Akasha is production software running today — not a roadmap.

### Core Capabilities

| Capability | Status | What it means |
|-----------|--------|---------------|
| **Persistent Key-Value Memory** | ✅ Production | Any agent reads/writes records via REST, gRPC, or MCP |
| **Four Memory Layers** | ✅ Production | Working, Episodic, Semantic, Procedural — each with appropriate retention |
| **Pheromone Trails** | ✅ Production | Agents coordinate via environmental signals, not direct messaging |
| **Memory Consolidation (Nidra)** | ✅ Production | Automatic pattern extraction — originals always preserved |
| **Optimistic Concurrency (CAS)** | ✅ Production | Multi-agent safe writes without locks |
| **3-Node HA Cluster** | ✅ Production | CRDT-based replication, zero-downtime operations |
| **MCP Server** | ✅ Production | Native integration with Claude, Gemini, Cursor, and any MCP client |
| **Auto-TLS** | ✅ Production | Encrypted by default, zero configuration |
| **Dashboard** | ✅ Production | Real-time visibility into memory state and cluster health |
| **Encryption at Rest (BYOK)** | ✅ Production | AES-256-GCM with Bring Your Own Key |
| **Immutable Audit Trail** | ✅ Production | All security events logged, append-only, non-deletable |
| **Sync Backpressure** | ✅ Production | Rate-limited anti-entropy, zero data loss under load |
| **Diagnostic Reports** | ✅ Production | Health scoring (0-100) with topology, security, and performance analysis |

### Distribution

| Channel | Link |
|---------|------|
| **Docker Hub** | `docker pull alejandrosl/akasha` |
| **Python SDK** | `pip install akasha-client` |
| **Node.js SDK** | `npm install akasha-memory` |
| **MCP Server** | [github.com/ocuil/akasha-public/mcp-server](https://github.com/ocuil/akasha-public/tree/main/mcp-server) |
| **GitHub** | [github.com/ocuil/akasha-public](https://github.com/ocuil/akasha-public) |

### Performance Profile

| Metric | Value | Context |
|--------|-------|---------|
| Read latency (P50) | **1.2 ms** | No LLM calls in the read path |
| Write latency (P50) | **1.5 ms** | No LLM calls in the write path |
| Throughput | **2,237 ops/sec** | Concurrent multi-agent workload |
| Binary size | **25 MB** | Single executable, no JVM, no runtime |
| Docker image | **46 MB** | Smaller than a Node.js hello-world |
| Memory footprint | **~50 MB** | For 100K records |
| QA Suite | **41/41 passing** | Unit + integration + cluster E2E |

---

## Concrete Use Cases

### Use Case 1: Persistent Context Across Sessions

**Without Akasha:**
```
Monday:  Claude analyzes 500 documents → generates conclusions
Tuesday: Claude remembers NOTHING from Monday
         Inject 10M tokens? → $15-40 per conversation, 30s latency
```

**With Akasha:**
```
Monday:  Claude stores key findings → memory/semantic/research/api-design
Tuesday: Claude reads 200 tokens → has full context → $0.001, instant
```

### Use Case 2: Multi-Agent Knowledge Sharing

**Without Akasha:**
```
Agent A: "Client prefers email over Slack" → dies with session
Agent B: Contacts client via Slack → client frustrated
```

**With Akasha:**
```
Agent A: writes memory/semantic/clients/acme/preferences → {"channel": "email"}
Agent B: reads it before acting → uses email → client happy
```

### Use Case 3: Agent Coordination (Stigmergy)

**Without Akasha:**
```
Agent A starts task → nobody knows
Agent B starts SAME task → wasted computation
```

**With Akasha:**
```
Agent A: emits pheromone("tasks/enrichment", signal=CLAIM) → "I'm on it"
Agent B: senses pheromone → "Already claimed, I'll do something else"
```

---

## Competitive Position

| | **Akasha** | **Mem0** | **Zep (Graphiti)** | **Custom (Redis + VectorDB)** |
|--|---|---|---|---|
| **Write latency** | **<1 ms** (0 LLM) | ~1,400 ms (2 LLM calls) | ~200 ms | Variable |
| **Read latency** | **<1 ms** | ~200-500 ms | ~200 ms | Variable |
| **LLM dependency** | **None** (optional) | **Critical** | **Critical** | None |
| **Multi-agent** | ✅ Native | ❌ Single-user | ❌ Single-user | DIY |
| **Coordination** | ✅ Stigmergy | ❌ | ❌ | ❌ |
| **Clustering (HA)** | ✅ CRDT 3+ nodes | ❌ | ❌ | DIY |
| **Self-hosted** | ✅ Single binary | ❌ Cloud + Qdrant | ❌ Neo4j | DIY |
| **MCP Server** | ✅ Native | ❌ | ❌ | ❌ |

**Key insight:** Mem0 asks *"what facts should I remember about this user?"* (single-user personalization). Akasha asks *"how should a community of agents share and build knowledge?"* (multi-agent coordination). They solve different problems.

---

## Architecture At a Glance

- **Engine:** Rust (single binary, zero dependencies)
- **Storage:** RocksDB (WAL, LSM, LZ4 compression, optional AES-256-GCM encryption)
- **APIs:** REST (HTTPS :7777) + gRPC (:50051) + MCP (stdio/SSE) + WebSocket + SSE
- **Clustering:** SWIM gossip discovery + CRDT delta replication + GossipRaft consensus
- **Auth:** JWT + API Keys, Argon2id hashing, RBAC, namespace isolation
- **Dashboards:** Embedded React SPA (rust-embed, no separate server)

---

## Roadmap

### Phase 1: Adoption (Now → Q3 2026)
*Make it trivially easy to try*

- ✅ MCP Server for Claude/Gemini/Cursor
- ✅ Python & Node.js SDKs
- ✅ Docker one-command deploy
- ◻️ LangGraph integration example
- ◻️ CrewAI integration example
- ◻️ Google ADK integration

### Phase 2: Intelligence (Q3 → Q4 2026)
*The memory layer starts thinking*

- ◻️ LLM-powered consolidation (Nidra + language models)
- ◻️ Automatic entity extraction and knowledge graphs
- ◻️ Temporal memory queries ("what changed last week?")

### Phase 3: Ecosystem (2027)
*Akasha becomes a standard*

- ◻️ Managed cloud offering
- ◻️ Pre-built agent memory schemas
- ◻️ SDKs for Go, Java, Rust

---

## The Name

**Akasha** (आकाश) is Sanskrit for the fundamental substance of the cosmos — the "space" in which everything exists and through which all information travels.

In Vedic cosmology, the Akashic Records are the universal memory — a field where every thought, action, and experience is inscribed. Owned by no individual, but accessible to all.

That's what we're building: **the shared memory field for intelligent agents.**

---

*Built with 🦀 Rust for performance · Designed with biology for intelligence · Distributed with intent to scale*

*One binary. Zero dependencies. Persistent memory.*
