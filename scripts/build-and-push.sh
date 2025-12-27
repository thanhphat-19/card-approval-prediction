#!/bin/bash
# Build and Push Docker Image to GCP Container Registry
# Run this BEFORE deploying with Helm

set -e

# Configuration
PROJECT_ID="product-recsys-mlops"
REGION="us-east1"
REPOSITORY="product-recsys-mlops-recsys"
IMAGE_NAME="card-approval-api"
IMAGE_TAG="${1:-latest}"  # Default to 'latest' or use first argument

FULL_IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🐳 =============================================="
echo "   Building and Pushing Docker Image"
echo "================================================"
echo ""
echo -e "${BLUE}Image:${NC} ${FULL_IMAGE_PATH}"
echo ""

# Step 1: Configure Docker authentication
echo "Step 1: Configuring Docker authentication..."
echo "---------------------------------------------"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
echo -e "${GREEN}✓${NC} Docker authenticated"
echo ""

# Step 2: Build Docker image
echo "Step 2: Building Docker image..."
echo "--------------------------------"
echo "This may take a few minutes..."
echo ""

docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

echo -e "${GREEN}✓${NC} Image built successfully"
echo ""

# Step 3: Tag for GCP
echo "Step 3: Tagging image for GCP..."
echo "----------------------------------"
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_PATH}
echo -e "${GREEN}✓${NC} Image tagged"
echo ""

# Step 4: Push to Container Registry
echo "Step 4: Pushing to Container Registry..."
echo "-----------------------------------------"
echo "This may take a few minutes..."
echo ""

docker push ${FULL_IMAGE_PATH}

echo -e "${GREEN}✓${NC} Image pushed successfully"
echo ""

# Also tag and push as 'latest' if using a version tag
if [ "${IMAGE_TAG}" != "latest" ]; then
    echo "Step 5: Also tagging as 'latest'..."
    echo "------------------------------------"
    LATEST_IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest"
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${LATEST_IMAGE_PATH}
    docker push ${LATEST_IMAGE_PATH}
    echo -e "${GREEN}✓${NC} Latest tag pushed"
    echo ""
fi

# Summary
echo "================================================"
echo -e "${GREEN}✅ Build and Push Complete!${NC}"
echo "================================================"
echo ""
echo "📦 Image Details:"
echo "  • Repository: ${REPOSITORY}"
echo "  • Image:      ${IMAGE_NAME}"
echo "  • Tag:        ${IMAGE_TAG}"
echo "  • Full path:  ${FULL_IMAGE_PATH}"
echo ""
echo "🔍 Verify image exists:"
echo "  gcloud artifacts docker images list ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}"
echo ""
echo "🚀 Now you can deploy:"
echo "  helm install card-approval ./helm-charts/card-approval \\"
echo "    --namespace card-approval \\"
echo "    --create-namespace \\"
echo "    --wait"
echo ""
