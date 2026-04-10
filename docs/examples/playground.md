# Interactive Playground

Try Akasha live in your browser — no install required.

## Open the Playground

The playground is a self-contained HTML page that connects to any Akasha instance:

**[→ Open Playground](https://github.com/ocuil/akasha-public/blob/main/examples/playground/index.html)**

Or serve it locally:

```bash
cd examples/playground
python3 -m http.server 8080
# Open http://localhost:8080
```

## Available Scenarios

| Scenario | Description |
|----------|-------------|
| **Hello Akasha** | Write + read + delete — the simplest interaction |
| **Memory Layers** | Write to Working, Episodic, Semantic, Procedural |
| **Optimistic Concurrency** | CAS race condition demo |
| **Pheromone Trails** | Deposit and sense coordination signals |
| **3-Agent Pipeline** | Scout → Analyst → Reporter with stigmergy |
| **Latency Benchmark** | 50 writes + 50 reads with P50/P99 metrics |
