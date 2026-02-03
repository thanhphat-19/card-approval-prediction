# Component 9: Docker Containerization

## Executive Summary

Docker containerization packages the FastAPI application with embedded ML model artifacts into immutable, reproducible images. The Dockerfile uses multi-stage optimization, health checks, and security best practices to create production-ready containers that deploy consistently across environments. The model-embedded approach ensures version consistency between code and model.

---

## 1. Concept & Theory

### What is Containerization for ML?

Containerization packages application code, dependencies, and model artifacts into a single deployable unit:
- **Reproducibility**: Same image = same behavior everywhere
- **Isolation**: No dependency conflicts with host system
- **Portability**: Run on any Docker-compatible environment
- **Immutability**: Versioned artifacts, no drift

### Why Docker for ML APIs?

| Challenge | Docker Solution |
|-----------|-----------------|
| Dependency hell | All deps in image |
| Model versioning | Model embedded in image tag |
| Environment parity | Same image dev → prod |
| Scaling | Stateless containers scale easily |

### Model Loading Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| **Embedded** | Fast startup, immutable | Rebuild for model update |
| **Runtime Load** | Hot-swap models | Cold start, network deps |
| **Hybrid** | Fallback support | Complexity |

This project uses **Embedded** with runtime fallback:
```python
if self.settings.MODEL_PATH:
    self._load_from_local_path()  # Embedded
else:
    self._load_from_mlflow()       # Fallback
```

---

## 2. Architecture & Design Decisions

### Docker Image Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Image                                  │
│                    Tag: {BUILD_NUMBER}-{GIT_SHA}                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Base: python:3.11-slim                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  System Dependencies                                     │    │
│  │  - build-essential, curl, git                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Python Dependencies (from pyproject.toml)              │    │
│  │  - fastapi, uvicorn, pydantic                           │    │
│  │  - mlflow, scikit-learn, xgboost, lightgbm             │    │
│  │  - prometheus-client, opentelemetry                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Application Code (/app)                                │    │
│  │  - app/main.py                                          │    │
│  │  - app/routers/, app/services/, app/schemas/           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Model Artifacts (/app/models)                          │    │
│  │  - MLmodel                                              │    │
│  │  - model.pkl (or model.xgb, etc.)                      │    │
│  │  - preprocessors/scaler.pkl, pca.pkl                   │    │
│  │  - model_metadata.json                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ENV MODEL_PATH=/app/models                                     │
│  EXPOSE 8000                                                     │
│  HEALTHCHECK /health                                             │
│  CMD ["python", "-m", "app.main"]                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. Slim Base Image
```dockerfile
FROM python:3.11-slim
```

**Rationale**: Smaller image size (~150MB base vs ~900MB full), faster pulls.

#### 2. UV for Fast Dependency Installation
```dockerfile
RUN pip install --no-cache-dir uv
RUN uv pip install . --system --no-cache-dir
```

**Benefit**: 10-100x faster than pip for large dependency trees.

#### 3. Model Embedding via CI/CD
```dockerfile
# Model downloaded during CI/CD, then copied
COPY models /app/models
ENV MODEL_PATH=/app/models
```

**Workflow**:
1. Jenkins downloads model from MLflow
2. Model copied into build context
3. Dockerfile embeds model in image

#### 4. Health Check for Kubernetes
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

**Purpose**: Kubernetes uses this for liveness/readiness probes.

---

## 3. Implementation Guide

### Complete Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# build-essential: For compiling Python packages with C extensions
# curl: For health checks and debugging
# git: Required by some Python packages during install
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installation
RUN pip install --upgrade pip && \
    pip install --no-cache-dir uv

# Copy dependency specification first (for caching)
COPY ./pyproject.toml .

# Install Python dependencies
# --system: Install to system Python (not venv)
# --no-cache-dir: Don't cache packages (smaller image)
RUN uv pip install . --system --no-cache-dir

# Create reports directory (for any generated outputs)
RUN mkdir -p /app/reports

# Copy application code
COPY . .

# Copy model artifacts (downloaded during CI/CD pipeline)
# This embeds the model into the image for consistent versioning
COPY models /app/models

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variable to use embedded model
# If MODEL_PATH is set, app loads from local path instead of MLflow
ENV MODEL_PATH=/app/models

# Expose the API port
EXPOSE 8000

# Health check for Kubernetes
# --interval: How often to run check
# --timeout: Max time for check to complete
# --start-period: Grace period during startup
# --retries: Failures before unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "app.main"]
```

### Multi-Stage Build (Alternative)

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy and install dependencies
COPY pyproject.toml .
RUN uv pip install . --system --no-cache-dir

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ /app/app/

# Copy model artifacts
COPY models /app/models

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment
ENV MODEL_PATH=/app/models
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "app.main"]
```

### .dockerignore

```gitignore
# .dockerignore
# Exclude everything not needed in container

# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.egg-info
.eggs
*.egg

# Virtual environments
venv/
.venv/
env/

# IDE
.vscode/
.idea/
*.swp

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Documentation
docs/
*.md
!README.md

# Data (large files)
data/
training/data/
*.csv
*.parquet

# MLflow local
mlruns/

# Jupyter
notebooks/
*.ipynb

# CI/CD
.github/
Jenkinsfile

# Terraform
terraform/

# Ansible
ansible/

# Helm charts (deployed separately)
helm-charts/

# Build artifacts
build/
dist/

# Logs (should be empty anyway)
logs/*.log

# Local config
config.env
*.env.local
```

### Building and Running

```bash
# Build image
docker build -t card-approval-api:v1.0.0 .

# Build with build args
docker build \
  --build-arg MODEL_VERSION=3 \
  -t card-approval-api:v1.0.0-model3 .

# Run container
docker run -d \
  --name card-approval-api \
  -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e OTEL_ENABLED=false \
  card-approval-api:v1.0.0

# Run with environment file
docker run -d \
  --name card-approval-api \
  -p 8000:8000 \
  --env-file config.env \
  card-approval-api:v1.0.0

# View logs
docker logs -f card-approval-api

# Execute command in container
docker exec -it card-approval-api bash

# Health check
curl http://localhost:8000/health
```

### Pushing to Artifact Registry

```bash
# Authenticate to GCP Artifact Registry
gcloud auth configure-docker us-east1-docker.pkg.dev

# Tag image
docker tag card-approval-api:v1.0.0 \
  us-east1-docker.pkg.dev/my-project/my-repo/card-approval-api:v1.0.0

# Push
docker push us-east1-docker.pkg.dev/my-project/my-repo/card-approval-api:v1.0.0
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Large image size | Use slim base, multi-stage builds |
| Slow builds | Order COPY commands for caching |
| Running as root | Create non-root user |
| No health check | Add HEALTHCHECK instruction |
| Missing .dockerignore | Exclude unnecessary files |

### Image Size Optimization

```bash
# Check image size
docker images card-approval-api

# Analyze layers
docker history card-approval-api:v1.0.0

# Use dive for detailed analysis
dive card-approval-api:v1.0.0
```

**Target Sizes**:
| Component | Size |
|-----------|------|
| Base (python:3.11-slim) | ~150 MB |
| Dependencies | ~400-600 MB |
| Application | ~10 MB |
| Model artifacts | ~50-200 MB |
| **Total** | **~600-1000 MB** |

### Security Best Practices

```dockerfile
# 1. Use specific image tag (not :latest)
FROM python:3.11.4-slim

# 2. Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# 3. Don't store secrets in image
# Use environment variables at runtime

# 4. Minimal packages
RUN apt-get install -y --no-install-recommends ...

# 5. Remove package lists
RUN rm -rf /var/lib/apt/lists/*
```

### Debugging Containers

```bash
# Shell into running container
docker exec -it card-approval-api bash

# Shell into failed container
docker run -it --entrypoint bash card-approval-api:v1.0.0

# Check environment variables
docker exec card-approval-api env

# Check model files
docker exec card-approval-api ls -la /app/models/

# View startup logs
docker logs card-approval-api 2>&1 | head -50
```

---

## 5. Testing & Validation

### Local Testing

```bash
# Build
docker build -t card-approval-api:test .

# Run
docker run -d --name test-api -p 8000:8000 card-approval-api:test

# Wait for startup
sleep 10

# Test health
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 1,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 180000,
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
  }'

# Cleanup
docker stop test-api && docker rm test-api
```

### Validation Checklist

- [ ] Image builds successfully
- [ ] Container starts without errors
- [ ] Health endpoint returns 200
- [ ] Prediction endpoint works
- [ ] Model version matches expected
- [ ] Metrics endpoint exposes Prometheus format
- [ ] Logs are properly formatted
- [ ] Container runs as non-root (if configured)
- [ ] Image size is reasonable (<1GB)

---

## 6. Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `/app/models` | Path to embedded model |
| `MLFLOW_TRACKING_URI` | - | MLflow server (fallback) |
| `MODEL_NAME` | `card_approval_model` | Model name in registry |
| `MODEL_STAGE` | `Production` | Model stage/alias |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `OTEL_ENABLED` | `true` | Enable tracing |
| `OTEL_EXPORTER_ENDPOINT` | - | Tempo/Jaeger endpoint |

### Docker Compose for Local Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=DEBUG
      - OTEL_ENABLED=false
    volumes:
      # Mount code for hot reload (dev only)
      - ./app:/app/app:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 7. Further Reading

- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Python Docker Images](https://hub.docker.com/_/python)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Container Security](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [uv Package Installer](https://github.com/astral-sh/uv)
- [Dive Image Analyzer](https://github.com/wagoodman/dive)
