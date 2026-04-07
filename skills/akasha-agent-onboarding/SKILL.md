---
name: akasha-agent-onboarding
description: |
  Step-by-step onboarding guide for connecting a new AI agent to Akasha.
  Use when setting up a new agent, configuring authentication, choosing 
  a namespace strategy, or writing the initial system prompt for Akasha 
  integration. Covers Python SDK, Node.js SDK, and raw HTTP/gRPC.
license: ASL-1.0
compatibility: Requires Python 3.10+ or Node.js 18+, or curl for HTTP.
metadata:
  author: ocuil
  version: "1.0.4"
  category: onboarding
  tags: setup onboarding agent configuration sdk
---

# Akasha Agent Onboarding Skill

Complete guide to connect a new agent to Akasha.

## Step 1: Get Your Credentials

### Option A: API Key (recommended for agents)

Ask an admin to create a key via Dashboard or API:

```bash
curl -sk -X POST "$AKASHA_URL/api/v1/admin/keys" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-new-agent",
    "namespaces": ["memory/working/my-new-agent/**", "memory/semantic/**", "memory/episodic/**"],
    "role": "agent"
  }'
```

Save the returned `key` — it's shown only once.

### Option B: JWT Token (user sessions)

```bash
TOKEN=$(curl -sk -X POST "$AKASHA_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"my-user","password":"my-password"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")
```

## Step 2: Choose Your SDK

### Python (gRPC — recommended for performance)

```bash
pip install akasha-client
```

```python
from akasha import AkashaClient

with AkashaClient("localhost:50051") as client:
    # Write
    client.put("memory/working/my-agent/status", {"state": "ready"})
    
    # Read
    record = client.get("memory/working/my-agent/status")
    print(record.value)  # {"state": "ready"}
    
    # Query
    results = client.query("memory/working/**")
```

### Python (HTTP — simpler, no proto compilation)

```python
from akasha import AkashaHttpClient

client = AkashaHttpClient(
    "https://localhost:7777",
    verify_ssl=False  # For self-signed TLS certs
)
client.login("my-user", "my-password")
# Or use API key:
# client = AkashaHttpClient("https://...", api_key="ak_my-agent_xxx")

client.put("memory/working/my-agent/status", {"state": "ready"})
```

### Node.js

```javascript
const { AkashaClient } = require('@akasha/client');

const client = new AkashaClient({
  address: 'localhost:50051',
  // or for HTTP:
  // url: 'https://localhost:7777',
  // token: 'ak_my-agent_xxx'
});

await client.put('memory/working/my-agent/status', { state: 'ready' });
const record = await client.get('memory/working/my-agent/status');
```

### Raw HTTP (any language)

```bash
# Set these in your agent's environment
export AKASHA_URL="https://localhost:7777"
export AKASHA_TOKEN="ak_my-agent_xxxxxxxxxxxx"

# Write
curl -sk -X POST "$AKASHA_URL/api/v1/records/memory/working/my-agent/status" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": {"state": "ready"}}'

# Read
curl -sk "$AKASHA_URL/api/v1/records/memory/working/my-agent/status" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## Step 3: Define Your Namespace Strategy

Choose a path structure based on your agent's role:

### Research Agent
```
memory/working/<agent-id>/task          ← Current task context
memory/episodic/research/<finding-id>   ← Raw findings
memory/semantic/research/<insight>      ← Confirmed knowledge
```

### Code Agent
```
memory/working/<agent-id>/context       ← Current code context
memory/procedural/coding/<pattern>      ← Reusable code patterns
memory/semantic/architecture/<decision> ← Architecture decisions
```

### Monitoring Agent
```
memory/working/<agent-id>/alerts        ← Active alerts
memory/episodic/incidents/<incident-id> ← Incident timeline
memory/semantic/runbooks/<procedure>    ← Proven remediation steps
```

### Multi-Agent Team
```
shared/                                 ← Team-wide shared state
  ├── config/<setting>                  ← Shared configuration
  ├── tasks/<task-id>                   ← Task assignments
  └── results/<task-id>                 ← Task results

memory/working/<agent-id>/              ← Each agent's private scratchpad
```

## Step 4: Add Akasha to Your System Prompt

Add this block to your agent's system prompt (adapt to your domain):

```
## Shared Memory (Akasha)

You are connected to a shared knowledge base. Use it to remember and share.

### Write: POST /api/v1/records/<path>
  Body: {"value": <json>, "ttl_secs": <optional>}

### Read: GET /api/v1/records/<path>

### Search: GET /api/v1/query?pattern=<glob-pattern>

### Signal: POST /api/v1/pheromones/<trail>
  Body: {"signal_type":"discovery","message":"...","intensity":0.8}

Auth header: Authorization: Bearer <your-token>
Base URL: <your-akasha-url>

Use working memory (ttl_secs) for temporary state.
Use semantic memory for confirmed knowledge.
Check signals before starting new work.
```

## Step 5: Verify Connection

```bash
# Health check (no auth)
curl -sk $AKASHA_URL/api/v1/health

# Write test
curl -sk -X POST "$AKASHA_URL/api/v1/records/test/hello" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -d '{"value": {"message": "Agent connected!"}}'

# Read test
curl -sk "$AKASHA_URL/api/v1/records/test/hello" \
  -H "Authorization: Bearer $AKASHA_TOKEN"

# Cleanup
curl -sk -X DELETE "$AKASHA_URL/api/v1/records/test/hello" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## Checklist

- [ ] API key or JWT token obtained
- [ ] SDK installed (Python/Node/HTTP)
- [ ] Namespace strategy defined
- [ ] System prompt updated with Akasha instructions
- [ ] Connection verified (health → write → read → delete)
- [ ] Working memory uses TTL to auto-expire
