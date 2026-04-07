# Akasha Node.js SDK

[![Version](https://img.shields.io/badge/version-1.0.0-purple.svg)](https://github.com/ocuil/akasha-public)
[![Node](https://img.shields.io/badge/node-18%2B-brightgreen.svg)](https://nodejs.org)
[![TypeScript](https://img.shields.io/badge/typescript-5.4%2B-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/license-ASL--1.0-blue.svg)](../../LICENSE)

Production-ready Node.js/TypeScript client for [Akasha](https://github.com/ocuil/akasha-public) — The Shared Cognitive Fabric for Intelligent Agent Systems.

## Features

- **gRPC Client** — High-performance client with connection management
- **HTTP Client** — REST + WebSocket client for browser and lightweight use
- **TypeScript** — Full type definitions and IntelliSense support
- **Stigmergy** — Deposit, sense, and reinforce pheromone trails
- **Cognitive Fabric** — Read/write across the 4-layer memory hierarchy
- **WebSocket Subscriptions** — Real-time event streaming

## Installation

```bash
# From source
cd sdks/node
npm install
npm run build

# Or add to your project
npm install @akasha/client
```

## Quick Start

### gRPC Client

```typescript
import { AkashaClient } from '@akasha/client';

const client = new AkashaClient({ address: 'localhost:50051' });

// Write agent state
await client.put('agents/my-agent/state', {
  status: 'processing',
  task: 'data-pipeline',
  progress: 0.42,
});

// Read another agent's state
const record = await client.get('agents/other-agent/state');
if (record) {
  console.log(`Status: ${record.value.status}`);
}

// Query all agents
const agents = await client.query('agents/*/state');
for (const agent of agents) {
  console.log(`${agent.path}: ${JSON.stringify(agent.value)}`);
}

// Close when done
client.close();
```

## Core API

### CRUD Operations

```typescript
import { AkashaClient } from '@akasha/client';

const client = new AkashaClient({ address: 'localhost:50051' });

// Write with TTL and tags
const record = await client.put(
  'sensors/temperature/lab-01',
  { celsius: 22.5, humidity: 0.65 },
  {
    ttlSeconds: 300,          // expires in 5 minutes
    tags: { type: 'sensor', location: 'lab' },
    source: 'sensor-collector',
  }
);

// Read
const data = await client.get('sensors/temperature/lab-01');
console.log(data?.value);     // { celsius: 22.5, humidity: 0.65 }
console.log(data?.version);   // monotonic version counter

// Delete
const deleted = await client.delete('sensors/temperature/lab-01');

// Query with glob patterns
const allSensors = await client.query('sensors/*/lab-*');
const allAgents = await client.query('agents/**');  // recursive

// List paths
const paths = await client.listPaths('agents/');
```

### Agent Lifecycle

```typescript
// Register an agent
const path = await client.registerAgent('planner-01', {
  agentType: 'planner',
  metadata: { model: 'gpt-4', version: '2.1' },
});
// Returns: "agents/planner-01"

// Send periodic heartbeats
await client.heartbeat('planner-01', { task: 'active' });
```

### Stigmergy — Pheromone System

```typescript
import { AkashaClient, SignalType } from '@akasha/client';

const client = new AkashaClient({ address: 'localhost:50051' });

// Deposit a pheromone after completing work
const result = await client.depositPheromone({
  trail: 'pipelines/data-enrichment',
  signalType: SignalType.SUCCESS,
  emitter: 'agent-alpha',
  intensity: 1.0,
  halfLifeSecs: 3600,
  payload: { durationMs: 320, qualityScore: 0.95 },
});
console.log(`Intensity: ${result.currentIntensity}`);
console.log(`Reinforced: ${result.reinforced}`);

// Sense active pheromones
const trails = await client.sensePheromones('pipelines/*');
for (const trail of trails) {
  console.log(`  ${trail.trail}: intensity=${trail.currentIntensity.toFixed(2)}`);
}

// Warning pheromone (others learn to avoid)
await client.depositPheromone({
  trail: 'pipelines/legacy-etl',
  signalType: SignalType.WARNING,
  emitter: 'agent-gamma',
  payload: { error: 'timeout', retryCount: 3 },
});
```

### Cognitive Fabric — Memory Layers

```typescript
import { AkashaClient, MemoryLayer } from '@akasha/client';

const client = new AkashaClient({ address: 'localhost:50051' });

// Working Memory — scratchpad (auto-expires)
await client.writeMemory(MemoryLayer.WORKING, 'planner-01', 'current-context', {
  task: 'analyze-report',
  step: 3,
});

// Episodic Memory — what happened
await client.writeMemory(MemoryLayer.EPISODIC, 'data-pipeline', 'run-2024-01-15', {
  outcome: 'success',
  durationMs: 4520,
  recordsProcessed: 15000,
});

// Semantic Memory — distilled knowledge
await client.writeMemory(MemoryLayer.SEMANTIC, 'enrichment-patterns', 'batch-vs-stream', {
  insight: 'Batch enrichment is 3x faster for datasets > 10K records',
  confidence: 0.87,
});

// Procedural Memory — proven workflows
await client.writeMemory(MemoryLayer.PROCEDURAL, 'data-pipeline', 'standard-etl', {
  steps: ['extract', 'validate', 'transform', 'load', 'verify'],
  timeoutPerStepMs: 5000,
});

// Query all semantic knowledge
const knowledge = await client.queryMemory(MemoryLayer.SEMANTIC);
for (const record of knowledge) {
  console.log(`  ${record.path}: ${JSON.stringify(record.value)}`);
}
```

### Real-Time Subscriptions (gRPC)

```typescript
// Server-streaming subscription
const stream = client.subscribe('agents/**');

stream.on('data', (event) => {
  console.log(`[${event.kind}] ${event.path}`);
  if (event.record) {
    console.log(`  Value: ${JSON.stringify(event.record.value)}`);
  }
});

stream.on('error', (err) => console.error('Stream error:', err));
stream.on('end', () => console.log('Stream ended'));
```

### HTTP Client

```typescript
import { AkashaHttpClient } from '@akasha/client';

// For scripts that don't need gRPC
const client = new AkashaHttpClient({
  baseUrl: 'https://localhost:7777',
  verifySsl: false,
});

// Login (if auth is enabled)
await client.login('akasha', 'akasha');

// Same API surface
await client.put('agents/script/state', { status: 'running' });
const record = await client.get('agents/script/state');
const records = await client.query('agents/*/state');

// WebSocket real-time events
client.subscribe('agents/**', (event) => {
  console.log(`[${event.kind}] ${event.path}`);
});
```

## Configuration

```typescript
const client = new AkashaClient({
  address: 'localhost:50051',   // gRPC server address
  timeout: 10000,              // default timeout in ms
  maxRetries: 3,               // max retries for transient failures
  maxMessageSize: 64 * 1024 * 1024,  // 64MB
});
```

## Signal Types

| Type | Use Case |
|------|----------|
| `SignalType.SUCCESS` | Task completed successfully |
| `SignalType.WARNING` | Issue detected, others should avoid |
| `SignalType.RESOURCE` | Resource availability signal |
| `SignalType.DISCOVERY` | New information found |
| `SignalType.CLAIM` | "I'm working on this" lock signal |

## Memory Layers

| Layer | Lifespan | Use Case |
|-------|----------|----------|
| `MemoryLayer.WORKING` | Minutes | Current task scratchpad |
| `MemoryLayer.EPISODIC` | Hours → Days | Event logs, decisions |
| `MemoryLayer.SEMANTIC` | Days → Permanent | Facts, patterns, insights |
| `MemoryLayer.PROCEDURAL` | Permanent | Workflows, playbooks |

## License

[Akasha Source License 1.0 (ASL-1.0)](../../LICENSE)
