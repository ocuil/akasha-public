# Monitoring

Akasha exposes Prometheus metrics at `/metrics` for integration with Grafana, Datadog, or any Prometheus-compatible scraper.

## Prometheus Configuration

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
    scrape_interval: 15s
```

## Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `akasha_records_total` | Gauge | Total records in the store |
| `akasha_agents_total` | Gauge | Registered agents |
| `akasha_pheromones_active` | Gauge | Active pheromone trails |
| `akasha_memory_records{layer}` | Gauge | Records per memory layer |
| `akasha_cluster_nodes{status}` | Gauge | Cluster nodes by status |
| `akasha_crdt_tracked_paths` | Gauge | CRDT tracked paths |
| `akasha_crdt_pending_deltas` | Gauge | Pending sync deltas |
| `akasha_raft_commit_index` | Gauge | Raft commit index |
| `akasha_raft_term` | Gauge | Current Raft term |
| `akasha_raft_is_leader` | Gauge | Whether this node is the leader |
| `akasha_nidra_is_leader` | Gauge | Whether this node runs Nidra |

## Grafana Dashboard

Import the ready-made Grafana dashboard:

1. Download [`deploy/grafana-dashboard.json`](https://github.com/ocuil/akasha-public/blob/main/deploy/grafana-dashboard.json)
2. In Grafana → Dashboards → Import → Upload JSON
3. Select your Prometheus data source
4. Done! 12 panels showing all Akasha metrics.

The dashboard includes:

- **Stat panels**: cluster health, records, agents, pheromones, CRDT sync, leader status
- **Time series**: records over time, memory layers (stacked), cluster nodes, CRDT deltas, Raft consensus, pheromone activity

## Manual Check

```bash
curl -sk https://localhost:7777/metrics | head -20
```

```text
# HELP akasha_records_total Total records in the store.
# TYPE akasha_records_total gauge
akasha_records_total 569
# HELP akasha_memory_records Records per memory layer.
# TYPE akasha_memory_records gauge
akasha_memory_records{layer="working"} 38
akasha_memory_records{layer="episodic"} 467
akasha_memory_records{layer="semantic"} 50
akasha_memory_records{layer="procedural"} 2
```
