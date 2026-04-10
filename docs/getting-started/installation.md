# Installation

Multiple ways to get Akasha running, from a single Docker command to a production HA cluster.

## Docker (Recommended)

```bash
docker run -d --name akasha \
  -p 7777:7777 \
  -p 50051:50051 \
  -v akasha-data:/data \
  alejandrosl/akasha:latest
```

!!! tip "Persistent storage"
    Mount a volume at `/data` to persist records across container restarts.

## One-Line Installer

```bash
curl -fsSL https://raw.githubusercontent.com/ocuil/akasha-public/main/deploy/get-akasha.sh | bash
```

This auto-detects your OS and architecture, downloads the correct binary, and installs to `/usr/local/bin/`.

## From Source

```bash
git clone https://github.com/ocuil/akasha-public.git
cd akasha-public
cargo build --release
./target/release/akasha
```

!!! note "Requirements"
    Rust 1.75+ and a C linker are required for building from source.

## SDK Installation

=== "Python"

    ```bash
    pip install akasha-client
    ```

    Requires Python 3.9+. See [Python SDK docs](../sdks/python.md).

=== "Node.js"

    ```bash
    npm install akasha-memory
    ```

    Requires Node.js 18+. See [Node.js SDK docs](../sdks/nodejs.md).

## Enterprise Cluster

For a production high-availability cluster, see the [Clustering guide](../deployment/clustering.md).
