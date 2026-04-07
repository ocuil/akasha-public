"""
Akasha gRPC Client — Synchronous, production-ready client.

Features:
  - Connection pooling via gRPC channel
  - Automatic retry with exponential backoff
  - Deadline/timeout support on every call
  - Thread-safe for use in multi-threaded agent systems
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Iterator, Optional

import grpc
import msgpack

from akasha.models import AkashaEvent, MemoryLayer, Record, SignalType

# Lazy-loaded generated protobuf stubs
_pb2 = None
_pb2_grpc = None

logger = logging.getLogger("akasha.client")


def _load_stubs():
    """Lazy-load the generated protobuf modules."""
    global _pb2, _pb2_grpc
    if _pb2 is None:
        from akasha.proto import akasha_pb2, akasha_pb2_grpc
        _pb2 = akasha_pb2
        _pb2_grpc = akasha_pb2_grpc


class AkashaClient:
    """
    Synchronous gRPC client for Akasha.

    Usage:
        client = AkashaClient("localhost:50051")

        # Write state
        record = client.put("agents/my-agent/state", {"status": "running"})

        # Read state
        record = client.get("agents/my-agent/state")

        # Query with glob
        records = client.query("agents/*/state")

        # Subscribe to changes
        for event in client.subscribe("agents/**"):
            print(f"{event.path} changed: {event.record.value}")

        client.close()
    """

    def __init__(
        self,
        address: str = "localhost:50051",
        *,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
        max_message_size: int = 64 * 1024 * 1024,  # 64MB
    ):
        """
        Initialize the Akasha gRPC client.

        Args:
            address: gRPC server address (host:port).
            timeout: Default timeout in seconds for unary calls.
            max_retries: Maximum number of retry attempts for transient failures.
            retry_backoff: Initial backoff in seconds (doubles on each retry).
            max_message_size: Maximum gRPC message size in bytes.
        """
        _load_stubs()

        self._address = address
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff

        self._channel = grpc.insecure_channel(
            address,
            options=[
                ("grpc.max_send_message_length", max_message_size),
                ("grpc.max_receive_message_length", max_message_size),
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.keepalive_permit_without_calls", 1),
                ("grpc.http2.min_ping_interval_without_data_ms", 15000),
            ],
        )
        self._stub = _pb2_grpc.AkashaStub(self._channel)

        logger.info(f"Akasha client connected to {address}")

    def close(self):
        """Close the gRPC channel."""
        if self._channel:
            self._channel.close()
            logger.info("Akasha client disconnected")

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
        content_type: str = "msgpack",
        ttl_seconds: float = 0,
        tags: Optional[dict[str, str]] = None,
        source: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Record:
        """
        Write a record to Akasha.

        Args:
            path: Hierarchical path (e.g., "agents/my-agent/state").
            value: Any JSON-serializable value.
            content_type: Encoding format ("msgpack" or "json").
            ttl_seconds: Time-to-live in seconds (0 = no expiry).
            tags: Metadata tags for filtering.
            source: Identifier of who wrote this record.
            timeout: Override the default timeout.

        Returns:
            The created/updated Record with version info.
        """
        encoded = self._encode_value(value, content_type)

        request = _pb2.PutRequest(
            path=path,
            value=encoded,
            content_type=content_type,
            ttl_seconds=ttl_seconds,
            tags=tags or {},
            source=source or "",
        )

        response = self._call_with_retry(
            self._stub.Put, request, timeout=timeout
        )
        return Record.from_grpc(response.record)

    def get(self, path: str, *, timeout: Optional[float] = None) -> Optional[Record]:
        """
        Read a record by exact path.

        Returns:
            The Record if found, None otherwise.
        """
        request = _pb2.GetRequest(path=path)
        response = self._call_with_retry(
            self._stub.Get, request, timeout=timeout
        )

        if response.found:
            return Record.from_grpc(response.record)
        return None

    def delete(self, path: str, *, timeout: Optional[float] = None) -> bool:
        """
        Delete a record.

        Returns:
            True if the record existed and was deleted.
        """
        request = _pb2.DeleteRequest(path=path)
        response = self._call_with_retry(
            self._stub.Delete, request, timeout=timeout
        )
        return response.deleted

    # -- Queries --

    def query(
        self,
        pattern: str,
        *,
        tag_filters: Optional[dict[str, str]] = None,
        limit: int = 0,
        timeout: Optional[float] = None,
    ) -> list[Record]:
        """
        Query records matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "agents/*/state", "agents/**").
            tag_filters: Filter by tags (AND logic).
            limit: Max results (0 = unlimited).

        Returns:
            List of matching Records.
        """
        request = _pb2.QueryRequest(
            pattern=pattern,
            tag_filters=tag_filters or {},
            limit=limit,
        )
        response = self._call_with_retry(
            self._stub.Query, request, timeout=timeout
        )
        return [Record.from_grpc(r) for r in response.records]

    def list_paths(
        self, prefix: str = "", *, timeout: Optional[float] = None
    ) -> list[str]:
        """List all paths under a prefix."""
        request = _pb2.ListPathsRequest(prefix=prefix)
        response = self._call_with_retry(
            self._stub.ListPaths, request, timeout=timeout
        )
        return list(response.paths)

    # -- Agent Lifecycle --

    def register_agent(
        self,
        agent_id: str,
        agent_type: str = "generic",
        metadata: Optional[dict[str, str]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Register an agent with Akasha.

        Returns:
            The agent's base path (e.g., "agents/my-agent").
        """
        request = _pb2.RegisterAgentRequest(
            agent_id=agent_id,
            agent_type=agent_type,
            metadata=metadata or {},
        )
        response = self._call_with_retry(
            self._stub.RegisterAgent, request, timeout=timeout
        )
        return response.agent_path

    def heartbeat(
        self,
        agent_id: str,
        status: Optional[dict[str, str]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> None:
        """Send a heartbeat for an agent, optionally updating its status."""
        request = _pb2.HeartbeatRequest(
            agent_id=agent_id,
            status=status or {},
        )
        self._call_with_retry(
            self._stub.Heartbeat, request, timeout=timeout
        )

    # -- Subscriptions --

    def subscribe(
        self,
        pattern: str = "**",
    ) -> Iterator[AkashaEvent]:
        """
        Subscribe to real-time events matching a glob pattern.

        This is a blocking iterator that yields events as they occur.
        Use in a loop or in a separate thread.

        Args:
            pattern: Glob pattern to filter events.

        Yields:
            AkashaEvent for each matching event.
        """
        request = _pb2.SubscribeRequest(pattern=pattern)

        for pb_event in self._stub.Subscribe(request):
            try:
                yield AkashaEvent.from_grpc(pb_event)
            except Exception as e:
                logger.warning(f"Failed to parse event: {e}")

    # -- System --

    def get_metrics(self, *, timeout: Optional[float] = None) -> dict:
        """Get server metrics."""
        request = _pb2.GetMetricsRequest()
        response = self._call_with_retry(
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

    # ================================================================
    # Stigmergy — Pheromone System
    # ================================================================

    def deposit_pheromone(
        self,
        trail: str,
        signal_type: str | SignalType = SignalType.SUCCESS,
        *,
        intensity: float = 1.0,
        half_life_secs: float = 3600,
        emitter: Optional[str] = None,
        payload: Any = None,
        timeout: Optional[float] = None,
    ) -> dict:
        """
        Deposit a pheromone trace at the given trail via native gRPC RPC.

        If a pheromone already exists at the same trail, it is automatically
        reinforced (intensities sum).

        Args:
            trail: Logical path (e.g., "pipelines/data-enrichment").
            signal_type: Type of signal (success, warning, resource, discovery, claim).
            intensity: Initial intensity (default 1.0).
            half_life_secs: Half-life for exponential decay in seconds.
            emitter: ID of the agent leaving the trace.
            payload: Optional data payload (will be MessagePack encoded).

        Returns:
            Dict with pheromone info including current_intensity and reinforced flag.
        """
        _load_stubs()
        signal = signal_type.value if isinstance(signal_type, SignalType) else signal_type

        payload_bytes = b""
        if payload is not None:
            payload_bytes = msgpack.packb(payload, use_bin_type=True)

        request = _pb2.DepositPheromoneRequest(
            trail=trail,
            signal_type=signal,
            emitter=emitter or "unknown",
            intensity=intensity,
            half_life_secs=half_life_secs,
            payload=payload_bytes,
        )

        response = self._stub.DepositPheromone(
            request,
            timeout=timeout or self._timeout,
        )

        return {
            "trail": response.trail,
            "store_path": response.store_path,
            "emitter": response.emitter,
            "signal_type": response.signal_type,
            "initial_intensity": response.initial_intensity,
            "current_intensity": response.current_intensity,
            "half_life_secs": response.half_life_secs,
            "deposited_at": response.deposited_at,
            "is_evaporated": response.is_evaporated,
            "reinforced": response.reinforced,
        }

    def sense_pheromones(
        self,
        pattern: str = "*",
        *,
        timeout: Optional[float] = None,
    ) -> list[dict]:
        """
        Sense active pheromone traces matching a pattern via native gRPC RPC.

        Args:
            pattern: Glob pattern relative to the pheromone prefix (e.g., "pipelines/*").

        Returns:
            List of pheromone info dicts with current_intensity and decay state.
        """
        _load_stubs()
        request = _pb2.SensePheromonesRequest(pattern=pattern)
        response = self._stub.SensePheromones(
            request,
            timeout=timeout or self._timeout,
        )

        return [
            {
                "trail": p.trail,
                "store_path": p.store_path,
                "emitter": p.emitter,
                "signal_type": p.signal_type,
                "initial_intensity": p.initial_intensity,
                "current_intensity": p.current_intensity,
                "half_life_secs": p.half_life_secs,
                "deposited_at": p.deposited_at,
                "is_evaporated": p.is_evaporated,
            }
            for p in response.pheromones
        ]

    def reinforce_pheromone(
        self,
        trail: str,
        additional_intensity: float = 0.5,
        *,
        emitter: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> dict:
        """
        Reinforce an existing pheromone trail by depositing again.

        This is a convenience wrapper around deposit_pheromone — deposits
        at the same trail so the server auto-reinforces (intensities sum).

        Args:
            trail: The trail path to reinforce.
            additional_intensity: Intensity to add.
            emitter: Agent reinforcing the trail.

        Returns:
            Updated pheromone info dict.
        """
        return self.deposit_pheromone(
            trail,
            signal_type=SignalType.SUCCESS,
            intensity=additional_intensity,
            emitter=emitter,
            timeout=timeout,
        )

    # ================================================================
    # Shared Cognitive Fabric — Memory Hierarchy
    # ================================================================

    def write_memory(
        self,
        layer: MemoryLayer,
        namespace: str,
        key: str,
        value: Any,
        *,
        ttl_seconds: Optional[float] = None,
        tags: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Record:
        """
        Write a record to a specific memory layer.

        Args:
            layer: The memory layer (WORKING, EPISODIC, SEMANTIC, PROCEDURAL).
            namespace: Namespace within the layer (e.g., agent ID or topic).
            key: Record key within the namespace.
            value: Any JSON-serializable value.
            ttl_seconds: Override the layer's default TTL.
            tags: Additional tags (layer tag is added automatically).

        Returns:
            The created/updated Record.
        """
        path = f"{layer.prefix}{namespace}/{key}"
        merged_tags = {"_memory_layer": layer.value}
        if tags:
            merged_tags.update(tags)

        ttl = ttl_seconds if ttl_seconds is not None else (layer.default_ttl_seconds or 0)

        return self.put(
            path, value,
            ttl_seconds=ttl,
            tags=merged_tags,
            timeout=timeout,
        )

    def read_memory(
        self,
        layer: MemoryLayer,
        namespace: str,
        key: str,
        *,
        timeout: Optional[float] = None,
    ) -> Optional[Record]:
        """
        Read a record from a specific memory layer.

        Returns:
            The Record if found, None otherwise.
        """
        path = f"{layer.prefix}{namespace}/{key}"
        return self.get(path, timeout=timeout)

    def query_memory(
        self,
        layer: MemoryLayer,
        namespace: Optional[str] = None,
        *,
        limit: int = 0,
        timeout: Optional[float] = None,
    ) -> list[Record]:
        """
        Query all records within a memory layer, optionally filtered by namespace.

        Args:
            layer: The memory layer to query.
            namespace: Optional namespace filter (None = all in layer).
            limit: Max results (0 = unlimited).

        Returns:
            List of matching Records.
        """
        if namespace:
            pattern = f"{layer.prefix}{namespace}/*"
        else:
            pattern = layer.glob_all

        return self.query(pattern, limit=limit, timeout=timeout)

    # ================================================================
    # Nidra — Consolidation Status
    # ================================================================

    def get_nidra_status(self, *, timeout: Optional[float] = None) -> Optional[dict]:
        """
        Get the last Nidra consolidation cycle report.

        Returns:
            The cycle report as a dict, or None if no cycles have run yet.
        """
        record = self.get("system/nidra/last-cycle", timeout=timeout)
        if record and isinstance(record.value, dict):
            return record.value
        return None

    # -- Internal helpers --

    def _encode_value(self, value: Any, content_type: str) -> bytes:
        """Encode a Python value to bytes for transmission."""
        if content_type == "json":
            return json.dumps(value).encode("utf-8")
        else:
            return msgpack.packb(value, use_bin_type=True)

    def _call_with_retry(self, method, request, *, timeout: Optional[float] = None):
        """Execute a gRPC call with retry logic for transient failures."""
        t = timeout or self._timeout
        last_error = None

        for attempt in range(self._max_retries + 1):
            try:
                return method(request, timeout=t)
            except grpc.RpcError as e:
                last_error = e
                code = e.code()

                # Only retry on transient errors
                if code in (
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                ):
                    if attempt < self._max_retries:
                        backoff = self._retry_backoff * (2 ** attempt)
                        logger.warning(
                            f"Akasha call failed ({code.name}), "
                            f"retrying in {backoff:.1f}s "
                            f"(attempt {attempt + 1}/{self._max_retries})"
                        )
                        time.sleep(backoff)
                        continue

                # Non-transient error or max retries exceeded
                raise

        raise last_error
