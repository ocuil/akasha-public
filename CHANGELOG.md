# Changelog

All notable changes to Akasha are documented in this file.

## [1.0.6] - 2026-04-08

### Fixed
- Gossip MTU exceeded warning eliminated (SystemMetrics excluded from gossip)
- Dashboard heartbeat green for all nodes regardless of serving node
- Dashboard sidebar active page highlights correctly when navigating
- Dashboard emoji icons render correctly across all browsers
- Anti-entropy and CRDT sync log spam eliminated in production

### Added
- Per-node CPU/MEM metrics propagated via gossip PingAck
- Background system metrics refresh every 5s per node
- Content-Security-Policy meta tag in dashboard
- Docker log rotation (30MB cap per container)
- Round-robin gossip probe for better cluster monitoring

### Changed
- UDP receive buffer increased to 8KB for internal cluster networks

## [1.0.5] - 2026-04-08

### Dashboard: System Metrics and Node Monitoring
- Cluster-aggregated resource gauges: CPU, Memory, Disk
- Per-node CPU/Memory bars in NodeCard
- Heartbeat indicator with color coding
- Responding node indicator in header

### Backend: System Metrics API
- GET /api/v1/system/metrics endpoint
- X-Akasha-Node response header

### WebSocket Stability
- TLS close_notify noise eliminated
- Nginx LB tuning (4096 workers, 24h timeout)

## [1.0.4] — 2026-04-07

### 🔐 UX Hardening & Agent Interoperability

- **Custom modals**: Replaced native browser `confirm()` with in-app modals
- **Error pages**: Browser-aware 401/403/404 HTML responses
- **Agent Skills**: 5 standardized skills (agentskills.io format)
- **User Guide**: Comprehensive installation, API, and memory architecture guide
- **Agent Integration Guide**: INTEGRATIONS.md — connect Pi, LangGraph, CrewAI, and more

## [1.0.0] — 2026-04-06

### 🎉 First Production Release

Akasha 1.0.0 is the first production-ready release of the distributed cognitive memory system for AI agent swarms.

### Core Engine
- **Record Store**: Hierarchical key-value store with glob pattern queries
- **Persistence**: RocksDB with WAL and LZ4 compression
- **TTL Reaper**: Automatic expiration of time-limited records
- **Event System**: WebSocket + gRPC pub/sub for real-time notifications

### Cognitive Fabric
- **4-Layer Memory Hierarchy**: Working → Episodic → Semantic → Procedural
- **Stigmergy (Pheromones)**: Typed signals with half-life decay for indirect agent coordination
- **Nidra Consolidation**: Automated memory promotion with configurable intervals
- **LLM Hook**: Optional LLM-powered semantic consolidation (Ollama/OpenAI)

### Distributed Cluster
- **SWIM Gossip**: Peer discovery and failure detection
- **GossipRaft Consensus**: Leader election for single-writer operations (Nidra)
- **CRDT Replication**: HLC + LWW for conflict-free eventual consistency
- **Anti-Entropy**: Full-state reconciliation after network partitions
- **HMAC Gossip Auth**: Signed inter-node messages with shared cluster key

### Security
- **JWT Authentication**: User/password login with configurable session lifetime
- **API Key Authentication**: Revocable keys for agents with namespace scoping
- **Argon2id Password Hashing**: Per-user salted hashes
- **Auto TLS**: Self-signed certificate generation on first boot
- **mTLS**: Mutual TLS for inter-node gRPC communication

### Server
- **REST API**: 35+ endpoints (CRUD, query, cluster, admin, pheromones, memory)
- **gRPC API**: High-performance proto-based API for SDKs
- **WebSocket**: Real-time event streaming
- **Prometheus**: `/metrics` scrape endpoint
- **Health Probes**: `/health/live` and `/health/ready` for Kubernetes

### Dashboard
- **Cluster Dashboard**: Unified global view with stats, node topology, memory fabric, and health
- **Explorer**: Tabbed browser for Records, Memory, and Pheromones
- **Administration**: User and API key management
- **Profile Modal**: Self-service password change
- **Embedded SPA**: Built into binary via `rust-embed` — zero external dependencies

### SDKs
- **Python SDK**: Sync + async clients for gRPC and HTTP (pip installable)
- **Node.js SDK**: TypeScript-first gRPC and HTTP clients

### Tooling
- **CLI Key Generator**: `akasha-tools api-key` for offline key creation
- **Docker Compose**: Production-ready 3-node cluster config
- **GKE Autopilot**: Kubernetes StatefulSet manifests

### Documentation (`akasha-docs/`)
- Installation guide (standalone, Docker, K8s)
- Configuration reference (all TOML parameters)
- Authentication & security guide
- Python SDK tutorial with examples
- Node.js SDK tutorial with examples
- Agent patterns (6 patterns + anti-patterns)
- Cluster operations (scaling, failover, monitoring)
- REST API reference (all endpoints with examples)
- Dashboard usage guide

### License
- **Akasha Source License 1.0 (ASL-1.0)**: Source-available, non-compete, free for internal use
- **Tiered licensing**: Community (free), Enterprise (paid)
- **Telemetry**: Anonymous heartbeat + opt-out usage metrics
