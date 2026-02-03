# Card Approval Prediction - Personal Setup Guide

> **Author's Notes:** This is my personal command reference for setting up the entire MLOps project. Use this as a step-by-step guide or quick reference.

---

## Quick Setup Checklist

Complete these steps in order to reproduce the entire project:

| Step | Task | Time | Status |
|------|------|------|--------|
| 1 | Terraform Infrastructure | 10 min | ☐ |
| 2 | Connect to GKE Cluster | 2 min | ☐ |
| 3 | Setup Workload Identity | 5 min | ☐ |
| 4 | Generate Service Account Key | 5 min | ☐ |
| 5 | Build & Push Docker Image | 10 min | ☐ |
| 6 | Deploy NGINX Ingress | 5 min | ☐ |
| 7 | Deploy Helm Charts | 15 min | ☐ |
| 8 | Train Models | 15 min | ☐ |
| 9 | Setup Jenkins CI/CD | 30 min | ☐ |
| 10 | Test & Verify | 10 min | ☐ |

**Total Estimated Time:** 2-3 hours

---

## Prerequisites Checklist

- [ ] GCP account with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] `kubectl`, `helm`, `terraform`, `docker` installed
- [ ] GitHub account with repository forked/cloned
- [ ] `config.env` configured with your values
- [ ] `terraform/terraform.tfvars` configured

---

## Project Info

| Property | Value |
|----------|-------|
| **Project ID** | `product-recsys-mlops` |
| **Project Name** | Card Approval Prediction |
| **Cluster** | `card-approval-prediction-mlops-gke` |
| **Zone** | `us-east1-b` |
| **Region** | `us-east1` |


---

## 1. Terraform (Infrastructure)

```bash
cd terraform

# Initialize
terraform init

# Plan changes
terraform plan -var="project_id=product-recsys-mlops"

# Apply changes
terraform apply -var="project_id=product-recsys-mlops"

# Check outputs
terraform output

# Destroy (careful!)
terraform destroy -var="project_id=product-recsys-mlops"
```

---

## 2. Cluster Connection

```bash
# Get credentials
gcloud container clusters get-credentials card-approval-prediction-mlops-gke \
  --zone us-east1-b --project product-recsys-mlops

# Verify connection
kubectl get nodes
kubectl get namespaces
```

---

## 3. Workload Identity Setup (Required for GCS Access!)

> **Why?** Kubernetes pods need permission to access GCP services (GCS, etc).
> Workload Identity allows K8s Service Accounts to impersonate GCP Service Accounts.
> Without this IAM binding, you get `403 Permission Denied` errors.

```bash
# Variables (source config.env for consistency)
source ../config.env
export GSA_NAME=${GSA_NAME}  # GCP Service Account name
export GSA_EMAIL=${GSA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# 1. Create GCP Service Account (if not exists)
gcloud iam service-accounts create ${GSA_NAME} \
  --display-name="MLflow GCS Service Account" \
  --project=${GCP_PROJECT_ID}
# 2. Grant GCS permissions to the GCP Service Account
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/storage.objectAdmin"

# 3. Allow K8s SA (card-approval namespace) to impersonate GCP SA
gcloud iam service-accounts add-iam-policy-binding ${GSA_EMAIL} \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[card-approval/card-approval-api-sa]" \
  --project=${GCP_PROJECT_ID}

# 4. Allow K8s SA (card-approval-training namespace) to impersonate GCP SA
gcloud iam service-accounts add-iam-policy-binding ${GSA_EMAIL} \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[card-approval-training/card-approval-training-mlflow-sa]" \
  --project=${GCP_PROJECT_ID}

# Verify bindings
gcloud iam service-accounts get-iam-policy ${GSA_EMAIL} --project=${GCP_PROJECT_ID}
```

---

## 4. Service Account Key for CI/CD (Jenkins)

> **Critical:** Jenkins needs a service account key to authenticate and deploy to GKE.

```bash
# Variables (source config.env for consistency)
source ../config.env

# 1. Generate service account key (first time or regenerate)

mkdir -p ~/secrets
gcloud iam service-accounts keys create ~/secrets/gcp-key.json \
  --iam-account=${GSA_EMAIL} \
  --project=${GCP_PROJECT_ID}

# 2. Grant CI/CD permissions to the service account
# Artifact Registry - push Docker images
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# GKE Cluster - get credentials
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/container.clusterViewer"

# GKE Deployment - deploy to cluster
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/container.developer"

# 3. Verify the key works
gcloud auth activate-service-account --key-file=/home/thanhphat/secrets/gcp-key.json

gcloud auth print-access-token  # Should generate token without errors
gcloud container clusters get-credentials card-approval-prediction-mlops-gke \
  --zone us-east1-b --project ${GCP_PROJECT_ID}  # Should succeed

# 4. Switch back to your main account
gcloud config set account thanhphat352@gmail.com
```

### Update Jenkins Credential

After generating the key, update Jenkins:
1. Go to Jenkins → **Manage Jenkins** → **Credentials** → **System** → **Global credentials**
2. Find credential ID `gcp-service-account`
3. Click **Update** → Replace with content from `~/secrets/gcp-key.json`
4. **Save**

>    **Common Errors:**
> - `Invalid JWT Signature` → Key is old/corrupted, regenerate it
> - `Permission denied` → Missing IAM roles, check step 2 above
> - `container.clusters.get` error → Missing `roles/container.clusterViewer`

---

## 5. Build & Push Docker Image (Before Helm Deploy!)

```bash
# Source config
source config.env

# Configure Docker for Artifact Registry
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

# Build the image
docker build -t card-approval-api:latest .

# Tag for Artifact Registry
docker tag card-approval-api:latest \
  ${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest

# Push to registry
docker push ${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest

# Verify image exists
gcloud artifacts docker images list \
  ${DOCKER_REGISTRY}/${DOCKER_REPOSITORY} \
  --include-tags
```

---

## 6. Helm Deployments

### 6.1 NGINX Ingress Controller (Deploy First!)

```bash
# Update Helm dependencies
helm dependency update helm-charts/infrastructure/nginx-ingress

# Deploy NGINX Ingress Controller
helm upgrade --install nginx-ingress helm-charts/infrastructure/nginx-ingress \
  -n ingress-nginx --create-namespace

34.138.115.181
35.237.250.189

export MLFLOW_TRACKING_URI="http://35.237.250.189 /mlflow"
export MODEL_NAME="card_approval_model"
export MODEL_STAGE="Production"
# Wait for LoadBalancer IP
kubectl get svc -n ingress-nginx -w

# Get the external IP (save this for DNS/access)
kubectl get svc nginx-ingress-ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### 6.2 Application Stacks

```bash
# Source config for passwords
source config.env

# Deploy training stack (MLflow + PostgreSQL)
helm upgrade --install card-approval-training helm-charts/card-approval-training \
  -n card-approval-training --create-namespace \
  --set postgres.password="${POSTGRES_MLFLOW_PASSWORD}" \
  --set mlflow.postgres.password="${POSTGRES_MLFLOW_PASSWORD}" \
  --set mlflow.gcs.bucket="${GCS_BUCKET_NAME}" \
  --set mlflow.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}"

# Deploy API stack (FastAPI + PostgreSQL + Redis)
helm upgrade --install card-approval helm-charts/card-approval \
  -n card-approval --create-namespace \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}"

# Deploy monitoring stack
helm upgrade --install monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring --create-namespace \
  --set kube-prometheus.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"

# Check all releases
helm list -A
```

### 6.3 Deploy Without CI/CD (Load Model from MLflow at Runtime)

> **Use Case:** Deploy the API without running the CI/CD pipeline. The model will be fetched from MLflow at runtime instead of being embedded in the Docker image.

```bash
# Source config
source config.env

# Deploy API with MLflow runtime loading (modelPath="")
helm upgrade --install card-approval helm-charts/card-approval \
  -n card-approval --create-namespace \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --set api.config.modelPath="" \
  --set api.tracing.enabled=true \
  --set api.tracing.exporterEndpoint="http://tempo.monitoring:4317" \
  --set api.tracing.samplingRate="1.0"
```

**Key Parameter:** `--set api.config.modelPath=""` tells the API to load the model from MLflow instead of the embedded `/app/models` directory.

### 6.4 Deploy Tempo (Distributed Tracing)

```bash
# Build Tempo dependencies
helm dependency build helm-charts/infrastructure/tempo

# Add Workload Identity binding for Tempo
gcloud iam service-accounts add-iam-policy-binding ${GCP_MLFLOW_SERVICE_ACCOUNT} \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[monitoring/tempo-sa]" \
  --project=${GCP_PROJECT_ID}

# Grant bucket access for traces storage
gcloud storage buckets add-iam-policy-binding gs://${GCS_BUCKET_NAME} \
  --member="serviceAccount:${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --role="roles/storage.legacyBucketReader"

# Deploy Tempo
helm upgrade --install tempo helm-charts/infrastructure/tempo \
  -n monitoring --create-namespace \
  --set tempo.tempo.storage.trace.gcs.bucket_name="${GCS_BUCKET_NAME}" \
  --set tempo.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}"

# Verify Tempo is running
kubectl get pods -n monitoring -l app.kubernetes.io/name=tempo
```

### 6.5 Test Distributed Tracing

```bash
# Test prediction endpoint (generates traces)
curl -X POST "http://35.237.250.189/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 12345,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 150000,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -3000,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 1,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2
  }'

# Expected response:
# {"prediction":1,"probability":0.9955715579954185,"decision":"APPROVED","confidence":0.9955715579954185,"version":"1","timestamp":"..."}
```

**View Traces in Grafana:**
1. Access Grafana: `http://35.237.250.189/grafana`
2. Go to **Explore** → Select **Tempo** datasource
3. TraceQL queries:
   ```
   { resource.service.name = "card-approval-api" }
   { span.name = "model_inference.predict" } | duration > 100ms
   ```

---

## 6.6 Tracing Troubleshooting Guide

### Issue #1: Tempo Datasource Not Appearing in Grafana

**Problem:**
- Grafana shows only Prometheus and Loki datasources
- Tempo datasource missing after deployment
- Error: `{"detail":"Not Found"}` when accessing datasources

**Root Cause:**
The Tempo datasource was defined in Helm values but Grafana pod didn't reload the configuration.

**Solution:**
```bash
# Upgrade monitoring stack to apply changes
source config.env
helm upgrade monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring \
  --set kube-prometheus.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"

# Restart Grafana to load new datasource
kubectl rollout restart deployment/monitoring-grafana -n monitoring

# Wait for pod to be ready
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana

# Verify datasource is added
curl -s -u "admin:${GRAFANA_ADMIN_PASSWORD}" \
  "http://35.237.250.189/grafana/api/datasources" | jq '.[].name'
```

**How to Avoid:**
- Always restart Grafana after updating monitoring Helm chart
- Check datasources via API after deployment

---

### Issue #2: "Bad Gateway" Error When Querying Tempo

**Problem:**
- Tempo datasource appears in Grafana
- Selecting "Tempo" in Explore shows: `Error (Bad Gateway). Please check the server logs`
- Service name dropdown shows "no option found"

**Root Cause:**
The Tempo datasource URL was configured with wrong port: `http://tempo.monitoring.svc.cluster.local:3100`

Tempo exposes multiple ports:
- **Port 3100**: Prometheus metrics endpoint (NOT the HTTP API)
- **Port 3200**: HTTP API endpoint for queries
- **Port 4317**: OTLP gRPC receiver (for traces ingestion)

**Diagnosis Commands:**
```bash
# Check what ports Tempo is listening on
kubectl exec -n monitoring tempo-0 -- ss -tlnp

# Output shows:
# tcp  :::3200  :::*  LISTEN  1/tempo  <- HTTP API (correct port)
# tcp  :::4317  :::*  LISTEN  1/tempo  <- OTLP gRPC
# tcp  :::9095  :::*  LISTEN  1/tempo  <- Internal gRPC

# Test connectivity from Grafana pod
kubectl exec -n monitoring $(kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -c grafana -- \
  wget -qO- "http://tempo.monitoring.svc.cluster.local:3200/api/search/tag/service.name/values"

# Should return: {"tagValues":["card-approval-api"]}
```

**Solution:**
```bash
# Fix the Tempo datasource URL in Helm values
# Edit: helm-charts/infrastructure/card-approval-monitoring/values.yaml
# Change: url: http://tempo.monitoring.svc.cluster.local:3100
# To:     url: http://tempo.monitoring.svc.cluster.local:3200

# Upgrade monitoring stack
helm upgrade monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring \
  --set kube-prometheus.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"

# Restart Grafana
kubectl rollout restart deployment/monitoring-grafana -n monitoring
```

**How to Avoid:**
- Always verify Tempo HTTP API port (3200) in documentation
- Test datasource connectivity before considering deployment complete

---

### Issue #3: Service Name Not Found in Tempo Search

**Problem:**
- Tempo datasource works (no Bad Gateway error)
- Service name dropdown shows "no option found"
- No traces appear even though API is running

**Root Cause:**
Port 3200 was not exposed in the Tempo Kubernetes service definition. The Helm chart only exposed OTLP receiver ports (4317, 4318) but not the HTTP API port (3200).

**Diagnosis Commands:**
```bash
# Check Tempo service ports
kubectl describe svc tempo -n monitoring | grep -A 20 "Port:"

# Notice port 3200 is missing!

# Test if port 3200 is reachable from Grafana
kubectl exec -n monitoring $(kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -c grafana -- \
  wget -qO- "http://tempo.monitoring.svc.cluster.local:3200/ready"

# Returns: Connection refused or timeout
```

**Solution:**
```bash
# Patch the Tempo service to expose port 3200
kubectl patch svc tempo -n monitoring --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/ports/-",
    "value": {
      "name": "tempo-http",
      "port": 3200,
      "targetPort": 3200,
      "protocol": "TCP"
    }
  }
]'

# Verify the port is now exposed
kubectl get svc tempo -n monitoring -o jsonpath='{.spec.ports[*].name}'

# Test connectivity again
kubectl exec -n monitoring $(kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -c grafana -- \
  wget -qO- "http://tempo.monitoring.svc.cluster.local:3200/api/search/tag/service.name/values"

# Should return: {"tagValues":["card-approval-api"]}
```

**Permanent Fix (Update Helm Chart):**
```yaml
# Add to helm-charts/infrastructure/tempo/values.yaml
tempo:
  service:
    type: ClusterIP
    ports:
      - name: tempo-http
        port: 3200
        targetPort: 3200
        protocol: TCP
```

**How to Avoid:**
- Verify all required ports are exposed in service definition
- Test service connectivity from consumer pods (Grafana)
- Document required ports in deployment guide

---

### Issue #4: Tracing Not Enabled in API

**Problem:**
- Tempo is working
- Service name appears but no traces found
- API logs don't show tracing initialization

**Root Cause:**
API was deployed without tracing configuration. Environment variables `OTEL_ENABLED`, `OTEL_SERVICE_NAME`, etc. were not set.

**Diagnosis Commands:**
```bash
# Check API environment variables
kubectl describe pod -n card-approval -l app.kubernetes.io/name=api | grep -A 15 "Environment:"

# Missing: OTEL_ENABLED, OTEL_SERVICE_NAME, OTEL_EXPORTER_ENDPOINT

# Check API logs for tracing initialization
kubectl logs -n card-approval -l app.kubernetes.io/name=api | grep -i "tracing\|otel"

# No output = tracing not initialized
```

**Solution:**
```bash
# Upgrade API with tracing enabled
source config.env
helm upgrade card-approval helm-charts/card-approval \
  -n card-approval \
  --set postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.postgres.password="${POSTGRES_APP_PASSWORD}" \
  --set api.image.repository="${DOCKER_REGISTRY}/${DOCKER_REPOSITORY}/${IMAGE_NAME}" \
  --set api.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}" \
  --set api.config.modelPath="" \
  --set api.tracing.enabled=true \
  --set api.tracing.exporterEndpoint="http://tempo.monitoring:4317" \
  --set api.tracing.samplingRate="1.0"

# Restart API to apply new env vars
kubectl rollout restart deployment/card-approval-api -n card-approval

# Verify tracing is enabled
kubectl logs -n card-approval -l app.kubernetes.io/name=api | head -10

# Should see:
# INFO | Initializing OpenTelemetry tracing: service=card-approval-api
# INFO | OTLP exporter configured: http://tempo.monitoring:4317
# INFO | Tracing initialized: sampling_rate=100.0%
```

**How to Avoid:**
- Always set tracing Helm values during initial API deployment
- Verify tracing initialization in pod logs after deployment

---

### Complete Tracing Deployment Checklist

Use this checklist to ensure tracing works from the start:

```bash
# 1. Deploy Tempo with GCS backend
helm upgrade --install tempo helm-charts/infrastructure/tempo \
  -n monitoring --create-namespace \
  --set tempo.tempo.storage.trace.gcs.bucket_name="${GCS_BUCKET_NAME}" \
  --set tempo.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="${GCP_MLFLOW_SERVICE_ACCOUNT}"

# 2. Verify Tempo is running and port 3200 is exposed
kubectl get pods -n monitoring -l app.kubernetes.io/name=tempo
kubectl get svc tempo -n monitoring -o jsonpath='{.spec.ports[*].name}' | grep tempo-http

# If tempo-http is missing, patch the service:
kubectl patch svc tempo -n monitoring --type='json' -p='[{"op": "add", "path": "/spec/ports/-", "value": {"name": "tempo-http", "port": 3200, "targetPort": 3200, "protocol": "TCP"}}]'

# 3. Deploy/Upgrade monitoring with Tempo datasource
helm upgrade monitoring helm-charts/infrastructure/card-approval-monitoring \
  -n monitoring \
  --set kube-prometheus.grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}"

kubectl rollout restart deployment/monitoring-grafana -n monitoring

# 4. Verify Tempo datasource in Grafana
curl -s -u "admin:${GRAFANA_ADMIN_PASSWORD}" \
  "http://35.237.250.189/grafana/api/datasources" | jq '.[] | select(.name=="Tempo") | {name, url}'

# Expected: {"name":"Tempo","url":"http://tempo.monitoring.svc.cluster.local:3200"}

# 5. Deploy API with tracing enabled
helm upgrade card-approval helm-charts/card-approval \
  -n card-approval \
  --set api.tracing.enabled=true \
  --set api.tracing.exporterEndpoint="http://tempo.monitoring:4317" \
  --set api.tracing.samplingRate="1.0"

# 6. Verify tracing in API logs
kubectl logs -n card-approval -l app.kubernetes.io/name=api | grep -i tracing

# 7. Generate test traces
for i in {1..3}; do
  curl -X POST "http://35.237.250.189/api/v1/predict" \
    -H "Content-Type: application/json" \
    -d '{"ID":'$i',"CODE_GENDER":"M","FLAG_OWN_CAR":"Y","FLAG_OWN_REALTY":"Y","CNT_CHILDREN":0,"AMT_INCOME_TOTAL":150000,"NAME_INCOME_TYPE":"Working","NAME_EDUCATION_TYPE":"Higher education","NAME_FAMILY_STATUS":"Married","NAME_HOUSING_TYPE":"House / apartment","DAYS_BIRTH":-12000,"DAYS_EMPLOYED":-3000,"FLAG_MOBIL":1,"FLAG_WORK_PHONE":0,"FLAG_PHONE":1,"FLAG_EMAIL":1,"OCCUPATION_TYPE":"Managers","CNT_FAM_MEMBERS":2}'
done

# 8. Wait 1 minute for traces to be indexed, then query Tempo
kubectl exec -n monitoring tempo-0 -- wget -qO- \
  "http://localhost:3200/api/search/tag/service.name/values"

# Expected: {"tagValues":["card-approval-api"]}

# 9. Test from Grafana UI
# - Open http://35.237.250.189/grafana
# - Explore → Tempo → Search → Service Name = "card-approval-api"
```

---

### Key Takeaways

| Issue | Root Cause | Prevention |
|-------|------------|------------|
| Datasource not appearing | Config not loaded | Restart Grafana after Helm upgrade |
| Bad Gateway error | Wrong port (3100 vs 3200) | Use port 3200 for Tempo HTTP API |
| Service name not found | Port 3200 not exposed | Patch service or update Helm chart |
| No traces appearing | Tracing not enabled in API | Set `api.tracing.enabled=true` |

**Critical Ports:**
- **4317** - OTLP gRPC (for sending traces from API to Tempo)
- **3200** - HTTP API (for Grafana to query traces)
- **3100** - Prometheus metrics (NOT for trace queries)

---

## 7. Port Forwarding

```bash
# MLflow UI
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training

# API
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval

# Grafana
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

# Prometheus
kubectl port-forward svc/prometheus-monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring
```

---

## 7. Check Status

```bash
# All pods
kubectl get pods -A | grep -E "card-approval|monitoring"

# Specific namespace
kubectl get pods -n card-approval
kubectl get pods -n card-approval-training
kubectl get pods -n monitoring

# Services
kubectl get svc -A | grep -E "card-approval|monitoring"

# Logs
kubectl logs -f deployment/card-approval-api -n card-approval
kubectl logs -f deployment/card-approval-training-mlflow -n card-approval-training
```

kubectl apply -f manifests/ingress.yaml

---

## 9. API Testing

```bash
# Health check
curl http://localhost:8000/health

# Prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 150000,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -3000,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 1,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2
  }'

# Metrics
curl http://localhost:8000/metrics
```

---

## 10. Model Training

```bash
cd cap_model

# Run training
python scripts/run_training.py --config src/config/config.yaml

# With MLflow tracking
export MLFLOW_TRACKING_URI=http://localhost:5000
python scripts/run_training.py --config src/config/config.yaml
```

---

## 10. Docker Commands (Reference)

```bash
# Build image
docker build -t card-approval-api:latest .

# Tag for registry
docker tag card-approval-api:latest \
  us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:latest

# Push to registry
gcloud auth configure-docker us-east1-docker.pkg.dev
docker push us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api:latest
```

---

## 12. Cost Management Scripts

```bash
# Morning - scale up
./scripts/morning-mode.sh

# Night - scale down
./scripts/night-mode.sh

# Weekend shutdown
./scripts/weekend-shutdown.sh

# Monday startup
./scripts/monday-startup.sh
```

---

## 12. Troubleshooting

```bash
# Describe pod (see events/errors)
kubectl describe pod <pod-name> -n <namespace>

# Get pod logs
kubectl logs <pod-name> -n <namespace> --previous

# Exec into pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Restart deployment
kubectl rollout restart deployment/<name> -n <namespace>

# Delete stuck pod
kubectl delete pod <pod-name> -n <namespace> --force --grace-period=0
```

---

## 13. Helm Troubleshooting

```bash
# List releases
helm list -A

# Release history
helm history <release-name> -n <namespace>

# Rollback
helm rollback <release-name> <revision> -n <namespace>

# Uninstall
helm uninstall <release-name> -n <namespace>

# Debug template
helm template <release-name> <chart-path> --debug
```

---


---

## 15. CI/CD Setup (Jenkins)

### 15.1 Deploy Jenkins VM (via Ansible)

```bash
cd ansible

# Install Ansible requirements
pip install ansible google-auth


# Create new key (if not exists)
gcloud iam service-accounts keys create ~/secrets/gcp-key.json \
  --iam-account=mlflow-gcs@product-recsys-mlops.iam.gserviceaccount.com

export GOOGLE_APPLICATION_CREDENTIALS=~/secrets/gcp-key.json

# IMPORTANT: Source config.env to set environment variables
source ../config.env

# Run playbooks in order (pass GCP vars via -e flag)
# Step 1: Create VM (runs on localhost)
ansible-playbook playbooks/01_create_jenkins_vm.yml -i inventory/hosts.ini \
  -e "gcp_project_id=${GCP_PROJECT_ID}" \
  -e "gcp_region=${GCP_REGION}" \
  -e "gcp_zone=${GCP_ZONE}"

# Step 2-4: Run on Jenkins VM (uses [jenkins] group in inventory)
ansible-playbook playbooks/02_install_docker.yml -i inventory/hosts.ini \
  -e "gcp_project_id=${GCP_PROJECT_ID}" \
  -e "gcp_zone=${GCP_ZONE}"

ansible-playbook playbooks/03_deploy_jenkins.yml -i inventory/hosts.ini \
  -e "gcp_project_id=${GCP_PROJECT_ID}" \
  -e "gcp_zone=${GCP_ZONE}"

ansible-playbook playbooks/04_configure_jenkins.yml -i inventory/hosts.ini \
  -e "gcp_project_id=${GCP_PROJECT_ID}" \
  -e "gcp_zone=${GCP_ZONE}"

# Or use the deploy script
./deploy_jenkins.sh

# Get Jenkins VM external IP
gcloud compute instances describe jenkins-server \
  --zone=us-east1-b --project=product-recsys-mlops \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```
24/01 - 34.23.187.207

### 15.2 Initial Jenkins Setup

Access Jenkins at `http://34.23.187.207:8080`

**Get Initial Admin Password:**
```bash
gcloud compute ssh jenkins-server --zone=us-east1-b --project=product-recsys-mlops \
  --command="sudo docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
# Output: de0009df848640019f8149df92a26a1a
```

**Login Credentials:**
- **User:** `phatngo` (or `admin` if using default ansible vars)
- **Password:** `phatngo123` (or set via `JENKINS_ADMIN_PASSWORD` env var)

**Install Required Plugins:**
1. **Manage Jenkins** → **Plugins** → **Available plugins**
2. Search and install:
   - `SonarQube Scanner`
   - `GitHub Branch Source` (for GitHub App support)
   - `GitHub Integration` (for webhook support)
   - `Docker Pipeline`
   - `Google Kubernetes Engine`

### 15.3 Configure SonarQube Server
**Login Credentials:**
- **User:** `admin`
- **Password:** `phatngo123`
-
**In Jenkins:**
1. **Manage Jenkins** → **System**
2. Scroll to **SonarQube servers**
3. Click **Add SonarQube**
   - Name: `SonarQube`
   - Server URL: `http://34.23.187.207:9000`
   - Server authentication token: Select credential (create in next step)

**Get SonarQube Token:**
```bash
# Access SonarQube at http://34.23.187.207:9000
# Login: admin / admin (change password on first login)
# My Account → Security → Generate Tokens
# Name: jenkins-integration
# Copy the generated token
```

### 15.4 Jenkins Service Account IAM Setup (REQUIRED!)

>    **CRITICAL:** The GCP service account used by Jenkins MUST have these IAM roles.
> Without them, the pipeline will fail with permission denied errors.

```bash
# Variables (source config.env for consistency)
source ../config.env

# 1. Grant Artifact Registry Writer (for pushing Docker images)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# 2. Grant GKE Developer (for deploying to GKE)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/container.developer"

# 3. Grant GKE Cluster Viewer (for getting cluster credentials)
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${GSA_EMAIL}" \
  --role="roles/container.clusterViewer"

# Verify permissions
gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${GSA_EMAIL}" \
  --format="table(bindings.role)"
```

**Required Roles Summary:**

| Role | Permission | Why Needed |
|------|------------|------------|
| `roles/artifactregistry.writer` | Push Docker images | Jenkins pushes built images to Artifact Registry |
| `roles/container.developer` | Deploy to GKE | Jenkins runs `helm upgrade` on GKE cluster |
| `roles/container.clusterViewer` | Get cluster credentials | Jenkins runs `gcloud container clusters get-credentials` |
| `roles/storage.objectAdmin` | Access GCS buckets | Already set up in Section 3 for MLflow |

---

### 15.5 Configure Jenkins Credentials

**Manage Jenkins → Credentials → System → Global credentials → Add Credentials:**

| ID | Type | Description | How to Get |
|----|------|-------------|------------|
| `gcp-service-account` | Secret file | GCP service account JSON key | Upload `~/secrets/gcp-key.json` (must have roles from 15.4!) |
| `gcp-project-id` | Secret text | GCP Project ID | `product-recsys-mlops` |
| `github-credentials` | Username with password | GitHub PAT for branch source | See below |
| `github-pat` | Secret text | GitHub PAT for API (PR status) | See below |
| `sonarqube-token` | Secret text | SonarQube authentication token | From SonarQube UI above |

#### Step 1: Generate GitHub Personal Access Token

```bash
# Go to: https://github.com/settings/tokens
# Generate new token (classic)
# Name: card-approval-cicd
# Scopes:
#     repo (Full control of private repositories)
#     admin:repo_hook (Full control of repository hooks)
# Copy the generated token - you'll use it for BOTH credentials below
```

#### Step 2: Create `github-credentials` (for Branch Source - clone code)

| Field | Value |
|-------|-------|
| **Kind** | Username with password |
| **Scope** | Global |
| **Username** | `thanhphat-19` |
| **Password** | Paste your GitHub PAT |
| **ID** | `github-credentials` |
| **Description** | GitHub credentials for branch source |

#### Step 3: Create `github-pat` (for GitHub Server API - PR status)

| Field | Value |
|-------|-------|
| **Kind** | Secret text |
| **Scope** | Global |
| **Secret** | Paste the SAME GitHub PAT |
| **ID** | `github-pat` |
| **Description** | GitHub PAT for commit status |

> **Why two credentials?**
> - `github-credentials` (Username/password) → GitHub branch source plugin needs this format
> - `github-pat` (Secret text) → GitHub Server API needs this format

### 15.6 Configure GitHub Server (for PR Status)

**This step is REQUIRED to see build status on GitHub PRs!**

1. **Manage Jenkins** → **System** → scroll to **GitHub** section
2. Click **Add GitHub Server**:

| Field | Value |
|-------|-------|
| **Name** | `GitHub` |
| **API URL** | `https://api.github.com` |
| **Credentials** | Select `github-pat` (the Secret text one!) |
| ☑️ **Manage hooks** | Check this box |

3. Click **Test connection**
   -   Should show: `Credentials verified for user thanhphat-19, rate limit: XXXX`
   -  If you don't see `github-pat` in dropdown → you created it as wrong type
4. Click **Save**

### 15.7 Create Jenkins Pipeline

**Create Multibranch Pipeline:**

1. **New Item** → **Multibranch Pipeline** → Name: `card-approval-prediction`
2. **Branch Sources** → **Add source** → **GitHub**
   - **Credentials:** Select `github-credentials` (Username with password)
   - **Repository HTTPS URL:** `https://github.com/thanhphat-19/card-approval-prediction`

3. **Build Configuration**
   - **Mode:** by Jenkinsfile
   - **Script Path:** `Jenkinsfile`
4. **Scan Multibranch Pipeline Triggers**
   -   Periodically if not otherwise run (15 minutes)
   -   Scan by webhook
5. **Save**

**Why Multibranch Pipeline?**
- Automatically discovers branches and PRs
- Runs different stages based on branch type
- Better GitHub integration
- GitHub App provides better PR status reporting

### 15.8 Setup GitHub Webhook (Auto-trigger)


**If using PAT - Configure in GitHub Repository:**

1. Go to: `https://github.com/<your-username>/card-approval-prediction/settings/hooks`
2. **Add webhook**
   - **Payload URL:** `http://34.23.187.207:8080/github-webhook/`
   - **Content type:** `application/json`
   - **SSL verification:** Disable (for HTTP)
   - **Events:**
     -   Pull requests
     -   Pushes
   -   Active
3. **Add webhook**

**Or use script:**
```bash
cd /home/thanhphat/workspace/card-approval-prediction
source config.env

./scripts/setup-github-webhook.sh
```

### 15.9 CI/CD Flow Explained

**📋 Current Flow Diagram:**
```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD WORKFLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CREATE PR (feature/*, fix/*)                               │
│         ↓                                                    │
│  ┌──────────────────────────────────────┐                  │
│  │ 1. Checkout Code                     │                  │
│  │ 2. Check Branch Type                 │                  │
│  │ 3. Linting (flake8, pylint, black)   │                  │
│  └──────────────────────────────────────┘                  │
│         ↓                                                    │
│    Linting Passed → Ready for review                       │
│                                                              │
│  ─────────────────────────────────────────                 │
│                                                              │
│  MERGE PR → main branch                                     │
│         ↓                                                    │
│  ┌──────────────────────────────────────┐                  │
│  │ 1. Checkout Code                     │                  │
│  │ 2. Check Branch Type                 │                  │
│  │ 3. Linting                           │                  │
│  │ 4. Build Docker Image 🐳             │                  │
│  │ 5. Security Scan (Trivy) 🔒          │                  │
│  │ 6. Push to Artifact Registry       │                  │
│  │ 7. Deploy to GKE ☸️                  │                  │
│  └──────────────────────────────────────┘                  │
│         ↓                                                    │
│    Production Deployment Complete                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

> **Note:** SonarQube analysis is currently disabled. To enable, add the SonarQube stages back to Jenkinsfile.

**🔍 Stage Details:**

| Stage | PR Branch | Main Branch | Purpose |
|-------|-----------|-------------|---------|
| Checkout |   |   | Get source code |
| Check Branch |   |   | Determine branch type |
| Linting |   |   | Code quality checks (flake8, pylint, black, isort) |
| Build Image |  |   | Create Docker image |
| Security Scan |  |   | Scan image vulnerabilities (Trivy) |
| Push Image |  |   | Upload to Artifact Registry |
| Deploy |  |   | Helm upgrade to GKE |

### 15.10 Verify Pipeline

```bash
# Trigger a build manually or push a commit
# Check build logs in Jenkins

# Verify deployment
kubectl get pods -n card-approval
kubectl logs -f deployment/card-approval-api -n card-approval
```

### 15.11 Test the CI/CD Pipeline

**Test PR Flow:**
```bash
# Create a feature branch
git checkout -b feature/test-cicd
echo "# Test" >> README.md
git add README.md
git commit -m "test: trigger CI/CD"
git push origin feature/test-cicd

# Create PR on GitHub
# Jenkins should automatically:
# 1. Detect the PR
# 2. Run linting
# 3. Run SonarQube analysis
# 4. Check quality gate
# 5. Report status back to GitHub PR
```

**Test Main Branch Deployment:**
```bash
# After PR is approved and merged
# Jenkins should automatically:
# 1. Build Docker image
# 2. Scan with Trivy
# 3. Push to Artifact Registry
# 4. Deploy to GKE

# Verify deployment
kubectl get pods -n card-approval
kubectl describe pod <pod-name> -n card-approval
```

### 15.12 Troubleshooting

**Common Issues:**

| Issue | Solution |
|-------|----------|
| `docker: Permission denied` | Install Docker CLI in Jenkins container: `docker exec jenkins apt-get update && apt-get install -y docker.io` |
| SonarQube analysis fails | Check SonarQube server is running: `docker ps` on Jenkins VM |
| SonarQube keeps restarting | Remove `SONAR_JDBC_URL` env var - use embedded H2 database |
| Image push fails (`Permission 'artifactregistry.repositories.uploadArtifacts' denied`) | Grant `roles/artifactregistry.writer` to service account (see section 15.4) |
| Deploy fails (GKE permission denied) | Grant `roles/container.developer` and `roles/container.clusterViewer` to service account (see section 15.4) |
| Quality gate timeout | Increase timeout in Jenkinsfile or check SonarQube connectivity |
| Missing `gcp-project-id` | Add credential: Manage Jenkins → Credentials → Secret text |
| **PR status not appearing** | 1) Verify `github-pat` is **Secret text** type. 2) Add GitHub Server in Manage Jenkins → System → GitHub using `github-pat` |
| `github-pat` not in dropdown | You created it as wrong type - delete and recreate as **Secret text** |
| Git clone fails | Ensure `github-pat` has `repo` scope and GitHub Branch Source plugin is installed |

**Check Jenkins logs:**
```bash
# On Jenkins VM
gcloud compute ssh jenkins-server --zone=us-east1-b --project=product-recsys-mlops

# View container logs
sudo docker logs jenkins -f
sudo docker logs sonarqube -f
```

---

## 📚 Complete Documentation Index

This guide covers manual commands for setting up the entire project. For detailed guides on specific topics, see:

### Core Setup Documentation

| Doc | Description |
|-----|-------------|
| **[00_Setup_Guide.md](./00_Setup_Guide.md)** | Initial project setup and prerequisites |
| **[01_Helm_Deployment.md](./01_Helm_Deployment.md)** | Helm chart deployment (NGINX, MLflow, Monitoring) |
| **[02_MLflow_Training.md](./02_MLflow_Training.md)** | Model training with MLflow tracking |
| **[03_CICD_Pipeline.md](./03_CICD_Pipeline.md)** | **Complete CI/CD setup with Jenkins** |
| **[04_NGINX.md](./04_NGINX.md)** | Accessing services via LoadBalancer |
| **[05_Tracing.md](./05_Tracing.md)** | Distributed tracing with OpenTelemetry & Tempo |

### Critical Setup Steps Summary

**For first-time setup, you must:**

1.    Create GCP service account with Workload Identity (Section 3)
2.    Generate service account key for Jenkins CI/CD (Section 4)
3.    Grant all 4 IAM roles to service account (Section 4):
   - `roles/storage.objectAdmin`
   - `roles/artifactregistry.writer`
   - `roles/container.clusterViewer`
   - `roles/container.developer`
4.    Add test data to git repository for Model Evaluation (See 04_CICD_Pipeline.md Step 7)
5.    Upload service account key to Jenkins credentials as `gcp-service-account`

**Common Pitfalls:**
-     Using old/corrupted service account key → `Invalid JWT Signature` error
-     Missing IAM roles → `403 Permission Denied` errors
-     Test data not in git → `ERROR: Test features not found`
-     Incorrect credential type in Jenkins → Pipeline failures

---

## 🎯 Next Steps After Setup

1. **Train a model**: Follow Section 10 or [02_MLflow_Training.md](./02_MLflow_Training.md)
2. **Test the API**: Use Section 9 or [04_NGINX.md](./04_NGINX.md)
3. **Setup monitoring**: Check [05_Tracing.md](./05_Tracing.md)
4. **Trigger CI/CD**: Push code to trigger Jenkins pipeline (Section 15)
5. **Cost optimization**: Use Section 12 for scale-up/scale-down scripts

---

## 🔧 Quick Troubleshooting Reference

### Most Common Issues & Fixes

| Issue | Quick Fix |
|-------|-----------|
| **MLflow "Invalid Host header"** | Add `--gunicorn-opts "--forwarded-allow-ips='*'"` to MLflow startup |
| **GCS Permission Denied** | Check Workload Identity bindings (Section 3) |
| **Jenkins "Invalid JWT Signature"** | Regenerate service account key (Section 4) |
| **Image pull error** | Check Artifact Registry permissions |
| **Pod CrashLoopBackOff** | `kubectl logs <pod-name> -n <namespace>` |
| **Model not found** | Train model first and check MLflow registry |

### Useful Debug Commands

```bash
# Check all pods status
kubectl get pods -A | grep -E "card-approval|monitoring|ingress"

# View pod logs
kubectl logs -f <pod-name> -n <namespace>

# Describe pod (see events)
kubectl describe pod <pod-name> -n <namespace>

# Test service connectivity
kubectl run test --rm -it --image=curlimages/curl -- curl http://<service>.<namespace>:port/health

# Check Helm releases
helm list -A

# Rollback Helm release
helm rollback <release> <revision> -n <namespace>
```

### Important URLs (replace with your LoadBalancer IP)

| Service | URL |
|---------|-----|
| **Swagger UI** | `http://<NGINX_IP>/docs` |
| **Grafana** | `http://<NGINX_IP>/grafana/` |
| **MLflow** | `http://<NGINX_IP>/mlflow/` |
| **Health Check** | `http://<NGINX_IP>/health` |

---

**Last Updated:** February 2026
**Version:** 3.0 - Comprehensive setup guide with troubleshooting
