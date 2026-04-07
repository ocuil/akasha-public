/**
 * Akasha HTTP Client — Lightweight REST client for Node.js.
 *
 * Uses the native fetch API (Node 18+) with no extra dependencies.
 * Great for scripts, dashboards, and environments where gRPC is overkill.
 */

import { AkashaRecord, AkashaEvent, recordFromJson, eventFromJson } from './models';

export interface AkashaHttpClientOptions {
  /** HTTP base URL (default: "http://localhost:7777") */
  baseUrl?: string;
  /** Default timeout in milliseconds (default: 10000) */
  timeout?: number;
}

export class AkashaHttpClient {
  private baseUrl: string;
  private timeout: number;

  constructor(options: AkashaHttpClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? 'http://localhost:7777').replace(/\/$/, '');
    this.timeout = options.timeout ?? 10000;
  }

  // -- Core CRUD --

  /** Write a record via REST API. */
  async put(
    path: string,
    value: unknown,
    options: { ttlSeconds?: number; tags?: { [key: string]: string } } = {}
  ): Promise<AkashaRecord> {
    const body: any = { value };
    if (options.ttlSeconds !== undefined) body.ttl_seconds = options.ttlSeconds;
    if (options.tags) body.tags = options.tags;

    const res = await this.fetch(`/api/v1/records/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    return recordFromJson(await res.json());
  }

  /** Read a record by path. Returns null if not found. */
  async get(path: string): Promise<AkashaRecord | null> {
    const res = await this.fetch(`/api/v1/records/${path}`);
    if (res.status === 404) return null;
    return recordFromJson(await res.json());
  }

  /** Delete a record. */
  async delete(path: string): Promise<boolean> {
    const res = await this.fetch(`/api/v1/records/${path}`, { method: 'DELETE' });
    return res.status === 204;
  }

  // -- Queries --

  /** Query records matching a glob pattern. */
  async query(
    pattern: string,
    options: { limit?: number } = {}
  ): Promise<AkashaRecord[]> {
    const params = new URLSearchParams({ pattern });
    if (options.limit !== undefined) params.set('limit', String(options.limit));

    const res = await this.fetch(`/api/v1/query?${params}`);
    const data = await res.json();
    return (data as any[]).map(recordFromJson);
  }

  // -- Convenience --

  /** List all registered agents. */
  async listAgents(): Promise<any[]> {
    const res = await this.fetch('/api/v1/agents');
    return res.json();
  }

  /** Get the full state tree snapshot. */
  async tree(): Promise<{ [key: string]: unknown }> {
    const res = await this.fetch('/api/v1/tree');
    return res.json();
  }

  /** Health check. */
  async health(): Promise<{ status: string; name: string; version: string; records: number }> {
    const res = await this.fetch('/api/v1/health');
    return res.json();
  }

  /** Get server metrics. */
  async metrics(): Promise<any> {
    const res = await this.fetch('/api/v1/metrics');
    return res.json();
  }

  // -- Stigmergy (Pheromone System) --

  /**
   * Deposit a pheromone trace. If a pheromone already exists at the
   * same trail, it is reinforced (intensities sum).
   */
  async depositPheromone(
    trail: string,
    options: {
      signalType?: string;
      emitter?: string;
      intensity?: number;
      halfLifeSecs?: number;
      payload?: unknown;
    } = {}
  ): Promise<any> {
    const body = {
      trail,
      signal_type: options.signalType ?? 'success',
      emitter: options.emitter ?? 'anonymous',
      intensity: options.intensity ?? 1.0,
      half_life_secs: options.halfLifeSecs ?? 3600,
      payload: options.payload,
    };

    const res = await this.fetch('/api/v1/pheromones', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    return res.json();
  }

  /** Sense active pheromones. */
  async sensePheromones(): Promise<any[]> {
    const res = await this.fetch('/api/v1/pheromones');
    return res.json();
  }

  // -- Cognitive Fabric --

  /**
   * Write a record to a specific memory layer.
   * @param layer One of: "working", "episodic", "semantic", "procedural"
   */
  async writeMemory(
    layer: string,
    namespace: string,
    key: string,
    value: unknown,
    options: { ttlSeconds?: number; tags?: { [key: string]: string } } = {}
  ): Promise<AkashaRecord> {
    const path = `memory/${layer}/${namespace}/${key}`;
    const merged = { ...options.tags, _memory_layer: layer };
    return this.put(path, value, { ttlSeconds: options.ttlSeconds, tags: merged });
  }

  /** Read a record from a memory layer. */
  async readMemory(
    layer: string,
    namespace: string,
    key: string
  ): Promise<AkashaRecord | null> {
    const path = `memory/${layer}/${namespace}/${key}`;
    return this.get(path);
  }

  /** Get Nidra consolidation status. */
  async nidraStatus(): Promise<any> {
    const res = await this.fetch('/api/v1/nidra/status');
    return res.json();
  }

  /** Get record counts per memory layer. */
  async memoryLayers(): Promise<any> {
    const res = await this.fetch('/api/v1/memory/layers');
    return res.json();
  }

  // -- WebSocket Subscription --

  /**
   * Subscribe to real-time events via WebSocket.
   * Requires the 'ws' package or a WebSocket-compatible environment.
   *
   * @param pattern Glob pattern to filter events
   * @param callback Function called for each event
   * @returns A close function to stop the subscription
   */
  subscribeWs(
    pattern: string,
    callback: (event: AkashaEvent) => void
  ): { close: () => void } {
    const wsUrl = this.baseUrl.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/api/v1/stream?pattern=${encodeURIComponent(pattern)}`);

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(typeof msg.data === 'string' ? msg.data : msg.data.toString());
        callback(eventFromJson(data));
      } catch (err) {
        console.warn('[Akasha] Failed to parse WebSocket event:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('[Akasha] WebSocket error:', err);
    };

    return {
      close: () => ws.close(),
    };
  }

  // -- Internal --

  private async fetch(path: string, init?: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const res = await globalThis.fetch(`${this.baseUrl}${path}`, {
        ...init,
        signal: controller.signal,
      });

      if (!res.ok && res.status !== 404 && res.status !== 204) {
        const body = await res.text().catch(() => '');
        throw new Error(`Akasha HTTP ${res.status}: ${body}`);
      }

      return res;
    } finally {
      clearTimeout(timer);
    }
  }
}
