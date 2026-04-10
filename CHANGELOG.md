# Changelog

All notable changes to Akasha are documented in this file.

## [1.0.9] — Unreleased

### Added
- **15 HTTP integration tests**: Full coverage for health, CRUD, CAS, query, memory layers, agents, license, and middleware headers (`akasha-server/tests/http_integration.rs`)
- **Server library crate**: `akasha-server` now exposes `lib.rs` for integration testing alongside the binary
- **CI release workflow**: GitHub Actions pipeline builds 4 targets (linux-amd64, linux-arm64, darwin-amd64, darwin-arm64) on tag push (`.github/workflows/release.yml`)
- **Docker Hub distribution**: Official image at `alejandrosl/akasha` with full overview page
- **Python SDK on PyPI**: `pip install akasha-client` — now publicly available at [pypi.org/project/akasha-client](https://pypi.org/project/akasha-client/)
- **SDK: CAS support**: New `put_cas()` method with `CasConflictError` exception for optimistic concurrency
- **SDK: Authentication**: API key (`X-API-Key`) and JWT (`Bearer`) token support
- **SDK: TLS toggle**: `verify_ssl=False` for self-signed certificate environments
- **LangGraph integration example**: 4-agent pipeline (Researcher → Analyst → Writer → Critic) sharing knowledge through Akasha (`examples/langgraph-memory/`)
- **One-line installer**: `curl -fsSL https://... | bash` — auto-detects OS/arch (`deploy/get-akasha.sh`)
- **Node.js SDK on npm**: `npm install akasha-memory` — TypeScript, gRPC + HTTP, CAS, auth, WebSocket subscriptions
- **VISION.md**: C-Level executive overview (English + Spanish)
- Docker Hub badge + PyPI badge + npm badge in README

### Changed
- Docker image references updated from `ghcr.io/ocuil/akasha` to `alejandrosl/akasha` (README, installation docs, Helm values)
- Python SDK install changed from `pip install -e sdks/python` to `pip install akasha-client`
- Node.js SDK import changed from `@akasha/client` (local) to `akasha-memory` (npm)

### Fixed
- **Python SDK v1.0.9**: `verify_ssl=False` now correctly propagated to `HTTPTransport` (was being ignored by httpx)
- **Python Async Client**: Added `api_key`, `token`, `verify_ssl` params (parity with sync client)
- Unused import warning in `telemetry.rs` (`info` removed after downgrade to `debug`)

### Metrics
- Total tests: **163** (145 unit + 15 integration + 3 doc tests), 0 failures

## [1.0.8] — 2026-04-09

### Added
- **CAS (Compare-And-Swap)**: Optimistic concurrency control via `If-Match` header on PUT. Returns `409 Conflict` with current record on version mismatch. Fully backwards-compatible — only activates when client sends `If-Match`.
- **ETag header**: GET responses include `ETag` with the record version for client-side caching and CAS workflows.
- **Graceful shutdown improvements**: Node transitions `Alive → Leaving → Left` during shutdown. Pending CRDT deltas are flushed to peers before Leave broadcast.
- `CasError` enum in `akasha-core::store` for typed CAS error handling.
- `NodeStatus::Leaving` variant for pre-shutdown signaling.
- `ClusterMembership::set_local_status()` method.

### Changed
- Telemetry initialization log downgraded from INFO to DEBUG (endpoint details no longer visible in production logs).
- PUT error responses now return structured JSON bodies (`{"error": "..."}`) instead of plain text strings.

## [1.0.7] — 2026-04-08

### Fixed
- Gossip probe round-robin: was always probing same peer (even sequence % 2 = 0)
- Health endpoint: `peers_total` no longer counts dead/phantom nodes from previous sessions
- Sync bridge log noise: downgraded `delta batch` message from INFO to debug
- RocksDB: LOG.old files no longer accumulate (limited to 3 retained, WAL recycled)

### Changed
- Nidra `/api/v1/nidra/status`: returns structured JSON (cycle_count, leader, is_leader, last_cycle_at) instead of raw integer

### Added
- **Explorer redesign**: Professional tree view with collapsible folders, color-coded namespaces, path search filter, namespace filter chips, memory layer summary, and syntax-highlighted JSON inspector with metadata panel
- **Explorer CRUD**: Inline JSON edit, single record delete with confirmation, namespace purge with confirmation, success/error feedback toasts
- `THIRD_PARTY_LICENSES`: Attribution for RocksDB (Apache-2.0), DashMap, Tokio, Axum, Tonic, rmp-serde, React

## [1.0.6] - 2026-04-08

### Fixed
- Gossip MTU: SystemMetrics excluded from gossip packets (was 2KB+ UDP)
- Dashboard heartbeat: all nodes show green regardless of serving node
- Dashboard sidebar: active page highlights correctly (useLocation)
- Dashboard icons: restored emoji icons rendering across browsers
- Anti-entropy and CRDT sync log spam downgraded to debug level

### Added
- Per-node metrics via gossip: cpu_pct/mem_pct piggybacked on PingAck
- Background metrics refresh every 5s per node
- CSP meta tag in dashboard
- Docker log rotation (30MB cap per container)

### Changed
- UDP receive buffer increased to 8KB for internal networks
- MTU warning downgraded to debug (fragmentation OK on Docker bridges)

## [1.0.5] — 2026-04-08

### 📊 Dashboard: System Metrics & Node Monitoring

- **Cluster-aggregated resource gauges**: CPU (avg), Memory, and Disk usage across all nodes
- **Per-node CPU/Memory bars**: Mini progress bars inside each NodeCard
- **Heartbeat indicator**: Replaced confusing "Last Seen" with color-coded heartbeat (green/amber/red)
- **Responding node indicator**: "⚡ Connected to: akasha-XX" shown in dashboard header
- **Alphabetical node sorting**: Nodes always rendered in consistent order
- **Nidra last cycle**: Shows relative time ("3m ago") instead of raw timestamp

### 🔧 Backend: System Metrics API

- **`GET /api/v1/system/metrics`**: New endpoint returning CPU, memory, and disk for the responding node
- **`X-Akasha-Node` response header**: Every API response includes the node ID that served it
- **`SystemMetrics` in `NodeInfo`**: CPU/memory/disk metrics carried via gossip to all nodes
- **`sysinfo` crate**: Cross-platform system metrics collection (CPU, memory, disk)

### 🛡️ WebSocket Stability

- **TLS close_notify suppression**: Downgraded from `WARN` to `debug!` — eliminates log spam from agent reconnections
- **WebSocket error noise reduction**: All WS disconnect/error logs moved to debug level

### ⚙️ Infrastructure (Nginx LB)

- **`worker_connections`**: 1024 → 4096 (prevents connection exhaustion under heavy agent load)
- **`proxy_timeout`**: 30s → 86400s (24h — WebSocket connections no longer killed by LB timeout)
- **TCP keepalive**: Enabled for dead connection detection

## [1.0.4] — 2026-04-07

### 🔐 UX Hardening & Agent Interoperability

- **Custom modals**: Replaced native browser `confirm()` with in-app modals
- **Error pages**: Browser-aware 401/403/404 HTML responses
- **Agent Skills**: 5 standardized skills (agentskills.io format)
- **User Guide**: ~1000 lines covering installation, API, memory architecture
- **Agent Integration Guide**: INTEGRATIONS.md with Pi, LangGraph, CrewAI, AutoGen + 6 more frameworks

## [1.0.3] — 2026-04-07

### 🔐 License Expiration Watchdog

- **Periodic expiry check**: Background watchdog verifies license every hour
- **Warning thresholds**: Logs warnings at 30, 7, and 1 day before expiration
- **Grace period**: 48h read-only mode after expiration — reads work, writes return 503
- **Hard shutdown**: Server exits after grace period ends
- **Startup check**: Server refuses to start if license is past grace period
- **License status API**: `GET /api/v1/license/status` reports expiry info (for dashboards)
- **CLI info**: `akasha-license info` now shows expiry status with visual indicators

### 🔧 CI/CD Fix

- Fixed `secrets` context in GitHub Actions step-level `if` conditions (was breaking all CI runs)
- All releases (v1.0.0, v1.0.1, v1.0.2) now published with binaries for linux-amd64, linux-arm64, darwin-arm64

### 📊 Benchmark Suite

- E2E benchmark with real LLM agents on DGX Spark
- Dockerfile now downloads published release binary (no source code exposure)
- Results: 2,237 ops/sec, 0.1% LLM pipeline overhead, zero scaling degradation

## [1.0.2] — 2026-04-06

### 🔄 Cluster Upgrade Mode (Grow & Shrink)

- **Upgrade mode API**: `POST /api/v1/cluster/upgrade` enables temporary node addition
- **Auto-eviction**: Extra nodes are evicted after grace period (default 1h)
- **License-aware**: Upgrade mode temporarily allows max_nodes+1 without license conflict

### 📄 License v2 — Installation-Bound Fingerprinting

- Licenses are now bound to an `installation_id` (generated on first boot)
- `akasha-license fingerprint` CLI for generating cluster fingerprints
- Prevents license reuse across different installations

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
