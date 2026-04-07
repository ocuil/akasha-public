---
name: akasha-stigmergy
description: |
  Coordinate with other agents through pheromone-based stigmergy signals in Akasha.
  Use when you need to signal discoveries, request help, warn about issues, or 
  coordinate work without direct agent-to-agent messaging. Pheromones decay over 
  time (configurable half-life), creating natural priority based on recency and intensity.
license: ASL-1.0
compatibility: Requires curl or httpx. Works with any LLM agent that can make HTTP requests.
metadata:
  author: ocuil
  version: "1.0.4"
  category: coordination
  tags: stigmergy pheromones coordination agents swarm
---

# Akasha Stigmergy Skill

Coordinate with other agents using **pheromone-based stigmergy** — indirect communication 
through the shared environment, inspired by ant colony optimization.

## Configuration

- `AKASHA_URL`: The Akasha endpoint (e.g., `https://localhost:7777`)
- `AKASHA_TOKEN`: A valid JWT token or API key

## Core Concepts

- **Trail**: A path where pheromones are deposited (e.g., `research/cybersecurity`)
- **Signal type**: What kind of signal (`discovery`, `warning`, `request`, `progress`)
- **Intensity**: How strong the signal is (0.0 to 1.0)
- **Half-life**: How fast the pheromone decays (seconds)
- **Evaporation**: Pheromones naturally decay — old signals fade, fresh ones dominate

## Operations

### Deposit a pheromone

```bash
curl -sk -X POST "$AKASHA_URL/api/v1/pheromones/<trail>" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signal_type": "discovery",
    "message": "Found critical vulnerability in auth module",
    "intensity": 0.9,
    "half_life_secs": 3600,
    "depositor": "security-agent"
  }'
```

### Read pheromones on a trail

```bash
curl -sk "$AKASHA_URL/api/v1/pheromones/<trail>" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### Query pheromones (glob pattern)

```bash
curl -sk "$AKASHA_URL/api/v1/pheromones?pattern=research/**" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

## Signal Types

| Type | Use when | Example |
|------|----------|---------|
| `discovery` | You found something valuable | "New CVE affects OpenSSL 3.x" |
| `warning` | Something needs attention | "API rate limit approaching" |
| `request` | You need help from others | "Need domain expert for legal review" |
| `progress` | Reporting task advancement | "Dataset analysis 75% complete" |
| `completion` | Task finished | "Report generated and saved" |

## Coordination Patterns

### 1. Broadcast a discovery
```bash
# Agent A finds something → deposits high-intensity pheromone
curl -sk -X POST "$AKASHA_URL/api/v1/pheromones/research/security" \
  -H "Authorization: Bearer $AKASHA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"signal_type":"discovery","message":"SQL injection in /api/users","intensity":0.95,"half_life_secs":7200}'
```

### 2. Check for relevant signals before starting work
```bash
# Agent B checks trail before duplicating effort
curl -sk "$AKASHA_URL/api/v1/pheromones/research/security" \
  -H "Authorization: Bearer $AKASHA_TOKEN"
```

### 3. Reinforce important signals
If you find a pheromone relevant, deposit your own on the same trail to reinforce it.

## Best Practices

1. **Use descriptive trails** — they're the discovery mechanism (`research/topic`, `tasks/domain`)
2. **Set appropriate half-lives** — urgent: 1h, normal: 6h, persistent: 24h+
3. **Check trails before working** — avoid duplicating effort
4. **High intensity for critical signals** — 0.9+ for urgent, 0.3-0.6 for informational
5. **Always include a clear message** — other agents need to understand the signal
