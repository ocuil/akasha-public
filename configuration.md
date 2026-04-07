# Configuration Reference

Akasha is configured via a single TOML file, typically `akasha.toml`. Every parameter is documented below with its default value and purpose.

## `[server]` — Core Server

| Parameter | Default | Description |
|-----------|---------|-------------|
| `http_addr` | `"0.0.0.0:7777"` | HTTP/HTTPS bind address (REST + WebSocket + Dashboard) |
| `grpc_addr` | `"0.0.0.0:50051"` | gRPC bind address (used by SDKs) |
| `name` | `"akasha"` | Server instance name (for logging) |

```toml
[server]
http_addr = "0.0.0.0:7777"
grpc_addr = "0.0.0.0:50051"
name = "akasha"
```

## `[persistence]` — Storage Backend

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `true` | Enable RocksDB persistence. If `false`, data is in-memory only |
| `data_dir` | `"./akasha-data"` | Directory for RocksDB files, TLS certs, and WAL |

```toml
[persistence]
enabled = true
data_dir = "./akasha-data"
```

> **Note**: The `data_dir` is created automatically on first boot. In Docker, mount this as a volume for data persistence across restarts.

## `[auth]` — Authentication & Authorization

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `false` | Enable JWT + API key authentication. **Set to `true` in production** |
| `jwt_secret` | `""` (auto) | HMAC-SHA256 signing key. Auto-generated if empty |
| `jwt_lifetime_hours` | `24` | JWT session duration in hours |

```toml
[auth]
enabled = true
# jwt_secret = "your-secret-key"  # Leave empty for auto-generation
# jwt_lifetime_hours = 24
```

### How auth works

1. **First boot**: Akasha creates a default user `akasha` with password `akasha`
2. **Login**: `POST /api/v1/auth/login` with `{"username":"akasha","password":"akasha"}` → returns JWT
3. **All API calls**: Include `Authorization: Bearer <JWT>` header
4. **API keys**: Alternative auth for agents: `Authorization: Bearer ak_xxxx`

### Open endpoints (no auth required)
- `GET /api/v1/health` — Health check
- `GET /api/v1/health/live` — Liveness probe
- `GET /api/v1/health/ready` — Readiness probe
- `POST /api/v1/auth/login` — Login
- `GET /api/v1/auth/status` — Check if auth is enabled
- `GET /dashboard/*` — Dashboard SPA

## `[tls]` — Transport Layer Security

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `true` | Enable HTTPS. Akasha auto-generates self-signed certs on first boot |
| `dns_suffix` | `"sslip.io"` | DNS wildcard service for IP-based hostname resolution |
| `cert_path` | `""` | Path to custom PEM certificate (overrides auto-generation) |
| `key_path` | `""` | Path to custom PEM private key |
| `ca_path` | `""` | Path to CA certificate for mTLS verification |
| `require_client_cert` | `false` | Enable mutual TLS (used for inter-node auth) |

```toml
[tls]
enabled = true
dns_suffix = "sslip.io"
# For production with real certs:
# cert_path = "/etc/ssl/akasha/cert.pem"
# key_path = "/etc/ssl/akasha/key.pem"
```

> **Self-signed certs**: When using auto-generation, clients need `-k` (curl) or to trust the CA at `{data_dir}/tls/ca.pem`.

## `[cluster]` — Distributed Mode

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `false` | Enable clustering. Requires ≥ 3 nodes for HA |
| `node_id` | `"akasha-01"` | **Unique** identifier per node. Must differ for each instance |
| `bind_addr` | `"0.0.0.0:7946"` | SWIM gossip listener (UDP + TCP) |
| `advertise_addr` | (bind_addr) | NAT-aware address advertised to peers |
| `seeds` | `[]` | Bootstrap peer addresses. At least 1 other node required |
| `cluster_id` | `"akasha-default"` | Shared cluster identifier. Must match across all nodes |
| `cluster_key` | `""` | HMAC authentication key for inter-node gossip |

```toml
[cluster]
enabled = true
node_id = "akasha-01"
bind_addr = "0.0.0.0:7946"
advertise_addr = "10.0.1.10:7946"
seeds = ["10.0.1.11:7946", "10.0.1.12:7946"]
cluster_id = "production"
cluster_key = "a-strong-shared-secret"
```

### Cluster sizing

| Nodes | Fault Tolerance | Use Case |
|-------|----------------|----------|
| 1 | None | Development, testing |
| 3 | 1 node failure | Production minimum |
| 5 | 2 node failures | High availability |

## `[nidra]` — Consolidation Engine

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `true` | Enable periodic memory consolidation |
| `sweep_interval_secs` | `300` | Seconds between consolidation sweeps (5 min) |
| `consolidation_every_n_sweeps` | `12` | Deep consolidation every N sweeps (~1 hour) |
| `evaporation_threshold` | `0.01` | Pheromone intensity below which trails evaporate |
| `max_episodic_per_topic` | `100` | Max episodic records per topic before forced consolidation |
| `emit_consolidation_events` | `true` | Emit events when consolidation actions occur |

```toml
[nidra]
enabled = true
sweep_interval_secs = 300
consolidation_every_n_sweeps = 12
evaporation_threshold = 0.01
max_episodic_per_topic = 100
emit_consolidation_events = true
```

## `[ttl]` — Time-To-Live Reaper

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sweep_interval_secs` | `10` | How often expired records are cleaned up |

```toml
[ttl]
sweep_interval_secs = 10
```

## `[elasticsearch]` — Telemetry Forwarder *(Enterprise)*

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `false` | Forward events to Elasticsearch |
| `url` | `"http://localhost:9200"` | Elasticsearch cluster URL |
| `index_prefix` | `"akasha"` | Index name prefix (creates `akasha-events`, etc.) |
| `batch_size` | `1000` | Events per batch |
| `flush_interval_secs` | `5` | Max seconds before flushing partial batch |
| `username` | `""` | ES basic auth username |
| `password` | `""` | ES basic auth password |
| `max_retries` | `3` | Retry attempts per batch |

## `[llm]` — LLM Consolidation Hook *(Enterprise)*

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `false` | Use LLM for semantic consolidation |
| `provider` | `"ollama"` | LLM provider: `"ollama"` or `"openai"` |
| `endpoint` | `"http://localhost:11434/api/generate"` | LLM API endpoint |
| `model` | `"kimi-k2.5:cloud"` | Model name |
| `max_tokens` | `1024` | Max tokens per consolidation request |

## `[telemetry]` — Usage Telemetry

| Parameter | Default | Description |
|-----------|---------|-------------|
| `usage_metrics` | `true` | Send anonymous usage metrics (opt-out by setting `false`) |

## Example: Production 3-Node Cluster

```toml
# Node 1 (node-01.toml)
[server]
http_addr = "0.0.0.0:7777"
grpc_addr = "0.0.0.0:50051"

[persistence]
enabled = true
data_dir = "/app/data"

[auth]
enabled = true

[tls]
enabled = true

[cluster]
enabled = true
node_id = "akasha-01"
bind_addr = "0.0.0.0:7946"
advertise_addr = "akasha-01:7946"
seeds = ["akasha-02:7946", "akasha-03:7946"]
cluster_id = "production"
cluster_key = "my-secure-key"

[nidra]
enabled = true
sweep_interval_secs = 300
```
