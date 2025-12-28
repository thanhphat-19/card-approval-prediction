pipeline {
    agent { label 'docker' }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timeout(time: 1, unit: 'HOURS')
    }

    environment {
        // GCP
        PROJECT_ID    = 'product-recsys-mlops'
        REGION        = 'us-east1'
        GKE_CLUSTER   = 'mlops-cluster'
        GKE_NAMESPACE = 'card-approval'

        // Docker
        REGISTRY   = "${REGION}-docker.pkg.dev"
        REPOSITORY = "${PROJECT_ID}/product-recsys-mlops-recsys"
        IMAGE_NAME = 'card-approval-api'

        // SonarQube
        SONAR_PROJECT_KEY = 'card-approval-prediction'
        // Note: Jenkins runs in Docker, volume mounts use host paths
        // The host has workspace at /workspace/card-approval-prediction
        DOCKER_WORKDIR = 'card-approval-prediction'
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
                }
            }
        }

        /* =====================
           TEST + LINT
        ====================== */
        stage('Code Quality') {
            parallel {

                stage('Unit Tests') {
                    steps {
                        sh '''
                        docker run --rm \
                          -v $WORKSPACE:/workspace \
                          -w /workspace/${DOCKER_WORKDIR} \
                          python:3.10-slim \
                          bash -c "
                            pip install --upgrade pip &&
                            pip install -r requirements.txt &&
                            pip install pytest pytest-cov &&
                            export PYTHONPATH=/workspace/${DOCKER_WORKDIR} &&
                            pytest tests \
                              --cov=app \
                              --cov=cap_model \
                              --cov-report=xml:coverage.xml \
                              --junitxml=test-results/pytest.xml
                          "
                        '''
                        junit "${DOCKER_WORKDIR}/test-results/*.xml"
                    }
                }

                stage('Linting') {
                    steps {
                        sh '''
                        docker run --rm \
                          -v $WORKSPACE:/workspace \
                          -w /workspace/${DOCKER_WORKDIR} \
                          python:3.10-slim \
                          bash -c "
                            pip install flake8 pylint black isort &&
                            export PYTHONPATH=/workspace/${DOCKER_WORKDIR} &&
                            flake8 app cap_model || true &&
                            pylint app cap_model || true &&
                            black --check app cap_model || true &&
                            isort --check-only app cap_model || true
                          "
                        '''
                    }
                }
            }
        }

        /* =====================
           SONARQUBE
        ====================== */
        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    changeRequest()
                }
            }
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                    docker run --rm \
                      -v $WORKSPACE:/usr/src \
                      -w /usr/src/${DOCKER_WORKDIR} \
                      sonarsource/sonar-scanner-cli \
                      sonar-scanner \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.sources=app,cap_model \
                        -Dsonar.tests=tests \
                        -Dsonar.python.coverage.reportPaths=coverage.xml \
                        -Dsonar.python.xunit.reportPath=test-results/*.xml
                    '''
                }
            }
        }

        stage('Quality Gate') {
            when { branch 'main' }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
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
                    gcloud auth activate-service-account --key-file=$GCP_KEY
                    gcloud auth configure-docker ${REGISTRY}

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
                    gcloud auth activate-service-account --key-file=$GCP_KEY
                    gcloud container clusters get-credentials ${GKE_CLUSTER} \
                      --region ${REGION} \
                      --project ${PROJECT_ID}

                    helm upgrade --install card-approval \
                      helm-charts/card-approval \
                      --namespace ${GKE_NAMESPACE} \
                      --create-namespace \
                      --set api.image.tag=${IMAGE_TAG} \
                      --wait \
                      --atomic
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo '✅ Pipeline completed successfully'
        }
        failure {
            echo '❌ Pipeline failed'
        }
    }
}
