# MLflow & Model Training Guide

## Overview

ML pipeline for credit card approval prediction using XGBoost with MLflow tracking.

```
cap_model/
├── scripts/
│   └── run_training.py      # Main training script
├── src/
│   ├── config/config.yaml   # Configuration
│   ├── data/                # Data loading
│   ├── preprocessing/       # Feature engineering
│   └── training/            # Model training
└── data/                    # Raw datasets
```

---

# **Step 1: Prepare Data**

```bash
cd cap_model
ls data/
```

**Required files:**
```bash
data/
├── application_record.csv   # Applicant information
└── credit_record.csv        # Credit history
```

**What the data contains:**
- `application_record.csv` - Demographics, income, employment
- `credit_record.csv` - Payment status history (0, 1-5, C, X)

---

# **Step 2: Configure Training**

Edit `src/config/config.yaml`:

```yaml
data:
  application_path: "data/application_record.csv"
  credit_path: "data/credit_record.csv"

preprocessing:
  test_size: 0.2
  random_state: 42
  pca_components: 5

model:
  hyperparameters:
    xgboost:
      n_estimators: 100
      max_depth: 6
      learning_rate: 0.1
```

**Key parameters:**
- `test_size: 0.2` - 20% for testing
- `pca_components: 5` - Reduce to 5 features
- `n_estimators: 100` - Number of trees

---

# **Step 3: Set MLflow Tracking URI**

**Local development:**
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
```

**Kubernetes (port-forward):**
```bash
kubectl port-forward svc/card-approval-training-mlflow 5000:5000 -n card-approval-training
export MLFLOW_TRACKING_URI=http://localhost:5000
```

**Verify connection:**
```bash
python -c "import mlflow; print(mlflow.get_tracking_uri())"
```

---

# **Step 4: Run Training**

```bash
python scripts/run_training.py --config src/config/config.yaml
```

**What this does:**

## 4.1 Load Data
```
✓ Loaded application_record.csv: 438,557 rows
✓ Loaded credit_record.csv: 1,048,575 rows
✓ Merged data: 36,457 customers
```

## 4.2 Create Target Variable
```
Target: Good (1) / Bad (0) based on credit status
- Status 0, C, X → Good (paid on time)
- Status 1-5 → Bad (late payment)
```

## 4.3 Feature Engineering
```
✓ One-hot encoding: 18 → 48 features
✓ SMOTE + Tomek: 36,457 → 72,496 samples (balanced)
✓ StandardScaler: Normalized features
✓ PCA: 48 → 5 components
```

## 4.4 Train Models
```
Training XGBoost...
✓ XGBoost: Accuracy=95.92%, F1=0.9589
Training LightGBM...
✓ LightGBM: Accuracy=95.10%, F1=0.9508
```

## 4.5 Log to MLflow
```
✓ Logged metrics to MLflow
✓ Logged model artifacts
✓ Registered model: card_approval_model
```

---

# **Step 5: View Results in MLflow**

```bash
# Start MLflow UI (if local)
mlflow ui --port 5000

# Open browser
open http://localhost:5000
```

**What you'll see:**
- Experiment runs with metrics
- Model artifacts (pkl files)
- Parameters used
- Comparison charts

---

# **Step 6: Register Model to Production**

**Option 1: MLflow UI**
1. Go to Models tab
2. Click `card_approval_model`
3. Select version → Stage → Production

**Option 2: Python**
```python
import mlflow
client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name="card_approval_model",
    version="1",
    stage="Production"
)
```

**Verify:**
```python
from mlflow import MlflowClient
client = MlflowClient()
for mv in client.search_model_versions("name='card_approval_model'"):
    print(f"Version: {mv.version}, Stage: {mv.current_stage}")
```

---

# **Step 7: Test Model Loading**

```python
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")

# Load production model
model = mlflow.pyfunc.load_model("models:/card_approval_model/Production")

# Test prediction
import pandas as pd
sample = pd.DataFrame([{
    "CODE_GENDER": "M",
    "AMT_INCOME_TOTAL": 150000,
    # ... other features
}])
prediction = model.predict(sample)
print(f"Prediction: {prediction}")
```

---

## Pipeline Summary

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Load Data  │───▶│  Preprocess │───▶│    Train    │───▶│   MLflow    │
│             │    │             │    │             │    │  Registry   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                   │                   │
     ▼                   ▼                   ▼                   ▼
  36,457            One-hot encode      XGBoost model      Production
  customers         SMOTE + Tomek       95.92% accuracy    stage
                    StandardScaler
                    PCA (5 components)
```

**Total training time:** ~5-10 minutes
