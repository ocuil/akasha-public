# Authentication & Security

## Overview

Akasha provides two authentication mechanisms:
1. **JWT Tokens** — For human users (dashboard login, scripts)
2. **API Keys** — For agents and automated systems

When `auth.enabled = true`, **all API requests** must include an `Authorization` header (except health and login endpoints).

## First Login

On first boot with `auth.enabled = true`, Akasha creates a default admin user:

| Field | Value |
|-------|-------|
| Username | `akasha` |
| Password | `akasha` |
| Role | `admin` |

> ⚠️ **Change this password immediately** — open the dashboard, click your username in the sidebar, and use the Change Password form.

## JWT Authentication

### Login

```bash
curl -sk -X POST https://localhost:7777/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"akasha","password":"akasha"}'
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "username": "akasha",
  "role": "admin",
  "expires_in": 86400
}
```

### Using the token

```bash
# Store the token
export AKASHA_TOKEN="eyJhbGciOiJIUzI1NiJ9..."

# All API calls include the token
curl -sk https://localhost:7777/api/v1/query?pattern=** \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### Python SDK with JWT

```python
from akasha import AkashaHttpClient

# Login and get token
import httpx
resp = httpx.post("https://localhost:7777/api/v1/auth/login",
                  json={"username": "akasha", "password": "new-password"},
                  verify=False)
token = resp.json()["token"]

# Create authenticated client
client = AkashaHttpClient(
    "https://localhost:7777",
    headers={"Authorization": f"Bearer {token}"}
)
```

## API Key Authentication

API keys are the recommended way to authenticate **agents**. They:
- Never expire (until revoked)
- Are scoped to specific namespaces
- Have a defined role (agent, readonly, admin)

### Create an API key

```bash
curl -sk -X POST https://localhost:7777/api/v1/admin/keys \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "planner-agent",
    "role": "agent",
    "namespaces": ["agents/planner/*", "memory/*", "pheromones/*"]
  }'
```

Response:
```json
{
  "id": "a1b2c3d4-...",
  "name": "planner-agent",
  "key": "ak_xxxxxxxxxxxxxxxxxxxx",
  "role": "agent",
  "namespaces": ["agents/planner/*", "memory/*", "pheromones/*"]
}
```

> ⚠️ **Copy the `key` value immediately** — it is only shown once.

### Using API keys

```bash
curl -sk https://localhost:7777/api/v1/query?pattern=** \
  -H "Authorization: Bearer ak_xxxxxxxxxxxxxxxxxxxx"
```

### Python SDK with API key

```python
from akasha import AkashaHttpClient

client = AkashaHttpClient(
    "https://localhost:7777",
    headers={"Authorization": "Bearer ak_xxxxxxxxxxxxxxxxxxxx"}
)
record = client.put("agents/planner/state", {"status": "planning"})
```

### CLI key generation (offline)

```bash
# Generate a key without a running server
cargo run -p akasha-tools -- api-key \
  --name "batch-agent" \
  --role agent \
  --namespaces "agents/batch/*,memory/*"
```

## User Management

### List users
```bash
curl -sk https://localhost:7777/api/v1/admin/users \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### Create user
```bash
curl -sk -X POST https://localhost:7777/api/v1/admin/users \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"operator","password":"secure-pass","role":"operator"}'
```

### Update user (change role or password)
```bash
curl -sk -X PUT https://localhost:7777/api/v1/admin/users/operator \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin","password":"new-password"}'
```

### Delete user
```bash
curl -sk -X DELETE https://localhost:7777/api/v1/admin/users/operator \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## Roles

| Role | Records | Memory | Pheromones | Admin | Dashboard |
|------|---------|--------|------------|-------|-----------|
| `admin` | R/W/D | R/W | R/W | ✅ Full | ✅ Full |
| `operator` | R/W/D | R/W | R/W | ❌ None | ✅ View only |
| `agent` | R/W (scoped) | R/W | R/W | ❌ None | ❌ No access |
| `readonly` | R only | R only | R only | ❌ None | ✅ View only |

## Inter-Node Security (mTLS + HMAC)

In cluster mode, nodes authenticate each other using:

1. **HMAC-SHA256 gossip authentication** — All gossip messages are signed with the shared `cluster_key`
2. **mTLS** — Nodes verify each other's TLS certificates for gRPC replication

```toml
[cluster]
cluster_key = "a-strong-secret-shared-across-all-nodes"

[tls]
require_client_cert = true
```

## Security Checklist for Production

- [ ] Set `auth.enabled = true`
- [ ] Change the default `akasha/akasha` password
- [ ] Set a strong `cluster_key` for inter-node auth
- [ ] Use real TLS certificates (not self-signed) if exposing to internet
- [ ] Create API keys with minimal namespace scoping
- [ ] Revoke unused API keys promptly
- [ ] Set `jwt_secret` explicitly (don't rely on auto-generation across restarts)
- [ ] Enable encryption at-rest with your own key (`[encryption] enabled = true`)
- [ ] Store the encryption key securely (Kubernetes Secret, Vault, etc.)
- [ ] Monitor the audit trail (`GET /api/v1/audit`) for suspicious activity

## Encryption At-Rest (BYOK)

All record values are encrypted before writing to disk using **AES-256-GCM** (authenticated encryption with associated data). The operator provides their own 256-bit master key.

### Configuration

```toml
[encryption]
enabled = true
algorithm = "aes-256-gcm"
key_file = "/secrets/akasha.key"    # 64 hex characters = 256-bit key
# key_env = "AKASHA_ENCRYPTION_KEY"  # Alternative: environment variable
```

### Generate a key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))" > encryption.key
# Result: 535655aa23fd38a46bda73e3025f94df1bb6130938b786e82f6c7b261a184687
```

### Key properties

- **Authenticated**: AES-GCM detects any tampering with ciphertext
- **Nonces**: 96-bit random per operation — never reused
- **Versioned wire format**: `[version(1)][nonce(12)][ciphertext+tag]`
- **Migration**: Unencrypted records are read transparently during transition
- **Performance**: ~3% overhead (AES-NI hardware acceleration)

## Audit Trail

All security events are recorded as immutable records in `audit/` (enforced `append_only` policy):

### Query the audit trail

```bash
# All events (last 100)
curl -sk -H "Authorization: Bearer $AKASHA_TOKEN" \
  "https://localhost:7777/api/v1/audit?limit=100"

# Filter by category
curl -sk -H "Authorization: Bearer $AKASHA_TOKEN" \
  "https://localhost:7777/api/v1/audit?category=auth&limit=50"
```

### Event categories

| Category | Events |
|----------|--------|
| `auth` | Login success/failure, rate limiting |
| `admin` | User created/updated/deleted, API key created/revoked |
| `policy` | Namespace policy violations (403) |
| `system` | Encryption loaded, Nidra consolidation |

### Retention

Audit records have a **90-day TTL** and are automatically cleaned up by the TTL reaper.
