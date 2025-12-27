#!/bin/bash

# Test Complete CI/CD Flow
# Usage: ./test-cicd-flow.sh

set -e

echo "=================================================="
echo "Testing Complete CI/CD Flow"
echo "=================================================="

# Configuration
PROJECT_ID="product-recsys-mlops"
REGION="us-east1"
CLUSTER_NAME="mlops-cluster"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Step 1: Verify GCP Configuration
echo ""
echo "Step 1: Verifying GCP Configuration..."
if gcloud config get-value project | grep -q ${PROJECT_ID}; then
    print_status "GCP project configured: ${PROJECT_ID}"
else
    print_error "GCP project not configured correctly"
    exit 1
fi

# Step 2: Check GKE Cluster
echo ""
echo "Step 2: Checking GKE Cluster..."
if gcloud container clusters describe ${CLUSTER_NAME} --region ${REGION} &>/dev/null; then
    print_status "GKE cluster '${CLUSTER_NAME}' exists"

    # Get cluster credentials
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region ${REGION}
    print_status "Kubectl configured for cluster"
else
    print_error "GKE cluster '${CLUSTER_NAME}' not found"
    exit 1
fi

# Step 3: Verify Kubernetes Deployments
echo ""
echo "Step 3: Verifying Kubernetes Deployments..."

# Check namespaces
for ns in card-approval monitoring; do
    if kubectl get namespace ${ns} &>/dev/null; then
        print_status "Namespace '${ns}' exists"
    else
        print_warning "Namespace '${ns}' not found. Creating..."
        kubectl create namespace ${ns}
    fi
done

# Step 4: Check Jenkins
echo ""
echo "Step 4: Checking Jenkins..."
JENKINS_IP=$(gcloud compute instances describe jenkins-server \
    --zone=us-east1-b \
    --project=${PROJECT_ID} \
    --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null || echo "")

if [ -n "$JENKINS_IP" ]; then
    print_status "Jenkins server found at: ${JENKINS_IP}"

    # Test Jenkins connectivity
    if curl -s -o /dev/null -w "%{http_code}" http://${JENKINS_IP}:8080 | grep -q "200\|403"; then
        print_status "Jenkins is accessible"
    else
        print_warning "Jenkins is not responding"
    fi
else
    print_warning "Jenkins server not found"
fi

# Step 5: Check SonarQube
echo ""
echo "Step 5: Checking SonarQube..."
if [ -n "$JENKINS_IP" ]; then
    if curl -s -o /dev/null -w "%{http_code}" http://${JENKINS_IP}:9000 | grep -q "200"; then
        print_status "SonarQube is accessible"
    else
        print_warning "SonarQube is not responding"
    fi
fi

# Step 6: Test Local Application
echo ""
echo "Step 6: Testing Local Application..."
if [ -f "docker-compose.yml" ]; then
    print_status "Docker Compose file found"

    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Docker containers are running"

        # Test health endpoint
        if curl -s http://localhost:8000/health | grep -q "status"; then
            print_status "API health check passed"
        else
            print_warning "API health check failed"
        fi
    else
        print_warning "Docker containers are not running"
        echo "  Run: docker-compose up -d"
    fi
else
    print_warning "Docker Compose file not found"
fi

# Step 7: Check Monitoring Stack
echo ""
echo "Step 7: Checking Monitoring Stack..."

# Check Prometheus
if kubectl get deployment prometheus -n monitoring &>/dev/null; then
    print_status "Prometheus is deployed"

    # Check if Prometheus is scraping metrics
    kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
    PF_PID=$!
    sleep 3

    if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus"; then
        print_status "Prometheus is healthy"
    else
        print_warning "Prometheus health check failed"
    fi

    kill $PF_PID 2>/dev/null || true
else
    print_warning "Prometheus not deployed"
fi

# Check Grafana
if kubectl get deployment grafana -n monitoring &>/dev/null; then
    print_status "Grafana is deployed"
else
    print_warning "Grafana not deployed"
fi

# Step 8: Verify Docker Registry
echo ""
echo "Step 8: Verifying Docker Registry..."
if gcloud auth configure-docker ${REGION}-docker.pkg.dev 2>/dev/null; then
    print_status "Docker registry configured"
else
    print_warning "Docker registry not configured"
fi

# Step 9: Test CI/CD Pipeline
echo ""
echo "Step 9: Testing CI/CD Pipeline..."
if [ -f "Jenkinsfile" ]; then
    print_status "Jenkinsfile exists"

    # Validate Jenkinsfile syntax (basic check)
    if grep -q "pipeline" Jenkinsfile && grep -q "stages" Jenkinsfile; then
        print_status "Jenkinsfile syntax appears valid"
    else
        print_warning "Jenkinsfile may have syntax issues"
    fi
else
    print_error "Jenkinsfile not found"
fi

# Step 10: Summary
echo ""
echo "=================================================="
echo "CI/CD Flow Test Summary"
echo "=================================================="
echo ""

# Count successes and warnings
SUCCESS_COUNT=$(echo -e "${GREEN}[✓]${NC}" | grep -c "✓" || echo 0)
WARNING_COUNT=$(echo -e "${YELLOW}[!]${NC}" | grep -c "!" || echo 0)
ERROR_COUNT=$(echo -e "${RED}[✗]${NC}" | grep -c "✗" || echo 0)

echo "Test Results:"
echo "  Successful: ${SUCCESS_COUNT}"
echo "  Warnings: ${WARNING_COUNT}"
echo "  Errors: ${ERROR_COUNT}"
echo ""

if [ ${ERROR_COUNT} -eq 0 ]; then
    print_status "CI/CD flow is ready!"
    echo ""
    echo "Next steps to trigger the pipeline:"
    echo "1. Make a code change"
    echo "2. Commit and push to GitHub"
    echo "3. The webhook will trigger Jenkins"
    echo "4. Monitor the pipeline in Jenkins UI"
    echo "5. Check deployment in GKE"
else
    print_error "CI/CD flow has errors. Please fix them before proceeding."
fi

echo ""
echo "Useful commands:"
echo "----------------"
echo "# Deploy to Kubernetes:"
echo "cd k8s && ./deploy.sh"
echo ""
echo "# Deploy monitoring:"
echo "cd k8s/monitoring && ./deploy-monitoring.sh"
echo ""
echo "# Deploy Jenkins:"
echo "cd ansible && ./deploy_jenkins.sh"
echo ""
echo "# Setup GitHub webhook:"
echo "./scripts/setup-github-webhook.sh"
echo ""
echo "# View application logs:"
echo "kubectl logs -f deployment/card-approval-api -n card-approval"
echo ""
echo "# Access services:"
echo "kubectl port-forward -n card-approval svc/card-approval-api 8000:80"
echo "kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo ""
