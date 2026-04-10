# Quick Start

Get Akasha running and execute your first operations in under 5 minutes.

## 1. Start Akasha

```bash
docker run -d --name akasha \
  -p 7777:7777 \
  -p 50051:50051 \
  alejandrosl/akasha:latest
```

Verify it's running:

```bash
curl -s http://localhost:7777/api/v1/health | jq
```

```json
{
  "status": "ok",
  "name": "akasha",
  "version": "1.0.8",
  "records": 0
}
```

## 2. Write Your First Record

```bash
curl -s http://localhost:7777/api/v1/records/hello/world \
  -X POST -H "Content-Type: application/json" \
  -d '{"value": {"message": "Hello from Akasha!"}}'
```

## 3. Read It Back

```bash
curl -s http://localhost:7777/api/v1/records/hello/world | jq
```

```json
{
  "path": "hello/world",
  "value": {"message": "Hello from Akasha!"},
  "version": 1,
  "content_type": "application/json"
}
```

## 4. Try With a SDK

=== "Python"

    ```bash
    pip install akasha-client
    ```

    ```python
    from akasha import AkashaHttpClient

    client = AkashaHttpClient(base_url="http://localhost:7777")

    # Write
    record = client.put("agents/planner/state", {
        "status": "analyzing",
        "confidence": 0.85,
    })
    print(f"Written: version {record.version}")

    # Read
    state = client.get("agents/planner/state")
    print(f"Status: {state.value['status']}")

    # Query
    agents = client.query("agents/*/state")
    print(f"Found {len(agents)} agents")

    # Subscribe to changes
    for event in client.subscribe("agents/**"):
        print(f"[{event.kind}] {event.path}")
    ```

=== "Node.js"

    ```bash
    npm install akasha-memory
    ```

    ```typescript
    import { AkashaHttpClient } from 'akasha-memory';

    const client = new AkashaHttpClient({
      baseUrl: 'http://localhost:7777',
    });

    // Write
    const record = await client.put('agents/planner/state', {
      status: 'analyzing',
      confidence: 0.85,
    });
    console.log(`Written: version ${record.version}`);

    // Read
    const state = await client.get('agents/planner/state');
    console.log(`Status: ${state?.value.status}`);

    // Query
    const agents = await client.query('agents/*/state');
    console.log(`Found ${agents.length} agents`);
    ```

## 5. Explore the Playground

Open the [Interactive Playground](../examples/playground.md) to try all Akasha features from your browser — no code required.

## Next Steps

- [Installation options](installation.md) — Docker, binary, source, cluster
- [Core concepts](../concepts/architecture.md) — Memory layers, pheromones, CAS
- [API Reference](../sdks/rest-api.md) — All 21 endpoints documented
