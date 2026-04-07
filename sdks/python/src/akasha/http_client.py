"""
Akasha HTTP Client — Lightweight client using the REST API.

For environments where gRPC is not available or when simplicity is preferred.
Uses httpx for both sync and async HTTP support.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Optional

import httpx

from akasha.models import AkashaEvent, Record

logger = logging.getLogger("akasha.http_client")


class AkashaHttpClient:
    """
    HTTP/REST client for Akasha — lightweight alternative to gRPC.

    Usage:
        client = AkashaHttpClient("http://localhost:7777")

        record = client.put("agents/my-agent/state", {"status": "thinking"})
        record = client.get("agents/my-agent/state")
        records = client.query("agents/*/state")
        agents = client.list_agents()
        tree = client.tree()

        client.close()
    """

    def __init__(
        self,
        base_url: str = "http://localhost:7777",
        *,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            transport=httpx.HTTPTransport(retries=max_retries),
        )
        logger.info(f"Akasha HTTP client connected to {base_url}")

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # -- Core CRUD --

    def put(
        self,
        path: str,
        value: Any,
        *,
        ttl_seconds: Optional[float] = None,
        tags: Optional[dict[str, str]] = None,
    ) -> Record:
        """Write a record via REST API."""
        body: dict[str, Any] = {"value": value}
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if tags:
            body["tags"] = tags

        response = self._client.post(
            f"/api/v1/records/{path}",
            json=body,
        )
        response.raise_for_status()
        return Record.from_dict(response.json())

    def get(self, path: str) -> Optional[Record]:
        """Read a record by path."""
        response = self._client.get(f"/api/v1/records/{path}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return Record.from_dict(response.json())

    def delete(self, path: str) -> bool:
        """Delete a record."""
        response = self._client.delete(f"/api/v1/records/{path}")
        return response.status_code == 204

    # -- Queries --

    def query(
        self,
        pattern: str,
        *,
        limit: Optional[int] = None,
    ) -> list[Record]:
        """Query records matching a glob pattern."""
        params: dict[str, Any] = {"pattern": pattern}
        if limit is not None:
            params["limit"] = limit

        response = self._client.get("/api/v1/query", params=params)
        response.raise_for_status()
        return [Record.from_dict(r) for r in response.json()]

    # -- Convenience --

    def list_agents(self) -> list[dict]:
        """List all registered agents."""
        response = self._client.get("/api/v1/agents")
        response.raise_for_status()
        return response.json()

    def tree(self) -> dict[str, Any]:
        """Get the full state tree snapshot."""
        response = self._client.get("/api/v1/tree")
        response.raise_for_status()
        return response.json()

    def health(self) -> dict:
        """Health check."""
        response = self._client.get("/api/v1/health")
        response.raise_for_status()
        return response.json()

    def metrics(self) -> dict:
        """Get server metrics."""
        response = self._client.get("/api/v1/metrics")
        response.raise_for_status()
        return response.json()


class AsyncAkashaHttpClient:
    """
    Async HTTP client for Akasha — for asyncio environments without gRPC.

    Usage:
        async with AsyncAkashaHttpClient("http://localhost:7777") as client:
            await client.put("agents/my-agent/state", {"status": "thinking"})
    """

    def __init__(
        self,
        base_url: str = "http://localhost:7777",
        *,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            transport=httpx.AsyncHTTPTransport(retries=max_retries),
        )

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def put(
        self,
        path: str,
        value: Any,
        *,
        ttl_seconds: Optional[float] = None,
        tags: Optional[dict[str, str]] = None,
    ) -> Record:
        body: dict[str, Any] = {"value": value}
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if tags:
            body["tags"] = tags

        response = await self._client.post(f"/api/v1/records/{path}", json=body)
        response.raise_for_status()
        return Record.from_dict(response.json())

    async def get(self, path: str) -> Optional[Record]:
        response = await self._client.get(f"/api/v1/records/{path}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return Record.from_dict(response.json())

    async def delete(self, path: str) -> bool:
        response = await self._client.delete(f"/api/v1/records/{path}")
        return response.status_code == 204

    async def query(self, pattern: str, *, limit: Optional[int] = None) -> list[Record]:
        params: dict[str, Any] = {"pattern": pattern}
        if limit is not None:
            params["limit"] = limit
        response = await self._client.get("/api/v1/query", params=params)
        response.raise_for_status()
        return [Record.from_dict(r) for r in response.json()]

    async def list_agents(self) -> list[dict]:
        response = await self._client.get("/api/v1/agents")
        response.raise_for_status()
        return response.json()

    async def tree(self) -> dict[str, Any]:
        response = await self._client.get("/api/v1/tree")
        response.raise_for_status()
        return response.json()

    async def health(self) -> dict:
        response = await self._client.get("/api/v1/health")
        response.raise_for_status()
        return response.json()

    async def metrics(self) -> dict:
        response = await self._client.get("/api/v1/metrics")
        response.raise_for_status()
        return response.json()
