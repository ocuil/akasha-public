---
name: akasha-cluster
description: |
  Monitor and manage an Akasha cluster — check node health, license status, 
  cluster topology, and admin operations. Use when the agent needs to verify 
  system health, inspect cluster state, manage users and API keys, or 
  troubleshoot connectivity between nodes.
license: ASL-1.0
compatibility: Requires curl. Works with any agent that can make HTTP requests.
metadata:
  author: ocuil
  version: "1.0.4"
  category: operations
  tags: cluster monitoring health admin devops
---

# Akasha Cluster Management Skill

Monitor health, manage users/keys, and inspect cluster topology.

## Configuration

- `AKASHA_URL`: The Akasha endpoint (e.g., `https://localhost:7777`)
- `AKASHA_TOKEN`: A valid JWT token or API key with `admin` role

## Health & Monitoring

### Check cluster health (no auth required)

```bash
curl -sk "$AKASHA_URL/api/v1/health"
# Returns: { "status": "ok", "version": "1.0.4", "records": 42, "cluster": {...} }
```

### Check if a specific node is alive

```bash
curl -sk "$AKASHA_URL/api/v1/health/live"
# Returns: empty 200 OK if alive
```

### List cluster nodes

```bash
curl -sk "$AKASHA_URL/api/v1/cluster/nodes" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
# Returns: { "node_count": 3, "nodes": [...] }
```

### Check license status

```bash
curl -sk "$AKASHA_URL/api/v1/license/status" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## User Management

### List users

```bash
curl -sk "$AKASHA_URL/api/v1/admin/users" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### Create a user

```bash
curl -sk -X POST "$AKASHA_URL/api/v1/admin/users" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "operator-01", "password": "secure-pwd", "role": "operator"}'
```

Roles: `admin`, `operator`, `readonly`

### Delete a user

```bash
curl -sk -X DELETE "$AKASHA_URL/api/v1/admin/users/<username>" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## API Key Management

### Create an API key for an agent

```bash
curl -sk -X POST "$AKASHA_URL/api/v1/admin/keys" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "research-agent",
    "namespaces": ["research/**", "memory/**"],
    "role": "agent"
  }'
# Returns: { "key": "ak_research-agent_xxx" }  ← save this, shown only once
```

### Revoke an API key

```bash
curl -sk -X DELETE "$AKASHA_URL/api/v1/admin/keys/<key-id>" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## Authentication

### Login and get JWT token

```bash
TOKEN=$(curl -sk -X POST "$AKASHA_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "akasha", "password": "akasha"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")
```

### Change password

```bash
curl -sk -X POST "$AKASHA_URL/api/v1/auth/change-password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "old", "new_password": "new"}'
```

## Troubleshooting

1. **401 Unauthorized**: Token expired or invalid. Re-login.
2. **503 Service Unavailable**: Node is starting up. Wait 10-15s.
3. **Cluster shows 1 node**: Check that all nodes share the same `cluster.identity` and `jwt_secret`.
4. **License error**: Run `GET /api/v1/license/status` to check expiry and binding.
