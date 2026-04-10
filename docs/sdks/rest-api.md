# REST API Reference

Akasha exposes a complete REST API over HTTP with 21 endpoints across 8 categories.

## Interactive Documentation

The full API is documented with OpenAPI 3.1 and can be explored interactively:

**[→ Open API Explorer (Redoc)](../api/index.html)**

## Base URL

```
https://localhost:7777/api/v1
```

## Authentication

All endpoints except `/health` require authentication:

```bash
# JWT
-H "Authorization: Bearer <token>"

# API Key
-H "X-API-Key: <key>"
```

## Endpoints Overview

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Full health check with cluster info |
| GET | `/health/live` | Kubernetes liveness probe |
| GET | `/health/ready` | Kubernetes readiness probe |

### Records

| Method | Path | Description |
|--------|------|-------------|
| GET | `/records/{path}` | Read a record |
| POST | `/records/{path}` | Write a record (+ CAS with `If-Match`) |
| DELETE | `/records/{path}` | Delete a record |

### Query

| Method | Path | Description |
|--------|------|-------------|
| GET | `/query?pattern=agents/*` | Pattern-based search |

### Memory

| Method | Path | Description |
|--------|------|-------------|
| GET | `/memory/layers` | Memory layer statistics |
| GET | `/nidra/status` | Nidra consolidation status |

### Pheromones

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pheromones` | Sense all active trails |
| POST | `/pheromones` | Deposit a pheromone |

### Cluster

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cluster/status` | Cluster health |
| GET | `/cluster/nodes` | Node list |
| GET | `/cluster/sync` | CRDT sync status |
| GET | `/cluster/raft` | Raft consensus state |

### Metrics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Application metrics |
| GET | `/system/metrics` | System metrics (CPU, memory) |
| GET | `/metrics` (root) | Prometheus scrape format |

## OpenAPI Spec

Download the spec for import into Postman, Insomnia, or any OpenAPI tool:

**[→ Download openapi.yaml](../openapi.yaml)**
