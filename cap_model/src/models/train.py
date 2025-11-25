"""
Model training module
"""

from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier


class ModelTrainer:
    """Train and manage classification models"""

    def __init__(self, config: dict):
        """
        Initialize ModelTrainer

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.model = None
        self.model_type = config["model"]["type"]

    def get_model(self) -> Any:
        """
        Initialize model based on configuration

        Returns:
            Initialized model
        """
        model_type = self.model_type
        params = self.config["model"]["hyperparameters"].get(model_type, {})

        print(f"\n{'='*60}")
        print(f"INITIALIZING {model_type.upper()} MODEL")
        print(f"{'='*60}")
        print(f"Parameters: {params}")

        if model_type == "logistic_regression":
            model = LogisticRegression(**params, random_state=42)

        elif model_type == "random_forest":
            model = RandomForestClassifier(**params, random_state=42)

        elif model_type == "xgboost":
            model = XGBClassifier(**params, random_state=42, use_label_encoder=False)

        elif model_type == "lightgbm":
            model = LGBMClassifier(**params, random_state=42, verbose=-1)

        else:
            raise ValueError(f"Unknown model type: {model_type}")

        return model

    def handle_class_imbalance(
        self, X: np.ndarray, y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Handle class imbalance in training data

        Args:
            X: Feature matrix
            y: Target vector

        Returns:
            Tuple of (X_resampled, y_resampled)
        """
        method = self.config["training"]["class_balance"]["method"]

        unique, counts = np.unique(y, return_counts=True)
        print(f"\nOriginal class distribution: {dict(zip(unique, counts))}")

        if method == "none":
            return X, y

        elif method == "smote":
            print("Applying SMOTE oversampling...")
            smote = SMOTE(random_state=42)
            X, y = smote.fit_resample(X, y)

        elif method == "undersample":
            print("Applying random undersampling...")
            rus = RandomUnderSampler(random_state=42)
            X, y = rus.fit_resample(X, y)

        elif method == "oversample":
            # Simple random oversampling of minority class
            from imblearn.over_sampling import RandomOverSampler

            ros = RandomOverSampler(random_state=42)
            X, y = ros.fit_resample(X, y)

        unique, counts = np.unique(y, return_counts=True)
        print(f"Resampled class distribution: {dict(zip(unique, counts))}")

        return X, y

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None,
    ) -> Any:
        """
        Train the model

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)

        Returns:
            Trained model
        """
        print(f"\n{'='*60}")
        print("TRAINING MODEL")
        print(f"{'='*60}")

        # Handle class imbalance
        X_train, y_train = self.handle_class_imbalance(X_train, y_train)

        # Initialize model
        self.model = self.get_model()

        # Train with cross-validation if enabled
        if self.config["training"]["cross_validation"]["enabled"]:
            self._train_with_cv(X_train, y_train)

        # Train on full training set
        print("\nTraining on full training set...")

        if self.model_type == "xgboost" and X_val is not None:
            # Use early stopping for XGBoost
            eval_set = [(X_train, y_train), (X_val, y_val)]
            self.model.fit(
                X_train,
                y_train,
                eval_set=eval_set,
                eval_metric="logloss",
                verbose=False,
            )
        else:
            self.model.fit(X_train, y_train)

        print("✓ Training complete")

        return self.model

    def _train_with_cv(self, X: np.ndarray, y: np.ndarray):
        """
        Perform cross-validation

        Args:
            X: Feature matrix
            y: Target vector
        """
        cv_config = self.config["training"]["cross_validation"]
        n_folds = cv_config["n_folds"]

        print(f"\nPerforming {n_folds}-fold cross-validation...")

        cv_scores = cross_val_score(
            self.model, X, y, cv=n_folds, scoring="roc_auc", n_jobs=-1
        )

        print(f"Cross-validation scores: {cv_scores}")
        print(f"Mean CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Log to MLflow if enabled
        if mlflow.active_run():
            mlflow.log_metric("cv_mean_auc", cv_scores.mean())
            mlflow.log_metric("cv_std_auc", cv_scores.std())

    def save_model(self, output_dir: str = "models/"):
        """
        Save trained model

        Args:
            output_dir: Output directory path
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")

        output_path = Path(output_dir) / self.model_type
        output_path.mkdir(parents=True, exist_ok=True)

        model_path = output_path / "model.pkl"
        joblib.dump(self.model, model_path)

        print(f"\n✓ Model saved to {model_path}")

        return str(model_path)

    def load_model(self, model_path: str):
        """
        Load trained model

        Args:
            model_path: Path to model file
        """
        self.model = joblib.load(model_path)
        print(f"✓ Model loaded from {model_path}")

        return self.model

    def get_feature_importance(self, feature_names: list) -> Dict[str, float]:
        """
        Get feature importance scores

        Args:
            feature_names: List of feature names

        Returns:
            Dictionary of feature importances
        """
        if self.model is None:
            raise ValueError("No model available. Train a model first.")

        # Get importances based on model type
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            importances = np.abs(self.model.coef_[0])
        else:
            return {}

        # Create sorted dictionary
        feature_importance = dict(zip(feature_names, importances))
        feature_importance = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )

        return feature_importance


def train_with_mlflow(
    config: dict,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list,
    run_name: str = None,
) -> Any:
    """
    Train model with MLflow tracking

    Args:
        config: Configuration dictionary
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        feature_names: List of feature names
        run_name: MLflow run name

    Returns:
        Trained model
    """
    # Set MLflow tracking
    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    # Start MLflow run
    with mlflow.start_run(run_name=run_name):
        # Log parameters
        if config["mlflow"]["log_params"]:
            mlflow.log_params(
                config["model"]["hyperparameters"][config["model"]["type"]]
            )
            mlflow.log_param("model_type", config["model"]["type"])
            mlflow.log_param("n_features", X_train.shape[1])
            mlflow.log_param("n_train_samples", X_train.shape[0])

        # Initialize trainer
        trainer = ModelTrainer(config)

        # Train model
        model = trainer.train(X_train, y_train, X_val, y_val)

        # Log model
        if config["mlflow"]["log_model"]:
            if config["model"]["type"] == "xgboost":
                mlflow.xgboost.log_model(model, "model")
            else:
                mlflow.sklearn.log_model(model, "model")

        # Save model locally
        model_path = trainer.save_model()

        # Log feature importance
        if config["mlflow"]["save_feature_importance"]:
            feature_importance = trainer.get_feature_importance(feature_names)
            if feature_importance:
                mlflow.log_dict(feature_importance, "feature_importance.json")

        print(f"\n✓ MLflow run completed")
        print(f"  Run ID: {mlflow.active_run().info.run_id}")
        print(f"  View at: {config['mlflow']['tracking_uri']}")

        return model
