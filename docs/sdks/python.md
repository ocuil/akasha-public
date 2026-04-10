# Python SDK

[![PyPI](https://img.shields.io/pypi/v/akasha-client?color=blue&label=PyPI)](https://pypi.org/project/akasha-client/)

Full-featured Python client for Akasha with sync, async, HTTP, and gRPC support.

## Installation

```bash
pip install akasha-client
```

## Quick Start

```python
from akasha import AkashaHttpClient

client = AkashaHttpClient(
    base_url="https://localhost:7777",
    api_key="your-api-key",       # or use token="jwt-token"
    verify_ssl=False,              # for self-signed certs
)

# CRUD
record = client.put("agents/planner/state", {"status": "active"})
state = client.get("agents/planner/state")
client.delete("agents/planner/state")

# Query
results = client.query("agents/*/state")

# CAS
from akasha import CasConflictError
try:
    client.put_cas("shared/counter", {"n": 1}, expected_version=record.version)
except CasConflictError:
    pass  # retry

# Subscribe to changes
for event in client.subscribe("agents/**"):
    print(f"[{event.kind}] {event.path}")
```

## Async Client

```python
from akasha import AsyncAkashaHttpClient

async def main():
    client = AsyncAkashaHttpClient(
        base_url="https://localhost:7777",
        token="your-jwt-token",
        verify_ssl=False,
    )
    
    await client.put("memory/working/task", {"step": 1})
    record = await client.get("memory/working/task")
```

Compatible with LangGraph, asyncio, and any async Python framework.

## Authentication

```python
# API Key
client = AkashaHttpClient(api_key="your-key")

# JWT Token
client = AkashaHttpClient(token="eyJ0eXAi...")

# Login to get a token
client = AkashaHttpClient(base_url="https://localhost:7777")
# POST /api/v1/auth/login
```

## API Reference

See the full [REST API documentation](rest-api.md) for all endpoints.
