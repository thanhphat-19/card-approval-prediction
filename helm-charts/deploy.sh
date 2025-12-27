#!/bin/bash

# Deploy Card Approval API using Helm
# Usage: ./deploy.sh

set -e

echo "=================================================="
echo "Deploying Card Approval API with Helm"
echo "=================================================="

# Configuration
NAMESPACE="card-approval"
RELEASE_NAME="card-approval"
CHART_PATH="./card-approval"

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "Error: Helm is not installed"
    echo "Install from: https://helm.sh/docs/intro/install/"
    exit 1
fi

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: kubectl is not configured or cluster is not accessible"
    exit 1
fi

# Step 1: Build dependencies
echo "Step 1: Building Helm dependencies..."
cd $CHART_PATH
helm dependency build
cd ..

# Step 2: Validate chart
echo "Step 2: Validating Helm chart..."
helm lint $CHART_PATH

# Step 3: Create namespace if it doesn't exist
echo "Step 3: Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Step 4: Check if MLflow is accessible (required dependency)
echo "Step 4: Checking MLflow connectivity..."
if kubectl get svc -n recsys-training recsys-training-mlflow &> /dev/null; then
    echo "✓ MLflow service found in recsys-training namespace"
else
    echo "⚠ Warning: MLflow service not found. Make sure recsys-training is deployed."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 5: Install or upgrade the chart
echo "Step 5: Installing/Upgrading Helm chart..."
helm upgrade --install $RELEASE_NAME $CHART_PATH \
  --namespace $NAMESPACE \
  --create-namespace \
  --wait \
  --timeout 10m \
  --atomic

# Step 6: Verify deployment
echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""

# Check pod status
echo "Pod Status:"
kubectl get pods -n $NAMESPACE

echo ""
echo "Service Status:"
kubectl get svc -n $NAMESPACE

echo ""
echo "=================================================="
echo "Access the API:"
echo "=================================================="
echo ""
echo "Port-forward:"
echo "  kubectl port-forward -n $NAMESPACE svc/card-approval-api 8000:80"
echo ""
echo "Then access:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"
echo "  - Metrics: http://localhost:8000/metrics"
echo ""

# Show release status
echo "Helm Release Status:"
helm status $RELEASE_NAME -n $NAMESPACE

echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/card-approval-api -n $NAMESPACE"
echo ""
