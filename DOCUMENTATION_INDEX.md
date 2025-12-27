# Documentation Index

## 📚 Documentation Structure

This project has been consolidated into **two main documentation files** that cover all aspects of deployment and operations:

### 1. 📘 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
**Purpose:** Complete guide for deploying the application using Helm charts

**Contains:**
- ✅ Helm chart deployment steps
- ✅ GKE cluster setup
- ✅ Configuration management
- ✅ Environment-specific deployments (dev/staging/prod)
- ✅ Monitoring setup (Prometheus/Grafana)
- ✅ Troubleshooting guide
- ✅ Maintenance operations
- ✅ Best practices

**Use this when:**
- Setting up a new environment
- Deploying updates to existing environments
- Configuring monitoring
- Troubleshooting deployment issues

### 2. 🔧 [CI_CD_README.md](CI_CD_README.md)
**Purpose:** Complete guide for CI/CD pipeline operations

**Contains:**
- ✅ Jenkins setup with Ansible
- ✅ SonarQube configuration
- ✅ Pipeline stages explanation
- ✅ GitHub webhook integration
- ✅ Credentials management
- ✅ Pipeline operations (trigger, monitor, rollback)
- ✅ Monitoring and alerts
- ✅ CI/CD troubleshooting

**Use this when:**
- Setting up CI/CD infrastructure
- Configuring Jenkins and SonarQube
- Creating or modifying pipelines
- Troubleshooting build failures
- Setting up GitHub integration

## 🗂️ Additional Documentation

### Helm Chart Specific
- **[helm-charts/card-approval/README.md](helm-charts/card-approval/README.md)** - Detailed Helm chart usage

### Code Documentation
- **[app/README.md](app/README.md)** - FastAPI application documentation
- **[cap_model/README.md](cap_model/)** - Model training documentation

### Project Setup
- **[README.md](README.md)** - Project overview and quick start

## 🚀 Quick Start Paths

### For DevOps Engineers

**Initial Setup:**
1. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Prerequisites section
2. Follow deployment steps
3. Set up monitoring

**CI/CD Setup:**
1. Read [CI_CD_README.md](CI_CD_README.md) - Setup Instructions
2. Deploy Jenkins with Ansible
3. Configure pipeline
4. Set up GitHub webhooks

### For Developers

**Local Development:**
1. Read [README.md](README.md) - Quick start
2. Use `docker-compose.yml` for local testing
3. Run tests locally before pushing

**Contributing:**
1. Make changes on feature branch
2. Push to trigger pipeline
3. Monitor Jenkins build
4. Review SonarQube results

### For Operations Teams

**Monitoring:**
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Monitoring Setup section
2. Access Grafana dashboards
3. Set up alerts

**Troubleshooting:**
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Troubleshooting section
2. Check [CI_CD_README.md](CI_CD_README.md) - Troubleshooting section
3. Review logs and events

## 📋 Consolidated Document Changes

### What Was Removed
The following redundant documents were consolidated:
- ❌ `IMPLEMENTATION_SUMMARY.md` - Merged into DEPLOYMENT_GUIDE.md
- ❌ `HELM_MIGRATION_GUIDE.md` - Merged into DEPLOYMENT_GUIDE.md
- ❌ Original `DEPLOYMENT_GUIDE.md` - Rewritten for Helm
- ❌ Original `CI_CD_README.md` - Rewritten without k8s/ references

### What Changed
- ✅ Removed all references to `k8s/` folder
- ✅ Updated to use Helm charts exclusively
- ✅ Consolidated information to avoid duplication
- ✅ Added more troubleshooting steps
- ✅ Improved structure and navigation

## 🎯 Architecture Overview

```
Project Structure:
├── app/                    # FastAPI application
├── cap_model/             # ML model code
├── helm-charts/           # Helm chart deployments
│   ├── infrastructure/   # Reusable components
│   └── card-approval/    # Main application chart
├── ansible/              # Jenkins infrastructure
├── scripts/              # Utility scripts
├── Jenkinsfile          # CI/CD pipeline
└── docker-compose.yml   # Local development

Documentation:
├── README.md                 # Project overview
├── DEPLOYMENT_GUIDE.md       # Deployment operations
├── CI_CD_README.md          # CI/CD operations
└── DOCUMENTATION_INDEX.md   # This file
```

## 🔍 Finding Information

### Common Questions

**"How do I deploy the application?"**
→ [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment Steps section

**"How do I set up Jenkins?"**
→ [CI_CD_README.md](CI_CD_README.md) - Setup Instructions section

**"How do I configure for different environments?"**
→ [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Configuration section

**"How do I rollback a failed deployment?"**
→ [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Maintenance section
→ [CI_CD_README.md](CI_CD_README.md) - Pipeline Operations section

**"How do I add a new stage to the pipeline?"**
→ [CI_CD_README.md](CI_CD_README.md) - Pipeline Stages section
→ Edit `Jenkinsfile`

**"How do I set up monitoring?"**
→ [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Monitoring Setup section

**"Why did my build fail?"**
→ [CI_CD_README.md](CI_CD_README.md) - Troubleshooting section

**"How do I scale the application?"**
→ [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Maintenance section

## 📞 Getting Help

1. **Search documentation** - Use your editor's search (Ctrl+F)
2. **Check troubleshooting sections** - Common issues are documented
3. **Review logs** - Follow commands in troubleshooting guides
4. **Open issue** - If problem persists

## ✅ Documentation Status

- [x] Deployment guide updated for Helm
- [x] CI/CD guide updated without k8s/ references
- [x] All redundant documents removed
- [x] Clear separation of concerns
- [x] Comprehensive troubleshooting
- [x] Best practices included
- [x] Quick start paths defined

---

**Last Updated:** December 14, 2025
**Documentation Version:** 2.0 (Helm-based)
