# REST API Reference

All endpoints are served over HTTPS on the configured `http_addr` (default: `7777`).

When `auth.enabled = true`, all endpoints except those marked **PUBLIC** require an `Authorization: Bearer <token>` header.

## Health & Status

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | PUBLIC | Full health with cluster info |
| GET | `/api/v1/health/live` | PUBLIC | Liveness probe (always 200) |
| GET | `/api/v1/health/ready` | PUBLIC | Readiness probe (503 if no peers) |
| GET | `/api/v1/metrics` | Required | Server metrics + uptime |

### `GET /api/v1/health`
```json
{
  "status": "ok",
  "name": "akasha",
  "version": "1.0.0",
  "records": 42,
  "pending_telemetry": false,
  "cluster": {
    "mode": "clustered",
    "node_id": "akasha-01",
    "role": "leader",
    "peers_alive": 3,
    "peers_total": 3
  }
}
```

### `GET /api/v1/metrics`
```json
{
  "total_records": 42,
  "uptime_seconds": 3600,
  "connected_agents": 3,
  "metrics": {
    "total_writes": 150,
    "total_reads": 800,
    "total_queries": 200
  }
}
```

---

## Records (CRUD)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/records/{path}` | Required | Read a single record |
| POST | `/api/v1/records/{path}` | Required | Create or update a record |
| DELETE | `/api/v1/records/{path}` | Required | Delete a record |
| GET | `/api/v1/query?pattern={glob}` | Required | Query records by glob pattern |
| GET | `/api/v1/tree` | Required | Full tree snapshot |

### `POST /api/v1/records/{path}`

Request:
```json
{
  "value": {"status": "active", "task": "analyze"},
  "ttl_seconds": 3600,
  "content_type": "json",
  "tags": {"agent": "planner", "priority": "high"}
}
```

Response (201 Created / 200 Updated):
```json
{
  "path": "agents/planner/state",
  "value": {"status": "active", "task": "analyze"},
  "version": 1,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "ttl_seconds": 3600.0,
  "tags": {"agent": "planner", "priority": "high"},
  "content_type": "json"
}
```

### `GET /api/v1/query?pattern={glob}&limit={n}`

```bash
curl -sk "https://localhost:7777/api/v1/query?pattern=agents/*/state&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

Glob patterns: `*` matches one level, `**` matches recursively.

---

## Agents

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/agents` | Required | List all registered agents |

Returns agents found under `agents/*/state`:
```json
[
  {
    "agent_id": "planner",
    "path": "agents/planner/state",
    "state": {"status": "active", "last_heartbeat": 1705312800}
  }
]
```

---

## Cognitive Fabric

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/memory/layers` | Required | Memory layer counts |
| GET | `/api/v1/nidra/status` | Required | Last consolidation cycle |
| GET | `/api/v1/pheromones` | Required | List active pheromone trails |
| POST | `/api/v1/pheromones` | Required | Deposit a pheromone trail |

### `GET /api/v1/memory/layers`
```json
{
  "layers": {
    "working": 5,
    "episodic": 12,
    "semantic": 3,
    "procedural": 1
  },
  "total_memory_records": 21
}
```

### `POST /api/v1/pheromones`
```json
{
  "path": "signals/task-complete/analyze-Q3",
  "signal_type": "success",
  "intensity": 0.9,
  "emitter": "planner-agent",
  "metadata": {"result_path": "memory/episodic/planner/Q3"},
  "half_life_secs": 3600
}
```

---

## Cluster

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/cluster/status` | Required | Cluster membership overview |
| GET | `/api/v1/cluster/nodes` | Required | Detailed node list |
| GET | `/api/v1/cluster/sync` | Required | CRDT sync status |
| GET | `/api/v1/cluster/raft` | Required | Raft consensus state |

### `GET /api/v1/cluster/nodes`
```json
{
  "node_count": 3,
  "nodes": [
    {
      "id": "akasha-01",
      "status": "alive",
      "role": "voter",
      "advertise_addr": "akasha-01:7946",
      "version": "1.0.0",
      "last_seen": "2024-01-15T10:05:00Z",
      "joined_at": "2024-01-15T09:00:00Z",
      "incarnation": 0
    }
  ]
}
```

### `GET /api/v1/cluster/raft`
```json
{
  "raft": {
    "role": "leader (gossip, 3 nodes)",
    "term": 1,
    "leader": "akasha-01",
    "commit_index": 0,
    "log_size": 0,
    "nidra_leader": "akasha-01"
  }
}
```

---

## Diagnostics

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/diag/report` | ADMIN | Full diagnostic report with health score |

### `GET /api/v1/diag/report`

Returns a comprehensive cluster health assessment. **Requires admin role.**

Response includes:
- `health_score` (0-100) — weighted aggregate from 8 checks
- `health_signal` — 🟢 (≥80), 🟡 (50-79), 🔴 (<50)
- `topology` — nodes, Raft state, versions
- `consistency` — records, CRDT HLC, pending deltas
- `performance` — CPU/MEM/Disk, R/W/Q counters, uptime
- `memory` — layer distribution (working/episodic/semantic/procedural)
- `security` — encryption, TLS, license, namespace policies
- `nidra` — consolidation engine status
- `findings` — issues with severity (critical/warning/info)
- `markdown` — full human-readable report for export

**Extract Markdown report:**
```bash
curl -sk https://host:7777/api/v1/diag/report \
  -H "Authorization: Bearer $TOKEN" | jq -r .markdown > report.md
```

---

## Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | PUBLIC | Login, returns JWT |
| GET | `/api/v1/auth/status` | PUBLIC | Check if auth enabled |
| GET | `/api/v1/admin/users` | ADMIN | List users |
| POST | `/api/v1/admin/users` | ADMIN | Create user |
| PUT | `/api/v1/admin/users/{username}` | ADMIN | Update user |
| DELETE | `/api/v1/admin/users/{username}` | ADMIN | Delete user |
| GET | `/api/v1/admin/keys` | ADMIN | List API keys |
| POST | `/api/v1/admin/keys` | ADMIN | Create API key |
| DELETE | `/api/v1/admin/keys/{id}` | ADMIN | Revoke API key |

### `POST /api/v1/auth/login`
```json
// Request
{"username": "akasha", "password": "akasha"}

// Response
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "username": "akasha",
  "role": "admin",
  "expires_in": 86400
}
```

### `POST /api/v1/admin/keys`
```json
// Request
{
  "name": "planner-agent",
  "role": "agent",
  "namespaces": ["agents/planner/*", "memory/*"]
}

// Response
{
  "id": "a1b2c3d4-...",
  "name": "planner-agent",
  "key": "ak_xxxxxxxxxxxxxxxxxxxx",
  "role": "agent",
  "namespaces": ["agents/planner/*", "memory/*"]
}
```

---

## WebSocket Events

| Path | Description |
|------|-------------|
| `ws://host:7777/api/v1/ws` | Real-time event stream |

Connect with a WebSocket client:
```javascript
const ws = new WebSocket('wss://localhost:7777/api/v1/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.kind}: ${data.path}`);
};
```

Events are JSON objects:
```json
{
  "kind": "put",
  "path": "agents/planner/state",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

---

## Dashboard

| Path | Description |
|------|-------------|
| `GET /dashboard/` | Web dashboard SPA (embedded in binary) |

No authentication needed to load the SPA. The SPA itself handles login.

---

## Prometheus Metrics

| Path | Description |
|------|-------------|
| `GET /metrics` | Prometheus-format metrics scrape endpoint |

## Error Responses

All errors follow this format:
```json
{
  "error": "Description of what went wrong"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request (invalid path, too many tags, etc.) |
| 401 | Authentication required or token expired |
| 403 | Insufficient permissions or license limit reached |
| 404 | Record or user not found |
| 503 | Service unavailable (cluster not ready) |
