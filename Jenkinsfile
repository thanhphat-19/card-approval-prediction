pipeline {
    agent { label 'docker' }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timeout(time: 1, unit: 'HOURS')
    }

    environment {
        // GCP Configuration
        PROJECT_ID   = 'product-recsys-mlops'
        REGION       = 'us-east1'
        GKE_CLUSTER  = 'mlops-cluster'
        GKE_NAMESPACE = 'card-approval'

        // Docker Registry
        REGISTRY   = "${REGION}-docker.pkg.dev"
        REPOSITORY = "${PROJECT_ID}/product-recsys-mlops-recsys"
        IMAGE_NAME = 'card-approval-api'
        IMAGE_TAG  = "${BUILD_NUMBER}-${GIT_COMMIT[0..7]}"

        // SonarQube
        SONAR_PROJECT_KEY = 'card-approval-prediction'

        // Paths
        DOCKERFILE_PATH = './Dockerfile'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.GIT_BRANCH = sh(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).trim()
                    echo "Branch: ${GIT_BRANCH}"
                    echo "Commit: ${GIT_COMMIT}"
                }
            }
        }

        stage('Code Quality Analysis') {
            parallel {

                stage('Unit Tests') {
                    steps {
                        sh '''
                            docker run --rm \
                              -v $WORKSPACE:/workspace \
                              -w /workspace \
                              python:3.10-slim \
                              bash -c "
                                pip install -r requirements.txt &&
                                pip install pytest pytest-cov &&
                                pytest tests/ \
                                  --cov=app \
                                  --cov=cap_model/src \
                                  --cov-report=xml:coverage.xml \
                                  --junitxml=test-results/pytest-report.xml
                              "
                        '''
                        junit 'test-results/*.xml'
                    }
                }

                stage('Linting') {
                    steps {
                        sh '''
                            docker run --rm \
                              -v $WORKSPACE:/workspace \
                              -w /workspace \
                              python:3.10-slim \
                              bash -c "
                                pip install flake8 pylint black isort &&
                                flake8 app cap_model/src || true &&
                                pylint app cap_model/src || true &&
                                black --check app cap_model/src || true &&
                                isort --check-only app cap_model/src || true
                              "
                        '''
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    changeRequest target: 'main'
                }
            }
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        docker run --rm \
                          -v $WORKSPACE:/usr/src \
                          -w /usr/src \
                          sonarsource/sonar-scanner-cli \
                          sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.sources=app,cap_model/src \
                            -Dsonar.tests=tests,cap_model/tests \
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

        stage('Build Docker Image') {
            when { branch 'main' }
            steps {
                sh """
                    docker build \
                      -t ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} \
                      -t ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest \
                      -f ${DOCKERFILE_PATH} .
                """

                sh """
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      aquasec/trivy image \
                      --severity HIGH,CRITICAL \
                      --exit-code 0 \
                      ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
                """
            }
        }

        stage('Push to Registry') {
            when { branch 'main' }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh """
                        gcloud auth activate-service-account --key-file=${GCP_KEY}
                        gcloud auth configure-docker ${REGISTRY}

                        docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Deploy to GKE') {
            when { branch 'main' }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh """
                        gcloud auth activate-service-account --key-file=${GCP_KEY}
                        gcloud container clusters get-credentials ${GKE_CLUSTER} \
                          --region ${REGION} \
                          --project ${PROJECT_ID}

                        helm upgrade --install card-approval ./helm-charts/card-approval \
                          --namespace ${GKE_NAMESPACE} \
                          --create-namespace \
                          --set api.image.tag=${IMAGE_TAG} \
                          --wait \
                          --atomic
                    """
                }
            }
        }

        stage('Smoke Tests') {
            when { branch 'main' }
            steps {
                sh '''
                    kubectl rollout status deploy/card-approval-api -n card-approval
                    kubectl get pods -n card-approval
                '''
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
