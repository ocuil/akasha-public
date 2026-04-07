"""
Akasha Python SDK — Production-ready client for the Akasha shared memory system.

Provides both gRPC (high-performance, for agents) and HTTP (convenience, for scripts)
clients with connection pooling, automatic retry, async support, and type safety.
"""

from akasha.client import AkashaClient
from akasha.async_client import AsyncAkashaClient
from akasha.http_client import AkashaHttpClient
from akasha.models import Record, AkashaEvent, EventKind, MemoryLayer, SignalType

__version__ = "1.0.0"
__all__ = [
    "AkashaClient",
    "AsyncAkashaClient",
    "AkashaHttpClient",
    "Record",
    "AkashaEvent",
    "EventKind",
    "MemoryLayer",
    "SignalType",
]
