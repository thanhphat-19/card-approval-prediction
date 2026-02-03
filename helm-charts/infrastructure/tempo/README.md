# Grafana Tempo Helm Chart

Distributed tracing backend for the Card Approval Prediction API.

## Overview

This chart deploys Grafana Tempo in monolithic mode for collecting and querying traces from the FastAPI application.

## Prerequisites

- Kubernetes 1.21+
- Helm 3.0+
- GCS bucket for trace storage (reuses MLflow bucket)
- Workload Identity configured for GCS access

## Installation

```bash
# Add Grafana Helm repository
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Tempo
helm dependency build helm-charts/infrastructure/tempo
helm upgrade --install tempo helm-charts/infrastructure/tempo \
  --namespace monitoring \
  --create-namespace
```

## Configuration

Key configuration options in `values.yaml`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `tempo.storage.trace.backend` | Storage backend | `gcs` |
| `tempo.storage.trace.gcs.bucket_name` | GCS bucket | `product-recsys-mlops-recsys-data` |
| `tempo.compactor.compaction.block_retention` | Trace retention | `336h` (14 days) |
| `tempo.receivers.otlp.protocols.grpc.endpoint` | OTLP gRPC endpoint | `0.0.0.0:4317` |

## Endpoints

| Port | Protocol | Purpose |
|------|----------|---------|
| 3200 | HTTP | Query API (Grafana datasource) |
| 4317 | gRPC | OTLP receiver |
| 4318 | HTTP | OTLP receiver |
| 9095 | gRPC | Internal gRPC |

## Grafana Datasource

Add Tempo as a datasource in Grafana:

```yaml
datasources:
  - name: Tempo
    type: tempo
    url: http://tempo.monitoring:3200
    access: proxy
```

## Verify Installation

```bash
# Check pods
kubectl get pods -n monitoring -l app.kubernetes.io/name=tempo

# Check service
kubectl get svc -n monitoring -l app.kubernetes.io/name=tempo

# Test OTLP endpoint
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -v http://tempo.monitoring:4318/v1/traces
```

## Troubleshooting

### No traces appearing

1. Check application OTEL_EXPORTER_OTLP_ENDPOINT is correct
2. Verify Tempo pod is running
3. Check Tempo logs: `kubectl logs -f deployment/tempo -n monitoring`

### GCS permission errors

Ensure Workload Identity is configured:
```bash
kubectl describe serviceaccount tempo-sa -n monitoring
```
