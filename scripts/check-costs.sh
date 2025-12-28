#!/bin/bash
# Check Current GCP Costs
# Shows what's currently running and approximate costs

set -e

echo "💰 =============================================="
echo "   GCP Cost Checker"
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
BLUE='\033[0;34m'
NC='\033[0m'

# Initialize cost counters
TOTAL_COST=0
DAILY_COST=0
MONTHLY_COST=0

echo "🔍 Checking GCP Resources..."
echo ""

# Check GKE Cluster
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 GKE Cluster: ${CLUSTER_NAME}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if gcloud container clusters describe ${CLUSTER_NAME} --region=${REGION} &>/dev/null; then
    # Get node count
    NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l || echo "0")

    echo -e "Status: ${GREEN}Running${NC}"
    echo "Nodes: ${NODE_COUNT}"

    # Cost calculation
    CONTROL_PLANE_COST=2.50  # $75/month ≈ $2.50/day
    NODE_COST_PER_DAY=1.67   # $50/month ≈ $1.67/day per node
    NODE_TOTAL=$( echo "$NODE_COUNT * $NODE_COST_PER_DAY" | bc )
    GKE_DAILY=$( echo "$CONTROL_PLANE_COST + $NODE_TOTAL" | bc )

    echo "Costs:"
    echo "  • Control Plane: \$2.50/day"
    echo "  • Nodes (${NODE_COUNT}):     \$$NODE_TOTAL/day"
    echo "  • Daily Total:  \$$GKE_DAILY/day"

    DAILY_COST=$( echo "$DAILY_COST + $GKE_DAILY" | bc )

    # Show pods
    echo ""
    echo "Running Pods:"
    kubectl get pods --all-namespaces --field-selector=status.phase=Running 2>/dev/null | grep -v "NAME" | wc -l | xargs echo "  Active pods:"
else
    echo -e "Status: ${RED}Not Found${NC}"
    echo "Cost: \$0.00/day"
fi

echo ""

# Check Jenkins VM
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Jenkins VM: ${JENKINS_VM}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} &>/dev/null; then
    STATUS=$(gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} --format='value(status)')
    MACHINE_TYPE=$(gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} --format='value(machineType)' | awk -F'/' '{print $NF}')

    if [ "$STATUS" = "RUNNING" ]; then
        echo -e "Status: ${GREEN}Running${NC}"
        echo "Type: ${MACHINE_TYPE}"

        JENKINS_DAILY=1.67  # n2-standard-2 ≈ $50/month ≈ $1.67/day
        echo "Cost: \$$JENKINS_DAILY/day"

        DAILY_COST=$( echo "$DAILY_COST + $JENKINS_DAILY" | bc )
    else
        echo -e "Status: ${YELLOW}Stopped${NC}"
        echo "Type: ${MACHINE_TYPE}"
        echo "Cost: \$0.00/day (stopped)"
    fi
else
    echo -e "Status: ${RED}Not Found${NC}"
    echo "Cost: \$0.00/day"
fi

echo ""

# Check Persistent Disks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 Persistent Storage"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get PVC total size
if kubectl get pvc --all-namespaces &>/dev/null; then
    TOTAL_STORAGE=$(kubectl get pvc --all-namespaces -o jsonpath='{.items[*].spec.resources.requests.storage}' 2>/dev/null | tr ' ' '\n' | sed 's/Gi//g' | awk '{s+=$1} END {print s}')

    if [ -z "$TOTAL_STORAGE" ] || [ "$TOTAL_STORAGE" = "0" ]; then
        TOTAL_STORAGE=0
    fi

    echo "Total PVC Storage: ${TOTAL_STORAGE}Gi"

    # $0.10 per GB per month ≈ $0.0033/GB/day
    STORAGE_DAILY=$( echo "$TOTAL_STORAGE * 0.0033" | bc )
    echo "Cost: \$$STORAGE_DAILY/day"

    DAILY_COST=$( echo "$DAILY_COST + $STORAGE_DAILY" | bc )

    # List PVCs
    echo ""
    echo "Persistent Volume Claims:"
    kubectl get pvc --all-namespaces 2>/dev/null | grep -v "NAME" | awk '{printf "  • %s/%s: %s\n", $1, $2, $4}' || echo "  None"
else
    echo "No persistent storage found"
    echo "Cost: \$0.00/day"
fi

echo ""

# Check Load Balancers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚖️  Load Balancers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

LB_COUNT=$(kubectl get svc --all-namespaces --field-selector spec.type=LoadBalancer 2>/dev/null | grep -v "NAME" | wc -l || echo "0")

if [ "$LB_COUNT" -gt 0 ]; then
    echo "Active Load Balancers: ${LB_COUNT}"
    LB_DAILY=$( echo "$LB_COUNT * 0.67" | bc )  # ~$20/month = $0.67/day
    echo "Cost: \$$LB_DAILY/day"
    DAILY_COST=$( echo "$DAILY_COST + $LB_DAILY" | bc )

    echo ""
    kubectl get svc --all-namespaces --field-selector spec.type=LoadBalancer 2>/dev/null
else
    echo "No Load Balancers found"
    echo "Cost: \$0.00/day"
fi

echo ""

# Summary
MONTHLY_COST=$( echo "$DAILY_COST * 30" | bc )

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 COST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}Current Daily Cost:${NC}   \$$(printf "%.2f" $DAILY_COST)"
echo -e "${BLUE}Estimated Monthly:${NC}    \$$(printf "%.2f" $MONTHLY_COST)"
echo ""

# Recommendations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 RECOMMENDATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if cost is high
COST_CHECK=$( echo "$DAILY_COST > 5" | bc )

if [ "$COST_CHECK" -eq 1 ]; then
    if [ "$NODE_COUNT" -gt 1 ]; then
        echo -e "${YELLOW}💰 Cost optimization available:${NC}"
        echo ""
        echo "Currently not coding?"
        echo "  → Run: ./scripts/night-mode.sh"
        NIGHT_SAVINGS=$( echo "($NODE_COUNT - 1) * 1.67" | bc )
        echo "  → Save: \$$(printf "%.2f" $NIGHT_SAVINGS)/day"
        echo ""
    fi

    echo "Done for the week?"
    echo "  → Run: ./scripts/weekend-shutdown.sh"
    WEEKEND_SAVINGS=$( echo "$NODE_COUNT * 1.67" | bc )
    echo "  → Save: \$$(printf "%.2f" $WEEKEND_SAVINGS)/day"
    echo ""

    if gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} &>/dev/null; then
        STATUS=$(gcloud compute instances describe ${JENKINS_VM} --zone=${JENKINS_ZONE} --format='value(status)')
        if [ "$STATUS" = "RUNNING" ]; then
            echo "Not using CI/CD right now?"
            echo "  → Stop Jenkins: gcloud compute instances stop ${JENKINS_VM} --zone=${JENKINS_ZONE}"
            echo "  → Save: \$1.67/day"
            echo ""
        fi
    fi
else
    echo -e "${GREEN}✓ Costs are optimized!${NC}"
    echo ""
    if [ "$NODE_COUNT" -eq 0 ]; then
        echo "Ready to start development?"
        echo "  → Run: ./scripts/morning-mode.sh"
        echo ""
    fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔄 Refresh: Run this script anytime to check costs"
echo ""
