#!/bin/bash
# Weekend Shutdown - Stop everything to save maximum cost
# Run on Friday evening, saves ~$200/weekend

set -e

echo "🏖️ =============================================="
echo "   Weekend Shutdown: Maximum Cost Saving"
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
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  WARNING: This will stop ALL resources${NC}"
echo ""
echo "This will:"
echo "  1. Scale all deployments to 0 replicas"
echo "  2. Scale cluster to 0 nodes"
echo "  3. Stop Jenkins VM"
echo ""
echo "💾 Data Preservation:"
echo "  • Persistent disks: ✓ Kept (your data is safe)"
echo "  • Deployments: ✓ Kept (configuration preserved)"
echo "  • Container images: ✓ Kept"
echo ""
echo "💰 Weekend Savings:"
echo "  • Stop paying for compute nodes"
echo "  • Only pay for control plane + storage"
echo "  • Save approximately \$30-40 per weekend"
echo ""

read -p "Shutdown for the weekend? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Scale all deployments to 0
echo ""
echo "Step 1: Scaling all deployments to 0..."
echo "----------------------------------------"

for namespace in card-approval recsys-training monitoring; do
    if kubectl get namespace ${namespace} &>/dev/null; then
        echo "  Scaling ${namespace}..."
        kubectl scale deployment --all --replicas=0 -n ${namespace} 2>/dev/null || true
        kubectl scale statefulset --all --replicas=0 -n ${namespace} 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓${NC} All deployments scaled to 0"

# Step 2: Scale cluster to 0 nodes
echo ""
echo "Step 2: Removing all cluster nodes..."
echo "---------------------------------------"
echo "  This will take a few minutes..."
echo ""

gcloud container clusters resize ${CLUSTER_NAME} \
    --num-nodes=0 \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --quiet

echo -e "${GREEN}✓${NC} All nodes removed"

# Step 3: Stop Jenkins VM
echo ""
echo "Step 3: Stopping Jenkins VM..."
echo "-------------------------------"

if gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} &>/dev/null; then
    gcloud compute instances stop ${JENKINS_VM} \
        --zone=${JENKINS_ZONE} \
        --project=${PROJECT_ID} \
        --quiet
    echo -e "${GREEN}✓${NC} Jenkins VM stopped"
else
    echo "  Jenkins VM not found, skipping..."
fi

# Summary
echo ""
echo "================================================"
echo -e "${GREEN}✅ Weekend Shutdown Complete!${NC}"
echo "================================================"
echo ""
echo "💰 Cost While Shutdown:"
echo "  • GKE Control Plane: ~\$2.50/day"
echo "  • Persistent Storage: ~\$0.33/day"
echo "  • Jenkins VM (stopped): \$0.00/day"
echo "  • Total: ~\$2.83/day (was \$7.67/day)"
echo "  • Weekend Savings: ~\$34 saved"
echo ""
echo "📅 Current Status:"
echo "  • Cluster nodes: 0 (no compute charges)"
echo "  • Jenkins: Stopped"
echo "  • Data: Preserved ✓"
echo ""
echo "🌅 To resume Monday morning:"
echo "  ./scripts/monday-startup.sh"
echo ""
echo "😴 Enjoy your weekend!"
echo ""
