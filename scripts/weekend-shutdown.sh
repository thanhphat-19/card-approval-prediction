#!/bin/bash
# Weekend Shutdown - Stop everything to save maximum cost
# Run on Friday evening or anytime to save money

set -e

echo "🏖️ =============================================="
echo "   Weekend Shutdown: Maximum Cost Saving"
echo "================================================"
echo ""

# Configuration - Update these values for your environment
CLUSTER_NAME="card-approval-prediction-mlops-gke"
REGION="us-east1"
ZONE="us-east1-b"
PROJECT_ID="product-recsys-mlops"

# VMs to stop (add more as needed)
JENKINS_VM="jenkins-server"
SONARQUBE_VM="sonarqube-server"  # Optional: if you have a separate SonarQube VM

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
echo "  1. Scale all deployments to 0 replicas"
echo "  2. GKE Autopilot auto-scales nodes to 0"
echo "  3. Stop Jenkins VM"
echo "  4. Stop SonarQube VM (if exists)"
echo ""
echo "💾 Data Preservation:"
echo "  • Persistent disks: ✓ Kept (your data is safe)"
echo "  • Helm releases: ✓ Kept (configuration preserved)"
echo "  • Container images: ✓ Kept in Artifact Registry"
echo "  • MLflow artifacts: ✓ Kept in GCS"
echo ""
echo "💰 Estimated Savings:"
echo "  • GKE nodes: ~\$5-10/day saved"
echo "  • Jenkins VM: ~\$1-2/day saved"
echo "  • SonarQube VM: ~\$1-2/day saved"
echo "  • Total: ~\$40-60 per weekend"
echo ""

read -p "Shutdown to save money? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Get cluster credentials
echo ""
echo -e "${BLUE}Step 1: Connecting to GKE cluster...${NC}"
echo "--------------------------------------"
gcloud container clusters get-credentials ${CLUSTER_NAME} \
    --zone ${ZONE} \
    --project ${PROJECT_ID} 2>/dev/null || {
    echo -e "${YELLOW}  Warning: Could not connect to cluster${NC}"
}

# Step 2: Scale all deployments to 0
echo ""
echo -e "${BLUE}Step 2: Scaling all deployments to 0...${NC}"
echo "----------------------------------------"

for namespace in "${NAMESPACES[@]}"; do
    if kubectl get namespace ${namespace} &>/dev/null; then
        echo "  📦 Scaling ${namespace}..."

        # Scale deployments
        DEPLOYMENTS=$(kubectl get deployment -n ${namespace} -o name 2>/dev/null)
        if [ -n "$DEPLOYMENTS" ]; then
            kubectl scale deployment --all --replicas=0 -n ${namespace} 2>/dev/null || true
            echo "    - Deployments scaled to 0"
        fi

        # Scale statefulsets
        STATEFULSETS=$(kubectl get statefulset -n ${namespace} -o name 2>/dev/null)
        if [ -n "$STATEFULSETS" ]; then
            kubectl scale statefulset --all --replicas=0 -n ${namespace} 2>/dev/null || true
            echo "    - StatefulSets scaled to 0"
        fi

        # Scale daemonsets (optional - some monitoring needs these)
        # kubectl patch daemonset --all -n ${namespace} -p '{"spec":{"template":{"spec":{"nodeSelector":{"non-existing":"true"}}}}}' 2>/dev/null || true
    else
        echo "  ⏭️  Namespace ${namespace} not found, skipping..."
    fi
done

echo -e "${GREEN}✓${NC} All deployments scaled to 0"

# Step 3: Wait for pods to terminate
echo ""
echo -e "${BLUE}Step 3: Waiting for pods to terminate...${NC}"
echo "-----------------------------------------"
sleep 10
for namespace in "${NAMESPACES[@]}"; do
    if kubectl get namespace ${namespace} &>/dev/null; then
        POD_COUNT=$(kubectl get pods -n ${namespace} --no-headers 2>/dev/null | wc -l)
        echo "  ${namespace}: ${POD_COUNT} pods remaining (will terminate shortly)"
    fi
done
echo -e "${GREEN}✓${NC} GKE Autopilot will auto-scale nodes to 0"

# Step 4: Stop VMs
echo ""
echo -e "${BLUE}Step 4: Stopping VMs...${NC}"
echo "-----------------------"

# Stop Jenkins
if gcloud compute instances describe ${JENKINS_VM} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null; then
    STATUS=$(gcloud compute instances describe ${JENKINS_VM} --zone=${ZONE} --project=${PROJECT_ID} --format='value(status)')
    if [ "$STATUS" = "RUNNING" ]; then
        echo "  🔧 Stopping Jenkins VM..."
        gcloud compute instances stop ${JENKINS_VM} \
            --zone=${ZONE} \
            --project=${PROJECT_ID} \
            --quiet
        echo -e "  ${GREEN}✓${NC} Jenkins VM stopped"
    else
        echo "  Jenkins VM already stopped"
    fi
else
    echo "  Jenkins VM not found, skipping..."
fi

# Stop SonarQube (if exists)
if gcloud compute instances describe ${SONARQUBE_VM} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null 2>&1; then
    STATUS=$(gcloud compute instances describe ${SONARQUBE_VM} --zone=${ZONE} --project=${PROJECT_ID} --format='value(status)')
    if [ "$STATUS" = "RUNNING" ]; then
        echo "  🔍 Stopping SonarQube VM..."
        gcloud compute instances stop ${SONARQUBE_VM} \
            --zone=${ZONE} \
            --project=${PROJECT_ID} \
            --quiet
        echo -e "  ${GREEN}✓${NC} SonarQube VM stopped"
    else
        echo "  SonarQube VM already stopped"
    fi
else
    echo "  SonarQube VM not found, skipping..."
fi

# Summary
echo ""
echo "================================================"
echo -e "${GREEN}✅ Shutdown Complete!${NC}"
echo "================================================"
echo ""
echo "💰 Cost While Shutdown:"
echo "  - GKE Autopilot (no pods): ~\$2.50/day (control plane only)"
echo "  - Persistent Storage: ~\$0.50/day"
echo "  - VMs (stopped): \$0.00/day"
echo "  - Artifact Registry: ~\$0.10/day"
echo "  - Total: ~\$3/day (vs ~\$15-20/day running)"
echo ""
echo "📊 Current Status:"
kubectl get nodes 2>/dev/null || echo "  Cluster scaling down..."
echo ""
echo "🌅 To resume:"
echo "  ./scripts/monday-startup.sh"
echo ""
echo "😴 Enjoy your time off!"
echo ""
