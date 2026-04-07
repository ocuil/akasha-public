/**
 * Akasha gRPC Client — Production-ready TypeScript gRPC client.
 *
 * Features:
 *   - Dynamic protobuf loading (no codegen required)
 *   - Connection keepalive and reconnection
 *   - Automatic retry with exponential backoff
 *   - Streaming subscriptions via async iterators
 *   - Full TypeScript type safety
 */

import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import * as path from 'path';
import { pack, unpack } from 'msgpackr';
import { AkashaRecord, AkashaEvent, EventKind } from './models';

export interface AkashaClientOptions {
  /** gRPC server address (default: "localhost:50051") */
  address?: string;
  /** Default timeout in milliseconds (default: 10000) */
  timeout?: number;
  /** Maximum retry attempts (default: 3) */
  maxRetries?: number;
  /** Initial retry backoff in ms (default: 500) */
  retryBackoff?: number;
  /** Path to the proto file (auto-resolved if not specified) */
  protoPath?: string;
}

// GRPC Event kind enum values from proto
const GRPC_EVENT_KIND_MAP: { [key: number]: EventKind } = {
  1: EventKind.CREATED,
  2: EventKind.UPDATED,
  3: EventKind.DELETED,
  4: EventKind.EXPIRED,
  5: EventKind.AGENT_REGISTERED,
  6: EventKind.AGENT_HEARTBEAT,
  7: EventKind.AGENT_LOST,
};

export class AkashaClient {
  private client: any;
  private timeout: number;
  private maxRetries: number;
  private retryBackoff: number;

  constructor(options: AkashaClientOptions = {}) {
    const {
      address = 'localhost:50051',
      timeout = 10000,
      maxRetries = 3,
      retryBackoff = 500,
      protoPath,
    } = options;

    this.timeout = timeout;
    this.maxRetries = maxRetries;
    this.retryBackoff = retryBackoff;

    // Resolve proto file path
    const resolvedProtoPath = protoPath ?? path.resolve(
      __dirname, '..', '..', '..', '..', 'akasha-server', 'proto', 'akasha.proto'
    );

    // Load proto definition dynamically
    const packageDefinition = protoLoader.loadSync(resolvedProtoPath, {
      keepCase: false,
      longs: Number,
      enums: Number,
      defaults: true,
      oneofs: true,
      includeDirs: [path.dirname(resolvedProtoPath)],
    });

    const protoDescriptor = grpc.loadPackageDefinition(packageDefinition) as any;
    const AkashaService = protoDescriptor.akasha.Akasha;

    this.client = new AkashaService(
      address,
      grpc.credentials.createInsecure(),
      {
        'grpc.max_send_message_length': 64 * 1024 * 1024,
        'grpc.max_receive_message_length': 64 * 1024 * 1024,
        'grpc.keepalive_time_ms': 30000,
        'grpc.keepalive_timeout_ms': 10000,
        'grpc.keepalive_permit_without_calls': 1,
      }
    );
  }

  /** Close the gRPC channel. */
  close(): void {
    this.client.close();
  }

  // -- Core CRUD --

  /** Write a record to Akasha. */
  async put(
    pathStr: string,
    value: unknown,
    options: {
      contentType?: string;
      ttlSeconds?: number;
      tags?: { [key: string]: string };
      source?: string;
    } = {}
  ): Promise<AkashaRecord> {
    const {
      contentType = 'msgpack',
      ttlSeconds = 0,
      tags = {},
      source = '',
    } = options;

    const encoded = this.encodeValue(value, contentType);

    const request = {
      path: pathStr,
      value: encoded,
      contentType,
      ttlSeconds,
      tags,
      source,
    };

    const response = await this.callWithRetry<any>('put', request);
    return this.recordFromGrpc(response.record);
  }

  /** Read a record by exact path. Returns null if not found. */
  async get(pathStr: string): Promise<AkashaRecord | null> {
    const response = await this.callWithRetry<any>('get', { path: pathStr });
    if (response.found) {
      return this.recordFromGrpc(response.record);
    }
    return null;
  }

  /** Delete a record. Returns true if the record existed. */
  async delete(pathStr: string): Promise<boolean> {
    const response = await this.callWithRetry<any>('delete', { path: pathStr });
    return response.deleted;
  }

  // -- Queries --

  /** Query records matching a glob pattern. */
  async query(
    pattern: string,
    options: { tagFilters?: { [key: string]: string }; limit?: number } = {}
  ): Promise<AkashaRecord[]> {
    const { tagFilters = {}, limit = 0 } = options;
    const response = await this.callWithRetry<any>('query', {
      pattern,
      tagFilters,
      limit,
    });
    return (response.records || []).map((r: any) => this.recordFromGrpc(r));
  }

  /** List all paths under a prefix. */
  async listPaths(prefix: string = ''): Promise<string[]> {
    const response = await this.callWithRetry<any>('listPaths', { prefix });
    return response.paths || [];
  }

  // -- Agent Lifecycle --

  /** Register an agent with Akasha. Returns the agent's base path. */
  async registerAgent(
    agentId: string,
    agentType: string = 'generic',
    metadata: { [key: string]: string } = {}
  ): Promise<{ agentPath: string; alreadyExisted: boolean }> {
    const response = await this.callWithRetry<any>('registerAgent', {
      agentId,
      agentType,
      metadata,
    });
    return {
      agentPath: response.agentPath,
      alreadyExisted: response.alreadyExisted,
    };
  }

  /** Send a heartbeat for an agent. */
  async heartbeat(
    agentId: string,
    status: { [key: string]: string } = {}
  ): Promise<void> {
    await this.callWithRetry<any>('heartbeat', { agentId, status });
  }

  // -- Subscriptions --

  /**
   * Subscribe to real-time events matching a glob pattern.
   * Returns an async iterable that yields AkashaEvent objects.
   */
  subscribe(pattern: string = '**'): AsyncIterable<AkashaEvent> {
    const stream = this.client.subscribe({ pattern });
    const self = this;

    return {
      [Symbol.asyncIterator]() {
        return {
          next(): Promise<IteratorResult<AkashaEvent>> {
            return new Promise((resolve, reject) => {
              stream.once('data', (data: any) => {
                try {
                  const event = self.eventFromGrpc(data);
                  resolve({ value: event, done: false });
                } catch (err) {
                  reject(err);
                }
              });
              stream.once('end', () => {
                resolve({ value: undefined as any, done: true });
              });
              stream.once('error', (err: Error) => {
                reject(err);
              });
            });
          },
          return(): Promise<IteratorResult<AkashaEvent>> {
            stream.cancel();
            return Promise.resolve({ value: undefined as any, done: true });
          },
        };
      },
    };
  }

  // -- System --

  /** Get server metrics. */
  async getMetrics(): Promise<{
    totalRecords: number;
    totalWrites: number;
    totalReads: number;
    totalQueries: number;
    totalDeletes: number;
    connectedAgents: number;
    uptimeSeconds: number;
    customMetrics: { [key: string]: number };
  }> {
    const response = await this.callWithRetry<any>('getMetrics', {});
    return {
      totalRecords: response.totalRecords ?? 0,
      totalWrites: response.totalWrites ?? 0,
      totalReads: response.totalReads ?? 0,
      totalQueries: response.totalQueries ?? 0,
      totalDeletes: response.totalDeletes ?? 0,
      connectedAgents: response.connectedAgents ?? 0,
      uptimeSeconds: response.uptimeSeconds ?? 0,
      customMetrics: response.customMetrics ?? {},
    };
  }

  // -- Internal helpers --

  private encodeValue(value: unknown, contentType: string): Buffer {
    if (contentType === 'json') {
      return Buffer.from(JSON.stringify(value), 'utf-8');
    }
    return Buffer.from(pack(value));
  }

  private decodeValue(raw: Uint8Array | Buffer, contentType: string): unknown {
    if (!raw || raw.length === 0) return null;
    try {
      return unpack(Buffer.from(raw));
    } catch {
      try {
        return JSON.parse(Buffer.from(raw).toString('utf-8'));
      } catch {
        return raw;
      }
    }
  }

  private recordFromGrpc(pb: any): AkashaRecord {
    return {
      path: pb.path,
      value: this.decodeValue(pb.value, pb.contentType),
      version: pb.version ?? 1,
      createdAt: pb.createdAt ? this.timestampToDate(pb.createdAt) : undefined,
      updatedAt: pb.updatedAt ? this.timestampToDate(pb.updatedAt) : undefined,
      ttlSeconds: pb.ttlSeconds > 0 ? pb.ttlSeconds : undefined,
      tags: pb.tags ?? {},
      contentType: pb.contentType ?? 'msgpack',
    };
  }

  private eventFromGrpc(pb: any): AkashaEvent {
    return {
      id: pb.id,
      kind: GRPC_EVENT_KIND_MAP[pb.kind] ?? EventKind.CREATED,
      path: pb.path,
      record: pb.record ? this.recordFromGrpc(pb.record) : undefined,
      timestamp: pb.timestamp ? this.timestampToDate(pb.timestamp) : undefined,
      source: pb.source || undefined,
    };
  }

  private timestampToDate(ts: any): Date {
    const seconds = typeof ts.seconds === 'number' ? ts.seconds : 0;
    const nanos = typeof ts.nanos === 'number' ? ts.nanos : 0;
    return new Date(seconds * 1000 + nanos / 1e6);
  }

  private callWithRetry<T>(method: string, request: any): Promise<T> {
    return new Promise((resolve, reject) => {
      let attempt = 0;

      const attempt_call = () => {
        const deadline = new Date(Date.now() + this.timeout);

        this.client[method](request, { deadline }, (err: any, response: T) => {
          if (err) {
            const retryable = [
              grpc.status.UNAVAILABLE,
              grpc.status.DEADLINE_EXCEEDED,
              grpc.status.RESOURCE_EXHAUSTED,
            ];

            if (retryable.includes(err.code) && attempt < this.maxRetries) {
              attempt++;
              const backoff = this.retryBackoff * Math.pow(2, attempt - 1);
              console.warn(
                `[Akasha] Call to ${method} failed (${err.code}), ` +
                `retrying in ${backoff}ms (attempt ${attempt}/${this.maxRetries})`
              );
              setTimeout(attempt_call, backoff);
              return;
            }

            reject(err);
            return;
          }

          resolve(response);
        });
      };

      attempt_call();
    });
  }
}
