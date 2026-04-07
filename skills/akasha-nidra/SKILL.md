---
name: akasha-nidra
description: |
  Monitor and interact with Akasha's Nidra consolidation engine — the subsystem 
  that automatically consolidates episodic memories into semantic knowledge.
  Use when you need to check consolidation status, understand memory lifecycle, 
  or query memory layer statistics.
license: ASL-1.0
compatibility: Requires curl or httpx. Works with any LLM agent that can make HTTP requests.
metadata:
  author: ocuil
  version: "1.0.4"
  category: memory
  tags: nidra consolidation memory lifecycle analytics
---

# Akasha Nidra Skill

Interact with the **Nidra consolidation engine** — Akasha's background process that 
mimics human memory consolidation during sleep.

## Configuration

- `AKASHA_URL`: The Akasha endpoint (e.g., `https://localhost:7777`)
- `AKASHA_TOKEN`: A valid JWT token or API key

## What Nidra Does

```
Episodic Memory (raw events)
    │
    ▼ Nidra scans every 5 min
    │
    ├── Groups related episodes by topic
    ├── Detects patterns and frequency
    ├── Weighs by recency and importance
    │
    ▼ Consolidates every ~1 hour
    │
Semantic Memory (distilled knowledge)
    │
    └── Old episodes pruned after consolidation
```

## Operations

### Check Nidra status

```bash
curl -sk "$AKASHA_URL/api/v1/nidra/status" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

Returns:
```json
{
  "enabled": true,
  "sweep_interval_secs": 300,
  "consolidation_every_n_sweeps": 12,
  "last_sweep": "2026-04-07T20:00:00Z",
  "total_sweeps": 42,
  "total_consolidations": 3,
  "pending_episodes": 15
}
```

### View memory layer statistics

```bash
curl -sk "$AKASHA_URL/api/v1/memory/layers" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

Returns breakdown of records per memory layer (working, episodic, semantic, procedural).

### Query episodes awaiting consolidation

```bash
curl -sk "$AKASHA_URL/api/v1/query?pattern=memory/episodic/**" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### View consolidated semantic knowledge

```bash
curl -sk "$AKASHA_URL/api/v1/query?pattern=memory/semantic/**" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## Writing Episodic Records (for Nidra to process)

When your agent experiences something worth remembering, log it as episodic memory:

```bash
curl -sk -X POST "$AKASHA_URL/api/v1/records/memory/episodic/<domain>/<event-id>" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "value": {
      "event": "API rate limit reached on provider X",
      "timestamp": "2026-04-07T20:15:00Z",
      "context": {"provider": "X", "limit": 100, "window": "1min"},
      "outcome": "switched to provider Y"
    }
  }'
```

Over time, if Nidra sees repeated "rate limit" episodes for provider X, it will 
consolidate them into a semantic insight like:
> "Provider X has a 100/min rate limit. Recommend using provider Y as fallback."

## Configuration Reference

These values are set in `akasha.toml`, not via API:

```toml
[nidra]
enabled = true
sweep_interval_secs = 300           # Scan every 5 minutes
consolidation_every_n_sweeps = 12   # Consolidate every 12 sweeps (~1 hour)
evaporation_threshold = 0.01        # Min intensity before pheromone removal

[llm]
enabled = false                      # Enable for LLM-enhanced consolidation
provider = "ollama"                  # or "openai"
endpoint = "http://localhost:11434/api/generate"
model = "llama3:8b"
```

## Best Practices

1. **Write episodic records with structured data** — Nidra needs consistent fields to find patterns
2. **Include domain in paths** — `memory/episodic/security/...` helps topic grouping
3. **Don't manually write to semantic** if Nidra handles it — avoid conflicts
4. **Monitor pending episodes** — if too many accumulate, consider reducing sweep interval
5. **LLM consolidation** produces richer summaries — enable it for production
