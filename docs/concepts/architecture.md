# Architecture

Akasha is built as a modular, layered system designed for sub-millisecond latency at the edge.

## System Overview

```mermaid
graph TB
    subgraph Clients
        P[Python SDK]
        N[Node.js SDK]
        C[curl / REST]
        G[gRPC Clients]
    end
    
    subgraph "Akasha Node"
        HTTP[HTTP Server<br/>Axum]
        GRPC[gRPC Server<br/>Tonic]
        AUTH[Auth Middleware<br/>JWT + API Keys]
        
        subgraph Core
            STORE[AkashaStore<br/>Radix Trie]
            PHER[Pheromone Engine<br/>Stigmergy]
            NIDRA[Nidra<br/>Memory Consolidation]
        end
        
        subgraph Cluster
            SWIM[SWIM Protocol<br/>Failure Detection]
            CRDT[CRDT State<br/>Eventual Consistency]
            RAFT[Raft Consensus<br/>Leader Election]
        end
    end
    
    P & N & C --> HTTP
    G --> GRPC
    HTTP & GRPC --> AUTH --> STORE
    STORE <--> PHER
    STORE --> NIDRA
    STORE <--> CRDT
    CRDT <--> SWIM
    SWIM <--> RAFT
    
    style STORE fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style PHER fill:#e84393,stroke:#fd79a8,color:#fff
    style NIDRA fill:#00cec9,stroke:#81ecec,color:#fff
```

## Core Components

### AkashaStore

The heart of Akasha — an in-memory **radix trie** (prefix tree) that provides:

- **O(k) lookups** where k is the key length (not the number of records)
- **Hierarchical paths** — `agents/planner/state` naturally forms a tree
- **Glob pattern queries** — `agents/*/state`, `memory/**`
- **Versioned records** — monotonically increasing version numbers
- **Atomic CAS** — Compare-And-Swap via `If-Match` headers

### Pheromone Engine

Agents coordinate without direct communication using **stigmergy** — the same principle ants use:

1. **Deposit** a signal on a trail with an intensity and half-life
2. **Sense** active trails to discover what other agents have found
3. Signals **decay exponentially** — recent information is stronger
4. Agents **reinforce** useful trails — emergent consensus

### Nidra (Memory Consolidation)

Inspired by how the human brain consolidates memories during sleep:

- **Working memory** (TTL: seconds-minutes) → scratch pad for active tasks
- **Episodic memory** (TTL: hours) → event logs, interactions
- **Semantic memory** (permanent) → distilled knowledge, facts
- **Procedural memory** (permanent) → how-to knowledge, workflows

Nidra periodically moves records from working → episodic → semantic based on access patterns and TTL policies.

### Clustering

Akasha supports 3+ node HA clusters using:

| Protocol | Purpose |
|----------|---------|
| **SWIM** | Failure detection, membership gossip |
| **CRDT** | Conflict-free replicated data types for eventual consistency |
| **Raft** | Leader election, configuration changes |

## Data Flow

```mermaid
sequenceDiagram
    participant A as Agent
    participant H as HTTP/gRPC
    participant S as AkashaStore
    participant C as CRDT
    participant P as Peers

    A->>H: PUT /records/agents/planner/state
    H->>S: Insert (path, value, version)
    S->>S: Radix trie insert + version bump
    S-->>C: Replicate delta
    C-->>P: Gossip to peers
    H-->>A: 200 OK {version: 3}
    
    Note over A,P: Entire flow: <2ms
```

## Performance Characteristics

| Operation | Latency (P50) | Latency (P99) |
|-----------|---------------|---------------|
| Write | 1.2ms | 3.5ms |
| Read | 0.8ms | 2.1ms |
| Query (100 results) | 2.5ms | 8.0ms |
| Pheromone deposit | 1.0ms | 2.8ms |
| Pheromone sense | 0.5ms | 1.5ms |

!!! info "Benchmark conditions"
    Measured on a 3-node Docker cluster, single-threaded sequential operations over HTTPS with self-signed certificates.
