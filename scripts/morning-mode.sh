#!/bin/bash
# Morning Mode - Scale up cluster to resume development
# Restores cluster to 3 nodes and redeploys services

set -e

echo "☀️ =============================================="
echo "   Morning Mode: Starting Development Day"
echo "================================================"
echo ""

# Configuration
CLUSTER_NAME="mlops-cluster"
REGION="us-east1"
PROJECT_ID="product-recsys-mlops"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "This will:"
echo "  1. Scale cluster from 1 node to 3 nodes"
echo "  2. Restore all deployments"
echo "  3. Wait for pods to be ready"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Scale up nodes
echo ""
echo "Step 1: Adding cluster nodes..."
echo "--------------------------------"
echo "  From: 1 node"
echo "  To:   3 nodes"
echo ""

gcloud container clusters resize ${CLUSTER_NAME} \
    --num-nodes=3 \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --quiet

echo -e "${GREEN}✓${NC} Cluster scaled up to 3 nodes"

# Wait for nodes to be ready
echo ""
echo "Step 2: Waiting for nodes to be ready..."
echo "-----------------------------------------"
sleep 30

kubectl wait --for=condition=Ready nodes --all --timeout=180s

echo -e "${GREEN}✓${NC} All nodes are ready"

# Step 3: Restore deployments
echo ""
echo "Step 3: Restoring deployments..."
echo "---------------------------------"

# Card Approval - restore using Helm
if helm list -n card-approval | grep -q card-approval; then
    echo "  Restoring card-approval..."
    helm upgrade card-approval ./helm-charts/card-approval \
        -n card-approval \
        --reuse-values \
        --wait
else
    echo "  Deploying card-approval (first time)..."
    helm install card-approval ./helm-charts/card-approval \
        -n card-approval \
        --create-namespace \
        --wait
fi

# Recsys Training - restore using Helm
if helm list -n recsys-training | grep -q recsys-training; then
    echo "  Restoring recsys-training..."
    helm upgrade recsys-training ./helm-charts/recsys-training \
        -n recsys-training \
        --reuse-values \
        --wait
else
    echo "  recsys-training not found, skipping..."
fi

echo -e "${GREEN}✓${NC} Deployments restored"

# Summary
echo ""
echo "================================================"
echo -e "${GREEN}✅ Morning Mode Complete!${NC}"
echo "================================================"
echo ""
echo "📊 Cluster Status:"
kubectl get nodes
echo ""
echo "🚀 Pod Status:"
kubectl get pods -n card-approval
echo ""
kubectl get pods -n recsys-training
echo ""
echo "🔗 Quick Access:"
echo "  • API:     kubectl port-forward -n card-approval svc/card-approval-api 8000:80"
echo "  • MLflow:  kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000"
echo ""
echo "🌙 To scale down when done:"
echo "  ./scripts/night-mode.sh"
echo ""
