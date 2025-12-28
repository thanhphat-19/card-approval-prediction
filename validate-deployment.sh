#!/bin/bash

# Validate Complete CI/CD Deployment
# This script checks if all components are properly deployed and functioning

set -e

echo "=================================================="
echo "Validating CI/CD Deployment"
echo "=================================================="
echo ""

# Configuration
PROJECT_ID="product-recsys-mlops"
REGION="us-east1"
CLUSTER_NAME="mlops-cluster"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Validation functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN_COUNT++))
}

# 1. Check GCP Configuration
echo "1. GCP Configuration"
echo "--------------------"
if gcloud config get-value project | grep -q ${PROJECT_ID}; then
    check_pass "Project configured: ${PROJECT_ID}"
else
    check_fail "Project not configured correctly"
fi

if gcloud container clusters describe ${CLUSTER_NAME} --region ${REGION} &>/dev/null; then
    check_pass "GKE cluster exists: ${CLUSTER_NAME}"

    # Get credentials
    gcloud container clusters get-credentials ${CLUSTER_NAME} --region ${REGION} &>/dev/null
    check_pass "Kubectl configured"
else
    check_fail "GKE cluster not found"
fi
echo ""

# 2. Check Kubernetes Deployments
echo "2. Kubernetes Deployments"
echo "-------------------------"

# Check card-approval namespace
if kubectl get namespace card-approval &>/dev/null; then
    check_pass "Namespace 'card-approval' exists"

    # Check API deployment
    if kubectl get deployment card-approval-api -n card-approval &>/dev/null; then
        READY=$(kubectl get deployment card-approval-api -n card-approval -o jsonpath='{.status.readyReplicas}')
        DESIRED=$(kubectl get deployment card-approval-api -n card-approval -o jsonpath='{.spec.replicas}')
        if [ "$READY" == "$DESIRED" ] && [ "$READY" -gt 0 ]; then
            check_pass "API deployment ready: ${READY}/${DESIRED} replicas"
        else
            check_warn "API deployment not fully ready: ${READY:-0}/${DESIRED} replicas"
        fi
    else
        check_fail "API deployment not found"
    fi

    # Check services
    for svc in card-approval-api card-approval-postgres card-approval-redis; do
        if kubectl get svc $svc -n card-approval &>/dev/null; then
            check_pass "Service exists: $svc"
        else
            check_fail "Service not found: $svc"
        fi
    done
else
    check_fail "Namespace 'card-approval' not found"
fi
echo ""

# 3. Check Monitoring Stack
echo "3. Monitoring Stack"
echo "-------------------"

if kubectl get namespace monitoring &>/dev/null; then
    check_pass "Namespace 'monitoring' exists"

    # Check Prometheus
    if kubectl get deployment prometheus -n monitoring &>/dev/null; then
        READY=$(kubectl get deployment prometheus -n monitoring -o jsonpath='{.status.readyReplicas}')
        if [ "$READY" -gt 0 ]; then
            check_pass "Prometheus is running"
        else
            check_warn "Prometheus deployment not ready"
        fi
    else
        check_fail "Prometheus not deployed"
    fi

    # Check Grafana
    if kubectl get deployment grafana -n monitoring &>/dev/null; then
        READY=$(kubectl get deployment grafana -n monitoring -o jsonpath='{.status.readyReplicas}')
        if [ "$READY" -gt 0 ]; then
            check_pass "Grafana is running"
        else
            check_warn "Grafana deployment not ready"
        fi
    else
        check_fail "Grafana not deployed"
    fi
else
    check_fail "Namespace 'monitoring' not found"
fi
echo ""

# 4. Check Jenkins
echo "4. Jenkins CI/CD"
echo "----------------"

JENKINS_IP=$(gcloud compute instances describe jenkins-server \
    --zone=us-east1-b \
    --project=${PROJECT_ID} \
    --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null || echo "")

if [ -n "$JENKINS_IP" ]; then
    check_pass "Jenkins VM exists: ${JENKINS_IP}"

    # Check Jenkins connectivity
    if curl -s -o /dev/null -w "%{http_code}" http://${JENKINS_IP}:8080 --max-time 5 | grep -q "200\|403"; then
        check_pass "Jenkins is accessible"
    else
        check_warn "Jenkins not responding (might be initializing)"
    fi

    # Check SonarQube
    if curl -s -o /dev/null -w "%{http_code}" http://${JENKINS_IP}:9000 --max-time 5 | grep -q "200"; then
        check_pass "SonarQube is accessible"
    else
        check_warn "SonarQube not responding"
    fi
else
    check_warn "Jenkins VM not found"
fi
echo ""

# 5. Test API Endpoints
echo "5. API Endpoint Tests"
echo "---------------------"

# Start port-forward in background
kubectl port-forward -n card-approval svc/card-approval-api 8001:80 >/dev/null 2>&1 &
PF_PID=$!
sleep 3

# Test health endpoint
if curl -s http://localhost:8001/health 2>/dev/null | grep -q "status"; then
    check_pass "Health endpoint working"
else
    check_warn "Health endpoint not accessible"
fi

# Test metrics endpoint
if curl -s http://localhost:8001/metrics 2>/dev/null | grep -q "fastapi_requests_total"; then
    check_pass "Metrics endpoint working"
else
    check_warn "Metrics endpoint not accessible"
fi

# Test prediction endpoint
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/predict \
    -H "Content-Type: application/json" \
    -d @test-data.json 2>/dev/null || echo "")

if echo "$RESPONSE" | grep -q "prediction"; then
    check_pass "Prediction endpoint working"
else
    check_warn "Prediction endpoint not working (model might not be loaded)"
fi

# Kill port-forward
kill $PF_PID 2>/dev/null || true
echo ""

# 6. Check Docker Registry
echo "6. Docker Registry"
echo "------------------"

if gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet 2>/dev/null; then
    check_pass "Docker registry configured"
else
    check_warn "Docker registry not configured"
fi

# Check if repository exists
if gcloud artifacts repositories describe product-recsys-mlops-recsys \
    --location=${REGION} \
    --project=${PROJECT_ID} &>/dev/null; then
    check_pass "Artifact repository exists"
else
    check_warn "Artifact repository not found"
fi
echo ""

# 7. Check Required Files
echo "7. Required Files"
echo "-----------------"

FILES=(
    "Jenkinsfile"
    "Dockerfile"
    "docker-compose.yml"
    "sonar-project.properties"
    "k8s/deployment.yaml"
    "ansible/site.yml"
    "DEPLOYMENT_GUIDE.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "File exists: $file"
    else
        check_fail "File missing: $file"
    fi
done
echo ""

# Summary
echo "=================================================="
echo "Validation Summary"
echo "=================================================="
echo ""
echo -e "✓ Passed:  ${GREEN}${PASS_COUNT}${NC}"
echo -e "⚠ Warnings: ${YELLOW}${WARN_COUNT}${NC}"
echo -e "✗ Failed:  ${RED}${FAIL_COUNT}${NC}"
echo ""

if [ ${FAIL_COUNT} -eq 0 ]; then
    if [ ${WARN_COUNT} -eq 0 ]; then
        echo -e "${GREEN}🎉 All validations passed! Your CI/CD pipeline is ready!${NC}"
    else
        echo -e "${YELLOW}⚠ Deployment is functional but has some warnings to address.${NC}"
    fi
else
    echo -e "${RED}❌ Deployment has issues that need to be fixed.${NC}"
fi
echo ""

# Provide next steps based on results
if [ ${FAIL_COUNT} -gt 0 ] || [ ${WARN_COUNT} -gt 0 ]; then
    echo "Recommended Actions:"
    echo "-------------------"

    if ! kubectl get namespace card-approval &>/dev/null; then
        echo "• Deploy application: cd k8s && ./deploy.sh"
    fi

    if ! kubectl get namespace monitoring &>/dev/null; then
        echo "• Deploy monitoring: cd k8s/monitoring && ./deploy-monitoring.sh"
    fi

    if [ -z "$JENKINS_IP" ]; then
        echo "• Deploy Jenkins: cd ansible && ./deploy_jenkins.sh"
    fi

    echo ""
fi

echo "For detailed deployment instructions, see: DEPLOYMENT_GUIDE.md"
echo ""
