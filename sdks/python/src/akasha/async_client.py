"""
Akasha Async gRPC Client — Production-ready async client for asyncio-based agents.

Features:
  - Full async/await support for non-blocking agents
  - Connection pooling via gRPC async channel
  - Automatic retry with exponential backoff
  - Async iterator for subscriptions
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Optional

import grpc.aio
import msgpack

from akasha.models import AkashaEvent, Record

_pb2 = None
_pb2_grpc = None

logger = logging.getLogger("akasha.async_client")


def _load_stubs():
    global _pb2, _pb2_grpc
    if _pb2 is None:
        from akasha.proto import akasha_pb2, akasha_pb2_grpc
        _pb2 = akasha_pb2
        _pb2_grpc = akasha_pb2_grpc


class AsyncAkashaClient:
    """
    Async gRPC client for Akasha — designed for asyncio-based agents.

    Usage:
        async with AsyncAkashaClient("localhost:50051") as client:
            await client.put("agents/my-agent/state", {"status": "thinking"})

            record = await client.get("agents/my-agent/state")

            async for event in client.subscribe("agents/**"):
                print(f"{event.path}: {event.record.value}")
    """

    def __init__(
        self,
        address: str = "localhost:50051",
        *,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
        max_message_size: int = 64 * 1024 * 1024,
    ):
        _load_stubs()

        self._address = address
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff

        self._channel = grpc.aio.insecure_channel(
            address,
            options=[
                ("grpc.max_send_message_length", max_message_size),
                ("grpc.max_receive_message_length", max_message_size),
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.keepalive_permit_without_calls", 1),
            ],
        )
        self._stub = _pb2_grpc.AkashaStub(self._channel)

        logger.info(f"Async Akasha client connected to {address}")

    async def close(self):
        """Close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            logger.info("Async Akasha client disconnected")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    # -- Core CRUD --

    async def put(
        self,
        path: str,
        value: Any,
        *,
        content_type: str = "msgpack",
        ttl_seconds: float = 0,
        tags: Optional[dict[str, str]] = None,
        source: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Record:
        """Write a record to Akasha."""
        encoded = self._encode_value(value, content_type)
        request = _pb2.PutRequest(
            path=path,
            value=encoded,
            content_type=content_type,
            ttl_seconds=ttl_seconds,
            tags=tags or {},
            source=source or "",
        )
        response = await self._call_with_retry(
            self._stub.Put, request, timeout=timeout
        )
        return Record.from_grpc(response.record)

    async def get(self, path: str, *, timeout: Optional[float] = None) -> Optional[Record]:
        """Read a record by exact path."""
        request = _pb2.GetRequest(path=path)
        response = await self._call_with_retry(
            self._stub.Get, request, timeout=timeout
        )
        if response.found:
            return Record.from_grpc(response.record)
        return None

    async def delete(self, path: str, *, timeout: Optional[float] = None) -> bool:
        """Delete a record."""
        request = _pb2.DeleteRequest(path=path)
        response = await self._call_with_retry(
            self._stub.Delete, request, timeout=timeout
        )
        return response.deleted

    # -- Queries --

    async def query(
        self,
        pattern: str,
        *,
        tag_filters: Optional[dict[str, str]] = None,
        limit: int = 0,
        timeout: Optional[float] = None,
    ) -> list[Record]:
        """Query records matching a glob pattern."""
        request = _pb2.QueryRequest(
            pattern=pattern,
            tag_filters=tag_filters or {},
            limit=limit,
        )
        response = await self._call_with_retry(
            self._stub.Query, request, timeout=timeout
        )
        return [Record.from_grpc(r) for r in response.records]

    async def list_paths(
        self, prefix: str = "", *, timeout: Optional[float] = None
    ) -> list[str]:
        """List all paths under a prefix."""
        request = _pb2.ListPathsRequest(prefix=prefix)
        response = await self._call_with_retry(
            self._stub.ListPaths, request, timeout=timeout
        )
        return list(response.paths)

    # -- Agent Lifecycle --

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str = "generic",
        metadata: Optional[dict[str, str]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> str:
        """Register an agent with Akasha."""
        request = _pb2.RegisterAgentRequest(
            agent_id=agent_id,
            agent_type=agent_type,
            metadata=metadata or {},
        )
        response = await self._call_with_retry(
            self._stub.RegisterAgent, request, timeout=timeout
        )
        return response.agent_path

    async def heartbeat(
        self,
        agent_id: str,
        status: Optional[dict[str, str]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> None:
        """Send a heartbeat for an agent."""
        request = _pb2.HeartbeatRequest(
            agent_id=agent_id,
            status=status or {},
        )
        await self._call_with_retry(
            self._stub.Heartbeat, request, timeout=timeout
        )

    # -- Subscriptions --

    async def subscribe(
        self,
        pattern: str = "**",
    ) -> AsyncIterator[AkashaEvent]:
        """
        Subscribe to real-time events matching a glob pattern.

        Yields AkashaEvent objects asynchronously.
        """
        request = _pb2.SubscribeRequest(pattern=pattern)

        async for pb_event in self._stub.Subscribe(request):
            try:
                yield AkashaEvent.from_grpc(pb_event)
            except Exception as e:
                logger.warning(f"Failed to parse event: {e}")

    # -- System --

    async def get_metrics(self, *, timeout: Optional[float] = None) -> dict:
        """Get server metrics."""
        request = _pb2.GetMetricsRequest()
        response = await self._call_with_retry(
            self._stub.GetMetrics, request, timeout=timeout
        )
        return {
            "total_records": response.total_records,
            "total_writes": response.total_writes,
            "total_reads": response.total_reads,
            "total_queries": response.total_queries,
            "total_deletes": response.total_deletes,
            "connected_agents": response.connected_agents,
            "uptime_seconds": response.uptime_seconds,
            "custom_metrics": dict(response.custom_metrics),
        }

    # -- Internals --

    def _encode_value(self, value: Any, content_type: str) -> bytes:
        if content_type == "json":
            return json.dumps(value).encode("utf-8")
        else:
            return msgpack.packb(value, use_bin_type=True)

    async def _call_with_retry(self, method, request, *, timeout: Optional[float] = None):
        t = timeout or self._timeout
        last_error = None

        for attempt in range(self._max_retries + 1):
            try:
                return await method(request, timeout=t)
            except grpc.aio.AioRpcError as e:
                last_error = e
                code = e.code()

                if code in (
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                ):
                    if attempt < self._max_retries:
                        backoff = self._retry_backoff * (2 ** attempt)
                        logger.warning(
                            f"Akasha async call failed ({code.name}), "
                            f"retrying in {backoff:.1f}s "
                            f"(attempt {attempt + 1}/{self._max_retries})"
                        )
                        await asyncio.sleep(backoff)
                        continue

                raise

        raise last_error
