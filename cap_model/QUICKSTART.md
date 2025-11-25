# Card Approval Prediction - Quick Start Guide

Get started with model development in **5 minutes**! 🚀

---

## 🎯 Prerequisites

- Python 3.8+
- MLflow running on Kubernetes (see `/docs/03_Helm_Deployment.md`)
- Port-forward to MLflow: `kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000`

---

## ⚡ Quick Setup

### 1. Navigate to Project Directory

```bash
cd /home/thanhphat/workspace/card-approval-prediction/cap_model
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 4. Setup Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env if needed (optional)
nano .env
```

---

## 🚀 Train Your First Model

### Option 1: Using Sample Data (Fastest)

The script will automatically generate sample data if no data file exists:

```bash
# Train with default configuration
python scripts/train.py

# Train with MLflow tracking
python scripts/train.py --track-mlflow

# Use specific configuration
python scripts/train.py --config src/config/config.yaml --track-mlflow
```

**Expected output:**
```
================================================================================
CARD APPROVAL PREDICTION - MODEL TRAINING
================================================================================

1. Loading configuration from src/config/config.yaml
2. Loading data...
   Generating sample data for demonstration...
   ✓ Sample data saved to data/raw/credit_applications.csv
   ...
5. Evaluating model...

================================================================================
TRAINING COMPLETED SUCCESSFULLY!
================================================================================

Test Set Performance:
  test_accuracy: 0.8650
  test_precision: 0.8523
  test_recall: 0.8712
  test_f1_score: 0.8617
  test_roc_auc: 0.9234
```

### Option 2: Using Your Own Data

```bash
# 1. Place your CSV file
cp your_data.csv data/raw/credit_applications.csv

# 2. Update config if needed (optional)
nano src/config/config.yaml

# 3. Train
python scripts/train.py --track-mlflow
```

**Required columns in your CSV:**
- `age`, `annual_income`, `credit_score`, `employment_years`
- `debt_to_income_ratio`, `num_existing_credit_cards`, `total_credit_limit`
- `employment_status`, `housing_type`, `education_level`, `marital_status`
- `approval_status` (target: 0=rejected, 1=approved)

---

## 📊 View Results in MLflow

### 1. Access MLflow UI

```bash
# Open in browser
http://localhost:5000
```

### 2. Navigate to Your Experiment

- Click on **"card-approval-classification"** experiment
- View all your training runs
- Compare metrics, parameters, and artifacts

### 3. Explore a Run

Click on any run to see:
- **Parameters**: Model hyperparameters
- **Metrics**: Accuracy, precision, recall, F1, ROC-AUC
- **Artifacts**: 
  - Confusion matrix
  - ROC curve
  - Feature importance plot
  - Trained model

---

## 🔮 Make Predictions

### Single Prediction

```bash
python scripts/predict.py --mode single
```

**Example output:**
```
Applicant Data:
  age: 35
  annual_income: 75000
  credit_score: 720
  ...

Prediction Result:
----------------------------------------
Decision: Approved
Approval Probability: 87.45%
Rejection Probability: 12.55%
Confidence: 87.45%
```

### Batch Predictions

```bash
# Create input file with applicant data
# Then run:
python scripts/predict.py \
  --mode batch \
  --input-file data/raw/new_applications.csv \
  --output-file outputs/predictions.csv
```

---

## 📓 Jupyter Notebooks

### Launch Jupyter

```bash
jupyter notebook
```

### Explore Notebooks

1. **`01_eda.ipynb`** - Exploratory Data Analysis
   - Data distribution
   - Feature correlations
   - Missing values analysis
   
2. **`02_feature_engineering.ipynb`** - Feature Engineering
   - Create derived features
   - Handle missing values
   - Feature scaling

3. **`03_baseline_models.ipynb`** - Baseline Models
   - Train simple models
   - Compare performance
   - Select best approach

4. **`04_model_comparison.ipynb`** - Model Comparison
   - Advanced models (XGBoost, LightGBM)
   - Hyperparameter tuning
   - Final model selection

---

## 🎯 Common Tasks

### Change Model Type

Edit `src/config/config.yaml`:
```yaml
model:
  type: "xgboost"  # Options: logistic_regression, random_forest, xgboost, lightgbm
```

Then retrain:
```bash
python scripts/train.py --track-mlflow
```

### Hyperparameter Tuning

Enable in config:
```yaml
hyperparameter_tuning:
  enabled: true
  method: "optuna"
  n_trials: 50
```

### Handle Imbalanced Data

Edit config:
```yaml
training:
  class_balance:
    method: "smote"  # Options: auto, smote, undersample, oversample, none
```

### Cross-Validation

Enable in config:
```yaml
training:
  cross_validation:
    enabled: true
    n_folds: 5
```

---

## 📁 Project Structure Overview

```
cap_model/
├── data/               # Data storage
│   ├── raw/           # Original data → Place your CSV here
│   └── processed/     # Cleaned data → Auto-generated
│
├── src/               # Source code
│   ├── config/        # Configuration files
│   ├── data/          # Data loading
│   ├── features/      # Feature engineering
│   ├── models/        # Model training
│   └── utils/         # Helper functions
│
├── scripts/           # Executable scripts
│   ├── train.py      # ← Main training script
│   └── predict.py    # ← Prediction script
│
├── notebooks/         # Jupyter notebooks for exploration
├── models/           # Trained models → Auto-generated
├── outputs/          # Plots and reports → Auto-generated
└── tests/            # Unit tests
```

---

## 🧪 Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_data/test_data_loader.py
```

---

## 🐛 Troubleshooting

### MLflow Connection Error

```bash
# Check if MLflow is running
curl http://localhost:5000/health

# Check port-forward
kubectl get pods -n recsys-training
kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000
```

### Import Errors

```bash
# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Data Not Found

```bash
# The script generates sample data automatically
# Or place your data:
cp your_data.csv data/raw/credit_applications.csv
```

### Dependencies Issues

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

---

## 📚 Next Steps

### 1. Improve Model Performance
- Try different models in config
- Enable hyperparameter tuning
- Add more features
- Handle class imbalance

### 2. Explore Data
- Open `notebooks/01_eda.ipynb`
- Understand feature distributions
- Identify important features

### 3. Deploy Model
- See `/docs` for deployment guides
- Build prediction API
- Deploy to Kubernetes

### 4. Monitor Performance
- Track predictions over time
- Monitor model drift
- Retrain regularly

---

## 💡 Example Workflow

```bash
# 1. Setup (one time)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Explore data
jupyter notebook notebooks/01_eda.ipynb

# 3. Train baseline model
python scripts/train.py --track-mlflow

# 4. Try different models
# Edit config.yaml: model.type = "random_forest"
python scripts/train.py --track-mlflow --run-name "random-forest-v1"

# Edit config.yaml: model.type = "xgboost"
python scripts/train.py --track-mlflow --run-name "xgboost-v1"

# 5. Compare in MLflow UI
# Open http://localhost:5000
# Select runs → Compare → Choose best model

# 6. Make predictions
python scripts/predict.py --mode batch --input-file data/raw/new_apps.csv
```

---

## 🎓 Learning Resources

### Internal Documentation
- `/docs/05_MLflow_Model_Development.md` - Comprehensive MLflow guide
- `/docs/03_Helm_Deployment.md` - Infrastructure setup
- `cap_model/README.md` - Detailed project documentation

### External Resources
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)

---

## ✅ Success Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] MLflow accessible at http://localhost:5000
- [ ] First model trained successfully
- [ ] Results visible in MLflow UI
- [ ] Can make predictions
- [ ] Understand project structure

---

## 🎉 You're Ready!

You now have a complete ML development environment for card approval prediction!

**Need help?** Check:
1. This guide for common tasks
2. `README.md` for detailed documentation
3. `/docs/05_MLflow_Model_Development.md` for MLflow specifics

**Happy modeling! 🚀**
