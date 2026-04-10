# Node.js SDK

[![npm](https://img.shields.io/npm/v/akasha-memory?color=CB3837&label=npm)](https://www.npmjs.com/package/akasha-memory)

TypeScript-first Node.js client for Akasha with HTTP and gRPC support.

## Installation

```bash
npm install akasha-memory
```

## Quick Start

```typescript
import { AkashaHttpClient } from 'akasha-memory';

const client = new AkashaHttpClient({
  baseUrl: 'https://localhost:7777',
  token: 'your-jwt-token',
  rejectUnauthorized: false,  // for self-signed certs
});

// Write
const record = await client.put('agents/planner/state', {
  status: 'analyzing',
  confidence: 0.85,
});

// Read
const state = await client.get('agents/planner/state');
console.log(state?.value); // { status: 'analyzing', ... }

// Query
const agents = await client.query('agents/*/state');

// Delete
await client.delete('agents/planner/state');
```

## CAS (Optimistic Concurrency)

```typescript
import { CasConflictError } from 'akasha-memory';

const record = await client.get('shared/counter');

try {
  await client.putCas(
    'shared/counter',
    { count: record!.value.count + 1 },
    record!.version,
  );
} catch (e) {
  if (e instanceof CasConflictError) {
    console.log(`Conflict: v${e.expectedVersion} vs v${e.actualVersion}`);
    // Retry with fresh data
  }
}
```

## gRPC Client

For streaming subscriptions and higher throughput:

```typescript
import { AkashaClient } from 'akasha-memory';

const grpc = new AkashaClient({ address: 'localhost:50051' });

await grpc.put('agents/worker/state', { status: 'idle' });

// Real-time streaming
for await (const event of grpc.subscribe('agents/**')) {
  console.log(`[${event.kind}] ${event.path}`);
}
```

## Authentication

```typescript
// JWT Token
const client = new AkashaHttpClient({ token: 'eyJ0eXAi...' });

// API Key
const client = new AkashaHttpClient({ apiKey: 'your-key' });
```
