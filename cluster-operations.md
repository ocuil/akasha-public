# Cluster Operations Guide

## Architecture

Akasha uses a hybrid consensus model:

```
┌─────────────────────────────────────────────┐
│           SWIM Gossip Layer                 │
│  (Peer discovery, failure detection, UDP)   │
│  akasha-01 ←→ akasha-02 ←→ akasha-03       │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│         GossipRaft Consensus                │
│  (Leader election, single-writer Nidra)     │
│  Leader: akasha-01  Voters: 02, 03          │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│         CRDT Replication (HLC + LWW)        │
│  (Eventually consistent, no conflicts)      │
│  Delta sync via gossip + anti-entropy       │
└─────────────────────────────────────────────┘
```

## Adding a Node

1. Configure the new node:
```toml
[cluster]
enabled = true
node_id = "akasha-04"
bind_addr = "0.0.0.0:7946"
advertise_addr = "10.0.1.14:7946"
seeds = ["10.0.1.10:7946"]  # Only need 1 existing node
cluster_id = "production"
cluster_key = "same-key-as-others"
```

2. Start the node — it auto-joins via SWIM gossip
3. Anti-entropy kicks in and syncs all existing data to the new node

## Removing a Node

1. Stop the node process (graceful shutdown)
2. The cluster detects the departure via SWIM (within seconds)
3. If the removed node was the leader, a new election happens automatically

## Monitoring

### Health Endpoints

```bash
# Quick cluster overview
curl -sk https://localhost:7771/api/v1/cluster/status

# Detailed node list
curl -sk https://localhost:7771/api/v1/cluster/nodes

# Raft state (who's leader, term, log)
curl -sk https://localhost:7771/api/v1/cluster/raft

# CRDT sync status (pending deltas)
curl -sk https://localhost:7771/api/v1/cluster/sync
```

### Key Metrics to Watch

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Nodes alive | All nodes alive | 1 node down | <majority down |
| Pending deltas | 0 | 1-10 | >100 (replication lag) |
| Raft term | Stable | Incrementing slowly | Rapidly incrementing (split-brain) |
| Last Nidra cycle | < 2x interval | < 5x interval | Never ran |

### Prometheus

Scrape `/metrics` on any node:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'akasha'
    scheme: https
    tls_config:
      insecure_skip_verify: true
    static_configs:
      - targets:
        - 'akasha-01:7777'
        - 'akasha-02:7777'
        - 'akasha-03:7777'
```

## Failure Scenarios

### Single Node Failure

| What happens | Automatic recovery |
|-------------|-------------------|
| SWIM detects node as "suspect" | Within 5 seconds |
| Node marked as "dead" | After 3 failed probes (~15s) |
| If leader died → new election | Within 10 seconds |
| Anti-entropy syncs data when node returns | Automatic |

**Impact**: Zero data loss. Reads/writes continue on surviving nodes.

### Network Partition

| What happens | Recovery |
|-------------|----------|
| Minority partition loses leader | Cannot elect new leader (no quorum) |
| Majority partition continues normally | All operations work |
| When partition heals | Anti-entropy reconciles all changes |

**Key rule**: Writes require a reachable node. The system is AP (Available + Partition-tolerant) during partitions, with eventual consistency on recovery.

### Full Cluster Restart

1. Start any node — it loads data from local RocksDB
2. Start remaining nodes — they discover via SWIM seeds
3. Leader election happens when majority is alive
4. Anti-entropy ensures all nodes converge

**Data is never lost** — each node persists its full state to RocksDB.

## Scaling Guidelines

| Agents | Writes/sec | Recommended Nodes | CPU/Node | Memory/Node |
|--------|-----------|-------------------|----------|-------------|
| 1-10 | <100 | 1 (standalone) | 0.5 vCPU | 256 MB |
| 10-50 | 100-500 | 3 | 1 vCPU | 512 MB |
| 50-200 | 500-2000 | 3-5 | 2 vCPU | 1 GB |
| 200+ | 2000+ | 5 | 4 vCPU | 2 GB |

### Important Notes

- **Odd numbers only** for cluster size (3, 5, 7) — required for Raft quorum
- **All nodes are equal** — any node can serve reads and writes
- **Reads scale linearly** — add nodes for more read throughput
- **Writes are eventually consistent** — no leader bottleneck for writes
- **Nidra runs on leader only** — consolidation is single-writer

## Backup & Restore

### Backup

```bash
# Option 1: RocksDB checkpoint (consistent snapshot)
docker exec akasha-01 cp -r /app/data /app/backup-$(date +%Y%m%d)

# Option 2: API-based backup (all records as JSON)
curl -sk https://localhost:7771/api/v1/tree \
  -H "Authorization: Bearer $TOKEN" > backup.json
```

### Restore

```bash
# From API backup
cat backup.json | python3 -c "
import json, httpx, sys
data = json.load(sys.stdin)
for path, value in data.items():
    httpx.post(f'https://localhost:7771/api/v1/records/{path}',
               json={'value': value},
               headers={'Authorization': 'Bearer TOKEN'},
               verify=False)
    print(f'Restored: {path}')
"
```
