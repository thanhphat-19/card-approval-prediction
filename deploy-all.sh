#!/bin/bash

# Complete Deployment Script for Card Approval CI/CD Pipeline
# This script orchestrates the deployment of all components

set -e

echo "=================================================="
echo "Card Approval CI/CD Complete Deployment"
echo "=================================================="
echo ""

# Configuration
PROJECT_ID="product-recsys-mlops"
REGION="us-east1"
CLUSTER_NAME="mlops-cluster"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${GREEN}[Step $1]${NC} $2"
    echo "=================================================="
}

print_info() {
    echo -e "${YELLOW}[Info]${NC} $1"
}

# Check prerequisites
print_step "0" "Checking Prerequisites"

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    echo "Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Ansible
if ! command -v ansible &> /dev/null; then
    print_info "Ansible not found. Installing..."
    pip3 install --user ansible
fi

print_info "All prerequisites satisfied!"
echo ""

# Step 1: Deploy Application to GKE
print_step "1" "Deploying Application to GKE"
cd k8s

# Check if cluster exists
if gcloud container clusters describe ${CLUSTER_NAME} --region ${REGION} &>/dev/null; then
    print_info "Cluster ${CLUSTER_NAME} exists"
else
    print_info "Creating GKE cluster..."
    gcloud container clusters create ${CLUSTER_NAME} \
        --region ${REGION} \
        --num-nodes 3 \
        --machine-type n1-standard-2 \
        --disk-size 50 \
        --enable-autoscaling \
        --min-nodes 2 \
        --max-nodes 5
fi

# Deploy application
print_info "Deploying application to Kubernetes..."
./deploy.sh

# Verify deployment
print_info "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/card-approval-api -n card-approval || true

cd ..
echo ""

# Step 2: Deploy Monitoring Stack
print_step "2" "Deploying Monitoring Stack"
cd k8s/monitoring

print_info "Deploying Prometheus and Grafana..."
./deploy-monitoring.sh

# Verify monitoring
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring || true
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n monitoring || true

cd ../..
echo ""

# Step 3: Deploy Jenkins with Ansible
print_step "3" "Deploying Jenkins with Ansible"
cd ansible

print_info "Installing Ansible dependencies..."
pip3 install -q -r requirements.txt

print_info "Running Ansible playbooks..."
ansible-playbook site.yml

# Get Jenkins IP
JENKINS_IP=$(gcloud compute instances describe jenkins-server \
    --zone=us-east1-b \
    --project=${PROJECT_ID} \
    --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null || echo "")

cd ..
echo ""

# Step 4: Setup GitHub Webhook
print_step "4" "Setting up GitHub Webhook"

if [ -n "$JENKINS_IP" ]; then
    print_info "Jenkins server found at: ${JENKINS_IP}"
    print_info "Please configure GitHub webhook manually:"
    echo "  1. Go to your GitHub repository settings"
    echo "  2. Add webhook URL: http://${JENKINS_IP}:8080/github-webhook/"
    echo "  3. Set content type to: application/json"
    echo "  4. Select events: Push, Pull Request"
else
    print_info "Jenkins server not found. Please check deployment."
fi

echo ""

# Step 5: Summary
print_step "5" "Deployment Summary"

echo "✅ Components Deployed:"
echo "----------------------"
echo ""

# Application status
echo "📦 Application:"
kubectl get pods -n card-approval --no-headers | while read line; do
    echo "   - $line"
done
echo ""

# Monitoring status
echo "📊 Monitoring:"
kubectl get pods -n monitoring --no-headers | while read line; do
    echo "   - $line"
done
echo ""

# Jenkins status
if [ -n "$JENKINS_IP" ]; then
    echo "🔧 CI/CD:"
    echo "   - Jenkins: http://${JENKINS_IP}:8080"
    echo "   - SonarQube: http://${JENKINS_IP}:9000"
fi
echo ""

# Access Information
echo "=================================================="
echo "📌 Access Information:"
echo "=================================================="
echo ""

echo "1️⃣ Application API:"
echo "   kubectl port-forward -n card-approval svc/card-approval-api 8000:80"
echo "   URL: http://localhost:8000"
echo ""

echo "2️⃣ Prometheus:"
echo "   kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "   URL: http://localhost:9090"
echo ""

echo "3️⃣ Grafana:"
echo "   kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "   URL: http://localhost:3000"
echo "   Credentials: admin/admin123"
echo ""

if [ -n "$JENKINS_IP" ]; then
    echo "4️⃣ Jenkins:"
    echo "   URL: http://${JENKINS_IP}:8080"
    echo "   Initial password: Check Ansible output or run:"
    echo "   gcloud compute ssh jenkins-server --zone=us-east1-b --command='sudo cat /var/jenkins_home/secrets/initialAdminPassword'"
    echo ""

    echo "5️⃣ SonarQube:"
    echo "   URL: http://${JENKINS_IP}:9000"
    echo "   Default: admin/admin"
fi
echo ""

echo "=================================================="
echo "🎉 Deployment Complete!"
echo "=================================================="
echo ""

echo "Next Steps:"
echo "-----------"
echo "1. Configure Jenkins with credentials"
echo "2. Create Jenkins pipeline from GitHub repo"
echo "3. Setup GitHub webhook"
echo "4. Make a test commit to trigger the pipeline"
echo "5. Monitor the deployment in Grafana"
echo ""

echo "For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo ""
