import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_KIND_UNSPECIFIED: _ClassVar[EventKind]
    CREATED: _ClassVar[EventKind]
    UPDATED: _ClassVar[EventKind]
    DELETED: _ClassVar[EventKind]
    EXPIRED: _ClassVar[EventKind]
    AGENT_REGISTERED: _ClassVar[EventKind]
    AGENT_HEARTBEAT: _ClassVar[EventKind]
    AGENT_LOST: _ClassVar[EventKind]
EVENT_KIND_UNSPECIFIED: EventKind
CREATED: EventKind
UPDATED: EventKind
DELETED: EventKind
EXPIRED: EventKind
AGENT_REGISTERED: EventKind
AGENT_HEARTBEAT: EventKind
AGENT_LOST: EventKind

class Record(_message.Message):
    __slots__ = ("path", "value", "version", "created_at", "updated_at", "ttl_seconds", "tags", "content_type")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PATH_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    TTL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    path: str
    value: bytes
    version: int
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    ttl_seconds: float
    tags: _containers.ScalarMap[str, str]
    content_type: str
    def __init__(self, path: _Optional[str] = ..., value: _Optional[bytes] = ..., version: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., ttl_seconds: _Optional[float] = ..., tags: _Optional[_Mapping[str, str]] = ..., content_type: _Optional[str] = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ("id", "kind", "path", "record", "timestamp", "source")
    ID_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    RECORD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    id: str
    kind: EventKind
    path: str
    record: Record
    timestamp: _timestamp_pb2.Timestamp
    source: str
    def __init__(self, id: _Optional[str] = ..., kind: _Optional[_Union[EventKind, str]] = ..., path: _Optional[str] = ..., record: _Optional[_Union[Record, _Mapping]] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., source: _Optional[str] = ...) -> None: ...

class PutRequest(_message.Message):
    __slots__ = ("path", "value", "content_type", "ttl_seconds", "tags", "source")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PATH_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TTL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    path: str
    value: bytes
    content_type: str
    ttl_seconds: float
    tags: _containers.ScalarMap[str, str]
    source: str
    def __init__(self, path: _Optional[str] = ..., value: _Optional[bytes] = ..., content_type: _Optional[str] = ..., ttl_seconds: _Optional[float] = ..., tags: _Optional[_Mapping[str, str]] = ..., source: _Optional[str] = ...) -> None: ...

class PutResponse(_message.Message):
    __slots__ = ("record",)
    RECORD_FIELD_NUMBER: _ClassVar[int]
    record: Record
    def __init__(self, record: _Optional[_Union[Record, _Mapping]] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class GetResponse(_message.Message):
    __slots__ = ("record", "found")
    RECORD_FIELD_NUMBER: _ClassVar[int]
    FOUND_FIELD_NUMBER: _ClassVar[int]
    record: Record
    found: bool
    def __init__(self, record: _Optional[_Union[Record, _Mapping]] = ..., found: bool = ...) -> None: ...

class DeleteRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class DeleteResponse(_message.Message):
    __slots__ = ("deleted",)
    DELETED_FIELD_NUMBER: _ClassVar[int]
    deleted: bool
    def __init__(self, deleted: bool = ...) -> None: ...

class QueryRequest(_message.Message):
    __slots__ = ("pattern", "tag_filters", "limit")
    class TagFiltersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    TAG_FILTERS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    pattern: str
    tag_filters: _containers.ScalarMap[str, str]
    limit: int
    def __init__(self, pattern: _Optional[str] = ..., tag_filters: _Optional[_Mapping[str, str]] = ..., limit: _Optional[int] = ...) -> None: ...

class QueryResponse(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[Record]
    def __init__(self, records: _Optional[_Iterable[_Union[Record, _Mapping]]] = ...) -> None: ...

class ListPathsRequest(_message.Message):
    __slots__ = ("prefix",)
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    prefix: str
    def __init__(self, prefix: _Optional[str] = ...) -> None: ...

class ListPathsResponse(_message.Message):
    __slots__ = ("paths",)
    PATHS_FIELD_NUMBER: _ClassVar[int]
    paths: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, paths: _Optional[_Iterable[str]] = ...) -> None: ...

class SubscribeRequest(_message.Message):
    __slots__ = ("pattern",)
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    pattern: str
    def __init__(self, pattern: _Optional[str] = ...) -> None: ...

class RegisterAgentRequest(_message.Message):
    __slots__ = ("agent_id", "agent_type", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    agent_type: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, agent_id: _Optional[str] = ..., agent_type: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class RegisterAgentResponse(_message.Message):
    __slots__ = ("agent_path", "already_existed")
    AGENT_PATH_FIELD_NUMBER: _ClassVar[int]
    ALREADY_EXISTED_FIELD_NUMBER: _ClassVar[int]
    agent_path: str
    already_existed: bool
    def __init__(self, agent_path: _Optional[str] = ..., already_existed: bool = ...) -> None: ...

class HeartbeatRequest(_message.Message):
    __slots__ = ("agent_id", "status")
    class StatusEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    status: _containers.ScalarMap[str, str]
    def __init__(self, agent_id: _Optional[str] = ..., status: _Optional[_Mapping[str, str]] = ...) -> None: ...

class HeartbeatResponse(_message.Message):
    __slots__ = ("server_time",)
    SERVER_TIME_FIELD_NUMBER: _ClassVar[int]
    server_time: _timestamp_pb2.Timestamp
    def __init__(self, server_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetMetricsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMetricsResponse(_message.Message):
    __slots__ = ("total_records", "total_writes", "total_reads", "total_queries", "total_deletes", "connected_agents", "uptime_seconds", "custom_metrics")
    class CustomMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    TOTAL_RECORDS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_WRITES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_READS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_QUERIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_DELETES_FIELD_NUMBER: _ClassVar[int]
    CONNECTED_AGENTS_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_METRICS_FIELD_NUMBER: _ClassVar[int]
    total_records: int
    total_writes: int
    total_reads: int
    total_queries: int
    total_deletes: int
    connected_agents: int
    uptime_seconds: int
    custom_metrics: _containers.ScalarMap[str, int]
    def __init__(self, total_records: _Optional[int] = ..., total_writes: _Optional[int] = ..., total_reads: _Optional[int] = ..., total_queries: _Optional[int] = ..., total_deletes: _Optional[int] = ..., connected_agents: _Optional[int] = ..., uptime_seconds: _Optional[int] = ..., custom_metrics: _Optional[_Mapping[str, int]] = ...) -> None: ...

class DepositPheromoneRequest(_message.Message):
    __slots__ = ("trail", "signal_type", "emitter", "intensity", "half_life_secs", "payload")
    TRAIL_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMITTER_FIELD_NUMBER: _ClassVar[int]
    INTENSITY_FIELD_NUMBER: _ClassVar[int]
    HALF_LIFE_SECS_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    trail: str
    signal_type: str
    emitter: str
    intensity: float
    half_life_secs: float
    payload: bytes
    def __init__(self, trail: _Optional[str] = ..., signal_type: _Optional[str] = ..., emitter: _Optional[str] = ..., intensity: _Optional[float] = ..., half_life_secs: _Optional[float] = ..., payload: _Optional[bytes] = ...) -> None: ...

class DepositPheromoneResponse(_message.Message):
    __slots__ = ("trail", "store_path", "emitter", "signal_type", "initial_intensity", "current_intensity", "half_life_secs", "deposited_at", "is_evaporated", "reinforced")
    TRAIL_FIELD_NUMBER: _ClassVar[int]
    STORE_PATH_FIELD_NUMBER: _ClassVar[int]
    EMITTER_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    INITIAL_INTENSITY_FIELD_NUMBER: _ClassVar[int]
    CURRENT_INTENSITY_FIELD_NUMBER: _ClassVar[int]
    HALF_LIFE_SECS_FIELD_NUMBER: _ClassVar[int]
    DEPOSITED_AT_FIELD_NUMBER: _ClassVar[int]
    IS_EVAPORATED_FIELD_NUMBER: _ClassVar[int]
    REINFORCED_FIELD_NUMBER: _ClassVar[int]
    trail: str
    store_path: str
    emitter: str
    signal_type: str
    initial_intensity: float
    current_intensity: float
    half_life_secs: float
    deposited_at: str
    is_evaporated: bool
    reinforced: bool
    def __init__(self, trail: _Optional[str] = ..., store_path: _Optional[str] = ..., emitter: _Optional[str] = ..., signal_type: _Optional[str] = ..., initial_intensity: _Optional[float] = ..., current_intensity: _Optional[float] = ..., half_life_secs: _Optional[float] = ..., deposited_at: _Optional[str] = ..., is_evaporated: bool = ..., reinforced: bool = ...) -> None: ...

class SensePheromonesRequest(_message.Message):
    __slots__ = ("pattern",)
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    pattern: str
    def __init__(self, pattern: _Optional[str] = ...) -> None: ...

class SensePheromonesResponse(_message.Message):
    __slots__ = ("pheromones",)
    PHEROMONES_FIELD_NUMBER: _ClassVar[int]
    pheromones: _containers.RepeatedCompositeFieldContainer[PheromoneInfo]
    def __init__(self, pheromones: _Optional[_Iterable[_Union[PheromoneInfo, _Mapping]]] = ...) -> None: ...

class PheromoneInfo(_message.Message):
    __slots__ = ("trail", "store_path", "emitter", "signal_type", "initial_intensity", "current_intensity", "half_life_secs", "deposited_at", "is_evaporated")
    TRAIL_FIELD_NUMBER: _ClassVar[int]
    STORE_PATH_FIELD_NUMBER: _ClassVar[int]
    EMITTER_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    INITIAL_INTENSITY_FIELD_NUMBER: _ClassVar[int]
    CURRENT_INTENSITY_FIELD_NUMBER: _ClassVar[int]
    HALF_LIFE_SECS_FIELD_NUMBER: _ClassVar[int]
    DEPOSITED_AT_FIELD_NUMBER: _ClassVar[int]
    IS_EVAPORATED_FIELD_NUMBER: _ClassVar[int]
    trail: str
    store_path: str
    emitter: str
    signal_type: str
    initial_intensity: float
    current_intensity: float
    half_life_secs: float
    deposited_at: str
    is_evaporated: bool
    def __init__(self, trail: _Optional[str] = ..., store_path: _Optional[str] = ..., emitter: _Optional[str] = ..., signal_type: _Optional[str] = ..., initial_intensity: _Optional[float] = ..., current_intensity: _Optional[float] = ..., half_life_secs: _Optional[float] = ..., deposited_at: _Optional[str] = ..., is_evaporated: bool = ...) -> None: ...

class NidraStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class NidraStatusResponse(_message.Message):
    __slots__ = ("status", "last_cycle_json")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    LAST_CYCLE_JSON_FIELD_NUMBER: _ClassVar[int]
    status: str
    last_cycle_json: bytes
    def __init__(self, status: _Optional[str] = ..., last_cycle_json: _Optional[bytes] = ...) -> None: ...

class ListMemoryLayersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListMemoryLayersResponse(_message.Message):
    __slots__ = ("layers", "total_memory_records", "total_store_records")
    class LayersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MEMORY_RECORDS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_STORE_RECORDS_FIELD_NUMBER: _ClassVar[int]
    layers: _containers.ScalarMap[str, int]
    total_memory_records: int
    total_store_records: int
    def __init__(self, layers: _Optional[_Mapping[str, int]] = ..., total_memory_records: _Optional[int] = ..., total_store_records: _Optional[int] = ...) -> None: ...
