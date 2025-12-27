#!/bin/bash

# Setup GitHub Webhook for Jenkins CI/CD
# Usage: ./setup-github-webhook.sh

set -e

echo "=================================================="
echo "Setting up GitHub Webhook for Jenkins"
echo "=================================================="

# Configuration
GITHUB_REPO_OWNER="yourusername"  # Change this
GITHUB_REPO_NAME="card-approval-prediction"
GITHUB_TOKEN=""  # Add your GitHub personal access token
JENKINS_URL=""  # Will be set after Jenkins deployment
WEBHOOK_SECRET="your-webhook-secret"  # Change this

# Check if required variables are set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN is not set"
    echo "Please create a GitHub personal access token with 'admin:repo_hook' permission"
    echo "Visit: https://github.com/settings/tokens"
    exit 1
fi

# Get Jenkins URL
if [ -z "$JENKINS_URL" ]; then
    echo "Getting Jenkins server IP..."
    JENKINS_IP=$(gcloud compute instances describe jenkins-server \
        --zone=us-east1-b \
        --project=product-recsys-mlops \
        --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null || echo "")

    if [ -z "$JENKINS_IP" ]; then
        echo "Error: Could not find Jenkins server. Please deploy Jenkins first."
        exit 1
    fi

    JENKINS_URL="http://${JENKINS_IP}:8080"
fi

echo "Jenkins URL: ${JENKINS_URL}"

# Create webhook payload
WEBHOOK_PAYLOAD=$(cat <<EOF
{
  "name": "web",
  "active": true,
  "events": [
    "push",
    "pull_request",
    "issues"
  ],
  "config": {
    "url": "${JENKINS_URL}/github-webhook/",
    "content_type": "json",
    "insecure_ssl": "0",
    "secret": "${WEBHOOK_SECRET}"
  }
}
EOF
)

# Create webhook using GitHub API
echo "Creating GitHub webhook..."
curl -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "${WEBHOOK_PAYLOAD}" \
  "https://api.github.com/repos/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/hooks"

echo ""
echo "=================================================="
echo "GitHub Webhook Created Successfully!"
echo "=================================================="
echo ""
echo "Webhook URL: ${JENKINS_URL}/github-webhook/"
echo ""
echo "Next steps:"
echo "1. In Jenkins, create a new Multibranch Pipeline"
echo "2. Configure GitHub as the source"
echo "3. Add GitHub credentials"
echo "4. Set 'Jenkinsfile' as the build configuration"
echo ""
echo "Jenkins Configuration:"
echo "----------------------"
echo "1. Go to: ${JENKINS_URL}"
echo "2. New Item > Enter name 'card-approval-pipeline'"
echo "3. Select 'Multibranch Pipeline' > OK"
echo "4. Branch Sources > Add Source > GitHub"
echo "5. Credentials > Add > Jenkins"
echo "   - Kind: Username with password"
echo "   - Username: ${GITHUB_REPO_OWNER}"
echo "   - Password: Your GitHub Token"
echo "6. Repository HTTPS URL: https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}"
echo "7. Build Configuration > Script Path: Jenkinsfile"
echo "8. Scan Multibranch Pipeline Triggers > Check 'Periodically if not otherwise run'"
echo "9. Save"
echo ""
