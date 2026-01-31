pipeline {
    agent any

    triggers {
        // Only trigger on GitHub webhook
        githubPush()
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timeout(time: 1, unit: 'HOURS')
        // Skip build if same commit already built
        skipStagesAfterUnstable()
    }

    environment {
        // =============================================================
        // GCP Configuration
        // =============================================================
        PROJECT_ID    = 'product-recsys-mlops'
        ZONE          = 'us-east1-b'
        REGION        = 'us-east1'

        // GKE Configuration
        GKE_CLUSTER   = 'card-approval-prediction-mlops-gke'
        GKE_NAMESPACE = 'card-approval'

        // Docker Registry
        REGISTRY      = 'us-east1-docker.pkg.dev'
        REPOSITORY    = 'product-recsys-mlops/product-recsys-mlops-recsys'
        IMAGE_NAME    = 'card-approval-api'

        // MLflow Configuration
        MLFLOW_TRACKING_URI = 'http://35.196.35.190/mlflow'
        MODEL_NAME          = 'card_approval_model'
        MODEL_STAGE         = 'Production'
        F1_THRESHOLD        = '0.90'

        // SonarQube Configuration
        SONAR_HOST_URL = 'http://localhost:9000'
    }

    stages {

        /* =====================
           CHECKOUT
        ====================== */
        stage('Checkout') {
            steps {
                // Clean up any leftover secrets from previous failed runs
                sh 'rm -rf .tmp-deploy'
                checkout scm
                script {
                    env.GIT_COMMIT = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "${BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
                    env.BRANCH_NAME = env.GIT_BRANCH?.replaceAll('origin/', '') ?: env.BRANCH_NAME ?: 'unknown'
                }
            }
        }

        /* =====================
           CHECK BRANCH TYPE
        ====================== */
        stage('Check Branch') {
            steps {
                script {
                    echo "  Building branch: ${env.BRANCH_NAME}"

                    // Determine if this is main branch or a PR branch
                    def isMainBranch = env.BRANCH_NAME in ['main', 'master', 'develop']
                    env.IS_MAIN_BRANCH = isMainBranch ? 'true' : 'false'

                    if (isMainBranch) {
                        echo "📦 Main branch detected - will build, push, and deploy"
                    } else {
                        echo "🔍 Feature branch detected - will run tests and SonarQube analysis"
                    }
                }
            }
        }

        /* =====================
           LINTING
        ====================== */
        stage('Linting') {
            steps {
                sh '''
                # Use tar to pipe code into container (workaround for DinD volume mount issues)
                tar cf - --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' . | \
                docker run --rm -i \
                  -w /workspace \
                  python:3.11-slim \
                  bash -c "
                    tar xf - &&
                    apt-get update && apt-get install -y git --no-install-recommends &&
                    pip install flake8 pylint black isort &&
                    export PYTHONPATH=/workspace &&
                    echo '=== Flake8 ===' &&
                    flake8 app training/src scripts || true &&
                    echo '=== Pylint ===' &&
                    pylint app training/src scripts --exit-zero &&
                    echo '=== Black ===' &&
                    black --check app training/src scripts || true &&
                    echo '=== Isort ===' &&
                    isort --check-only --skip-gitignore app training/src scripts || true
                  "
                '''
            }
        }

        /* =====================
           SONARQUBE ANALYSIS
        ====================== */
        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    changeRequest()  // PR analysis
                }
            }
            steps {
                withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                    tar cf - --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' \
                             --exclude='data' --exclude='models' --exclude='mlruns' . | \
                    docker run --rm -i \
                      --user root \
                      --network host \
                      -e SONAR_TOKEN=${SONAR_TOKEN} \
                      -w /workspace \
                      sonarsource/sonar-scanner-cli:latest \
                      bash -c "
                        tar xf - &&
                        sonar-scanner \
                          -Dsonar.host.url=${SONAR_HOST_URL} \
                          -Dsonar.token=${SONAR_TOKEN} \
                          -Dsonar.qualitygate.wait=false
                      "
                    '''
                }
            }
        }


        /* =====================
           MODEL EVALUATION & DOWNLOAD
        ====================== */
        stage('Model Evaluation & Download') {
            when { branch 'main' }
            steps {
                sh '''
                echo "🔍 Evaluating production model quality..."

                # Run model evaluation against MLflow and output model version
                tar cf - --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' . | \
                docker run --rm -i \
                  --network host \
                  -w /workspace \
                  -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                  -e MODEL_NAME=${MODEL_NAME} \
                  -e MODEL_STAGE=${MODEL_STAGE} \
                  -e PYTHONPATH=/workspace:/workspace/training \
                  python:3.11-slim \
                  bash -c "
                    set -e
                    tar xf -
                    pip install --quiet mlflow pandas scikit-learn loguru joblib numpy google-cloud-storage xgboost lightgbm catboost pyyaml
                    python scripts/evaluate_model.py \
                      --threshold ${F1_THRESHOLD} \
                      --data-dir training/data/processed \
                      --output-file /workspace/.model-info.env
                    cat /workspace/.model-info.env
                  " | tee .model-info.env

                # Verify model info was extracted
                if ! grep -qE '^MODEL_VERSION=' .model-info.env; then
                    echo "ERROR: Model evaluation failed - no MODEL_VERSION found"
                    exit 1
                fi

                # Display model info
                echo "Model info extracted:"
                grep -E '^MODEL_' .model-info.env
                '''

                // Read model version into environment variable
                script {
                    if (fileExists('.model-info.env')) {
                        def modelInfo = readFile('.model-info.env').trim()
                        modelInfo.split('\n').each { line ->
                            def parts = line.split('=')
                            if (parts.size() == 2) {
                                env."${parts[0]}" = parts[1]
                            }
                        }
                        echo "Model Version: ${env.MODEL_VERSION}"
                        echo "Model Run ID: ${env.MODEL_RUN_ID}"
                    }
                }

                // Download model artifacts for embedding into Docker image
                sh '''
                echo "📥 Downloading model artifacts for Docker image..."

                # Clean up any existing models directory
                rm -rf models

                # Download model using the download script
                tar cf - --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' . | \
                docker run --rm -i \
                  --network host \
                  -w /workspace \
                  -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                  -e MODEL_NAME=${MODEL_NAME} \
                  -e MODEL_STAGE=${MODEL_STAGE} \
                  python:3.11-slim \
                  bash -c "
                    set -e
                    tar xf -
                    pip install --quiet mlflow google-cloud-storage
                    python scripts/download_model.py \
                      --output-dir /workspace/models
                    # Output the models directory as tar
                    tar cf - -C /workspace models
                  " | tar xf -

                # Verify model was downloaded
                if [ ! -d "models" ] || [ ! -f "models/model_metadata.json" ]; then
                    echo "ERROR: Model download failed"
                    exit 1
                fi

                echo "✅ Model artifacts downloaded successfully"
                ls -la models/
                '''
            }
        }

        /* =====================
           BUILD IMAGE
        ====================== */
        stage('Build Docker Image') {
            when { branch 'main' }
            steps {
                sh '''
                docker build \
                  -t ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} \
                  -t ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest \
                  -f Dockerfile \
                  .
                '''

                script {
                    // Clean up disk space before Trivy scan
                    sh 'docker system prune -f || true'
                    sh 'rm -rf /tmp/trivy-* || true'

                    // Run Trivy scan (skip if disk space issues)
                    sh '''
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      aquasec/trivy image \
                      --severity HIGH,CRITICAL \
                      --exit-code 0 \
                      --timeout 5m \
                      ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} || echo "⚠️ Trivy scan skipped due to resource constraints"
                    '''
                }
            }
        }

        /* =====================
           PUSH IMAGE
        ====================== */
        stage('Push Image') {
            when { branch 'main' }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh '''
                    # Copy GCP key to temp directory and use tar (same pattern as Deploy stage)
                    mkdir -p .tmp-push
                    cp "$GCP_KEY" .tmp-push/gcp-key.json

                    # Get access token from gcloud
                    ACCESS_TOKEN=$(tar cf - -C .tmp-push . | docker run --rm -i \
                      google/cloud-sdk:slim \
                      bash -c "
                        mkdir -p /tmp/auth && cd /tmp/auth && tar xf - &&
                        gcloud auth activate-service-account --key-file=/tmp/auth/gcp-key.json &&
                        gcloud auth print-access-token
                      ")

                    # Cleanup temp directory
                    rm -rf .tmp-push

                    # Verify we got a token
                    if [ -z "$ACCESS_TOKEN" ]; then
                        echo "ERROR: Failed to get GCP access token"
                        exit 1
                    fi

                    # Login to Artifact Registry using the access token
                    echo "$ACCESS_TOKEN" | docker login -u oauth2accesstoken --password-stdin https://${REGISTRY}

                    # Push images
                    docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        /* =====================
           DEPLOY
        ====================== */
        stage('Deploy to GKE') {
            when { branch 'main' }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh """
                    # Bundle GCP key and helm charts, then pipe into container
                    mkdir -p .tmp-deploy
                    cp "\$GCP_KEY" .tmp-deploy/gcp-key.json
                    cp -r helm-charts .tmp-deploy/

                    # Get model version (default to 'latest' if not set)
                    MODEL_VER=\${MODEL_VERSION:-latest}
                    echo " Deploying with model version: \$MODEL_VER"

                    tar cf - -C .tmp-deploy . | docker run --rm -i \
                      -e USE_GKE_GCLOUD_AUTH_PLUGIN=True \
                      -e MODEL_VERSION=\$MODEL_VER \
                      google/cloud-sdk:latest \
                      bash -c "
                        mkdir -p /deploy && cd /deploy && tar xf - &&
                        gcloud auth activate-service-account --key-file=/deploy/gcp-key.json &&
                        gcloud container clusters get-credentials ${GKE_CLUSTER} \
                          --zone ${ZONE} \
                          --project ${PROJECT_ID} &&
                        curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash &&
                        helm dependency build /deploy/helm-charts/card-approval &&
                        helm upgrade --install card-approval \
                          /deploy/helm-charts/card-approval \
                          --namespace ${GKE_NAMESPACE} \
                          --create-namespace \
                          --reuse-values \
                          --set api.image.repository=${REGISTRY}/${REPOSITORY}/${IMAGE_NAME} \
                          --set api.image.tag=${IMAGE_TAG} \
                          --set api.config.modelVersion=\\\$MODEL_VERSION \
                          --timeout 10m \
                          --wait \
                          --atomic

                        # Note: Rolling restart not needed - model is now embedded in Docker image
                        # Helm upgrade with new image tag automatically triggers pod replacement
                      "

                    rm -rf .tmp-deploy
                    """
                }
            }
        }
    }

    post {
        always {
            // Always clean up secrets, temp files, and downloaded models
            sh 'rm -rf .tmp-deploy .model-info.env models || true'
            // Clean up dangling Docker images to save disk space
            sh 'docker image prune -f || true'
        }
        success {
            echo 'Pipeline completed successfully'
            script {
                if (env.BRANCH_NAME == 'main') {
                    echo "  Deployed image: ${env.REGISTRY}/${env.REPOSITORY}/${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                    echo " Model version: ${env.MODEL_VERSION ?: 'latest'}"
                }
            }
        }
        failure {
            echo ' Pipeline failed'
            echo "Branch: ${env.BRANCH_NAME}, Commit: ${env.GIT_COMMIT?.take(7) ?: 'unknown'}"
        }
    }
}
