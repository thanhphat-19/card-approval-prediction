# Component 4: Helm Charts

## Executive Summary

Helm Charts provide templated Kubernetes deployments for the Card Approval Prediction system. The charts follow an umbrella pattern with `card-approval` (API stack) and `card-approval-training` (MLflow infrastructure) as parent charts, depending on infrastructure subcharts (PostgreSQL, Redis, MLflow, monitoring). This enables consistent, configurable deployments across environments.

---

## 1. Concept & Theory

### What is Helm?

Helm is the **package manager for Kubernetes**:
- **Charts**: Pre-configured Kubernetes resource templates
- **Values**: Customizable configuration parameters
- **Releases**: Deployed instances of charts
- **Repositories**: Chart distribution mechanism

### Why Helm for ML Deployments?

| Challenge | Helm Solution |
|-----------|---------------|
| Complex YAML management | Templated resources with variables |
| Environment differences | Values files per environment |
| Dependency management | Chart dependencies (PostgreSQL, Redis) |
| Rollback capability | Release history with rollback |
| Upgrade strategy | Rolling updates, atomic deployments |

### Helm Chart Types

1. **Application Charts**: Deploy single applications (FastAPI, MLflow)
2. **Library Charts**: Reusable templates (not deployed directly)
3. **Umbrella Charts**: Aggregate multiple subcharts

### MLOps Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Namespace: card-approval                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             card-approval (Umbrella Chart)               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │  FastAPI    │  │  PostgreSQL │  │    Redis    │      │   │
│  │  │    API      │  │             │  │             │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Namespace: card-approval-training                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │        card-approval-training (Umbrella Chart)           │   │
│  │  ┌─────────────┐  ┌─────────────┐                       │   │
│  │  │   MLflow    │  │  PostgreSQL │                       │   │
│  │  │   Server    │  │  (MLflow)   │                       │   │
│  │  └─────────────┘  └─────────────┘                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Namespace: monitoring                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ Prometheus  │  │   Grafana   │  │    Tempo    │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture & Design Decisions

### Chart Structure

```
helm-charts/
├── card-approval/              # Umbrella: API + dependencies
│   ├── Chart.yaml              # Chart metadata + dependencies
│   ├── values.yaml             # Default configuration
│   └── templates/              # (empty - uses subcharts)
│
├── card-approval-training/     # Umbrella: MLflow + dependencies
│   ├── Chart.yaml
│   └── values.yaml
│
└── infrastructure/             # Individual component charts
    ├── card-approval-api/      # FastAPI application
    │   ├── Chart.yaml
    │   ├── values.yaml
    │   └── templates/
    │       ├── deployment.yaml
    │       ├── service.yaml
    │       ├── configmap.yaml
    │       ├── hpa.yaml
    │       └── ingress.yaml
    ├── postgres/               # PostgreSQL database
    ├── redis/                  # Redis cache
    ├── mlflow/                 # MLflow tracking server
    ├── monitoring/             # Prometheus + Grafana
    ├── tempo/                  # Distributed tracing
    └── nginx-ingress/          # Ingress controller
```

### Key Design Decisions

#### 1. Umbrella Chart Pattern
```yaml
# helm-charts/card-approval/Chart.yaml
apiVersion: v2
name: card-approval
version: 1.0.0
dependencies:
  - name: card-approval-api
    version: "1.0.0"
    repository: "file://../infrastructure/card-approval-api"
    alias: api
  - name: postgres
    version: "1.0.0"
    repository: "file://../infrastructure/postgres"
  - name: redis
    version: "1.0.0"
    repository: "file://../infrastructure/redis"
```

**Benefit**: Single `helm upgrade` deploys entire stack with correct configuration.

#### 2. Conditional Dependencies
```yaml
# values.yaml
postgres:
  enabled: true  # Can disable for external DB

redis:
  enabled: true  # Can disable for stateless mode
```

#### 3. Workload Identity Integration
```yaml
# values.yaml
api:
  serviceAccount:
    create: true
    annotations:
      iam.gke.io/gcp-service-account: "mlflow-gcs@project.iam.gserviceaccount.com"
```

**Rationale**: Pods authenticate to GCS without service account keys.

#### 4. HPA Configuration
```yaml
api:
  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 3
    targetCPUUtilizationPercentage: 70
```

---

## 3. Implementation Guide

### Card Approval API Chart

#### Chart.yaml
```yaml
# helm-charts/infrastructure/card-approval-api/Chart.yaml
apiVersion: v2
name: card-approval-api
description: FastAPI Credit Card Approval Prediction API
type: application
version: 1.0.0
appVersion: "1.0.0"
```

#### Deployment Template
```yaml
# helm-charts/infrastructure/card-approval-api/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "card-approval-api.fullname" . }}
  labels:
    {{- include "card-approval-api.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "card-approval-api.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        {{- if .Values.monitoring.enabled }}
        prometheus.io/scrape: "true"
        prometheus.io/port: "{{ .Values.service.targetPort }}"
        prometheus.io/path: "/metrics"
        {{- end }}
      labels:
        {{- include "card-approval-api.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "card-approval-api.serviceAccountName" . }}
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.targetPort }}
          envFrom:
            - configMapRef:
                name: {{ include "card-approval-api.fullname" . }}-config
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          livenessProbe:
            httpGet:
              path: /health/live
              port: {{ .Values.service.targetPort }}
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: {{ .Values.service.targetPort }}
            initialDelaySeconds: 10
            periodSeconds: 5
```

#### ConfigMap Template
```yaml
# helm-charts/infrastructure/card-approval-api/templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "card-approval-api.fullname" . }}-config
data:
  APP_NAME: {{ .Values.config.appName | quote }}
  APP_VERSION: {{ .Values.config.appVersion | quote }}
  LOG_LEVEL: {{ .Values.config.logLevel | quote }}
  MODEL_NAME: {{ .Values.config.modelName | quote }}
  MODEL_STAGE: {{ .Values.config.modelStage | quote }}
  MODEL_PATH: {{ .Values.config.modelPath | quote }}
  MLFLOW_TRACKING_URI: {{ .Values.mlflow.trackingUri | quote }}
  OTEL_ENABLED: {{ .Values.tracing.enabled | quote }}
  OTEL_SERVICE_NAME: {{ .Values.tracing.serviceName | quote }}
  OTEL_EXPORTER_ENDPOINT: {{ .Values.tracing.exporterEndpoint | quote }}
  OTEL_SAMPLING_RATE: {{ .Values.tracing.samplingRate | quote }}
```

#### Service Template
```yaml
# helm-charts/infrastructure/card-approval-api/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "card-approval-api.fullname" . }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
  selector:
    {{- include "card-approval-api.selectorLabels" . | nindent 4 }}
```

#### HPA Template
```yaml
# helm-charts/infrastructure/card-approval-api/templates/hpa.yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "card-approval-api.fullname" . }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "card-approval-api.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
{{- end }}
```

### Values Configuration

```yaml
# helm-charts/card-approval/values.yaml
namespace: card-approval

# PostgreSQL
postgres:
  enabled: true
  database: card_approval_db
  username: app_user
  password: ""  # Set via --set
  persistence:
    enabled: true
    size: 5Gi

# Redis
redis:
  enabled: true
  persistence:
    enabled: true
    size: 1Gi

# FastAPI API
api:
  enabled: true

  image:
    repository: ""  # Set via --set
    tag: "latest"
    pullPolicy: Always

  replicaCount: 2

  service:
    type: ClusterIP
    port: 80
    targetPort: 8000

  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"

  config:
    appName: "Card Approval API"
    logLevel: "INFO"
    modelName: "card_approval_model"
    modelStage: "Production"
    modelPath: "/app/models"  # Embedded model

  tracing:
    enabled: true
    serviceName: "card-approval-api"
    exporterEndpoint: "http://tempo.monitoring:4317"
    samplingRate: "1.0"

  mlflow:
    trackingUri: "http://card-approval-training-mlflow.card-approval-training:5000"

  serviceAccount:
    create: true
    annotations:
      iam.gke.io/gcp-service-account: ""  # Workload Identity

  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 3
    targetCPUUtilizationPercentage: 70

  ingress:
    enabled: false
    className: "nginx"
    host: "api.example.com"
```

### Deployment Commands

```bash
# Load config.env
source config.env

# Build dependencies
cd helm-charts/card-approval
helm dependency build
cd ../..

# Deploy API stack
helm upgrade --install card-approval ./helm-charts/card-approval \
  --namespace ${GKE_NAMESPACE} \
  --create-namespace \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.image.tag="v1.0.0" \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --wait \
  --atomic

# Deploy MLflow training stack
helm upgrade --install card-approval-training ./helm-charts/card-approval-training \
  --namespace card-approval-training \
  --create-namespace \
  --set mlflow.gcs.bucket="${GCS_BUCKET_NAME}" \
  --set postgres.password="${POSTGRES_MLFLOW_PASSWORD}"

# Deploy monitoring
helm upgrade --install tempo ./helm-charts/infrastructure/tempo \
  --namespace monitoring \
  --create-namespace
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Committing passwords | Use `--set` or external secrets |
| Forgetting dependency build | Always run `helm dependency build` |
| Using `latest` tag | Always use specific image tags |
| No resource limits | Set requests and limits |

### Secrets Management

#### Option 1: Kubernetes Secrets + --set
```bash
# Create secret first
kubectl create secret generic api-secrets \
  --from-literal=postgres-password="${POSTGRES_PASSWORD}" \
  --namespace card-approval

# Reference in values
--set api.postgres.existingSecret="api-secrets"
```

#### Option 2: External Secrets Operator
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: api-secrets
spec:
  secretStoreRef:
    name: gcp-secret-manager
  target:
    name: api-secrets
  data:
    - secretKey: postgres-password
      remoteRef:
        key: postgres-app-password
```

### Rolling Updates

```yaml
# Deployment strategy
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### Debugging Commands

```bash
# View rendered templates
helm template card-approval ./helm-charts/card-approval \
  --set api.image.repository="test" > rendered.yaml

# Dry-run install
helm install card-approval ./helm-charts/card-approval \
  --dry-run --debug

# Get deployed values
helm get values card-approval -n card-approval

# Check release history
helm history card-approval -n card-approval

# Rollback to previous
helm rollback card-approval 1 -n card-approval
```

---

## 5. Testing & Validation

### Validation Checklist

```bash
# After helm upgrade:

# 1. Check pods
kubectl get pods -n card-approval

# 2. Check services
kubectl get svc -n card-approval

# 3. Check HPA
kubectl get hpa -n card-approval

# 4. Test API health
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
curl http://localhost:8000/health

# 5. Check logs
kubectl logs -l app=card-approval-api -n card-approval

# 6. Check metrics
curl http://localhost:8000/metrics
```

### Helm Test
```yaml
# templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ .Release.Name }}-test"
  annotations:
    "helm.sh/hook": test
spec:
  containers:
    - name: curl
      image: curlimages/curl
      command: ['curl', '-s', 'http://{{ include "card-approval-api.fullname" . }}:{{ .Values.service.port }}/health']
  restartPolicy: Never
```

```bash
# Run Helm tests
helm test card-approval -n card-approval
```

---

## 6. Configuration Reference

### Resource Recommendations

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| FastAPI API | 100m | 500m | 256Mi | 512Mi |
| PostgreSQL | 100m | 500m | 256Mi | 512Mi |
| Redis | 50m | 200m | 128Mi | 256Mi |
| MLflow | 100m | 500m | 256Mi | 512Mi |

### Important values.yaml Options

| Path | Default | Description |
|------|---------|-------------|
| `api.image.repository` | "" | Docker image URL |
| `api.image.tag` | "latest" | Image tag |
| `api.replicaCount` | 2 | Pod replicas |
| `api.config.modelPath` | "" | Local model path |
| `api.tracing.enabled` | true | Enable OTEL |
| `api.autoscaling.enabled` | true | Enable HPA |
| `postgres.enabled` | true | Deploy PostgreSQL |
| `redis.enabled` | true | Deploy Redis |

---

## 7. Further Reading

- [Helm Documentation](https://helm.sh/docs/)
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Kubernetes Patterns](https://kubernetes.io/docs/concepts/workloads/)
- [External Secrets Operator](https://external-secrets.io/)
- [HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
