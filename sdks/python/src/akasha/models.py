"""
Akasha data models — Pure Python representations of Akasha records and events.

These models are framework-agnostic and work with both gRPC and HTTP clients.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EventKind(str, Enum):
    """Types of events emitted by the Akasha store."""
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    EXPIRED = "EXPIRED"
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_HEARTBEAT = "AGENT_HEARTBEAT"
    AGENT_LOST = "AGENT_LOST"


class MemoryLayer(str, Enum):
    """The four memory layers of the cognitive fabric."""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

    @property
    def prefix(self) -> str:
        return f"memory/{self.value}/"

    @property
    def glob_all(self) -> str:
        return f"memory/{self.value}/**"

    @property
    def default_ttl_seconds(self) -> Optional[float]:
        defaults = {
            "working": 30 * 60,       # 30 min
            "episodic": 24 * 3600,     # 24 hours
            "semantic": None,          # permanent
            "procedural": None,        # permanent
        }
        return defaults[self.value]


class SignalType(str, Enum):
    """Types of pheromone signals agents can emit."""
    SUCCESS = "success"
    WARNING = "warning"
    RESOURCE = "resource"
    DISCOVERY = "discovery"
    CLAIM = "claim"


@dataclass
class Record:
    """A record in the Akasha shared memory store."""
    path: str
    value: Any
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    ttl_seconds: Optional[float] = None
    tags: dict[str, str] = field(default_factory=dict)
    content_type: str = "msgpack"

    def to_dict(self) -> dict:
        """Convert to a JSON-serializable dictionary."""
        d = {
            "path": self.path,
            "value": self.value,
            "version": self.version,
            "content_type": self.content_type,
        }
        if self.created_at:
            d["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            d["updated_at"] = self.updated_at.isoformat()
        if self.ttl_seconds is not None:
            d["ttl_seconds"] = self.ttl_seconds
        if self.tags:
            d["tags"] = self.tags
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Record:
        """Create a Record from a dictionary (e.g., HTTP API response)."""
        return cls(
            path=data["path"],
            value=data.get("value"),
            version=data.get("version", 1),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
            ttl_seconds=data.get("ttl_seconds"),
            tags=data.get("tags", {}),
            content_type=data.get("content_type", "msgpack"),
        )

    @classmethod
    def from_grpc(cls, pb_record) -> Record:
        """Create a Record from a gRPC protobuf Record message."""
        return cls(
            path=pb_record.path,
            value=_decode_grpc_value(pb_record.value, pb_record.content_type),
            version=pb_record.version,
            created_at=_timestamp_to_datetime(pb_record.created_at),
            updated_at=_timestamp_to_datetime(pb_record.updated_at),
            ttl_seconds=pb_record.ttl_seconds if pb_record.ttl_seconds > 0 else None,
            tags=dict(pb_record.tags),
            content_type=pb_record.content_type,
        )


@dataclass
class AkashaEvent:
    """An event emitted by the Akasha store."""
    id: str
    kind: EventKind
    path: str
    record: Optional[Record] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = None

    @classmethod
    def from_grpc(cls, pb_event) -> AkashaEvent:
        """Create an AkashaEvent from a gRPC protobuf Event message."""
        kind_map = {
            1: EventKind.CREATED,
            2: EventKind.UPDATED,
            3: EventKind.DELETED,
            4: EventKind.EXPIRED,
            5: EventKind.AGENT_REGISTERED,
            6: EventKind.AGENT_HEARTBEAT,
            7: EventKind.AGENT_LOST,
        }
        return cls(
            id=pb_event.id,
            kind=kind_map.get(pb_event.kind, EventKind.CREATED),
            path=pb_event.path,
            record=Record.from_grpc(pb_event.record) if pb_event.HasField("record") else None,
            timestamp=_timestamp_to_datetime(pb_event.timestamp),
            source=pb_event.source or None,
        )

    @classmethod
    def from_dict(cls, data: dict) -> AkashaEvent:
        """Create an AkashaEvent from a dictionary (e.g., WebSocket JSON)."""
        return cls(
            id=data["id"],
            kind=EventKind(data["kind"]),
            path=data["path"],
            record=Record.from_dict(data["record"]) if data.get("record") else None,
            timestamp=_parse_datetime(data.get("timestamp")),
            source=data.get("source"),
        )


# -- Helpers --

def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string."""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _timestamp_to_datetime(ts) -> Optional[datetime]:
    """Convert a protobuf Timestamp to a Python datetime."""
    if ts is None or (ts.seconds == 0 and ts.nanos == 0):
        return None
    return datetime.fromtimestamp(ts.seconds + ts.nanos / 1e9)


def _decode_grpc_value(raw_bytes: bytes, content_type: str) -> Any:
    """Decode gRPC raw bytes based on content type."""
    if not raw_bytes:
        return None
    try:
        import msgpack
        return msgpack.unpackb(raw_bytes, raw=False)
    except Exception:
        # Fallback: try JSON, then return raw bytes
        try:
            return json.loads(raw_bytes)
        except Exception:
            return raw_bytes
