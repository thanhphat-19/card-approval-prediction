#!/bin/bash

# Run SonarQube Analysis for Card Approval Project

set -e

echo "=================================================="
echo "Running Code Quality Analysis with SonarQube"
echo "=================================================="

# Configuration
SONAR_HOST_URL=${SONAR_HOST_URL:-"http://localhost:9000"}
SONAR_PROJECT_KEY="card-approval-prediction"
SONAR_TOKEN=${SONAR_TOKEN:-""}  # Will be set after SonarQube setup

# Check if sonar-scanner is installed
if ! command -v sonar-scanner &> /dev/null; then
    echo "sonar-scanner is not installed. Installing..."

    # Download and install sonar-scanner
    SONAR_SCANNER_VERSION="5.0.1.3006"
    wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip
    unzip -q sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip
    sudo mv sonar-scanner-${SONAR_SCANNER_VERSION}-linux /opt/sonar-scanner
    sudo ln -sf /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner
    rm sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip
fi

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q pytest pytest-cov coverage pylint flake8

# Run tests with coverage
echo "Running tests with coverage..."
python -m pytest tests/ \
    --cov=app \
    --cov=cap_model/src \
    --cov-report=xml:coverage.xml \
    --cov-report=term \
    --junitxml=test-results/pytest-report.xml || true

# Run pylint
echo "Running pylint analysis..."
python -m pylint app cap_model/src --output-format=parseable > pylint-report.txt || true

# Run flake8
echo "Running flake8 analysis..."
python -m flake8 app cap_model/src --output-file=flake8-report.txt || true

# Run SonarQube analysis
echo "Running SonarQube Scanner..."

if [ -z "$SONAR_TOKEN" ]; then
    echo "Warning: SONAR_TOKEN is not set. Running without authentication."
    sonar-scanner \
        -Dsonar.host.url="${SONAR_HOST_URL}" \
        -Dsonar.projectKey="${SONAR_PROJECT_KEY}"
else
    sonar-scanner \
        -Dsonar.host.url="${SONAR_HOST_URL}" \
        -Dsonar.projectKey="${SONAR_PROJECT_KEY}" \
        -Dsonar.login="${SONAR_TOKEN}"
fi

echo ""
echo "=================================================="
echo "Code Quality Analysis Complete!"
echo "=================================================="
echo ""
echo "View results at: ${SONAR_HOST_URL}/dashboard?id=${SONAR_PROJECT_KEY}"
echo ""

# Deactivate virtual environment
deactivate
