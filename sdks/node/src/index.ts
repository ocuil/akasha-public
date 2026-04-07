/**
 * Akasha Node.js SDK — Production-ready client for the Akasha shared memory system.
 *
 * Provides both gRPC (high-performance) and HTTP (convenience) clients
 * with TypeScript support, automatic retry, and streaming subscriptions.
 *
 * @module @akasha/client
 */

export { AkashaClient, AkashaClientOptions } from './client';
export { AkashaHttpClient, AkashaHttpClientOptions } from './http-client';
export { AkashaRecord, AkashaEvent, EventKind } from './models';
