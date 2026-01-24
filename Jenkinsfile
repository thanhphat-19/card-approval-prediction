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
        // GCP Configuration - Set these in Jenkins credentials or here
        // =============================================================
        // To override: Manage Jenkins > Credentials > Add credentials
        // Or set as Jenkins environment variables
        PROJECT_ID    = credentials('gcp-project-id')    // Create a 'Secret text' credential
        ZONE          = "${env.GCP_ZONE ?: 'us-east1-b'}"
        REGION        = "${env.GCP_REGION ?: 'us-east1'}"

        // GKE Configuration
        GKE_CLUSTER   = "${env.GKE_CLUSTER_NAME ?: 'card-approval-prediction-mlops-gke'}"
        GKE_NAMESPACE = 'card-approval'

        // Docker Registry
        REGISTRY      = "${REGION}-docker.pkg.dev"
        REPOSITORY    = "${PROJECT_ID}/${env.DOCKER_REPO_NAME ?: 'card-approval-repo'}"
        IMAGE_NAME    = 'card-approval-api'
    }

    stages {

        /* =====================
           CHECKOUT
        ====================== */
        stage('Checkout') {
            steps {
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
                    echo "✅ Building branch: ${env.BRANCH_NAME}"

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
                  python:3.10-slim \
                  bash -c "
                    tar xf - &&
                    apt-get update && apt-get install -y git --no-install-recommends &&
                    pip install flake8 pylint black isort &&
                    export PYTHONPATH=/workspace &&
                    echo '=== Flake8 ===' &&
                    flake8 app cap_model || true &&
                    echo '=== Pylint ===' &&
                    pylint app cap_model --exit-zero &&
                    echo '=== Black ===' &&
                    black --check app cap_model || true &&
                    echo '=== Isort ===' &&
                    isort --check-only --skip-gitignore app cap_model || true
                  "
                '''
            }
        }

        /* =====================
           SONARQUBE ANALYSIS & QUALITY GATE (PR branches only)
        ====================== */
        stage('SonarQube Analysis') {
            when {
                not { branch 'main' }
            }
            steps {
                script {
                    withSonarQubeEnv('SonarQube') {
                        sh '''
                        # Run SonarQube scanner in Docker
                        # Uses sonar-project.properties for configuration
                        docker run --rm \
                          --user $(id -u):$(id -g) \
                          -e SONAR_HOST_URL="${SONAR_HOST_URL}" \
                          -e SONAR_TOKEN="${SONAR_AUTH_TOKEN}" \
                          -v "$(pwd):/usr/src" \
                          -w /usr/src \
                          sonarsource/sonar-scanner-cli \
                          -Dsonar.host.url="${SONAR_HOST_URL}" \
                          -Dsonar.token="${SONAR_AUTH_TOKEN}" \
                          -Dsonar.working.directory=/usr/src/.scannerwork

                        # Copy report-task.txt to workspace root for Jenkins plugin
                        cp .scannerwork/report-task.txt .
                        '''
                    }
                }
            }
        }

        /* =====================
           QUALITY GATE (PR branches only)
        ====================== */
        stage('Quality Gate') {
            when {
                not { branch 'main' }
            }
            steps {
                script {
                    withSonarQubeEnv('SonarQube') {
                        timeout(time: 5, unit: 'MINUTES') {
                            waitForQualityGate abortPipeline: true
                        }
                    }
                }
            }
        }

        /* =====================
           BUILD IMAGE (main branch only)
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

                sh '''
                docker run --rm \
                  -v /var/run/docker.sock:/var/run/docker.sock \
                  aquasec/trivy image \
                  --severity HIGH,CRITICAL \
                  --exit-code 0 \
                  ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
                '''
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
                    # Get access token from gcloud and use it for docker login
                    ACCESS_TOKEN=$(cat "$GCP_KEY" | docker run --rm -i \
                      google/cloud-sdk:slim \
                      bash -c "
                        cat > /tmp/gcp-key.json &&
                        gcloud auth activate-service-account --key-file=/tmp/gcp-key.json 2>/dev/null &&
                        gcloud auth print-access-token &&
                        rm -f /tmp/gcp-key.json
                      ")

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
                    sh '''
                    # Bundle GCP key and helm charts, then pipe into container
                    mkdir -p .tmp-deploy
                    cp "$GCP_KEY" .tmp-deploy/gcp-key.json
                    cp -r helm-charts .tmp-deploy/

                    tar cf - -C .tmp-deploy . | docker run --rm -i \
                      -e USE_GKE_GCLOUD_AUTH_PLUGIN=True \
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
                          --set api.image.tag=${IMAGE_TAG} \
                          --wait \
                          --atomic
                      "

                    rm -rf .tmp-deploy
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                try {
                    cleanWs()
                } catch (Exception e) {
                    echo "Workspace cleanup skipped: ${e.message}"
                }
            }
        }
        success {
            echo '✅ Pipeline completed successfully'
        }
        failure {
            echo '❌ Pipeline failed'
        }
    }
}
