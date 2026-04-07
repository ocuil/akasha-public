# Akasha Python SDK Reference

## Installation

```bash
pip install akasha-client
# Or from source:
pip install git+https://github.com/ocuil/akasha-public.git#subdirectory=sdks/python
```

## Quick Start

```python
from akasha import AkashaClient

client = AkashaClient(
    url="https://localhost:7777",
    token="ak_your_api_key_here",
    verify_ssl=False  # For self-signed TLS certs
)

# Store memory
client.put("memory/working/my-agent/task", {
    "objective": "analyze security logs",
    "progress": 0.5,
    "findings": ["suspicious IP detected"]
})

# Retrieve memory
data = client.get("memory/working/my-agent/task")

# Query with glob
results = client.query("memory/working/**")

# Deposit pheromone
client.deposit_pheromone(
    trail="security/alerts",
    signal_type="warning",
    message="Brute force attempt detected from 10.0.0.5",
    intensity=0.85,
    half_life_secs=3600
)

# Read pheromones
signals = client.get_pheromones(trail="security/**")
```

## API Reference

### `AkashaClient(url, token, verify_ssl=True)`
Create a new client instance.

### `client.put(path, value, ttl_secs=None, content_type=None)`
Write a record. Returns the stored record metadata.

### `client.get(path)`
Read a record. Returns the record value or `None` if not found.

### `client.delete(path)`
Delete a record. Returns `True` if deleted.

### `client.query(pattern)`
Query records matching a glob pattern. Returns list of records.

### `client.deposit_pheromone(trail, signal_type, message, intensity=0.5, half_life_secs=3600, depositor=None)`
Deposit a pheromone signal on a trail.

### `client.get_pheromones(trail)`
Read pheromone signals from a trail or glob pattern.

### `client.health()`
Check cluster health. Returns health response dict.
