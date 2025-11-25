# Card Approval Prediction - Complete Folder Structure

This document shows the complete folder structure created for model development.

---

## 📁 Complete Directory Tree

```
cap_model/
│
├── 📄 README.md                          # Main project documentation
├── 📄 QUICKSTART.md                      # Quick start guide (START HERE!)
├── 📄 STRUCTURE.md                       # This file
├── 📄 requirements.txt                   # Python dependencies
├── 📄 setup.py                           # Package installation
├── 📄 .env.example                       # Environment variables template
├── 📄 .gitignore                         # Git ignore rules
│
├── 📂 data/                              # Data storage
│   ├── 📂 raw/                          # Original, immutable data
│   │   ├── .gitkeep
│   │   └── credit_applications.csv      # Your data goes here
│   ├── 📂 processed/                    # Cleaned data (auto-generated)
│   │   ├── .gitkeep
│   │   ├── train.csv
│   │   ├── val.csv
│   │   └── test.csv
│   ├── 📂 features/                     # Feature engineering outputs
│   └── 📂 external/                     # External datasets
│
├── 📂 src/                               # Source code (main package)
│   ├── __init__.py
│   │
│   ├── 📂 config/                       # Configuration files
│   │   └── config.yaml                  # Main configuration
│   │
│   ├── 📂 data/                         # Data loading & processing
│   │   ├── __init__.py
│   │   └── data_loader.py               # DataLoader class
│   │
│   ├── 📂 features/                     # Feature engineering
│   │   ├── __init__.py
│   │   └── feature_engineering.py       # FeatureEngineer class
│   │
│   ├── 📂 models/                       # Model training & evaluation
│   │   ├── __init__.py
│   │   ├── train.py                     # ModelTrainer class
│   │   └── evaluate.py                  # ModelEvaluator class
│   │
│   └── 📂 utils/                        # Utility functions
│       ├── __init__.py
│       └── helpers.py                   # Helper functions
│
├── 📂 scripts/                           # Executable scripts
│   ├── train.py                         # 🚀 Main training script
│   └── predict.py                       # 🔮 Prediction script
│
├── 📂 notebooks/                         # Jupyter notebooks
│   ├── 01_eda.ipynb                     # Exploratory Data Analysis
│   ├── 02_feature_engineering.ipynb     # Feature engineering
│   ├── 03_baseline_models.ipynb         # Baseline models
│   └── 04_model_comparison.ipynb        # Model comparison
│
├── 📂 models/                            # Trained models (auto-generated)
│   ├── .gitkeep
│   ├── 📂 baseline/                     # Baseline models
│   ├── 📂 experimental/                 # Experimental models
│   ├── 📂 production/                   # Production models
│   ├── 📂 preprocessors/                # Feature preprocessors
│   │   ├── scaler.pkl
│   │   ├── imputer_numerical.pkl
│   │   ├── imputer_categorical.pkl
│   │   └── feature_names.pkl
│   └── 📂 xgboost/                      # XGBoost specific
│       └── model.pkl
│
├── 📂 outputs/                           # Training outputs (auto-generated)
│   ├── 📂 figures/                      # Plots and visualizations
│   │   ├── confusion_matrix.png
│   │   ├── roc_curve.png
│   │   ├── precision_recall_curve.png
│   │   └── feature_importance.png
│   ├── 📂 reports/                      # Analysis reports
│   └── 📂 metrics/                      # Evaluation metrics
│       └── metrics.csv
│
├── 📂 experiments/                       # Experiment tracking
│   └── 📂 configs/                      # Experiment configurations
│       ├── baseline.yaml
│       ├── xgboost.yaml
│       └── neural_net.yaml
│
└── 📂 tests/                             # Unit and integration tests
    └── 📂 test_data/
        └── test_data_loader.py          # Data loader tests
```

---

## 🎯 Key Files Explained

### **Configuration**
- **`src/config/config.yaml`** - Central configuration file
  - Data paths and split ratios
  - Feature definitions
  - Model hyperparameters
  - MLflow settings
  - Training options

### **Core Modules**

#### Data (`src/data/`)
- **`data_loader.py`** - Load and split data
  - `DataLoader` class
  - `load_sample_data()` function
  - Data validation

#### Features (`src/features/`)
- **`feature_engineering.py`** - Feature preprocessing
  - `FeatureEngineer` class
  - Handle missing values
  - Create derived features
  - Encode categorical variables
  - Scale numerical features

#### Models (`src/models/`)
- **`train.py`** - Model training
  - `ModelTrainer` class
  - Cross-validation
  - Class imbalance handling
  - MLflow integration

- **`evaluate.py`** - Model evaluation
  - `ModelEvaluator` class
  - Calculate metrics
  - Generate plots
  - Classification reports

#### Utils (`src/utils/`)
- **`helpers.py`** - Utility functions
  - Config loading
  - Logging setup
  - Threshold optimization
  - Data summaries

### **Executable Scripts**

- **`scripts/train.py`** - Main training pipeline
  ```bash
  python scripts/train.py --track-mlflow
  ```
  - Loads data
  - Preprocesses features
  - Trains model
  - Evaluates performance
  - Saves artifacts

- **`scripts/predict.py`** - Make predictions
  ```bash
  python scripts/predict.py --mode single
  python scripts/predict.py --mode batch --input-file data.csv
  ```
  - Single prediction
  - Batch predictions
  - Load trained model

### **Notebooks**

- **`01_eda.ipynb`** - Explore your data
- **`02_feature_engineering.ipynb`** - Feature analysis
- **`03_baseline_models.ipynb`** - Quick model comparison
- **`04_model_comparison.ipynb`** - Advanced model selection

---

## 🚀 Usage Flow

### 1. **First Time Setup**
```bash
cd cap_model
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. **Train Model**
```bash
# With sample data (automatic)
python scripts/train.py --track-mlflow

# With your data
cp your_data.csv data/raw/credit_applications.csv
python scripts/train.py --track-mlflow
```

### 3. **View Results**
```bash
# MLflow UI
http://localhost:5000
```

### 4. **Make Predictions**
```bash
python scripts/predict.py --mode single
```

---

## 📦 What Gets Generated

### During Training:
```
data/processed/
├── train.csv
├── val.csv
└── test.csv

models/
├── preprocessors/
│   ├── scaler.pkl
│   ├── imputer_numerical.pkl
│   └── feature_names.pkl
└── xgboost/
    └── model.pkl

outputs/
├── figures/
│   ├── confusion_matrix.png
│   ├── roc_curve.png
│   └── feature_importance.png
└── metrics/
    └── metrics.csv
```

### In MLflow:
- All parameters
- All metrics
- All plots as artifacts
- Trained model

---

## 🔧 Customization

### Change Model Type
Edit `src/config/config.yaml`:
```yaml
model:
  type: "xgboost"  # or logistic_regression, random_forest, lightgbm
```

### Add New Features
Edit `src/features/feature_engineering.py`:
```python
def _create_derived_features(self, df):
    # Add your feature engineering logic
    df['new_feature'] = ...
    return df
```

### Add New Model
1. Add model type in `src/models/train.py`
2. Add hyperparameters in `src/config/config.yaml`

---

## 📊 Outputs Explained

### **Confusion Matrix**
Shows true positives, false positives, true negatives, false negatives

### **ROC Curve**
Shows model's ability to discriminate between classes

### **Feature Importance**
Shows which features matter most for predictions

### **Metrics CSV**
Contains all numeric metrics for easy comparison

---

## 🎓 Best Practices

### ✅ Do:
- Use version control for code (Git)
- Track experiments with MLflow
- Keep data separate from code
- Write tests for critical functions
- Document your findings in notebooks

### ❌ Don't:
- Commit large data files
- Commit trained models (unless necessary)
- Hardcode passwords or API keys
- Skip data validation
- Train without tracking

---

## 🐛 Troubleshooting

### Cannot import modules
```bash
pip install -e .
# or
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### MLflow not accessible
```bash
kubectl port-forward -n recsys-training svc/recsys-training-mlflow 5000:5000
```

### Out of memory
- Reduce batch size in config
- Use smaller dataset for testing
- Close other applications

---

## 📚 Documentation

- **QUICKSTART.md** - Get started in 5 minutes
- **README.md** - Comprehensive documentation
- **This file** - Structure reference

---

## ✅ Checklist

Setup:
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] MLflow accessible
- [ ] Data placed in `data/raw/`

Development:
- [ ] Explored data with notebook
- [ ] Trained baseline model
- [ ] Compared models in MLflow
- [ ] Selected best model
- [ ] Tested predictions

Production:
- [ ] Model saved
- [ ] Documentation updated
- [ ] Tests written
- [ ] Ready for deployment

---

**You now have a complete, production-ready ML development environment!** 🎉

For questions, see:
- `QUICKSTART.md` for quick tasks
- `README.md` for detailed info
- `/docs/05_MLflow_Model_Development.md` for MLflow guide
