#!/bin/bash
# Night Mode - Scale down cluster when done coding for the day
# Saves ~$4/hour by reducing from 3 nodes to 1 node

set -e

echo "🌙 =============================================="
echo "   Night Mode: Scaling Down Cluster"
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
echo "  1. Scale all deployments to 0 replicas"
echo "  2. Reduce cluster from 3 nodes to 1 node"
echo "  3. Save approximately \$4/hour"
echo ""
echo -e "${YELLOW}Persistent disks and data will be preserved${NC}"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Scale all deployments to 0
echo ""
echo "Step 1: Scaling deployments to 0 replicas..."
echo "---------------------------------------------"

# # Card Approval namespace
# if kubectl get namespace card-approval &>/dev/null; then
#     echo "  Scaling card-approval deployments..."
#     kubectl scale deployment --all --replicas=0 -n card-approval
# fi

# Recsys Training namespace
if kubectl get namespace recsys-training &>/dev/null; then
    echo "  Scaling recsys-training deployments..."
    kubectl scale deployment --all --replicas=0 -n recsys-training
fi

# # Monitoring namespace (optional, keeps monitoring light)
# if kubectl get namespace monitoring &>/dev/null; then
#     echo "  Scaling monitoring deployments..."
#     kubectl scale deployment --all --replicas=0 -n monitoring || true
# fi

echo -e "${GREEN}✓${NC} All deployments scaled to 0"

# # Step 2: Scale down nodes
# echo ""
# echo "Step 2: Reducing cluster nodes..."
# echo "-----------------------------------"
# echo "  From: 3 nodes"
# echo "  To:   1 node"
# echo ""

# gcloud container clusters resize ${CLUSTER_NAME} \
#     --num-nodes=1 \
#     --region=${REGION} \
#     --project=${PROJECT_ID} \
#     --quiet

# echo -e "${GREEN}✓${NC} Cluster scaled down to 1 node"

# Summary
echo ""
echo "================================================"
echo -e "${GREEN}✅ Night Mode Activated!${NC}"
echo "================================================"
echo ""
echo "💰 Cost Savings:"
echo "  • Before: ~\$7/day (3 nodes + control plane)"
echo "  • Now:    ~\$4/day (1 node + control plane)"
echo "  • Saving: ~\$3/day"
echo ""
echo "📊 Current Status:"
kubectl get nodes
echo ""
echo "🌅 To resume development tomorrow:"
echo "  ./scripts/morning-mode.sh"
echo ""
