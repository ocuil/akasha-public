# Node.js SDK Guide

## Installation

```bash
npm install akasha-sdk
# Or from source:
cd sdks/node && npm install && npm run build
```

## Client Options

| Client | Transport | Best For |
|--------|-----------|----------|
| `AkashaClient` | gRPC | Agents, microservices |
| `AkashaHttpClient` | HTTP/REST | Scripts, serverless functions |

## Quick Start

```typescript
import { AkashaHttpClient } from 'akasha-sdk';

const client = new AkashaHttpClient('https://localhost:7777', {
  apiKey: 'ak_your-api-key-here',
  rejectUnauthorized: false, // For self-signed certs
});

// Write a record
const record = await client.put('agents/node-agent/state', {
  status: 'active',
  language: 'typescript',
  startedAt: new Date().toISOString(),
});
console.log(`Created: ${record.path} v${record.version}`);

// Read
const state = await client.get('agents/node-agent/state');
console.log(`Status: ${state?.value.status}`);

// Query with glob
const allAgents = await client.query('agents/*/state');
allAgents.forEach(a => console.log(`  ${a.path}: ${JSON.stringify(a.value)}`));

// Delete
await client.delete('agents/node-agent/state');
await client.close();
```

## gRPC Client

```typescript
import { AkashaClient } from 'akasha-sdk';

const client = new AkashaClient('localhost:50051');

// CRUD operations
await client.put('tasks/123', { title: 'Process report', priority: 'high' });
const task = await client.get('tasks/123');

// Real-time event subscription
const stream = client.subscribe('agents/*');
stream.on('data', (event) => {
  console.log(`${event.kind}: ${event.path}`);
  if (event.record) {
    console.log(`  Value: ${JSON.stringify(event.record.value)}`);
  }
});
```

## Working with Memory Layers

```typescript
const client = new AkashaHttpClient('https://localhost:7777', {
  apiKey: 'ak_your-key',
});

// Working Memory — ephemeral context
await client.put('memory/working/analyzer/current-batch', {
  batchId: 'batch-2024-001',
  itemsTotal: 150,
  itemsProcessed: 0,
}, { ttlSeconds: 3600 }); // Auto-expires in 1 hour

// Episodic Memory — what happened
await client.put('memory/episodic/analyzer/batch-2024-001', {
  result: 'completed',
  itemsProcessed: 150,
  errorsFound: 3,
  duration: 45000,
});

// Semantic Memory — distilled knowledge
await client.put('memory/semantic/data-quality/common-errors', {
  patterns: [
    { type: 'missing_field', frequency: 0.12, fields: ['email', 'phone'] },
    { type: 'invalid_format', frequency: 0.05, fields: ['date'] },
  ],
  lastUpdated: new Date().toISOString(),
  sampleSize: 10000,
});

// Query all memories about a topic
const memories = await client.query('memory/**/data-quality/*');
```

## Working with Pheromones

```typescript
// Deposit a trail (via REST — pheromone endpoints are HTTP-only)
const resp = await fetch('https://localhost:7777/api/v1/pheromones', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ak_your-key',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    path: 'signals/data-ready/batch-001',
    signal_type: 'success',
    intensity: 0.95,
    emitter: 'analyzer-agent',
    metadata: {
      batch_id: 'batch-001',
      output_path: 'memory/episodic/analyzer/batch-001',
    },
    half_life_secs: 7200,
  }),
});

// Read trails
const trails = await fetch('https://localhost:7777/api/v1/pheromones', {
  headers: { 'Authorization': 'Bearer ak_your-key' },
}).then(r => r.json());

trails.forEach(t => {
  console.log(`Trail: ${t.path} (intensity: ${t.value.intensity})`);
});
```

## Building a TypeScript Agent

```typescript
import { AkashaHttpClient } from 'akasha-sdk';

const AGENT_ID = 'executor';
const client = new AkashaHttpClient('https://localhost:7777', {
  apiKey: 'ak_your-key',
  rejectUnauthorized: false,
});

async function runAgent() {
  // Register
  await client.put(`agents/${AGENT_ID}/state`, {
    status: 'active',
    startedAt: new Date().toISOString(),
    capabilities: ['execution', 'validation'],
  });
  console.log(`✅ Agent ${AGENT_ID} registered`);

  // Main loop
  while (true) {
    // Check for pheromone signals from other agents
    const signals = await fetch('https://localhost:7777/api/v1/pheromones', {
      headers: { 'Authorization': 'Bearer ak_your-key' },
    }).then(r => r.json());

    const readySignals = signals.filter(
      (s: any) => s.value.signal_type === 'success' && s.value.intensity > 0.3
    );

    for (const signal of readySignals) {
      const taskId = signal.path.split('/').pop();
      console.log(`📋 Detected ready signal: ${taskId}`);

      // Read the source data
      const source = await client.get(signal.value.metadata?.output_path);
      if (!source) continue;

      // Process...
      await client.put(`agents/${AGENT_ID}/state`, {
        status: 'executing',
        currentTask: taskId,
      });

      // Write result
      await client.put(`memory/episodic/${AGENT_ID}/${taskId}`, {
        action: 'executed',
        input: source.value,
        result: { success: true },
        completedAt: new Date().toISOString(),
      });

      console.log(`  ✅ Task ${taskId} executed`);
    }

    // Heartbeat
    await client.put(`agents/${AGENT_ID}/state`, {
      status: 'idle',
      lastHeartbeat: new Date().toISOString(),
    });

    await new Promise(r => setTimeout(r, 5000)); // 5s poll
  }
}

runAgent().catch(console.error);
```

## Path Conventions

Same as [Python SDK conventions](sdk-python.md#path-conventions).

## Error Handling

```typescript
try {
  const record = await client.get('nonexistent/path');
  // Returns null if not found
  if (!record) {
    console.log('Record not found');
  }
} catch (error) {
  if (error.status === 401) {
    console.error('Authentication failed — check your API key');
  } else if (error.status === 403) {
    console.error('Forbidden — API key lacks namespace access');
  } else {
    console.error('Unexpected error:', error.message);
  }
}
```
