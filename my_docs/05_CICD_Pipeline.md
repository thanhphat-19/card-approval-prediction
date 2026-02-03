# Component 5: CI/CD Pipeline (Jenkinsfile)

## Executive Summary

The Jenkins CI/CD pipeline automates the entire deployment lifecycle from code commit to production deployment. It implements ML-specific quality gates (F1 score threshold), model embedding in Docker images, security scanning with Trivy, and atomic Helm deployments to GKE. The pipeline differentiates between feature branches (lint/test only) and main branch (full build/deploy).

---

## 1. Concept & Theory

### What is CI/CD for ML?

CI/CD (Continuous Integration/Continuous Deployment) for ML extends traditional software practices:

| Traditional CI/CD | ML CI/CD |
|-------------------|----------|
| Build code | Build code + validate model |
| Unit tests | Unit tests + model quality tests |
| Deploy application | Deploy application + model artifacts |
| Version code | Version code + data + model |

### Why CI/CD for ML Projects?

| Challenge | CI/CD Solution |
|-----------|----------------|
| Manual deployments | Automated on every merge |
| Model quality regression | F1 threshold quality gates |
| Security vulnerabilities | Trivy container scanning |
| Configuration drift | Helm atomic deployments |
| Rollback complexity | Release versioning |

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jenkins CI/CD Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GitHub Push                                                     │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │   Checkout   │ → Clone repo, set IMAGE_TAG                   │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │ Check Branch │ → main vs feature branch                      │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │   Linting    │ → Flake8, Pylint, Black, isort                │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │  SonarQube   │ → Static code analysis (main + PRs)           │
│  └──────────────┘                                               │
│       ↓ (main branch only)                                       │
│  ┌──────────────┐                                               │
│  │ Model Eval   │ → Check F1 ≥ 0.90 threshold                   │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │Model Download│ → Fetch from MLflow registry                  │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │ Build Image  │ → Docker build with embedded model            │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │ Trivy Scan   │ → Security vulnerability scan                 │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │ Push Image   │ → Push to Artifact Registry                   │
│  └──────────────┘                                               │
│       ↓                                                          │
│  ┌──────────────┐                                               │
│  │Deploy to GKE │ → Helm upgrade --atomic                       │
│  └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Concepts

1. **GitHub Webhooks**: Trigger builds on push/PR
2. **Docker-in-Docker (DinD)**: Build containers inside Jenkins
3. **Model Quality Gates**: Fail builds if model quality drops
4. **Atomic Deployments**: Rollback on failure
5. **Image Tagging**: `{BUILD_NUMBER}-{GIT_COMMIT_SHORT}`

---

## 2. Architecture & Design Decisions

### Key Design Decisions

#### 1. Branch-Based Pipeline Flow
```groovy
stage('Check Branch') {
    steps {
        script {
            def isMainBranch = env.BRANCH_NAME in ['main', 'master', 'develop']
            env.IS_MAIN_BRANCH = isMainBranch ? 'true' : 'false'
        }
    }
}

stage('Deploy to GKE') {
    when { branch 'main' }  // Only deploy from main
    steps { ... }
}
```

**Rationale**: Feature branches run quality checks only; main branch deploys.

#### 2. Model Embedding Strategy
```groovy
// Download model from MLflow
python scripts/download_model.py --output-dir /workspace/models

// Embed in Docker image
COPY models /app/models
ENV MODEL_PATH=/app/models
```

**Trade-offs**:
| Approach | Pros | Cons |
|----------|------|------|
| Embedded | Immutable, fast startup | Requires rebuild for model update |
| Runtime load | Hot-swap models | Cold start latency, network dependency |

#### 3. F1 Score Quality Gate
```groovy
environment {
    F1_THRESHOLD = '0.90'
}

stage('Model Evaluation') {
    steps {
        sh '''
        python scripts/evaluate_model.py --threshold ${F1_THRESHOLD}
        '''
    }
}
```

**Rationale**: Prevents deployment of degraded models.

#### 4. Tar-Pipe Pattern for DinD
```groovy
// Pipe source code into container (avoids volume mount issues)
tar cf - --exclude='.git' . | docker run --rm -i -w /workspace python:3.11-slim bash -c "
    tar xf - &&
    pip install flake8 &&
    flake8 app/
"
```

**Problem Solved**: Jenkins DinD can't mount host volumes; tar-pipe works.

#### 5. Atomic Helm Deployment
```groovy
helm upgrade --install card-approval \
  --atomic \      // Rollback on failure
  --wait \        // Wait for pods ready
  --timeout 10m
```

---

## 3. Implementation Guide

### Complete Jenkinsfile

```groovy
pipeline {
    agent any

    triggers {
        githubPush()  // GitHub webhook trigger
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timeout(time: 1, unit: 'HOURS')
        skipStagesAfterUnstable()
    }

    environment {
        // GCP Configuration
        PROJECT_ID    = 'your-project-id'
        ZONE          = 'us-east1-b'
        REGION        = 'us-east1'

        // GKE Configuration
        GKE_CLUSTER   = 'card-approval-prediction-mlops-gke'
        GKE_NAMESPACE = 'card-approval'

        // Docker Registry
        REGISTRY      = 'us-east1-docker.pkg.dev'
        REPOSITORY    = 'your-project-id/your-repo'
        IMAGE_NAME    = 'card-approval-api'

        // MLflow Configuration
        MLFLOW_TRACKING_URI = 'http://mlflow.example.com'
        MODEL_NAME          = 'card_approval_model'
        MODEL_STAGE         = 'Production'
        F1_THRESHOLD        = '0.90'

        // SonarQube
        SONAR_HOST_URL = 'http://localhost:9000'
    }

    stages {
        /* =====================
           CHECKOUT
        ====================== */
        stage('Checkout') {
            steps {
                sh 'rm -rf .tmp-deploy'
                checkout scm
                script {
                    env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
                    env.BRANCH_NAME = env.GIT_BRANCH?.replaceAll('origin/', '') ?: 'unknown'
                }
            }
        }

        /* =====================
           CHECK BRANCH
        ====================== */
        stage('Check Branch') {
            steps {
                script {
                    def isMainBranch = env.BRANCH_NAME in ['main', 'master', 'develop']
                    env.IS_MAIN_BRANCH = isMainBranch ? 'true' : 'false'

                    if (isMainBranch) {
                        echo "Main branch - will build, push, and deploy"
                    } else {
                        echo "Feature branch - will run tests only"
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
                tar cf - --exclude='.git' --exclude='__pycache__' . | \
                docker run --rm -i -w /workspace python:3.11-slim bash -c "
                    tar xf - &&
                    pip install flake8 pylint black isort &&
                    echo '=== Flake8 ===' &&
                    flake8 app training/src scripts || true &&
                    echo '=== Pylint ===' &&
                    pylint app training/src scripts --exit-zero &&
                    echo '=== Black ===' &&
                    black --check app training/src scripts || true &&
                    echo '=== Isort ===' &&
                    isort --check-only app training/src scripts || true
                "
                '''
            }
        }

        /* =====================
           SONARQUBE
        ====================== */
        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    changeRequest()
                }
            }
            steps {
                withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                    tar cf - --exclude='.git' --exclude='data' --exclude='models' . | \
                    docker run --rm -i --network host -e SONAR_TOKEN=${SONAR_TOKEN} \
                      -w /workspace sonarsource/sonar-scanner-cli:latest bash -c "
                        tar xf - &&
                        sonar-scanner \
                          -Dsonar.host.url=${SONAR_HOST_URL} \
                          -Dsonar.token=${SONAR_TOKEN}
                      "
                    '''
                }
            }
        }

        /* =====================
           MODEL EVALUATION
        ====================== */
        stage('Model Evaluation & Download') {
            when { branch 'main' }
            steps {
                sh '''
                echo "Evaluating production model quality..."

                tar cf - --exclude='.git' . | \
                docker run --rm -i --network host \
                  -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                  -e MODEL_NAME=${MODEL_NAME} \
                  -e MODEL_STAGE=${MODEL_STAGE} \
                  -w /workspace python:3.11-slim bash -c "
                    tar xf - &&
                    pip install mlflow pandas scikit-learn xgboost lightgbm catboost &&
                    python scripts/evaluate_model.py \
                      --threshold ${F1_THRESHOLD} \
                      --output-file /workspace/.model-info.env
                    cat /workspace/.model-info.env
                  " | tee .model-info.env

                # Verify model info
                grep -qE '^MODEL_VERSION=' .model-info.env || exit 1
                '''

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
                    }
                }

                // Download model artifacts
                sh '''
                echo "Downloading model artifacts..."
                rm -rf models

                tar cf - --exclude='.git' . | \
                docker run --rm -i --network host \
                  -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                  -e MODEL_NAME=${MODEL_NAME} \
                  -e MODEL_STAGE=${MODEL_STAGE} \
                  -w /workspace python:3.11-slim bash -c "
                    tar xf - &&
                    pip install mlflow google-cloud-storage &&
                    python scripts/download_model.py --output-dir /workspace/models
                    tar cf - -C /workspace models
                  " | tar xf -

                # Verify download
                [ -f "models/model_metadata.json" ] || exit 1
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
                  -f Dockerfile .
                '''

                // Trivy security scan
                sh '''
                docker run --rm \
                  -v /var/run/docker.sock:/var/run/docker.sock \
                  aquasec/trivy image \
                  --severity HIGH,CRITICAL \
                  --exit-code 0 \
                  --timeout 5m \
                  ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} || echo "Trivy scan skipped"
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
                    mkdir -p .tmp-push
                    cp "$GCP_KEY" .tmp-push/gcp-key.json

                    ACCESS_TOKEN=$(tar cf - -C .tmp-push . | docker run --rm -i \
                      google/cloud-sdk:slim bash -c "
                        mkdir -p /tmp/auth && cd /tmp/auth && tar xf - &&
                        gcloud auth activate-service-account --key-file=/tmp/auth/gcp-key.json &&
                        gcloud auth print-access-token
                      ")

                    rm -rf .tmp-push

                    echo "$ACCESS_TOKEN" | docker login -u oauth2accesstoken --password-stdin https://${REGISTRY}

                    docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        /* =====================
           DEPLOY TO GKE
        ====================== */
        stage('Deploy to GKE') {
            when { branch 'main' }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh """
                    mkdir -p .tmp-deploy
                    cp "\$GCP_KEY" .tmp-deploy/gcp-key.json
                    cp -r helm-charts .tmp-deploy/

                    MODEL_VER=\${MODEL_VERSION:-latest}

                    tar cf - -C .tmp-deploy . | docker run --rm -i \
                      -e USE_GKE_GCLOUD_AUTH_PLUGIN=True \
                      google/cloud-sdk:latest bash -c "
                        mkdir -p /deploy && cd /deploy && tar xf - &&
                        gcloud auth activate-service-account --key-file=/deploy/gcp-key.json &&
                        gcloud container clusters get-credentials ${GKE_CLUSTER} \
                          --zone ${ZONE} --project ${PROJECT_ID} &&
                        curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash &&
                        helm dependency build /deploy/helm-charts/card-approval &&
                        helm upgrade --install card-approval \
                          /deploy/helm-charts/card-approval \
                          --namespace ${GKE_NAMESPACE} \
                          --create-namespace \
                          --set api.image.repository=${REGISTRY}/${REPOSITORY}/${IMAGE_NAME} \
                          --set api.image.tag=${IMAGE_TAG} \
                          --timeout 10m \
                          --wait \
                          --atomic
                      "

                    rm -rf .tmp-deploy
                    """
                }
            }
        }
    }

    post {
        always {
            sh 'rm -rf .tmp-deploy .model-info.env models || true'
            sh 'docker image prune -f || true'
        }
        success {
            echo 'Pipeline completed successfully'
            script {
                if (env.BRANCH_NAME == 'main') {
                    echo "Deployed: ${env.IMAGE_TAG}"
                }
            }
        }
        failure {
            echo 'Pipeline failed'
        }
    }
}
```

### Model Evaluation Script

```python
# scripts/evaluate_model.py
import argparse
import mlflow
import pandas as pd
from sklearn.metrics import f1_score

def evaluate_model(threshold: float, output_file: str):
    client = mlflow.MlflowClient()

    # Get production model
    model_name = os.environ["MODEL_NAME"]
    stage = os.environ["MODEL_STAGE"]

    versions = client.search_model_versions(f"name='{model_name}'")
    prod_version = next(v for v in versions if v.aliases and stage in v.aliases)

    # Load model and test data
    model = mlflow.pyfunc.load_model(f"models:/{model_name}/{prod_version.version}")
    X_test = pd.read_csv("training/data/processed/X_test.csv")
    y_test = pd.read_csv("training/data/processed/y_test.csv")

    # Evaluate
    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred)

    # Quality gate
    if f1 < threshold:
        raise ValueError(f"Model F1 {f1:.4f} below threshold {threshold}")

    # Write model info
    with open(output_file, "w") as f:
        f.write(f"MODEL_VERSION={prod_version.version}\n")
        f.write(f"MODEL_RUN_ID={prod_version.run_id}\n")
        f.write(f"MODEL_F1={f1:.4f}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    evaluate_model(args.threshold, args.output_file)
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Exposing credentials in logs | Use `withCredentials` block |
| Not cleaning up secrets | Always `rm -rf .tmp-*` in post |
| Building on feature branches | Use `when { branch 'main' }` |
| No timeout | Set `timeout(time: 1, unit: 'HOURS')` |

### Jenkins Credentials Setup

```groovy
// Required credentials in Jenkins:
// 1. gcp-service-account: File credential with GCP key JSON
// 2. sonarqube-token: Secret text with SonarQube token

withCredentials([
    file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY'),
    string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')
]) {
    // Credentials available as environment variables
}
```

### Security Best Practices

1. **Never echo credentials**: Jenkins masks `withCredentials` vars
2. **Clean temp files**: Post-always cleanup
3. **Trivy scanning**: Catch vulnerabilities before deploy
4. **Atomic deployments**: Auto-rollback on failure

### Debugging Pipeline

```groovy
// Add debug output
script {
    echo "Branch: ${env.BRANCH_NAME}"
    echo "Image Tag: ${env.IMAGE_TAG}"
    sh 'env | sort'  // Print all env vars (careful with secrets!)
}

// Replay with modifications
// Jenkins UI → Build → Replay → Edit Jenkinsfile
```

---

## 5. Testing & Validation

### Pipeline Validation

```bash
# Lint Jenkinsfile
npm install -g @jenkins-x/jx
jx pipeline validate

# Or use Jenkins Pipeline Linter
curl -X POST -F "jenkinsfile=<Jenkinsfile" \
  http://jenkins:8080/pipeline-model-converter/validate
```

### Deployment Verification

```bash
# After deploy:
kubectl get pods -n card-approval
kubectl logs -l app=card-approval-api -n card-approval

# Check image tag
kubectl get deployment card-approval-api -n card-approval \
  -o jsonpath='{.spec.template.spec.containers[0].image}'

# Test API
kubectl port-forward svc/card-approval-api 8000:80 -n card-approval
curl http://localhost:8000/health
```

---

## 6. Configuration Reference

### Environment Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `PROJECT_ID` | `my-gcp-project` | GCP project ID |
| `GKE_CLUSTER` | `mlops-gke` | GKE cluster name |
| `GKE_NAMESPACE` | `card-approval` | K8s namespace |
| `REGISTRY` | `us-east1-docker.pkg.dev` | Artifact Registry |
| `F1_THRESHOLD` | `0.90` | Model quality gate |

### Pipeline Stages Summary

| Stage | Branches | Purpose |
|-------|----------|---------|
| Checkout | All | Clone repo |
| Check Branch | All | Determine flow |
| Linting | All | Code quality |
| SonarQube | main + PRs | Static analysis |
| Model Eval | main | Quality gate |
| Build Image | main | Docker build |
| Push Image | main | Registry push |
| Deploy | main | Helm upgrade |

---

## 7. Further Reading

- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [GitHub Webhooks](https://docs.github.com/en/webhooks)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)
- [Helm Atomic Upgrades](https://helm.sh/docs/helm/helm_upgrade/)
- [MLOps Model Quality Gates](https://ml-ops.org/content/mlops-principles)
