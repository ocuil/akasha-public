---
name: akasha-memory
description: |
  Store, retrieve, and query shared memory records in Akasha — a distributed cognitive fabric 
  for intelligent agent collaboration. Use when the agent needs persistent memory, wants to 
  share findings with other agents, or needs to read context written by other agents.
  Supports working, episodic, semantic, and procedural memory layers with automatic 
  consolidation via the Nidra engine.
license: ASL-1.0
compatibility: Requires curl or httpx. Works with any LLM agent that can make HTTP requests.
metadata:
  author: ocuil
  version: "1.0.4"
  category: memory
  tags: memory shared-memory agents collaboration distributed
---

# Akasha Memory Skill

You have access to **Akasha**, a shared cognitive fabric. Use it to persist and retrieve 
structured memory across sessions and across agents.

## Configuration

Before using this skill, ensure you have:
- `AKASHA_URL`: The Akasha endpoint (e.g., `https://localhost:7777`)
- `AKASHA_TOKEN`: A valid JWT token or API key (e.g., `ak_xxx`)

## Memory Layers

| Layer | Path prefix | Purpose | Lifecycle |
|-------|-------------|---------|-----------|
| **Working** | `memory/working/` | Active task state, scratchpad | Auto-expires (TTL) |
| **Episodic** | `memory/episodic/` | Events, experiences, interactions | Consolidates via Nidra |
| **Semantic** | `memory/semantic/` | Distilled knowledge, insights | Permanent |
| **Procedural** | `memory/procedural/` | How-to instructions, recipes | Permanent |

## Operations

### Write a record

```bash
curl -sk -X POST "$AKASHA_URL/api/v1/records/<namespace>/<path>" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": {"key": "value"}, "ttl_secs": 3600}'
```

- `ttl_secs` is optional. Omit for permanent records.
- `value` can be any valid JSON object.

### Read a record

```bash
curl -sk "$AKASHA_URL/api/v1/records/<namespace>/<path>" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### Query records (glob pattern)

```bash
curl -sk "$AKASHA_URL/api/v1/query?pattern=memory/working/**" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### Delete a record

```bash
curl -sk -X DELETE "$AKASHA_URL/api/v1/records/<namespace>/<path>" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## Recommended Path Structure

```
memory/working/<agent-id>/current-task     → Active task context
memory/working/<agent-id>/scratchpad       → Temporary notes
memory/episodic/<domain>/<event-id>        → What happened  
memory/semantic/<domain>/<insight-id>      → What was learned
memory/procedural/<domain>/<procedure-id>  → How to do things
```

## Best Practices

1. **Always namespace by agent-id** for working memory to avoid collisions
2. **Use semantic memory** for important conclusions you want other agents to find
3. **Set TTLs on working memory** — it's meant to be ephemeral
4. **Query before writing** — check if similar knowledge already exists
5. **Use descriptive paths** — they serve as the primary discovery mechanism

## Python SDK

If available, use the Python SDK for a cleaner API. See [references/python-sdk.md](references/python-sdk.md).
