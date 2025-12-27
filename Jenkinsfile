pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timeout(time: 1, unit: 'HOURS')
    }

    environment {
        // GCP Configuration
        PROJECT_ID = 'product-recsys-mlops'
        REGION = 'us-east1'
        GKE_CLUSTER = 'mlops-cluster'
        GKE_NAMESPACE = 'card-approval'

        // Docker Registry
        REGISTRY = "${REGION}-docker.pkg.dev"
        REPOSITORY = "${PROJECT_ID}/product-recsys-mlops-recsys"
        IMAGE_NAME = 'card-approval-api'
        IMAGE_TAG = "${BUILD_NUMBER}-${GIT_COMMIT[0..7]}"

        // SonarQube
        SONAR_HOST_URL = 'http://localhost:9000'
        SONAR_PROJECT_KEY = 'card-approval-prediction'

        // Paths
        DOCKERFILE_PATH = './Dockerfile'
        K8S_MANIFESTS = './k8s'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.GIT_BRANCH = sh(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).trim()
                    echo "Building branch: ${GIT_BRANCH}"
                    echo "Commit: ${GIT_COMMIT}"
                }
            }
        }

        stage('Code Quality Analysis') {
            parallel {
                stage('Unit Tests') {
                    agent {
                        docker {
                            image 'python:3.10-slim'
                            args '-v ${WORKSPACE}:/workspace -w /workspace'
                        }
                    }
                    steps {
                        sh '''
                            pip install --no-cache-dir -q -r requirements.txt
                            pip install --no-cache-dir -q pytest pytest-cov coverage

                            # Run tests with coverage
                            python -m pytest tests/ \
                                --cov=app \
                                --cov=cap_model/src \
                                --cov-report=xml:coverage.xml \
                                --cov-report=html:htmlcov \
                                --junitxml=test-results/pytest-report.xml \
                                -v
                        '''

                        // Archive test results
                        junit 'test-results/*.xml'
                        publishHTML([
                            allowMissing: false,
                            alwaysLinkToLastBuild: true,
                            keepAll: true,
                            reportDir: 'htmlcov',
                            reportFiles: 'index.html',
                            reportName: 'Coverage Report'
                        ])
                    }
                }

                stage('Linting') {
                    agent {
                        docker {
                            image 'python:3.10-slim'
                            args '-v ${WORKSPACE}:/workspace -w /workspace'
                        }
                    }
                    steps {
                        sh '''
                            pip install --no-cache-dir -q pylint flake8 black isort

                            # Run linters
                            echo "Running flake8..."
                            flake8 app cap_model/src --output-file=flake8-report.txt || true

                            echo "Running pylint..."
                            pylint app cap_model/src --output-format=parseable > pylint-report.txt || true

                            echo "Checking black formatting..."
                            black --check app cap_model/src || true

                            echo "Checking import sorting..."
                            isort --check-only app cap_model/src || true
                        '''
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            agent {
                docker {
                    image 'sonarsource/sonar-scanner-cli:latest'
                    args '-v ${WORKSPACE}:/usr/src --network host'
                }
            }
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
                        sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.sources=app,cap_model/src \
                            -Dsonar.tests=tests,cap_model/tests \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.python.xunit.reportPath=test-results/*.xml \
                            -Dsonar.python.pylint.reportPaths=pylint-report.txt \
                            -Dsonar.python.flake8.reportPaths=flake8-report.txt
                    '''
                }
            }
        }

        stage('Quality Gate') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Building Docker image..."
                    sh """
                        docker build \
                            -t ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} \
                            -t ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest \
                            -f ${DOCKERFILE_PATH} .
                    """

                    // Scan image for vulnerabilities
                    sh """
                        echo "Scanning image for vulnerabilities..."
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy image \
                            --severity HIGH,CRITICAL \
                            --exit-code 0 \
                            ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                script {
                    withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                        sh """
                            # Authenticate with GCP
                            gcloud auth activate-service-account --key-file=${GCP_KEY}
                            gcloud auth configure-docker ${REGISTRY}

                            # Push images
                            docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
                            docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest

                            echo "Image pushed successfully!"
                            echo "Image: ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"
                        """
                    }
                }
            }
        }

        stage('Deploy to GKE') {
            when {
                branch 'main'
            }
            steps {
                script {
                    withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                        sh """
                            # Configure kubectl
                            gcloud auth activate-service-account --key-file=${GCP_KEY}
                            gcloud container clusters get-credentials ${GKE_CLUSTER} \
                                --region ${REGION} \
                                --project ${PROJECT_ID}

                            # Build Helm dependencies
                            cd helm-charts/card-approval
                            helm dependency build
                            cd ../..

                            # Deploy using Helm
                            helm upgrade --install card-approval ./helm-charts/card-approval \
                                --namespace ${GKE_NAMESPACE} \
                                --create-namespace \
                                --set api.image.tag=${IMAGE_TAG} \
                                --wait \
                                --timeout 10m \
                                --atomic

                            # Verify deployment
                            kubectl get pods -n ${GKE_NAMESPACE}
                            helm status card-approval -n ${GKE_NAMESPACE}
                        """
                    }
                }
            }
        }

        stage('Smoke Tests') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh """
                        # Get service endpoint
                        SERVICE_IP=\$(kubectl get svc card-approval-api -n ${GKE_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || echo "localhost")

                        # If no external IP, use port-forward
                        if [ "\${SERVICE_IP}" = "localhost" ]; then
                            kubectl port-forward -n ${GKE_NAMESPACE} svc/card-approval-api 8080:80 &
                            PF_PID=\$!
                            sleep 5
                            SERVICE_IP="localhost:8080"
                        fi

                        # Test health endpoint
                        echo "Testing health endpoint..."
                        curl -f http://\${SERVICE_IP}/health || exit 1

                        # Test prediction endpoint
                        echo "Testing prediction endpoint..."
                        curl -f -X POST http://\${SERVICE_IP}/api/v1/predict \
                            -H "Content-Type: application/json" \
                            -d '{
                                "ID": 5008804,
                                "CODE_GENDER": "M",
                                "FLAG_OWN_CAR": "Y",
                                "FLAG_OWN_REALTY": "Y",
                                "CNT_CHILDREN": 0,
                                "AMT_INCOME_TOTAL": 180000.0,
                                "NAME_INCOME_TYPE": "Working",
                                "NAME_EDUCATION_TYPE": "Higher education",
                                "NAME_FAMILY_STATUS": "Married",
                                "NAME_HOUSING_TYPE": "House / apartment",
                                "DAYS_BIRTH": -14000,
                                "DAYS_EMPLOYED": -2500,
                                "FLAG_MOBIL": 1,
                                "FLAG_WORK_PHONE": 0,
                                "FLAG_PHONE": 1,
                                "FLAG_EMAIL": 0,
                                "OCCUPATION_TYPE": "Managers",
                                "CNT_FAM_MEMBERS": 2.0
                            }' || exit 1

                        # Kill port-forward if used
                        if [ ! -z "\${PF_PID}" ]; then
                            kill \${PF_PID} || true
                        fi

                        echo "Smoke tests passed!"
                    """
                }
            }
        }
    }

    post {
        always {
            // Clean workspace
            cleanWs()

            // Clean Docker images
            sh """
                docker image prune -f || true
                docker container prune -f || true
            """
        }

        success {
            echo 'Pipeline completed successfully!'

            // Send notification (Slack/Email)
            // slackSend(color: 'good', message: "Build Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}")
        }

        failure {
            echo 'Pipeline failed!'

            // Send notification (Slack/Email)
            // slackSend(color: 'danger', message: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}")
        }
    }
}
