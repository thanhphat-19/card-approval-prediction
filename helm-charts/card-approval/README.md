# Card Approval API - Helm Deployment Guide

This Helm chart deploys the complete Card Approval Prediction API stack including PostgreSQL, Redis, and the FastAPI application.

## Architecture

```
card-approval (umbrella chart)
├── postgres (infrastructure/postgres)
├── redis (infrastructure/redis)
└── api (infrastructure/api)
```

## Prerequisites

- Kubernetes cluster (GKE recommended)
- Helm 3.x installed
- `kubectl` configured
- Existing `recsys-training` namespace with MLflow deployed

## Quick Start

###1: Build Dependencies

```bash
cd helm-charts/card-approval
helm dependency build
```

This will download/link the infrastructure charts.

### Step 2: Review Configuration

Edit `values.yaml` to configure:
- Database credentials (IMPORTANT!)
- Image repository and tag
- Resource limits
- Autoscaling settings

### Step 3: Create Namespace

```bash
kubectl create namespace card-approval
```

### Step 4: Install Chart

```bash
helm install card-approval . \
  --namespace card-approval \
  --create-namespace \
  --values values.yaml
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n card-approval

# Check services
kubectl get svc -n card-approval

# View logs
kubectl logs -f deployment/card-approval-api -n card-approval
```

## Configuration

### Database Configuration

The chart includes PostgreSQL by default. To use an external database:

```yaml
postgres:
  enabled: false  # Disable internal PostgreSQL

api:
  postgres:
    host: "external-db.example.com"
    port: 5432
    database: "card_approval_db"
    username: "app_user"
    password: "secure_password"
```

### Redis Configuration

Similarly, Redis can be disabled if using external Redis:

```yaml
redis:
  enabled: false

api:
  redis:
    host: "external-redis.example.com"
    port: 6379
```

### Image Configuration

Update the image when deploying new versions:

```yaml
api:
  image:
    repository: us-east1-docker.pkg.dev/product-recsys-mlops/product-recsys-mlops-recsys/card-approval-api
    tag: "v1.2.3"  # Specify version tag
    pullPolicy: Always
```

### Autoscaling

Adjust autoscaling based on load:

```yaml
api:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
```

### Ingress (External Access)

To expose the API externally:

```yaml
api:
  ingress:
    enabled: true
    className: "nginx"
    host: "card-approval-api.example.com"
    annotations:
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

## Upgrading

### Update Image Tag

```bash
helm upgrade card-approval . \
  --namespace card-approval \
  --set api.image.tag=v1.2.4 \
  --reuse-values
```

### Update Configuration

```bash
helm upgrade card-approval . \
  --namespace card-approval \
  --values values.yaml
```

### Rollback

```bash
helm rollback card-approval -n card-approval
```

## Accessing the API

### Port-Forward (Development)

```bash
kubectl port-forward -n card-approval svc/card-approval-api 8000:80
# Access at http://localhost:8000
```

### NodePort (Testing)

```bash
# Update service type
helm upgrade card-approval . \
  --namespace card-approval \
  --set api.service.type=NodePort

# Get NodePort
kubectl get svc card-approval-api -n card-approval
```

### LoadBalancer (Production)

```bash
helm upgrade card-approval . \
  --namespace card-approval \
  --set api.service.type=LoadBalancer

# Get external IP
kubectl get svc card-approval-api -n card-approval
```

## Monitoring

The API exposes Prometheus metrics at `/metrics`:

```bash
kubectl port-forward -n card-approval svc/card-approval-api 8000:80
curl http://localhost:8000/metrics
```

To deploy Prometheus/Grafana monitoring, see [../monitoring/README.md](../monitoring/README.md)

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n card-approval

# Check events
kubectl get events -n card-approval --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl logs -f deployment/card-approval-postgres -n card-approval

# Test database connection
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -n card-approval -- \
  psql -h card-approval-postgres -U app_user -d card_approval_db
```

### MLflow Connection Issues

```bash
# Verify MLflow is accessible
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n card-approval -- \
  curl http://recsys-training-mlflow.recsys-training.svc.cluster.local:5000/health
```

## Uninstalling

```bash
helm uninstall card-approval -n card-approval
```

**Note:** PVCs are not deleted by default. To delete them:

```bash
kubectl delete pvc -n card-approval --all
```

## CI/CD Integration

This chart is designed to work with Jenkins CI/CD. See [/Jenkinsfile](../../Jenkinsfile) for the pipeline configuration.

### Jenkins Deployment Stage

```groovy
stage('Deploy to GKE') {
    steps {
        sh '''
            helm upgrade --install card-approval ./helm-charts/card-approval \
              --namespace card-approval \
              --create-namespace \
              --set api.image.tag=${IMAGE_TAG} \
              --wait \
              --timeout 5m
        '''
    }
}
```

## Security Best Practices

1. **Use Secrets for Passwords:**
   ```bash
   kubectl create secret generic db-credentials \
     --from-literal=username=app_user \
     --from-literal=password=<strong-password> \
     -n card-approval
   ```

2. **Enable Pod Security Standards:**
   ```yaml
   api:
     securityContext:
       runAsNonRoot: true
       runAsUser: 1000
   ```

3. **Use Workload Identity (GKE):**
   ```yaml
   api:
     serviceAccount:
       annotations:
         iam.gke.io/gcp-service-account: "api-sa@project.iam.gserviceaccount.com"
   ```

## Support

For issues or questions, please open an issue in the repository.
