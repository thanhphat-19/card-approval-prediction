#!/bin/bash
# Monday Startup - Resume after weekend shutdown
# Brings everything back online

set -e

echo "💼 =============================================="
echo "   Monday Startup: Back to Work!"
echo "================================================"
echo ""

# Configuration
CLUSTER_NAME="mlops-cluster"
REGION="us-east1"
JENKINS_VM="jenkins-server"
JENKINS_ZONE="us-east1-b"
PROJECT_ID="product-recsys-mlops"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "This will:"
echo "  1. Start Jenkins VM"
echo "  2. Add 3 nodes to cluster"
echo "  3. Restore all deployments"
echo ""
echo "⏱️  Estimated time: 5-7 minutes"
echo ""

read -p "Start up for Monday? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Start Jenkins VM
echo ""
echo "Step 1: Starting Jenkins VM..."
echo "-------------------------------"

if gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} &>/dev/null; then
    STATUS=$(gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} --format='value(status)')

    if [ "$STATUS" = "TERMINATED" ]; then
        echo "  Starting Jenkins..."
        gcloud compute instances start ${JENKINS_VM} \
            --zone=${JENKINS_ZONE} \
            --project=${PROJECT_ID} \
            --quiet

        echo "  Waiting for Jenkins to boot..."
        sleep 30
        echo -e "${GREEN}✓${NC} Jenkins VM started"
    else
        echo "  Jenkins is already running"
    fi
else
    echo "  Jenkins VM not found, skipping..."
fi

# Step 2: Restore cluster nodes
echo ""
echo "Step 2: Adding cluster nodes..."
echo "--------------------------------"
echo "  Adding 3 nodes (this takes ~3-5 minutes)..."
echo ""

gcloud container clusters resize ${CLUSTER_NAME} \
    --num-nodes=3 \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --quiet

echo -e "${GREEN}✓${NC} Nodes added to cluster"

# Wait for nodes to be ready
echo ""
echo "Step 3: Waiting for nodes to be ready..."
echo "-----------------------------------------"
echo "  Checking node status..."

sleep 45
kubectl wait --for=condition=Ready nodes --all --timeout=300s || true

echo -e "${GREEN}✓${NC} All nodes are ready"

# Step 4: Restore deployments with Helm
echo ""
echo "Step 4: Restoring deployments..."
echo "---------------------------------"

# Restore card-approval
if helm list -n card-approval | grep -q card-approval; then
    echo "  Restoring card-approval..."
    helm upgrade card-approval ./helm-charts/card-approval \
        -n card-approval \
        --reuse-values \
        --wait \
        --timeout 5m
else
    echo "  card-approval not found, deploying fresh..."
    helm install card-approval ./helm-charts/card-approval \
        -n card-approval \
        --create-namespace \
        --wait \
        --timeout 5m
fi

# Restore recsys-training
if helm list -n recsys-training | grep -q recsys-training; then
    echo "  Restoring recsys-training..."
    helm upgrade recsys-training ./helm-charts/recsys-training \
        -n recsys-training \
        --reuse-values \
        --wait \
        --timeout 5m
else
    echo "  recsys-training not found, skipping..."
fi

# Optional: Restore monitoring
if kubectl get namespace monitoring &>/dev/null; then
    echo "  Restoring monitoring (if installed)..."
    helm upgrade monitoring prometheus-community/kube-prometheus-stack \
        -n monitoring \
        --reuse-values \
        --wait \
        --timeout 3m 2>/dev/null || echo "  Monitoring not found, skipping..."
fi

echo -e "${GREEN}✓${NC} Deployments restored"

# Wait a bit for pods to fully start
echo ""
echo "Step 5: Verifying pod health..."
echo "--------------------------------"
sleep 20

# Summary
echo ""
echo "================================================"
echo -e "${GREEN}✅ Monday Startup Complete!${NC}"
echo "================================================"
echo ""
echo "📊 Cluster Status:"
kubectl get nodes
echo ""
echo "🚀 Application Status:"
echo ""
echo "Card Approval:"
kubectl get pods -n card-approval 2>/dev/null || echo "  Not deployed"
echo ""
echo "MLflow Training:"
kubectl get pods -n recsys-training 2>/dev/null || echo "  Not deployed"
echo ""

# Get Jenkins URL
if gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} &>/dev/null; then
    JENKINS_IP=$(gcloud compute instances describe ${JENKINS_VM} \
        --zone=${JENKINS_ZONE} \
        --format='value(networkInterfaces[0].accessConfigs[0].natIP)')
    echo "🔧 Jenkins: http://${JENKINS_IP}:8080"
fi

echo ""
echo "🔗 Quick Access Commands:"
echo "  • API:     kubectl port-forward -n card-approval svc/card-approval-api 8000:80"
echo "  • MLflow:  kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000"
echo "  • Grafana: kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
echo ""
echo "🌙 To shutdown tonight:"
echo "  ./scripts/night-mode.sh"
echo ""
echo "🏖️ To shutdown next weekend:"
echo "  ./scripts/weekend-shutdown.sh"
echo ""
echo "☕ Ready to code! Have a productive week!"
echo ""
