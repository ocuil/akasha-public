/**
 * Akasha data models — TypeScript representations of Akasha records and events.
 */

export enum EventKind {
  CREATED = 'CREATED',
  UPDATED = 'UPDATED',
  DELETED = 'DELETED',
  EXPIRED = 'EXPIRED',
  AGENT_REGISTERED = 'AGENT_REGISTERED',
  AGENT_HEARTBEAT = 'AGENT_HEARTBEAT',
  AGENT_LOST = 'AGENT_LOST',
}

export interface AkashaRecord {
  /** Hierarchical path (e.g., "agents/my-agent/state") */
  path: string;
  /** The stored value (deserialized) */
  value: unknown;
  /** Monotonically increasing version counter */
  version: number;
  /** Creation timestamp */
  createdAt?: Date;
  /** Last update timestamp */
  updatedAt?: Date;
  /** Time-to-live in seconds (undefined = no expiry) */
  ttlSeconds?: number;
  /** Metadata tags for filtering */
  tags: { [key: string]: string };
  /** Content encoding type */
  contentType: string;
}

export interface AkashaEvent {
  /** Event ID */
  id: string;
  /** Type of event */
  kind: EventKind;
  /** Affected path */
  path: string;
  /** The record involved (present for CREATED/UPDATED) */
  record?: AkashaRecord;
  /** When the event occurred */
  timestamp?: Date;
  /** Who originated the event */
  source?: string;
}

/** Convert a REST API JSON response to an AkashaRecord */
export function recordFromJson(data: any): AkashaRecord {
  return {
    path: data.path,
    value: data.value,
    version: data.version ?? 1,
    createdAt: data.created_at ? new Date(data.created_at) : undefined,
    updatedAt: data.updated_at ? new Date(data.updated_at) : undefined,
    ttlSeconds: data.ttl_seconds,
    tags: data.tags ?? {},
    contentType: data.content_type ?? 'msgpack',
  };
}

/** Convert a WebSocket JSON event to an AkashaEvent */
export function eventFromJson(data: any): AkashaEvent {
  return {
    id: data.id,
    kind: data.kind as EventKind,
    path: data.path,
    record: data.record ? recordFromJson(data.record) : undefined,
    timestamp: data.timestamp ? new Date(data.timestamp) : undefined,
    source: data.source,
  };
}
