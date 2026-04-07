# Installation Guide

## Prerequisites

- **Docker** ≥ 24.0 (for containerized deployment)
- **Rust** ≥ 1.75 (only if building from source)
- **Node.js** ≥ 18 (only if building dashboard from source)

## Quick Start (Curl Installer)

The fastest way to install Akasha on Linux or macOS:

```bash
curl -fsSL https://akasha-installer.akasha.workers.dev/install | bash
```

This auto-detects your OS and architecture, downloads the correct binary, and installs it.

Options:
```bash
# Install a specific version
curl -fsSL https://akasha-installer.akasha.workers.dev/install | bash -s -- --version v1.0.0

# Install to a custom directory
curl -fsSL https://akasha-installer.akasha.workers.dev/install | bash -s -- --dir /opt/akasha/bin

# Skip systemd service installation
curl -fsSL https://akasha-installer.akasha.workers.dev/install | bash -s -- --no-service
```

Supported platforms:
| Platform | Architecture | Archive |
|----------|-------------|---------|
| Linux | x86_64 (amd64) | `akasha-vX.Y.Z-linux-amd64.tar.gz` |
| Linux | aarch64 (arm64) | `akasha-vX.Y.Z-linux-arm64.tar.gz` |
| macOS | Apple Silicon (arm64) | `akasha-vX.Y.Z-darwin-arm64.tar.gz` |

## Quick Start (Docker — Standalone)

The fastest way to run Akasha:

```bash
# Pull and run a single node
docker run -d \
  --name akasha \
  -p 7777:7777 \
  -p 50051:50051 \
  -v akasha-data:/app/data \
  ghcr.io/ocuil/akasha:latest

# Verify it's running
curl -k https://localhost:7777/api/v1/health
```

Expected output:
```json
{
  "status": "ok",
  "name": "akasha",
  "version": "1.0.0",
  "records": 0,
  "pending_telemetry": false,
  "cluster": null
}
```

## Docker Compose — 3-Node Cluster

This is the **recommended production deployment**:

```bash
git clone https://github.com/ocuil/akasha.git
cd akasha
docker compose up -d
```

This starts:
| Node | HTTP | gRPC | Role |
|------|------|------|------|
| akasha-01 | `https://localhost:7771` | `localhost:50051` | Leader (auto-elected) |
| akasha-02 | `https://localhost:7772` | `localhost:50052` | Voter |
| akasha-03 | `https://localhost:7773` | `localhost:50053` | Voter |

### Verify cluster health

```bash
# Check all nodes are alive
curl -sk https://localhost:7771/api/v1/cluster/nodes | python3 -m json.tool

# Check Raft leader election
curl -sk https://localhost:7771/api/v1/cluster/raft | python3 -m json.tool

# Open the dashboard
open https://localhost:7771/dashboard/
```

### First login

When `auth.enabled = true` (production default):
- **Username**: `akasha`
- **Password**: `akasha`
- ⚠️ **Change this immediately** via Dashboard → Profile → Change Password

## Building from Source

```bash
# 1. Clone the repository
git clone https://github.com/ocuil/akasha.git
cd akasha

# 2. Build the dashboard SPA
cd dashboard-spa
npm install
npm run build
cd ..

# 3. Build the Rust binary
cargo build --release

# 4. Run standalone
./target/release/akasha akasha.toml
```

## GKE Autopilot Deployment

### Prerequisites
- `gcloud` CLI configured with a project
- `kubectl` configured with a GKE Autopilot cluster

### Step 1: Build and push the image

```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker us-docker.pkg.dev

# Build the image
docker build -t us-docker.pkg.dev/YOUR_PROJECT/akasha/akasha:1.0.0 .

# Push
docker push us-docker.pkg.dev/YOUR_PROJECT/akasha/akasha:1.0.0
```

### Step 2: Create the Kubernetes manifests

Create `k8s/akasha-cluster.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: akasha

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: akasha-config
  namespace: akasha
data:
  akasha.toml: |
    [server]
    http_addr = "0.0.0.0:7777"
    grpc_addr = "0.0.0.0:50051"
    node_id = "${HOSTNAME}"

    [storage]
    engine = "rocksdb"
    data_dir = "/app/data"

    [auth]
    enabled = true

    [cluster]
    enabled = true
    bind_addr = "0.0.0.0:7946"
    advertise_addr = "${HOSTNAME}.akasha-headless.akasha.svc.cluster.local:7946"
    seeds = [
      "akasha-0.akasha-headless.akasha.svc.cluster.local:7946",
      "akasha-1.akasha-headless.akasha.svc.cluster.local:7946",
      "akasha-2.akasha-headless.akasha.svc.cluster.local:7946"
    ]
    cluster_key = "your-cluster-key-change-me"

    [tls]
    auto_cert = true

    [nidra]
    enabled = true
    interval_seconds = 300

---
apiVersion: v1
kind: Service
metadata:
  name: akasha-headless
  namespace: akasha
spec:
  type: ClusterIP
  clusterIP: None
  ports:
    - name: http
      port: 7777
    - name: grpc
      port: 50051
    - name: gossip
      port: 7946
      protocol: UDP
  selector:
    app: akasha

---
apiVersion: v1
kind: Service
metadata:
  name: akasha-lb
  namespace: akasha
spec:
  type: LoadBalancer
  ports:
    - name: https
      port: 443
      targetPort: 7777
    - name: grpc
      port: 50051
      targetPort: 50051
  selector:
    app: akasha

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: akasha
  namespace: akasha
spec:
  serviceName: akasha-headless
  replicas: 3
  selector:
    matchLabels:
      app: akasha
  template:
    metadata:
      labels:
        app: akasha
    spec:
      containers:
        - name: akasha
          image: us-docker.pkg.dev/YOUR_PROJECT/akasha/akasha:1.0.0
          ports:
            - containerPort: 7777
              name: http
            - containerPort: 50051
              name: grpc
            - containerPort: 7946
              name: gossip
              protocol: UDP
          env:
            - name: HOSTNAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          volumeMounts:
            - name: config
              mountPath: /app/akasha.toml
              subPath: akasha.toml
            - name: data
              mountPath: /app/data
          livenessProbe:
            httpGet:
              path: /api/v1/health/live
              port: 7777
              scheme: HTTPS
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/health/ready
              port: 7777
              scheme: HTTPS
            initialDelaySeconds: 10
            periodSeconds: 5
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "2Gi"
      volumes:
        - name: config
          configMap:
            name: akasha-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

### Step 3: Deploy

```bash
kubectl apply -f k8s/akasha-cluster.yaml

# Watch pods come up
kubectl -n akasha get pods -w

# Check cluster formation
kubectl -n akasha exec akasha-0 -- curl -sk https://localhost:7777/api/v1/cluster/nodes
```

### Step 4: Access the dashboard

```bash
# Get the external IP
kubectl -n akasha get svc akasha-lb

# Open in browser
open https://EXTERNAL_IP/dashboard/
```

## Directory Structure After Installation

```
/app/
├── akasha          # Binary
├── akasha.toml     # Configuration
├── data/           # RocksDB data directory
│   ├── db/         # Main database
│   └── wal/        # Write-ahead log
└── certs/          # Auto-generated TLS certificates (if auto_cert = true)
    ├── cert.pem
    └── key.pem
```

## Health Checks

| Endpoint | Purpose | Use For |
|----------|---------|---------|
| `GET /api/v1/health` | Full health with cluster info | Monitoring dashboards |
| `GET /api/v1/health/live` | Returns 200 if process alive | K8s `livenessProbe` |
| `GET /api/v1/health/ready` | Returns 200 when ready to serve | K8s `readinessProbe` |

## Next Steps

1. [Configure authentication](authentication.md)
2. [Connect your first agent](agent-patterns.md)
3. [Set up monitoring](cluster-operations.md)
