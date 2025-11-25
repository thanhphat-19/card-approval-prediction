# Card Approval Prediction - Model Development

This directory contains all machine learning model development code for credit card approval prediction.

---

## 📁 Directory Structure

```
cap_model/
├── data/                   # Data storage and management
│   ├── raw/               # Original, immutable data
│   ├── processed/         # Cleaned and transformed data
│   ├── features/          # Feature engineering outputs
│   └── external/          # External datasets (e.g., credit bureau data)
│
├── notebooks/             # Jupyter notebooks for exploration
│   ├── 01_eda.ipynb      # Exploratory Data Analysis
│   ├── 02_feature_engineering.ipynb
│   ├── 03_baseline_models.ipynb
│   └── 04_model_comparison.ipynb
│
├── src/                   # Source code for model development
│   ├── data/             # Data loading and processing
│   ├── features/         # Feature engineering pipeline
│   ├── models/           # Model training and evaluation
│   ├── utils/            # Utility functions
│   └── config/           # Configuration files
│
├── models/                # Trained model artifacts
│   ├── baseline/         # Baseline models
│   ├── experimental/     # Experimental models
│   └── production/       # Production-ready models
│
├── experiments/           # MLflow experiment tracking
│   └── configs/          # Experiment configurations
│
├── tests/                 # Unit and integration tests
│   ├── test_data/
│   ├── test_features/
│   └── test_models/
│
├── scripts/               # Executable scripts
│   ├── train.py          # Model training script
│   ├── evaluate.py       # Model evaluation script
│   └── predict.py        # Batch prediction script
│
├── outputs/               # Training outputs
│   ├── figures/          # Plots and visualizations
│   ├── reports/          # Analysis reports
│   └── metrics/          # Evaluation metrics
│
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
└── README.md             # This file
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd cap_model

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Preparation

```bash
# Place raw data in data/raw/
# Run preprocessing
python scripts/preprocess_data.py
```

### 3. Exploratory Analysis

```bash
# Launch Jupyter
jupyter notebook notebooks/01_eda.ipynb
```

### 4. Train Models

```bash
# Train baseline model
python scripts/train.py --config experiments/configs/baseline.yaml

# Train with MLflow tracking
python scripts/train.py --config experiments/configs/xgboost.yaml --track-mlflow
```

---

## 📊 Model Development Workflow

### Phase 1: Data Understanding
1. Load and explore raw data
2. Understand feature distributions
3. Identify missing values and outliers
4. Analyze target variable (approval/rejection rate)

### Phase 2: Feature Engineering
1. Handle missing values
2. Encode categorical variables
3. Create derived features
4. Feature scaling and normalization
5. Feature selection

### Phase 3: Model Training
1. Train baseline models (Logistic Regression)
2. Train tree-based models (Random Forest, XGBoost)
3. Train neural networks
4. Hyperparameter tuning
5. Cross-validation

### Phase 4: Model Evaluation
1. Accuracy, Precision, Recall, F1-Score
2. ROC-AUC curve
3. Confusion matrix
4. Feature importance
5. Model interpretability (SHAP values)

### Phase 5: Model Selection
1. Compare model performance
2. Consider business constraints
3. Evaluate model fairness
4. Select production model

---

## 🔬 Experiment Tracking with MLflow

All experiments are tracked in MLflow:

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("card-approval-classification")

with mlflow.start_run(run_name="xgboost-v1"):
    # Train model
    model = train_xgboost(X_train, y_train)
    
    # Log parameters
    mlflow.log_params(params)
    
    # Log metrics
    mlflow.log_metrics(metrics)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
```

---

## 📈 Model Performance Targets

| Metric | Baseline | Target | Production |
|--------|----------|--------|------------|
| Accuracy | 0.70 | 0.85 | 0.90 |
| Precision | 0.65 | 0.80 | 0.85 |
| Recall | 0.60 | 0.75 | 0.80 |
| F1-Score | 0.62 | 0.77 | 0.82 |
| ROC-AUC | 0.75 | 0.88 | 0.92 |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_models/test_training.py

# Run with coverage
pytest --cov=src tests/
```

---

## 📝 Documentation

- [Data Dictionary](docs/data_dictionary.md)
- [Feature Engineering](docs/feature_engineering.md)
- [Model Architecture](docs/model_architecture.md)
- [Evaluation Metrics](docs/evaluation_metrics.md)

---

## 🔗 Related Documentation

- Main project: `/docs/README.md`
- MLflow guide: `/docs/05_MLflow_Model_Development.md`
- Deployment: `/docs/03_Helm_Deployment.md`
