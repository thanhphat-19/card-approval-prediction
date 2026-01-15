#!/bin/bash
# Monday Startup - Resume after weekend shutdown
# Brings everything back online for GKE Standard cluster

set -e

echo "💼 =============================================="
echo "   Monday Startup: Back to Work!"
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

# VMs to start
JENKINS_VM="jenkins-server"
SONARQUBE_VM="sonarqube-server"

# Replica counts to restore
declare -A DEPLOYMENT_REPLICAS=(
    ["card-approval:card-approval-api"]=1
    ["card-approval:card-approval-postgres"]=1
    ["card-approval:card-approval-redis"]=1
    ["card-approval-training:card-approval-training-mlflow"]=1
    ["card-approval-training:card-approval-training-postgres"]=1
    ["monitoring:prometheus-grafana"]=1
    ["monitoring:prometheus-kube-prometheus-operator"]=1
    ["monitoring:prometheus-kube-state-metrics"]=1
    ["monitoring:prometheus-loki-gateway"]=1
)

declare -A STATEFULSET_REPLICAS=(
    ["monitoring:prometheus-loki"]=1
    ["monitoring:prometheus-prometheus-kube-prometheus-prometheus"]=1
)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# SCRIPT DIR
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "This will:"
echo "  1. Start Jenkins & SonarQube VMs"
echo "  2. Connect to GKE cluster"
echo "  3. Scale all deployments back up"
echo ""
echo "⏱️  Estimated time: 3-5 minutes"
echo ""

read -p "Start up for Monday? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# ============================================
# STEP 1: Start VMs
# ============================================
echo ""
echo -e "${BLUE}Step 1: Starting VMs...${NC}"
echo "------------------------"

start_vm() {
    local VM_NAME=$1
    local VM_ZONE=$2

    if gcloud compute instances describe ${VM_NAME} --zone=${VM_ZONE} --project=${PROJECT_ID} &>/dev/null; then
        STATUS=$(gcloud compute instances describe ${VM_NAME} --zone=${VM_ZONE} --project=${PROJECT_ID} --format='value(status)')

        if [ "$STATUS" = "TERMINATED" ]; then
            echo "  🚀 Starting ${VM_NAME}..."
            gcloud compute instances start ${VM_NAME} \
                --zone=${VM_ZONE} \
                --project=${PROJECT_ID} \
                --quiet
            echo -e "  ${GREEN}✓${NC} ${VM_NAME} started"
        else
            echo "  ${VM_NAME} is already running"
        fi
    else
        echo "  ${VM_NAME} not found, skipping..."
    fi
}

start_vm "$JENKINS_VM" "$ZONE"
start_vm "$SONARQUBE_VM" "$ZONE"

# Wait for VMs to boot
echo "  Waiting for VMs to boot (20s)..."
sleep 20

# ============================================
# STEP 2: Connect to GKE cluster
# ============================================
echo ""
echo -e "${BLUE}Step 2: Connecting to GKE cluster...${NC}"
echo "--------------------------------------"

gcloud container clusters get-credentials ${CLUSTER_NAME} \
    --zone ${ZONE} \
    --project ${PROJECT_ID}

echo -e "${GREEN}✓${NC} Connected to cluster"

# Verify node is ready
echo "  Checking node status..."
kubectl wait --for=condition=Ready nodes --all --timeout=120s 2>/dev/null || true
kubectl get nodes

# ============================================
# STEP 3: Scale up Deployments
# ============================================
echo ""
echo -e "${BLUE}Step 3: Scaling up deployments...${NC}"
echo "-----------------------------------"

for key in "${!DEPLOYMENT_REPLICAS[@]}"; do
    NAMESPACE="${key%%:*}"
    DEPLOYMENT="${key##*:}"
    REPLICAS="${DEPLOYMENT_REPLICAS[$key]}"

    if kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} &>/dev/null; then
        kubectl scale deployment ${DEPLOYMENT} -n ${NAMESPACE} --replicas=${REPLICAS}
        echo -e "  ${GREEN}✓${NC} ${NAMESPACE}/${DEPLOYMENT} → ${REPLICAS} replicas"
    else
        echo -e "  ${YELLOW}⏭${NC} ${NAMESPACE}/${DEPLOYMENT} not found, skipping..."
    fi
done

# ============================================
# STEP 4: Scale up StatefulSets
# ============================================
echo ""
echo -e "${BLUE}Step 4: Scaling up statefulsets...${NC}"
echo "------------------------------------"

for key in "${!STATEFULSET_REPLICAS[@]}"; do
    NAMESPACE="${key%%:*}"
    STATEFULSET="${key##*:}"
    REPLICAS="${STATEFULSET_REPLICAS[$key]}"

    if kubectl get statefulset ${STATEFULSET} -n ${NAMESPACE} &>/dev/null; then
        kubectl scale statefulset ${STATEFULSET} -n ${NAMESPACE} --replicas=${REPLICAS}
        echo -e "  ${GREEN}✓${NC} ${NAMESPACE}/${STATEFULSET} → ${REPLICAS} replicas"
    else
        echo -e "  ${YELLOW}⏭${NC} ${NAMESPACE}/${STATEFULSET} not found, skipping..."
    fi
done

# ============================================
# STEP 5: Wait for pods to be ready
# ============================================
echo ""
echo -e "${BLUE}Step 5: Waiting for pods to be ready...${NC}"
echo "-----------------------------------------"

echo "  Waiting 30s for pods to start..."
sleep 30

# ============================================
# SUMMARY
# ============================================
echo ""
echo "================================================"
echo -e "${GREEN}✅ Monday Startup Complete!${NC}"
echo "================================================"
echo ""

echo "📊 Cluster Status:"
kubectl get nodes
echo ""

echo "🚀 Pod Status:"
echo ""
echo "Card Approval (card-approval):"
kubectl get pods -n card-approval 2>/dev/null || echo "  Not deployed"
echo ""
echo "MLflow Training (card-approval-training):"
kubectl get pods -n card-approval-training 2>/dev/null || echo "  Not deployed"
echo ""
echo "Monitoring (monitoring):"
kubectl get pods -n monitoring 2>/dev/null | head -10 || echo "  Not deployed"
echo ""

# Get VM URLs
echo "🔗 Service URLs:"
if gcloud compute instances describe ${JENKINS_VM} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null; then
    JENKINS_IP=$(gcloud compute instances describe ${JENKINS_VM} \
        --zone=${ZONE} --project=${PROJECT_ID} \
        --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)
    echo "  • Jenkins:   http://${JENKINS_IP}:8080"
fi

if gcloud compute instances describe ${SONARQUBE_VM} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null; then
    SONAR_IP=$(gcloud compute instances describe ${SONARQUBE_VM} \
        --zone=${ZONE} --project=${PROJECT_ID} \
        --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)
    echo "  • SonarQube: http://${SONAR_IP}:9000"
fi

echo ""
echo "🔗 Port-Forward Commands:"
echo "  • API:      kubectl port-forward svc/card-approval-api 8000:8000 -n card-approval"
echo "  • MLflow:   kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training"
echo "  • Grafana:  kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring"
echo ""
echo "🏖️ To shutdown:"
echo "  ./scripts/weekend-shutdown.sh"
echo ""
echo "☕ Ready to code! Have a productive day!"
echo ""
