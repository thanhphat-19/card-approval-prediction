#!/bin/bash

# Deploy Jenkins using Ansible
# Usage: ./deploy_jenkins.sh

set -e

echo "=================================================="
echo "Deploying Jenkins with Ansible"
echo "=================================================="

# Check if ansible is installed
if ! command -v ansible &> /dev/null; then
    echo "Ansible is not installed. Installing..."
    pip3 install --user -r requirements.txt
fi

# Check if gcloud is configured
if ! gcloud config get-value project &> /dev/null; then
    echo "Please configure gcloud first:"
    echo "gcloud auth login"
    echo "gcloud config set project product-recsys-mlops"
    exit 1
fi

# Run the main playbook
echo "Starting deployment..."
ansible-playbook site.yml -v

echo ""
echo "=================================================="
echo "Jenkins deployment complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Access Jenkins at the URL shown above"
echo "2. Complete initial setup if needed"
echo "3. Configure GitHub webhook for CI/CD"
echo "4. Update credentials with actual values"
echo ""
