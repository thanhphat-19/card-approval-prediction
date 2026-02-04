# Monitoring with Grafana Stack (Logs, Metrics, Traces)

This document describes the complete observability implementation for the Card Approval Prediction system using the Grafana Stack.

## Overview

The project implements a full observability stack with:
- **Logs** - Grafana Loki for log aggregation and querying
- **Metrics** - Prometheus for metrics collection and alerting
- **Traces** - Grafana Tempo with OpenTelemetry for distributed tracing

Together, these three pillars provide end-to-end visibility into system behavior, performance, and issues.

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │      Application Services           │
                        │  (API, MLflow, Jenkins, etc.)       │
                        └──────┬──────────┬──────────┬────────┘
                               │          │          │
                         Logs  │    Metrics│    Traces│
                               │          │          │
                    ┌──────────▼─┐    ┌───▼───┐  ┌──▼────────┐
                    │   Loki     │    │ Prom- │  │   Tempo   │
                    │   (Logs)   │    │etheus │  │ (Traces)  │
                    └──────┬─────┘    └───┬───┘  └──┬────────┘
                           │              │         │
                           └──────┬───────┴─────────┘
                                  │
                           ┌──────▼──────┐
                           │   Grafana   │
                           │  Dashboard  │
                           └─────────────┘
```

## Components

| Component | Purpose |
|-----------|---------|
| **Grafana Loki** | Log aggregation and querying |
| **Prometheus** | Metrics collection, storage, and alerting |
| **Grafana Tempo** | Distributed tracing backend |
| **Grafana** | Unified visualization and exploration |
| **OpenTelemetry SDK** | Application instrumentation |
| **Promtail** | Log shipper (collects logs from pods) |


# Distributed Tracing with Tempo

## Overview

Grafana Tempo provides distributed tracing for the Card Approval API using OpenTelemetry instrumentation.

## Tracing Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FastAPI    │────▶│    Tempo    │◀────│   Grafana   │
│  (OTLP)     │     │  (Storage)  │     │  (Query)    │
└─────────────┘     └─────────────┘     └─────────────┘
```


## Viewing Traces in Grafana

### Step 1: Access Tempo Datasource

1. Open Grafana: `http://<NGINX_IP>/grafana`
2. Navigate to **Explore** (compass icon 🧭)
3. Select **Tempo** from the datasource dropdown

### Step 2: Query Traces


```traceql
# Search by service name
{ resource.service.name = "card-approval-api" }

# Find slow predictions
{ span.name = "model_inference.predict" } | duration > 100ms

# Find errors
{ status = error }

# Search by trace ID
{ trace.id = "abc123..." }
```

---

# Logs Management with Grafana Loki

## Overview

Grafana Loki is a log aggregation system designed for efficiency and ease of use.

## Log Collection Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ K8s Pods    │────▶│  Promtail   │────▶│    Loki     │
│ (stdout)    │     │ DaemonSet   │     │  (Storage)  │
└─────────────┘     └─────────────┘     └─────────────┘
```


## Viewing Logs in Grafana

### Step 1: Access Loki Datasource

1. Open Grafana: `http://<NGINX_IP>/grafana`
2. Navigate to **Explore** (compass icon 🧭)
3. Select **Loki** from the datasource dropdown

### Step 2: Query Logs


```logql
# All logs from card-approval namespace
{namespace="card-approval"}

# API logs only
{namespace="card-approval", app="card-approval-api"}

# MLflow logs
{namespace="card-approval-training", app="mlflow"}

# Error logs only
{namespace="card-approval"} |= "ERROR"

# Logs containing "prediction"
{namespace="card-approval"} |~ "prediction"
```



# Metrics Collection with Prometheus

## Overview

Prometheus is a time-series database that collects metrics from instrumented applications and infrastructure. It provides powerful querying (PromQL) and alerting capabilities.

## Metrics Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Applications   │────▶│  Service     │◀────│ Prometheus  │
│  (Metrics Port) │     │  Discovery   │     │  (Scraper)  │
└─────────────────┘     └──────────────┘     └─────────────┘
                                                     │
                                              ┌──────▼──────┐
                                              │   Grafana   │
                                              │  Dashboard  │
                                              └─────────────┘
```



## Viewing Metrics in Grafana

### Step 1: Access Prometheus Datasource

1. Open Grafana: `http://<NGINX_IP>/grafana`
2. Navigate to **Explore** (compass icon 🧭)
3. Select **Prometheus** from the datasource dropdown

### Step 2: Query Metrics


```promql
# Current request rate (requests per second)
rate(http_requests_total{namespace="card-approval"}[5m])

# Average request duration
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{namespace="card-approval"}[5m])
)

# Prediction success rate
sum(rate(predictions_total{decision="APPROVED"}[5m])) /
sum(rate(predictions_total[5m]))

# Memory usage
sum(container_memory_usage_bytes{namespace="card-approval", pod=~"card-approval-api.*"})
/ 1024 / 1024  # Convert to MB
```




---

**Congratulations!** Your Card Approval Prediction system now has enterprise-grade observability. 🎉
