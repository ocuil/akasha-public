# 📖 Akasha — User Guide

> **The Shared Cognitive Fabric for Intelligent Agent Systems**

---

## Table of Contents

1. [What is Akasha?](#what-is-akasha)
2. [Key Concepts](#key-concepts)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Memory Architecture](#memory-architecture)
6. [Stigmergy & Coordination](#stigmergy--coordination)
7. [Nidra — Memory Consolidation](#nidra--memory-consolidation)
8. [Configuring Agents](#configuring-agents)
9. [System Prompts for Agents](#system-prompts-for-agents)
10. [Dashboard](#dashboard)
11. [Security & Authentication](#security--authentication)
12. [Cluster Operations](#cluster-operations)
13. [SDK Reference](#sdk-reference)
14. [Complete REST API Reference](#complete-rest-api-reference)
15. [Troubleshooting](#troubleshooting)
16. [FAQ](#faq)
17. [Agent Skills](#agent-skills)

---

## What is Akasha?

Akasha is a **shared memory layer** designed for multi-agent AI systems. Think of it as a cognitive fabric where multiple AI agents can:

- **Remember** — Store and retrieve structured knowledge across sessions
- **Share** — Read what other agents have discovered without direct messaging
- **Coordinate** — Signal discoveries and needs through pheromone-based stigmergy
- **Learn** — Automatically consolidate episodic experiences into lasting knowledge

Unlike traditional databases, Akasha is purpose-built for how AI agents think:
- **Hierarchical paths** instead of tables — `memory/working/agent-01/task`
- **Time-aware** — Records have TTLs, pheromones evaporate naturally
- **Bio-inspired** — Memory layers mirror human cognition (working → episodic → semantic)

---

## Key Concepts

### Memory Layers

| Layer | Purpose | Analogy | Lifecycle |
|-------|---------|---------|-----------|
| **Working** | Current task state | Your desk | Expires (TTL) |
| **Episodic** | Events & experiences | Your diary | Consolidates over time |
| **Semantic** | Distilled knowledge | Your textbooks | Permanent |
| **Procedural** | How-to instructions | Your muscle memory | Permanent |

### Stigmergy

Agents don't talk to each other directly. Instead, they leave **pheromone signals** on trails in the shared environment:

```
Agent A discovers a vulnerability
  → deposits pheromone on trail "security/alerts" (intensity: 0.9)

Agent B checks trail "security/**" before starting work
  → finds Agent A's signal, adjusts its priorities

Over time, the pheromone fades (half-life: 1 hour)
  → signal naturally loses priority as it ages
```

### Nidra (Consolidation Engine)

The Nidra engine runs in the background and automatically:
1. Scans episodic memories for patterns
2. Groups related experiences by topic
3. Distills them into semantic knowledge
4. Prunes old, consolidated episodes

This mimics how the human brain consolidates memories during sleep.

---

## Installation

### Option A: Docker Compose (Recommended)

**Single node (development):**

```bash
# 1. Clone the repository
git clone https://github.com/ocuil/akasha-public.git
cd akasha-public

# 2. Start with Docker Compose
docker compose up -d

# 3. Verify
curl -sk https://localhost:7777/api/v1/health
```

**3-node cluster (production):**

```bash
# 1. Create deployment directory
mkdir akasha-cluster && cd akasha-cluster

# 2. Generate license and identity
akasha-license keygen -o .
akasha-license fingerprint --cluster-id my-cluster
akasha-license issue \
  --customer "My Org" \
  --tier enterprise \
  --private-key ./akasha.key \
  --output ./license.json \
  --cluster-id my-cluster \
  --max-nodes 5 \
  --days 365

# 3. Use the deploy/cluster/ templates
cp ../deploy/cluster/docker-compose.yml .
cp ../deploy/cluster/node-*.toml .

# 4. Start the cluster
docker compose up -d
```

### Option B: Binary

```bash
# Build from source
cargo build --release --bin akasha

# Run with config
./target/release/akasha /path/to/akasha.toml
```

### Option C: Kubernetes (Helm)

```bash
helm repo add akasha https://ocuil.github.io/akasha-charts
helm install akasha akasha/akasha-cluster \
  --set replicas=3 \
  --set license.secret=akasha-license
```

---

## Quick Start

### 1. Get authenticated

```bash
# Default credentials (change immediately!)
TOKEN=$(curl -sk -X POST https://localhost:7777/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "akasha", "password": "akasha"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

echo "Token: ${TOKEN:0:20}..."
```

### 2. Store a memory

```bash
curl -sk -X POST https://localhost:7777/api/v1/records/memory/semantic/greetings/hello \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": {"message": "Hello from Akasha!", "language": "en"}}'
```

### 3. Read it back

```bash
curl -sk https://localhost:7777/api/v1/records/memory/semantic/greetings/hello \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Query with patterns

```bash
curl -sk "https://localhost:7777/api/v1/query?pattern=memory/semantic/**" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Deposit a pheromone

```bash
curl -sk -X POST https://localhost:7777/api/v1/pheromones/getting-started \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signal_type": "discovery",
    "message": "Successfully connected to Akasha!",
    "intensity": 0.8,
    "half_life_secs": 3600
  }'
```

### 6. Open the Dashboard

Navigate to `https://localhost:7777/dashboard/` and login with your credentials.

---

## Memory Architecture

### Path Structure

All data in Akasha is addressed by a **hierarchical path**, similar to a filesystem:

```
namespace/category/subcategory/record-id
```

**Recommended structure:**

```
memory/
├── working/<agent-id>/                 ← Agent's current scratchpad
│   ├── current-task                    ← What the agent is doing now
│   ├── context                         ← Relevant context for the task
│   └── scratchpad                      ← Temporary calculations
├── episodic/<domain>/                  ← Events and experiences
│   ├── <event-id>                      ← A specific event
│   └── <interaction-id>                ← A specific interaction
├── semantic/<domain>/                  ← Distilled knowledge
│   ├── <concept>                       ← A learned concept
│   └── <insight>                       ← A derived insight
└── procedural/<domain>/                ← How-to instructions
    ├── <procedure>                     ← Step-by-step procedure
    └── <recipe>                        ← Reusable pattern

research/
├── <topic>/<finding-id>                ← Research findings

config/
├── <service>/<setting>                 ← Shared configuration
```

### Record Format

Each record has:

```json
{
  "path": "memory/semantic/math/pythagorean",
  "value": {
    "theorem": "a² + b² = c²",
    "domain": "geometry",
    "confidence": 0.99
  },
  "content_type": "application/json",
  "created_at": "2026-04-07T10:00:00Z",
  "updated_at": "2026-04-07T10:00:00Z",
  "ttl_secs": null,
  "version": 1
}
```

### TTL (Time-To-Live)

Set `ttl_secs` when writing to auto-expire records:

```bash
# This record will disappear after 1 hour
curl -sk -X POST "$AKASHA_URL/api/v1/records/memory/working/agent-01/temp" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": {"note": "temporary"}, "ttl_secs": 3600}'
```

---

## Stigmergy & Coordination

### How It Works

Stigmergy is **indirect coordination through the environment**. Instead of agents sending messages to each other, they leave signals (pheromones) that others can detect:

```
┌─────────┐    deposit     ┌──────────────┐    read      ┌─────────┐
│ Agent A  │──────────────▶│   Akasha     │◀────────────│ Agent B  │
│(finds X) │               │ trail: "X"   │              │(needs X) │
└─────────┘               │ intensity:0.9│              └─────────┘
                           │ half-life:1h │
                           └──────────────┘
                                  │
                                  ▼ (after 1 hour)
                           ┌──────────────┐
                           │ intensity:0.45│  ← natural decay
                           └──────────────┘
```

### Signal Types

| Type | Use Case | Example |
|------|----------|---------|
| `discovery` | Found something valuable | "New API endpoint documented" |
| `warning` | Something needs attention | "Rate limit approaching" |
| `request` | Need help or input | "Need domain expert review" |
| `progress` | Reporting advancement | "Analysis 75% complete" |
| `completion` | Task finished | "Report generated, saved at..." |

### Intensity Guidelines

| Intensity | Meaning |
|-----------|---------|
| 0.1 - 0.3 | Informational, low priority |
| 0.4 - 0.6 | Normal importance |
| 0.7 - 0.8 | High priority |
| 0.9 - 1.0 | Critical, immediate attention |

### Half-Life Guidelines

| Duration | Use Case |
|----------|----------|
| 300s (5 min) | Real-time coordination |
| 3600s (1h) | Active task signals |
| 21600s (6h) | Work session signals |
| 86400s (24h) | Daily reports |

---

## Nidra — Memory Consolidation

Nidra is Akasha's built-in consolidation engine that mimics human memory consolidation:

### How It Works

1. **Sweep** (every 5 min by default): Scans episodic memories
2. **Group**: Clusters related episodes by topic/domain
3. **Consolidate** (every 12 sweeps): Distills patterns into semantic memory
4. **Prune**: Removes consolidated episodes to save space

### Configuration

```toml
[nidra]
enabled = true
sweep_interval_secs = 300          # How often to scan
consolidation_every_n_sweeps = 12  # Consolidate every 12 sweeps (1 hour)
```

### LLM-Enhanced Consolidation (Enterprise)

With an LLM provider configured, Nidra can produce richer semantic summaries:

```toml
[llm]
enabled = true
provider = "ollama"
endpoint = "http://localhost:11434/api/generate"
model = "llama3:8b"
```

Without LLM, Nidra uses rule-based consolidation (frequency counting, recency weighting).

---

## Configuring Agents

### Step 1: Create an API Key

In the Dashboard → Administration → API Keys → **+ New Key**:
- **Name**: `my-agent` (descriptive name)
- **Namespaces**: `**` (all) or `memory/working/my-agent/**` (restricted)
- **Role**: `agent`

Click **Create** and **copy the key** (it's shown only once).

### Step 2: Set Environment Variables

```bash
export AKASHA_URL="https://your-akasha-host:7777"
export AKASHA_TOKEN="ak_my-agent_xxxxxxxxxxxx"
```

### Step 3: Install the SDK

**Python:**
```bash
pip install akasha-client
```

**Node.js:**
```bash
npm install akasha-sdk
```

### Step 4: Connect

```python
from akasha import AkashaClient

client = AkashaClient(
    url=os.environ["AKASHA_URL"],
    token=os.environ["AKASHA_TOKEN"],
    verify_ssl=False  # Only for self-signed TLS
)

# Verify connection
health = client.health()
print(f"Connected to Akasha v{health['version']}")
```

---

## System Prompts for Agents

### Minimal System Prompt

Add this to any LLM agent's system prompt to enable Akasha integration:

```
You have access to Akasha, a shared cognitive memory system.

To STORE knowledge:
  POST {AKASHA_URL}/api/v1/records/<path>
  Body: {"value": <json>, "ttl_secs": <optional>}

To READ knowledge:
  GET {AKASHA_URL}/api/v1/records/<path>

To SEARCH knowledge:
  GET {AKASHA_URL}/api/v1/query?pattern=<glob>

Use paths like: memory/working/<your-id>/task, memory/semantic/<topic>/<id>
Always include: Authorization: Bearer {AKASHA_TOKEN}
```

### Full System Prompt (Recommended)

```
## Shared Memory System (Akasha)

You are connected to Akasha, a shared cognitive fabric. Other agents also 
have access. Use it to persist your work and discover what others have found.

### Memory Layers
- `memory/working/<your-agent-id>/<key>` — Your scratchpad (use TTL)
- `memory/episodic/<domain>/<event-id>` — Log events and interactions
- `memory/semantic/<domain>/<concept>` — Store confirmed knowledge
- `memory/procedural/<domain>/<procedure>` — Store how-to procedures

### Coordination (Stigmergy)
Leave pheromone signals when you discover something important:
  POST /api/v1/pheromones/<trail>
  Body: {"signal_type": "discovery", "message": "...", "intensity": 0.8}

Check for signals before starting work to avoid duplication:
  GET /api/v1/pheromones/<trail-pattern>

### Rules
1. Always store important findings in semantic memory
2. Use working memory for temporary state (set ttl_secs)
3. Check existing knowledge before creating duplicates
4. Signal important discoveries via pheromones
5. You don't need to know about other agents — just read and write to the fabric

### API
- Base URL: {AKASHA_URL}
- Auth: Authorization: Bearer {AKASHA_TOKEN}
- All requests use JSON, TLS (may need verify=False for self-signed)
```

### Domain-Specific System Prompt (Research Agent)

```
## Memory & Knowledge Management

You are a research agent with access to Akasha, a shared knowledge base.

### When you DISCOVER something:
1. Store it: POST /api/v1/records/research/<topic>/<finding-id>
2. Signal it: POST /api/v1/pheromones/research/<topic>
   with signal_type: "discovery" and intensity proportional to importance

### When you START a task:
1. Check what's known: GET /api/v1/query?pattern=research/<topic>/**
2. Check signals: GET /api/v1/pheromones/research/<topic>
3. Store your work state: POST /api/v1/records/memory/working/{agent_id}/task

### When you FINISH:
1. Store conclusions in semantic memory:
   POST /api/v1/records/memory/semantic/<topic>/<conclusion-id>
2. Signal completion: POST /api/v1/pheromones/research/<topic>
   with signal_type: "completion"
```

---

## Dashboard

Access the web dashboard at `https://<host>:<port>/dashboard/`

### Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | Overview: record count, cluster health, memory stats |
| **Explorer** | Browse and search all records with glob patterns |
| **Administration** | Manage users, API keys, change password |

### First Login

1. Navigate to `https://localhost:7777/dashboard/`
2. Login: `akasha` / `akasha`
3. **Immediately change the password** (click your username in the sidebar)
4. Create API keys for your agents

---

## Security & Authentication

### Authentication Methods

| Method | Header | Use Case |
|--------|--------|----------|
| JWT Token | `Authorization: Bearer eyJ...` | Interactive sessions, dashboard |
| API Key | `Authorization: Bearer ak_xxx` | Agents, scripts, automation |

### Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access: users, keys, records, cluster |
| `operator` | Read/write records, deploy agents |
| `readonly` | Read-only access to records |
| `agent` | Read/write records within assigned namespaces |

### Namespace Restrictions

API keys can be restricted to specific path patterns:
- `**` — All paths (unrestricted)
- `memory/working/my-agent/**` — Only this agent's working memory
- `research/**, memory/semantic/**` — Multiple patterns

### TLS

Akasha auto-generates TLS certificates on first boot. For production:
- Replace with CA-signed certificates
- Set `cert_path`, `key_path`, `ca_path` in `[tls]` config

---

## Cluster Operations

### Configuration (akasha.toml)

```toml
# Basic server config
[server]
grpc_addr = "0.0.0.0:50051"
http_addr = "0.0.0.0:7777"
name = "my-akasha-node"

# Persistence (RocksDB)
[persistence]
enabled = true
data_dir = "/data"

# Cluster (Enterprise only)
[cluster]
enabled = true
node_id = "node-01"
bind_addr = "0.0.0.0:7946"
advertise_addr = "node-01.example.com:7946"
seeds = ["node-01:7946", "node-02:7946", "node-03:7946"]
cluster_id = "production"

# Authentication
[auth]
enabled = true
jwt_secret = "shared-secret-across-all-nodes"  # MUST be same on all nodes!

# Nidra consolidation
[nidra]
enabled = true
sweep_interval_secs = 300
consolidation_every_n_sweeps = 12

# TLS
[tls]
enabled = true
```

### Important: Shared JWT Secret

When running a cluster behind a load balancer, **all nodes must share the same `jwt_secret`**. Otherwise, tokens issued by one node will be rejected by others.

### Load Balancer

Use Nginx with `least_conn` strategy for optimal distribution:

```nginx
stream {
    upstream akasha_cluster {
        least_conn;
        server node-01:7777;
        server node-02:7777;
        server node-03:7777;
    }
    server {
        listen 443;
        proxy_pass akasha_cluster;
    }
}
```

---

## SDK Reference

### Python SDK

Install:

```bash
pip install akasha-client
# Or from source:
pip install git+https://github.com/ocuil/akasha-public.git#subdirectory=sdks/python
```

#### gRPC Client (recommended for performance)

```python
from akasha import AkashaClient

with AkashaClient("localhost:50051") as client:
    # Write with TTL and tags
    client.put(
        "sensors/temperature/lab-01",
        {"celsius": 22.5, "humidity": 0.65},
        ttl_seconds=300,
        tags={"type": "sensor", "location": "lab"},
        source="sensor-collector",
    )

    # Read
    record = client.get("sensors/temperature/lab-01")
    print(record.value)    # {"celsius": 22.5, ...}
    print(record.version)  # monotonic version counter
    print(record.tags)     # {"type": "sensor", ...}

    # Query with glob patterns
    all_sensors = client.query("sensors/*/lab-*")
    all_agents = client.query("agents/**")  # recursive

    # Delete
    client.delete("sensors/temperature/lab-01")
```

#### Memory Layers API

```python
from akasha import AkashaClient, MemoryLayer

with AkashaClient("localhost:50051") as client:
    # Working Memory — scratchpad (auto-expires)
    client.write_memory(MemoryLayer.WORKING, "my-agent", "task",
        {"objective": "analyze-report", "step": 3})

    # Episodic Memory — what happened
    client.write_memory(MemoryLayer.EPISODIC, "security", "scan-001",
        {"outcome": "clean", "duration_ms": 4520})

    # Semantic Memory — distilled knowledge
    client.write_memory(MemoryLayer.SEMANTIC, "patterns", "batch-size",
        {"insight": "Batch >10K is 3x faster", "confidence": 0.87})

    # Read specific memory
    ctx = client.read_memory(MemoryLayer.WORKING, "my-agent", "task")
```

#### Stigmergy (Pheromones)

```python
from akasha import AkashaClient, SignalType

with AkashaClient("localhost:50051") as client:
    # Deposit
    result = client.deposit_pheromone(
        trail="research/security",
        signal_type=SignalType.DISCOVERY,
        emitter="agent-alpha",
        intensity=0.9,
        half_life_secs=3600,
        payload={"finding": "SQL injection in /api/users"},
    )

    # Sense
    trails = client.sense_pheromones("research/*")
    for trail in trails:
        print(f"  {trail['trail']}: {trail['current_intensity']:.2f}")

    # Reinforce (intensities sum)
    client.reinforce_pheromone("research/security", 0.5, emitter="agent-beta")
```

#### Async Client

```python
import asyncio
from akasha import AsyncAkashaClient

async def main():
    async with AsyncAkashaClient("localhost:50051") as client:
        await client.put("agents/async/state", {"status": "running"})
        record = await client.get("agents/async/state")
        print(record.value)

asyncio.run(main())
```

#### HTTP Client

```python
from akasha import AkashaHttpClient

client = AkashaHttpClient("https://localhost:7777", verify_ssl=False)
client.login("akasha", "akasha")
# Or with API key:
# client = AkashaHttpClient("https://...", api_key="ak_xxx")

client.put("agents/script/state", {"status": "running"})
record = client.get("agents/script/state")
```

#### Real-Time Subscriptions

```python
# Blocking iterator — use in a dedicated thread
for event in client.subscribe("agents/**"):
    print(f"[{event.kind}] {event.path}")
    if event.record:
        print(f"  Value: {event.record.value}")
```

### Node.js SDK

Install:

```bash
npm install @akasha/client
```

```javascript
const { AkashaClient } = require('@akasha/client');

const client = new AkashaClient({ address: 'localhost:50051' });

await client.put('memory/semantic/math/pi', { value: 3.14159 });
const data = await client.get('memory/semantic/math/pi');
const results = await client.query('memory/semantic/**');
```

---

## Complete REST API Reference

All endpoints use `https://<host>:<port>` with JSON. Auth header: `Authorization: Bearer <token>`.

### Health & Monitoring (no auth required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Full health status (version, records, cluster) |
| `GET` | `/api/v1/health/live` | Liveness probe (returns 200 if alive) |
| `GET` | `/api/v1/health/ready` | Readiness probe (returns 200 if ready to serve) |
| `GET` | `/metrics` | Prometheus-format metrics |

### Records (CRUD)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/records/*path` | Read a record by path |
| `POST` | `/api/v1/records/*path` | Write/update a record (body: `{"value": {...}, "ttl_secs": N}`) |
| `DELETE` | `/api/v1/records/*path` | Delete a record |
| `GET` | `/api/v1/query?pattern=<glob>` | Query records matching glob pattern |
| `GET` | `/api/v1/tree` | Tree snapshot of all paths |

### Pheromones (Stigmergy)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/pheromones` | List all active pheromone trails |
| `POST` | `/api/v1/pheromones` | Deposit a pheromone signal |

### Memory & Consolidation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/memory/layers` | Memory layer statistics |
| `GET` | `/api/v1/nidra/status` | Nidra consolidation engine status |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/agents` | List registered agents |

### Cluster (Enterprise)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/cluster/status` | Cluster status overview |
| `GET` | `/api/v1/cluster/nodes` | List all cluster nodes |
| `GET` | `/api/v1/cluster/sync` | Sync status between nodes |
| `GET` | `/api/v1/cluster/raft` | Raft consensus status |
| `GET` | `/api/v1/cluster/upgrade` | Upgrade mode status |
| `POST` | `/api/v1/cluster/upgrade` | Enable upgrade mode |
| `DELETE` | `/api/v1/cluster/upgrade` | Disable upgrade mode |

### License

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/license/fingerprint` | Get cluster fingerprint (for license binding) |
| `GET` | `/api/v1/license/status` | Current license details |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | Login (body: `{"username":"...","password":"..."}`) → JWT |
| `GET` | `/api/v1/auth/status` | Auth system status (public) |
| `GET` | `/api/v1/auth/me` | Current user info |
| `POST` | `/api/v1/auth/change-password` | Change password |

### Administration (admin role required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/users` | List all users |
| `POST` | `/api/v1/admin/users` | Create user |
| `PUT` | `/api/v1/admin/users/:username` | Update user |
| `DELETE` | `/api/v1/admin/users/:username` | Delete user |
| `GET` | `/api/v1/admin/keys` | List API keys |
| `POST` | `/api/v1/admin/keys` | Create API key |
| `DELETE` | `/api/v1/admin/keys/:id` | Revoke API key |
| `GET` | `/api/v1/admin/auth-status` | Auth system details |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard` | Web dashboard SPA |

---

## Troubleshooting

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `401 Unauthorized` | Token expired or wrong | Re-login or check API key |
| `403 Forbidden` | Insufficient role/namespace | Check key permissions |
| Cluster shows 1 node | Nodes can't gossip | Verify `seeds`, `advertise_addr`, network |
| JWT works on 1 node only | Different `jwt_secret` | Set same `jwt_secret` in all node configs |
| License error | Fingerprint mismatch | Check `cluster.identity` matches license |
| Dashboard blank | Browser cache | Hard refresh (Ctrl+Shift+R) |
| SDK install fails | Build system issue | Use `hatchling`: check `pyproject.toml` |

### Checking Logs

```bash
# Docker Compose
docker logs akasha-01 --tail 50 -f

# Look for specific issues
docker logs akasha-01 2>&1 | grep -i "error\|warn\|license\|cluster"
```

### Verifying Cluster Health

```bash
# Quick check all nodes
for port in 7771 7772 7773; do
  echo -n "Node $port: "
  curl -sk https://localhost:$port/api/v1/health | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'], d.get('cluster',{}).get('peers_alive','?'))"
done
```

---

## FAQ

### Q: How is Akasha different from Redis/Memcached?

Akasha is designed for AI agent cognition, not generic caching:
- **Hierarchical paths** instead of flat keys
- **Memory layers** (working/episodic/semantic/procedural)
- **Automatic consolidation** (Nidra engine)
- **Stigmergy** for agent coordination
- **Built-in auth** with agent roles

### Q: Can agents on different machines share memory?

Yes. Point all agents to the same Akasha endpoint. Use a load balancer for clusters.

### Q: What happens if a node goes down?

In a 3-node cluster, the remaining 2 nodes continue serving. Data replicates via the SWIM gossip protocol. When the node comes back, it automatically re-syncs.

### Q: How much data can Akasha store?

Community: 10,000 records. Enterprise: unlimited. Data is stored in RocksDB which can handle millions of records efficiently.

### Q: Do I need an LLM for Nidra consolidation?

No. Nidra uses rule-based consolidation by default (frequency counting, recency, co-occurrence). LLM integration is optional for richer semantic summaries.

### Q: Can I use Akasha with Claude/GPT/Gemini?

Yes. Any LLM that can make HTTP requests can use Akasha. Add the system prompt from the [System Prompts](#system-prompts-for-agents) section and provide the API endpoint and token.

### Q: What are Agent Skills?

Akasha ships with skills following the [agentskills.io](https://agentskills.io) open standard — a format supported by Claude Code, Gemini, and other agentic products. See the [Agent Skills](#agent-skills) section below.

### Q: Should I use gRPC or HTTP?

- **gRPC** (port 50051): Best for performance-critical agents, streaming subscriptions, and production workloads. Requires proto compilation.
- **HTTP** (port 7777): Best for scripts, quick tests, REST-based agents, and when you can't install gRPC dependencies. Also serves the Dashboard.

### Q: How is Akasha different from Mem0 or Letta?

| Feature | Akasha | Mem0 | Letta |
|---------|--------|------|-------|
| Multi-agent coordination | ✅ Stigmergy | ❌ | ❌ |
| Memory consolidation | ✅ Nidra (auto) | ❌ | ✅ (manual) |
| Clustering | ✅ SWIM + Raft | ❌ | ❌ |
| Protocol | gRPC + HTTP | HTTP | HTTP |
| Self-hosted | ✅ Docker/Binary | ✅ Cloud/Docker | ✅ Cloud/Docker |
| Real-time events | ✅ gRPC streaming | ❌ | ❌ |

### Q: How do I generate a license?

Use the `akasha-license` CLI tool:

```bash
# 1. Generate signing keypair
akasha-license keygen -o .

# 2. Get cluster fingerprint
akasha-license fingerprint --cluster-id my-cluster

# 3. Issue license
akasha-license issue \
  --customer "My Org" \
  --tier enterprise \
  --private-key ./akasha.key \
  --output ./license.json \
  --cluster-id my-cluster \
  --max-nodes 5 \
  --days 365
```

---

## Agent Skills

Akasha includes pre-built skills following the [agentskills.io](https://agentskills.io) open standard. These can be loaded by compatible agent products (Claude Code, Gemini, etc.) to give agents structured knowledge about how to use Akasha.

### Available Skills

| Skill | Directory | Purpose |
|-------|-----------|---------|
| **akasha-memory** | `skills/akasha-memory/` | Store, retrieve, and query shared memory records |
| **akasha-stigmergy** | `skills/akasha-stigmergy/` | Pheromone-based agent coordination |
| **akasha-cluster** | `skills/akasha-cluster/` | Cluster management and admin operations |
| **akasha-nidra** | `skills/akasha-nidra/` | Monitor the Nidra consolidation engine |
| **akasha-agent-onboarding** | `skills/akasha-agent-onboarding/` | Step-by-step new agent setup |

### Using Skills

Each skill is a directory with a `SKILL.md` file containing:
- **Frontmatter** (YAML): name, description, metadata
- **Instructions**: Step-by-step operations with curl/SDK examples
- **References**: Additional docs in the `references/` folder

To use a skill, copy the `skills/` directory to your project or point your agent tool at the skill directory:

```bash
# Example: Install Akasha skills for Claude Code
cp -r skills/ /path/to/your/project/.agent/skills/
```

The agent will automatically discover the skills based on the description in the frontmatter and load the instructions when relevant.

---

*Akasha v1.0.4 — © 2026 Ocuil. Licensed under ASL-1.0.*

