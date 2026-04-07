# License Management

## Overview

Akasha uses **Ed25519-signed licenses** with cluster binding. The license system is fully offline — no phone-home or license server required.

### Tiers

| Tier | License Required | Cluster | Agents | Records | Cost |
|------|-----------------|---------|--------|---------|------|
| **Community** | No (auto-generated) | Standalone only | 5 | 10,000 | Free |
| **Basic** | Yes | Standalone only | 100 | 1,000,000 | Paid |
| **Enterprise** | Yes | 3+ nodes HA | Unlimited | Unlimited | Paid |

## License Workflow

```
┌───────────────┐       ┌──────────────────┐       ┌────────────────┐
│   Customer     │       │   Ocuil (you)    │       │  Akasha Node   │
│                │       │                  │       │                │
│ 1. Requests    │──────>│ 2. Issues        │──────>│ 3. Loads       │
│    license     │       │    signed        │       │    license.json │
│                │       │    license       │       │                │
│ Sends:         │       │ Uses:            │       │ Verifies:      │
│ - cluster_id   │       │ - akasha.key     │       │ - Ed25519 sig  │
│ - tier         │       │   (private)      │       │ - Fingerprint  │
│ - company name │       │                  │       │ - Expiry       │
└───────────────┘       └──────────────────┘       └────────────────┘
```

## CLI Commands

### 1. Generate Keypair (one-time)

```bash
# Generate the Ed25519 signing keypair
akasha-license keygen --output keys/

# Output:
#   keys/akasha.key  — PRIVATE KEY (keep secret!)
#   keys/akasha.pub  — Public key (embed in binary / share)
```

> ⚠️ **The private key (`akasha.key`) must be kept secure.** If lost, you cannot issue new licenses. If compromised, anyone can issue valid licenses. Store it in a secrets manager (e.g., GCP Secret Manager, 1Password).

### 2. Issue a License

```bash
# Basic license (standalone)
akasha-license issue \
  --private-key keys/akasha.key \
  --customer "Acme Corp" \
  --tier basic \
  --cluster-id "acme-production" \
  --days 365 \
  --output acme-license.json

# Enterprise license (cluster, node-limited)
akasha-license issue \
  --private-key keys/akasha.key \
  --customer "BigCo Inc" \
  --tier enterprise \
  --cluster-id "bigco-prod" \
  --max-nodes 10 \
  --days 365 \
  --output bigco-license.json
```

### 3. Verify a License

```bash
akasha-license verify \
  --license acme-license.json \
  --public-key keys/akasha.pub
```

### 4. Inspect a License (without verification)

```bash
akasha-license info --license acme-license.json
```

### 5. Get Cluster Fingerprint

The customer needs to provide their `cluster_id` from their config:

```bash
akasha-license fingerprint --cluster-id "acme-production"
```

## License File Format

```json
{
  "license_id": "akasha-enterprise-ebf3957e",
  "customer": "Acme Corp",
  "tier": "Enterprise",
  "features": [
    "core_store", "cognitive_fabric", "pheromones",
    "nidra", "clustering", "multi_node",
    "analytics", "elasticsearch_forwarder",
    "llm_consolidation", "custom_hooks"
  ],
  "max_agents": null,
  "max_records": null,
  "max_pheromone_trails": null,
  "max_nodes": 10,
  "cluster_fingerprint": "fb33300faff624c2...",
  "issued_at": "2026-04-06T15:50:44Z",
  "expires_at": "2027-04-06T15:50:44Z",
  "signature": "base64-ed25519-signature..."
}
```

## Installing a License

The customer places `license.json` in the Akasha data directory or sets the path in config:

```toml
# akasha.toml
license_path = "license.json"
```

Or via environment variable:
```bash
AKASHA_LICENSE_PATH=/path/to/license.json
```

## Cluster Binding

Licenses are bound to a **cluster fingerprint** — a SHA-256 hash of:
- `cluster_id` from the config

This means:
- A license issued for `cluster_id = "acme-production"` will **not work** on a cluster with `cluster_id = "acme-staging"`
- Changing the `cluster_id` invalidates the license
- No network call needed — binding is verified locally

## Key Security

| Asset | Location | Access |
|-------|----------|--------|
| Private key (`akasha.key`) | Your machine / secrets manager | **Only you** — never share |
| Public key (`akasha.pub`) | Embedded in binary + repo | Public — safe to share |
| License file (`license.json`) | Customer's server | Customer-specific, cluster-bound |

### Recommended key storage

```
# Store private key in GCP Secret Manager
gcloud secrets create akasha-signing-key \
  --data-file=keys/akasha.key \
  --project=akasha-492418

# Retrieve when needed
gcloud secrets versions access latest \
  --secret=akasha-signing-key \
  --project=akasha-492418 > /tmp/akasha.key
```

## Customer Onboarding Checklist

1. Customer provides: company name, cluster_id, desired tier, node count
2. You issue: `akasha-license issue --customer "..." --tier enterprise --cluster-id "..." --max-nodes N`
3. You send: `license.json` (via secure channel)
4. Customer installs: places file in data dir, restarts Akasha
5. Akasha verifies: Ed25519 signature + cluster binding + expiry
