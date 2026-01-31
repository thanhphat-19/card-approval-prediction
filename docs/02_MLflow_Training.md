# Model Training Guide

Train credit card approval models with MLflow tracking.

---

## Prerequisites

Before starting, ensure you have:
1. Completed the [Helm Deployment Guide](01_Helm_Deployment.md) - MLflow must be deployed and running
2. MLflow accessible via port-forward or ingress
3. GCS bucket configured in Helm deployment for artifact storage
4. Kaggle API credentials configured

---

## Step 1: Setup Kaggle API

```bash
# Create Kaggle directory
mkdir -p ~/.kaggle
chmod 600 ~/.kaggle

# Get API key from https://www.kaggle.com/settings → API → Create New Token
# Move downloaded kaggle.json to ~/.kaggle/
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Verify
kaggle --version
```

## Step 2: Download Data

```bash
cd training
python scripts/download_data.py
```


**Expected output:**
```
data/
├── raw/
│   ├── application_record.csv   # 438,557 rows
│   └── credit_record.csv        # 1,048,575 rows
```
![Succefully Downloaded Data](../img/02_download_data.png)

---

## Step 3: Connect to MLflow


```bash
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training
```
**Terminal**
![Succefully Port Forward MLflow](../img/02_port_forward.png)

## Step 4: Preprocess Data

```bash
cd training
python scripts/run_preprocessing.py
```

**Output:**
```
data/processed/
├── X_train.csv, X_test.csv
├── y_train.csv, y_test.csv
├── scaler.pkl, pca.pkl
└── feature_names.json
```
**Terminal**
![Succefully Preprocess Data](../img/02_preprocess_data.png)


---

## Step 5: Train Models

```bash
cd training
python scripts/run_training.py
```

**What happens:**
1. Trains: XGBoost, LightGBM, CatBoost, AdaBoost, NaiveBayes
2. Logs metrics & artifacts to MLflow
3. Registers best model (by F1-Score) to MLflow Model Registry
4. Stores model and preprocessor artifacts in GCS bucket (configured in Helm deployment)

---

**Terminal**
![Succefully Train Models](../img/02_train_models.png)

**MLflow**
![Succefully Train Models MLflow](../img/02_train_models_mlflow.png)

## Step 6: Verify in MLflow

Open http://localhost:5000

- **Experiments**: View all training runs
- **Models**: Check `card_approval_model`

---
