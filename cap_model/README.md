# Card Approval Model - Training Pipeline

This folder contains the ML model training pipeline for credit card approval prediction.

## 📁 Structure

```
cap_model/
├── data/               # Data storage
│   ├── raw/           # Raw application and credit records
│   └── processed/     # Processed data + preprocessing artifacts
├── notebooks/         # Jupyter notebooks for experimentation
├── scripts/           # Training automation scripts
├── src/               # Source code modules
│   ├── data/         # Data loading
│   ├── features/     # Feature engineering
│   ├── models/       # Model training
│   └── utils/        # Utility functions
└── models/           # Trained model artifacts
```

## 🚀 Quick Start

### 1. **Create Kaggle Confidential**

```bash
mkdir ~/.kaggle
chmod 600 ~/.kaggle
```

### 2. **Download Data**
```bash
cd cap_model
python scripts/download_data.py
```

### 2. **Run Data Preprocessing**
```bash
# Basic preprocessing
python scripts/run_preprocessing.py

# Custom settings
python scripts/run_preprocessing.py \
  --raw-data-dir data/raw \
  --output-dir data/processed \
  --test-size 0.2 \
  --pca-components 5
```

**Output:**
- `data/processed/X_train.csv`
- `data/processed/X_test.csv`
- `data/processed/y_train.csv`
- `data/processed/y_test.csv`
- `data/processed/scaler.pkl`
- `data/processed/pca.pkl`
- `data/processed/feature_names.json`

### 3. **Train Models**
```bash
# Train all models with auto-registration
python scripts/run_training.py

# Train specific model
python scripts/run_training.py --models XGBoost

# Train without auto-registration
python scripts/run_training.py --no-auto-register
```

**Options:**
- `--data-dir`: Processed data directory (default: `data/processed`)
- `--output-dir`: Model output directory (default: `models`)
- `--mlflow-uri`: MLflow tracking URI (default: `http://127.0.0.1:5000`)
- `--models`: Specific models to train (choices: XGBoost, LightGBM, CatBoost, AdaBoost, NaiveBayes)
- `--metric`: Metric for best model selection (default: `F1-Score`)
- `--no-auto-register`: Disable automatic model registration to MLflow

**Output:**
- Best model saved to `models/best_model_<name>.pkl`
- Model metadata in `models/best_model_metadata.json`
- Evaluation plots in `models/evaluation/`
- Model registered to MLflow Production

### 4. **View MLflow UI**
```bash
mlflow ui --host 0.0.0.0 --port 5000
# Open: http://localhost:5000
```

## 📊 Complete Pipeline

Run the entire pipeline from scratch:

```bash
cd cap_model

# Step 1: Download data
python scripts/download_data.py

# Step 2: Preprocess
python scripts/run_preprocessing.py

# Step 3: Train and register best model
python scripts/run_training.py

# Step 4: Verify in MLflow
mlflow ui
```

## 🔍 Exploratory Data Analysis (Optional)

Run EDA to understand the data:

```bash
python scripts/run_eda.py
```

## 📝 Key Files

| File | Description |
|------|-------------|
| `scripts/run_preprocessing.py` | Data preprocessing pipeline |
| `scripts/run_training.py` | Model training with MLflow |
| `src/data/data_loader.py` | Data loading utilities |
| `src/features/feature_engineering.py` | Feature engineering |
| `src/models/train.py` | Model training logic |
| `notebooks/01_eda.ipynb` | Exploratory analysis |
| `notebooks/02_data_processing.ipynb` | Data preparation |
| `notebooks/03_model_training.ipynb` | Model experiments |

## 🎯 Model Performance

Best model (XGBoost):
- **Accuracy**: 96.7%
- **F1-Score**: 0.9667
- **ROC-AUC**: 0.9932
- **Precision**: 97.3%
- **Recall**: 96.0%

## 🛠️ Requirements

```bash
# Install dependencies
pip install -r ../requirements.txt
```

## 📌 Notes

- **Preprocessing artifacts** (scaler.pkl, pca.pkl, feature_names.json) are automatically logged to MLflow
- **Auto-registration** is enabled by default - best model goes to Production
- **Feature alignment** is critical - feature_names.json must contain 48 one-hot encoded features
- **MLflow** must be running before training: `mlflow ui --port 5000`
