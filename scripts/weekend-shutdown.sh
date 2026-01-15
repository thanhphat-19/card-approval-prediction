#!/bin/bash
# Weekend Shutdown - Stop everything to save maximum cost
# Run on Friday evening or anytime to save money
# Works with GKE Standard cluster

set -e

echo "🏖️ =============================================="
echo "   Weekend Shutdown: Maximum Cost Saving"
echo "   (GKE Standard Mode)"
echo "================================================"
echo ""

# ============================================
# CONFIGURATION - Update these for your environment
# ============================================
CLUSTER_NAME="card-approval-prediction-mlops-gke"
ZONE="us-east1-b"
REGION="us-east1"
PROJECT_ID="product-recsys-mlops"

# VMs to stop
JENKINS_VM="jenkins-server"
SONARQUBE_VM="sonarqube-server"

# Namespaces to scale down
NAMESPACES=("card-approval" "card-approval-training" "monitoring")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  WARNING: This will stop ALL resources${NC}"
echo ""
echo "This will:"
echo "  1. Scale all deployments/statefulsets to 0 replicas"
echo "  2. Stop Jenkins VM"
echo "  3. Stop SonarQube VM"
echo ""
echo "💾 Data Preservation:"
echo "  • Persistent disks: ✓ Kept (your data is safe)"
echo "  • Helm releases: ✓ Kept (configuration preserved)"
echo "  • Container images: ✓ Kept in Artifact Registry"
echo "  • MLflow artifacts: ✓ Kept in GCS"
echo ""
echo "💰 Estimated Savings:"
echo "  • GKE Standard (idle node): ~\$3-5/day"
echo "  • Jenkins VM (stopped): ~\$1-2/day"
echo "  • SonarQube VM (stopped): ~\$1-2/day"
echo "  • Total: ~\$30-50 per weekend"
echo ""

read -p "Shutdown to save money? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# ============================================
# STEP 1: Connect to GKE cluster
# ============================================
echo ""
echo -e "${BLUE}Step 1: Connecting to GKE cluster...${NC}"
echo "--------------------------------------"

gcloud container clusters get-credentials ${CLUSTER_NAME} \
    --zone ${ZONE} \
    --project ${PROJECT_ID} 2>/dev/null || {
    echo -e "${YELLOW}  Warning: Could not connect to cluster${NC}"
}
echo -e "${GREEN}✓${NC} Connected to cluster"

# ============================================
# STEP 2: Scale all deployments to 0
# ============================================
echo ""
echo -e "${BLUE}Step 2: Scaling all deployments to 0...${NC}"
echo "----------------------------------------"

for namespace in "${NAMESPACES[@]}"; do
    if kubectl get namespace ${namespace} &>/dev/null; then
        echo "  📦 Namespace: ${namespace}"

        # Scale deployments
        DEPLOY_COUNT=$(kubectl get deployment -n ${namespace} --no-headers 2>/dev/null | wc -l)
        if [ "$DEPLOY_COUNT" -gt 0 ]; then
            kubectl scale deployment --all --replicas=0 -n ${namespace} 2>/dev/null || true
            echo -e "    ${GREEN}✓${NC} ${DEPLOY_COUNT} deployments → 0 replicas"
        fi

        # Scale statefulsets
        SS_COUNT=$(kubectl get statefulset -n ${namespace} --no-headers 2>/dev/null | wc -l)
        if [ "$SS_COUNT" -gt 0 ]; then
            kubectl scale statefulset --all --replicas=0 -n ${namespace} 2>/dev/null || true
            echo -e "    ${GREEN}✓${NC} ${SS_COUNT} statefulsets → 0 replicas"
        fi
    else
        echo -e "  ${YELLOW}⏭${NC} Namespace ${namespace} not found, skipping..."
    fi
done

echo ""
echo -e "${GREEN}✓${NC} All workloads scaled to 0"

# ============================================
# STEP 3: Wait for pods to terminate
# ============================================
echo ""
echo -e "${BLUE}Step 3: Waiting for pods to terminate...${NC}"
echo "-----------------------------------------"

echo "  Waiting 15s for graceful shutdown..."
sleep 15

for namespace in "${NAMESPACES[@]}"; do
    if kubectl get namespace ${namespace} &>/dev/null; then
        POD_COUNT=$(kubectl get pods -n ${namespace} --no-headers 2>/dev/null | wc -l)
        if [ "$POD_COUNT" -gt 0 ]; then
            echo "  ${namespace}: ${POD_COUNT} pods still terminating..."
        else
            echo -e "  ${namespace}: ${GREEN}All pods terminated${NC}"
        fi
    fi
done

# ============================================
# STEP 4: Stop VMs
# ============================================
echo ""
echo -e "${BLUE}Step 4: Stopping VMs...${NC}"
echo "-----------------------"

stop_vm() {
    local VM_NAME=$1
    local VM_ZONE=$2

    if gcloud compute instances describe ${VM_NAME} --zone=${VM_ZONE} --project=${PROJECT_ID} &>/dev/null 2>&1; then
        STATUS=$(gcloud compute instances describe ${VM_NAME} --zone=${VM_ZONE} --project=${PROJECT_ID} --format='value(status)')
        if [ "$STATUS" = "RUNNING" ]; then
            echo "  🛑 Stopping ${VM_NAME}..."
            gcloud compute instances stop ${VM_NAME} \
                --zone=${VM_ZONE} \
                --project=${PROJECT_ID} \
                --quiet
            echo -e "  ${GREEN}✓${NC} ${VM_NAME} stopped"
        else
            echo "  ${VM_NAME} already stopped"
        fi
    else
        echo "  ${VM_NAME} not found, skipping..."
    fi
}

stop_vm "$JENKINS_VM" "$ZONE"
stop_vm "$SONARQUBE_VM" "$ZONE"

# ============================================
# SUMMARY
# ============================================
echo ""
echo "================================================"
echo -e "${GREEN}✅ Shutdown Complete!${NC}"
echo "================================================"
echo ""

echo "💰 Cost While Shutdown (GKE Standard):"
echo "  • GKE control plane: ~\$2.40/day (fixed)"
echo "  • Idle node (e2-medium): ~\$0.80/day"
echo "  • Persistent Storage: ~\$0.50/day"
echo "  • VMs (stopped): \$0.00/day"
echo "  • Total: ~\$4/day (vs ~\$15-20/day running)"
echo ""

echo "📊 Final Status:"
echo ""
echo "Nodes:"
kubectl get nodes 2>/dev/null || echo "  Could not get nodes"
echo ""
echo "Pods remaining:"
for namespace in "${NAMESPACES[@]}"; do
    POD_COUNT=$(kubectl get pods -n ${namespace} --no-headers 2>/dev/null | wc -l)
    echo "  ${namespace}: ${POD_COUNT} pods"
done
echo ""

echo "🌅 To resume:"
echo "  ./scripts/monday-startup.sh"
echo ""
echo "😴 Enjoy your time off!"
echo ""
