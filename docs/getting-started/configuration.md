# Configuration

Akasha uses a `akasha.toml` configuration file. All settings have sensible defaults — you can run Akasha without any configuration.

## Configuration File

Create an `akasha.toml` in the working directory:

```toml
[server]
grpc_addr = "0.0.0.0:50051"
http_addr = "0.0.0.0:7777"
name = "akasha"

[tls]
enabled = true
cert_path = "certs/server.crt"
key_path = "certs/server.key"

[auth]
enabled = true
jwt_secret = "your-secret-key-here"
default_user = "akasha"
default_password = "akasha"

[nidra]
enabled = true
interval_secs = 300
working_memory_ttl = 3600

[cluster]
enabled = true
node_id = "akasha-01"
bind_addr = "0.0.0.0:7946"
peers = ["akasha-02:7946", "akasha-03:7946"]
```

## Environment Variables

Any config option can be overridden via environment variable:

| Variable | Default | Description |
|----------|---------|-------------|
| `AKASHA_HTTP_ADDR` | `0.0.0.0:7777` | HTTP listen address |
| `AKASHA_GRPC_ADDR` | `0.0.0.0:50051` | gRPC listen address |
| `AKASHA_TLS_ENABLED` | `true` | Enable TLS |
| `AKASHA_AUTH_ENABLED` | `true` | Require authentication |
| `AKASHA_JWT_SECRET` | auto-generated | JWT signing key |
| `AKASHA_CLUSTER_ENABLED` | `false` | Enable clustering |
| `AKASHA_CLUSTER_NODE_ID` | hostname | Node identifier |
| `AKASHA_CLUSTER_PEERS` | empty | Comma-separated peer addresses |

## Authentication

Akasha supports two authentication methods:

### JWT Tokens

```bash
# Login to get a token
curl -s http://localhost:7777/api/v1/auth/login \
  -X POST -H "Content-Type: application/json" \
  -d '{"username": "akasha", "password": "akasha"}' | jq .token

# Use the token
curl -s http://localhost:7777/api/v1/records/test \
  -H "Authorization: Bearer <token>"
```

### API Keys

Configure API keys in `akasha.toml`:

```toml
[auth]
api_keys = ["key-1-abcdef", "key-2-ghijkl"]
```

```bash
curl -s http://localhost:7777/api/v1/records/test \
  -H "X-API-Key: key-1-abcdef"
```

## TLS

Akasha generates self-signed certificates on first start. For production, provide your own:

```toml
[tls]
enabled = true
cert_path = "/path/to/server.crt"
key_path = "/path/to/server.key"
```

!!! warning "Self-signed certificates"
    When using self-signed certs, set `verify_ssl=False` (Python) or `rejectUnauthorized: false` (Node.js) in your SDK client.
