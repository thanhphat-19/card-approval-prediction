# Component 2: ML Training Pipeline

## Executive Summary

The ML Training Pipeline is a reproducible, MLflow-tracked system for training and comparing multiple classification models for credit card approval prediction. It handles data loading, feature engineering, multi-model training (XGBoost, LightGBM, CatBoost), model selection, and automatic registration to MLflow Model Registry with Production aliases.

---

## 1. Concept & Theory

### What is this component?

The training pipeline transforms raw credit card application data into a production-ready ML model through:
1. **Data Loading**: Merge application and credit bureau records
2. **Feature Engineering**: Encoding, scaling, PCA transformation
3. **Model Training**: Train and compare multiple algorithms
4. **Model Registry**: Register best model to MLflow Production

### Why a Structured Training Pipeline?

| Challenge | Solution |
|-----------|----------|
| Irreproducible experiments | MLflow tracks all params, metrics, artifacts |
| Manual model selection | Automated comparison and best model selection |
| Feature drift | Preprocessing artifacts (scaler, PCA) versioned with model |
| Deployment friction | Direct registration to Production alias |

### Core ML Concepts

1. **Class Imbalance**: Credit approval is often imbalanced (more approvals than rejections)
2. **Feature Engineering**: Transform raw features into model-ready inputs
3. **Model Comparison**: Evaluate multiple algorithms on same data
4. **Model Registry**: Version control for ML models

### Credit Scoring Metrics

| Metric | Why It Matters |
|--------|----------------|
| **Precision** | Avoid false approvals (financial risk) |
| **Recall** | Don't reject good customers |
| **F1-Score** | Balance between precision and recall |
| **ROC-AUC** | Overall discriminative ability |

---

## 2. Architecture & Design Decisions

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Training Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Data Loading │ →  │   Feature    │ →  │    Model     │       │
│  │              │    │ Engineering  │    │   Training   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         ↓                   ↓                   ↓                │
│    Raw CSVs          Scaler, PCA,        MLflow Runs            │
│                      feature_names                               │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │    Model     │ →  │    Model     │ →  │   Deploy     │       │
│  │  Comparison  │    │  Selection   │    │   Ready!     │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         ↓                   ↓                   ↓                │
│  metrics DataFrame    Best F1 model      MLflow Registry        │
│                                          (Production alias)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. Multi-Model Training Strategy
```python
model_configs = {
    "XGBoost": {
        "class": XGBClassifier,
        "params": {"n_estimators": 200, "max_depth": 6, ...}
    },
    "LightGBM": {...},
    "CatBoost": {...},
    "AdaBoost": {...},
    "NaiveBayes": {...},
}
```

**Rationale**: Different algorithms may perform better on different data distributions.

#### 2. Preprocessing Artifact Versioning
```python
# Log preprocessing artifacts to MLflow
mlflow.log_artifact("preprocessors/scaler.pkl")
mlflow.log_artifact("preprocessors/pca.pkl")
mlflow.log_artifact("preprocessors/feature_names.json")
```

**Critical**: Preprocessing MUST match between training and inference.

#### 3. F1-Score as Selection Metric
```python
best_result = max(self.results, key=lambda x: x["F1-Score"])
```

**Rationale**: F1 balances precision and recall, important for credit decisions.

#### 4. Automatic Model Registration
```python
# Auto-register best model to Production
mlflow.register_model(model_uri, model_name)
client.set_registered_model_alias(model_name, "Production", version)
```

**Benefit**: Eliminates manual promotion steps.

---

## 3. Implementation Guide

### Directory Structure

```
training/
├── data/
│   ├── raw/                    # Original Kaggle dataset
│   │   ├── application_record.csv
│   │   └── credit_record.csv
│   └── processed/              # Processed features
│       ├── X_train.csv
│       ├── X_test.csv
│       ├── y_train.csv
│       ├── y_test.csv
│       ├── scaler.pkl
│       ├── pca.pkl
│       └── feature_names.json
├── scripts/
│   ├── download_data.py        # Kaggle API download
│   ├── run_preprocessing.py    # Feature engineering
│   └── run_training.py         # Model training
├── src/
│   ├── data/
│   │   └── data_loader.py      # Load and merge CSVs
│   ├── features/
│   │   └── feature_engineering.py  # Preprocessing pipeline
│   ├── models/
│   │   ├── train.py            # ModelTrainer class
│   │   └── evaluate.py         # Evaluation utilities
│   └── utils/
│       ├── model_configs.py    # Model configurations
│       └── mlflow_registry.py  # Registry operations
├── notebooks/
│   ├── 01_eda.ipynb            # Exploratory analysis
│   ├── 02_data_processing.ipynb
│   └── 03_model_training.ipynb
└── README.md
```

### Step-by-Step Implementation

#### Step 1: Download Data from Kaggle

```bash
# Setup Kaggle credentials
mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Download data
python training/scripts/download_data.py
```

```python
# training/scripts/download_data.py
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()
api.dataset_download_files(
    "rikdifos/credit-card-approval-prediction",
    path="training/data/raw",
    unzip=True,
)
```

#### Step 2: Data Loading

```python
# training/src/data/data_loader.py
def load_data(raw_data_dir: str) -> pd.DataFrame:
    """Load and merge application + credit records"""
    app_df = pd.read_csv(f"{raw_data_dir}/application_record.csv")
    credit_df = pd.read_csv(f"{raw_data_dir}/credit_record.csv")

    # Create target variable from credit status
    credit_agg = credit_df.groupby("ID").agg({
        "STATUS": lambda x: 1 if any(s in ["2","3","4","5"] for s in x) else 0
    })

    # Merge datasets
    merged = app_df.merge(credit_agg, on="ID")
    merged = merged.rename(columns={"STATUS": "TARGET"})

    return merged
```

#### Step 3: Feature Engineering Pipeline

```python
# training/src/features/feature_engineering.py
class FeatureEngineer:
    def __init__(self, test_size=0.2, pca_components=5):
        self.test_size = test_size
        self.pca_components = pca_components
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=pca_components)

    def fit_transform(self, df: pd.DataFrame) -> tuple:
        """Full preprocessing pipeline"""
        # Separate features and target
        X = df.drop(["ID", "TARGET"], axis=1)
        y = df["TARGET"]

        # One-hot encode categorical features
        X_encoded = pd.get_dummies(X, drop_first=True)
        self.feature_names = X_encoded.columns.tolist()

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_encoded, y, test_size=self.test_size, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Apply PCA
        X_train_pca = self.pca.fit_transform(X_train_scaled)
        X_test_pca = self.pca.transform(X_test_scaled)

        return X_train_pca, X_test_pca, y_train, y_test

    def save_artifacts(self, output_dir: str):
        """Save preprocessing artifacts"""
        joblib.dump(self.scaler, f"{output_dir}/scaler.pkl")
        joblib.dump(self.pca, f"{output_dir}/pca.pkl")
        with open(f"{output_dir}/feature_names.json", "w") as f:
            json.dump({"feature_names": self.feature_names}, f)
```

#### Step 4: Model Training

```python
# training/src/models/train.py
class ModelTrainer:
    def __init__(self, tracking_uri: str, experiment_name: str):
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)

    def train_single_model(
        self,
        model_name: str,
        model_class,
        params: dict,
        X_train, y_train, X_test, y_test,
    ) -> dict:
        """Train model and log to MLflow"""

        with mlflow.start_run(run_name=model_name):
            # Create and train model
            model = model_class(**params)
            model.fit(X_train, y_train)

            # Predict
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            # Calculate metrics
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(y_test, y_pred),
                "recall": recall_score(y_test, y_pred),
                "f1_score": f1_score(y_test, y_pred),
                "roc_auc": roc_auc_score(y_test, y_proba),
            }

            # Log to MLflow
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)

            # Log model with appropriate flavor
            if "XGBoost" in model_name:
                mlflow.xgboost.log_model(model, "model")
            elif "LightGBM" in model_name:
                mlflow.lightgbm.log_model(model, "model")
            elif "CatBoost" in model_name:
                mlflow.catboost.log_model(model, "model")
            else:
                mlflow.sklearn.log_model(model, "model")

            return {
                "model": model,
                "metrics": metrics,
                "run_id": mlflow.active_run().info.run_id,
            }

    def train_all_models(self, X_train, y_train, X_test, y_test):
        """Train all configured models"""
        results = []
        for name, config in get_model_configs().items():
            result = self.train_single_model(
                name, config["class"], config["params"],
                X_train, y_train, X_test, y_test
            )
            results.append(result)
        return results
```

#### Step 5: Model Configurations

```python
# training/src/utils/model_configs.py
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

def get_model_configs():
    return {
        "XGBoost": {
            "class": XGBClassifier,
            "params": {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42,
                "use_label_encoder": False,
                "eval_metric": "logloss",
            }
        },
        "LightGBM": {
            "class": LGBMClassifier,
            "params": {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "num_leaves": 31,
                "random_state": 42,
                "verbose": -1,
            }
        },
        "CatBoost": {
            "class": CatBoostClassifier,
            "params": {
                "iterations": 200,
                "depth": 6,
                "learning_rate": 0.1,
                "random_state": 42,
                "verbose": False,
            }
        },
    }
```

#### Step 6: Model Registration

```python
# training/src/utils/mlflow_registry.py
def register_best_model(
    run_id: str,
    model_name: str,
    stage: str = "Production"
):
    """Register model to MLflow Registry with Production alias"""
    client = MlflowClient()

    # Create or get registered model
    try:
        client.create_registered_model(model_name)
    except MlflowException:
        pass  # Already exists

    # Create model version
    model_uri = f"runs:/{run_id}/model"
    result = mlflow.register_model(model_uri, model_name)
    version = result.version

    # Set Production alias
    client.set_registered_model_alias(
        name=model_name,
        alias="Production",
        version=version
    )

    return version
```

#### Step 7: Complete Training Script

```bash
# Run complete pipeline
python training/scripts/run_preprocessing.py \
    --raw-data-dir training/data/raw \
    --output-dir training/data/processed \
    --pca-components 5

python training/scripts/run_training.py \
    --data-dir training/data/processed \
    --output-dir models \
    --mlflow-uri http://localhost:5000 \
    --models XGBoost LightGBM CatBoost \
    --metric F1-Score
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Training/serving skew | Version preprocessing with model |
| Leaking test data | Use stratified split before preprocessing |
| Not handling class imbalance | Use `scale_pos_weight` in XGBoost |
| Overfitting to single metric | Track multiple metrics |

### Class Imbalance Handling

```python
# Calculate class weights
scale_pos_weight = len(y_train[y_train==0]) / len(y_train[y_train==1])

# XGBoost with class weight
XGBClassifier(scale_pos_weight=scale_pos_weight, ...)
```

### Feature Names Consistency

```json
// training/data/processed/feature_names.json
{
  "feature_names": [
    "CODE_GENDER_M",
    "FLAG_OWN_CAR_Y",
    "FLAG_OWN_REALTY_Y",
    "AMT_INCOME_TOTAL",
    "NAME_INCOME_TYPE_Pensioner",
    "NAME_INCOME_TYPE_State servant",
    "NAME_INCOME_TYPE_Student",
    "NAME_INCOME_TYPE_Working"
    // ... total 48 one-hot encoded features
  ]
}
```

### MLflow Artifact Structure

```
runs/<run_id>/
├── artifacts/
│   ├── model/
│   │   ├── MLmodel
│   │   ├── model.pkl (or model.xgb, etc.)
│   │   └── requirements.txt
│   └── preprocessors/
│       ├── scaler.pkl
│       ├── pca.pkl
│       └── feature_names.json
├── metrics/
│   ├── accuracy
│   ├── f1_score
│   ├── precision
│   └── recall
└── params/
    ├── n_estimators
    ├── max_depth
    └── learning_rate
```

### Debugging Training Issues

```python
# Check data shapes
print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
print(f"X_test: {X_test.shape}, y_test: {y_test.shape}")

# Check class distribution
print(f"Class distribution: {y_train.value_counts(normalize=True)}")

# Verify preprocessing artifacts
import joblib
scaler = joblib.load("training/data/processed/scaler.pkl")
print(f"Scaler feature count: {scaler.n_features_in_}")
```

---

## 5. Testing & Validation

### Test Files

```
tests/
├── test_training_data_loader.py
├── test_training_features.py
├── test_training_model_configs.py
├── test_training_mlflow_registry.py
└── test_training_utils.py
```

### Key Test Scenarios

```python
# Test data loading
def test_load_data():
    df = load_data("training/data/raw")
    assert "TARGET" in df.columns
    assert df["TARGET"].isin([0, 1]).all()

# Test feature engineering
def test_feature_engineering():
    fe = FeatureEngineer(pca_components=5)
    X_train, X_test, y_train, y_test = fe.fit_transform(df)
    assert X_train.shape[1] == 5  # PCA components

# Test model training
def test_train_xgboost():
    trainer = ModelTrainer(tracking_uri="file:./mlruns")
    result = trainer.train_single_model("XGBoost", ...)
    assert result["metrics"]["accuracy"] > 0.9
```

### Validation Checklist

- [ ] Data loads without errors
- [ ] Class distribution is reasonable (not too imbalanced)
- [ ] All preprocessing artifacts are saved
- [ ] MLflow experiment contains runs
- [ ] Best model registered to Production
- [ ] Model achieves F1 > 0.90 threshold

---

## 6. Model Performance Benchmarks

### Expected Results

| Model | Accuracy | F1-Score | ROC-AUC |
|-------|----------|----------|---------|
| **XGBoost** | 96.7% | 0.9667 | 0.9932 |
| LightGBM | 96.5% | 0.9650 | 0.9925 |
| CatBoost | 96.3% | 0.9630 | 0.9920 |
| AdaBoost | 94.2% | 0.9420 | 0.9800 |

### Hyperparameter Tuning (Future)

```python
# Optuna integration example
import optuna

def objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
    }
    # Train and return F1 score
    ...
```

---

## 7. Further Reading

- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [Handling Imbalanced Data](https://imbalanced-learn.org/stable/)
- [Kaggle Credit Card Dataset](https://www.kaggle.com/datasets/rikdifos/credit-card-approval-prediction)
