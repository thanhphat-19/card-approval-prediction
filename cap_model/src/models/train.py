"""
Model training module
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import mlflow
import pandas as pd
from loguru import logger
from src.utils.metrics import calculate_metrics
from src.utils.model_configs import get_model_configs


class ModelTrainer:
    """Handle model training and comparison"""

    def __init__(
        self,
        tracking_uri: str = "http://127.0.0.1:5000",
        experiment_name: str = "credit_card_approval_model_training",
    ):
        """
        Initialize ModelTrainer

        Args:
            tracking_uri: MLflow tracking URI
            experiment_name: MLflow experiment name
        """
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.trained_models = {}
        self.results = []

        # Setup MLflow
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)

        logger.info(f"MLflow tracking URI: {tracking_uri}")
        logger.info(f"Experiment: {experiment_name}")

    def get_model_configs(self) -> Dict:
        """Get model configurations from utils"""
        return get_model_configs()

    def train_single_model(
        self,
        model_name: str,
        model_class,
        params: Dict,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict:
        """
        Train a single model and log to MLflow

        Args:
            model_name: Name of the model
            model_class: Model class
            params: Model parameters
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target

        Returns:
            Dictionary containing model and metrics
        """
        logger.info("=" * 80)
        logger.info(f"Training: {model_name}")
        logger.info("=" * 80)

        # Create fresh model instance
        model = model_class(**params)
        logger.info(f"Created fresh {model_name} instance")

        # Start MLflow run
        with mlflow.start_run(run_name=model_name):
            # Log model parameters
            mlflow.log_param("model_type", model_name)
            mlflow.log_params(model.get_params())

            # Train model
            start_time = time.time()
            model.fit(X_train, y_train)
            training_time = time.time() - start_time

            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

            # Calculate metrics
            metrics_dict = calculate_metrics(y_test, y_pred, y_pred_proba)
            accuracy = metrics_dict["accuracy"]
            precision = metrics_dict["precision"]
            recall = metrics_dict["recall"]
            f1 = metrics_dict["f1_score"]
            roc_auc = metrics_dict.get("roc_auc")

            # Log metrics to MLflow
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("recall", recall)
            mlflow.log_metric("f1_score", f1)
            if roc_auc is not None:
                mlflow.log_metric("roc_auc", roc_auc)
            mlflow.log_metric("training_time", training_time)

            # Log model
            try:
                if "XGBoost" in model_name:
                    mlflow.xgboost.log_model(model, artifact_path="model")
                elif "LightGBM" in model_name:
                    mlflow.lightgbm.log_model(model, artifact_path="model")
                elif "CatBoost" in model_name:
                    mlflow.catboost.log_model(model, artifact_path="model")
                else:
                    mlflow.sklearn.log_model(model, artifact_path="model")
            except Exception as e:
                logger.warning(f"Could not log model to MLflow: {e}")

            # Print results
            logger.info("\nResults:")
            logger.info(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
            logger.info(f"  Precision: {precision:.4f} ({precision*100:.2f}%)")
            logger.info(f"  Recall:    {recall:.4f} ({recall*100:.2f}%)")
            logger.info(f"  F1-Score:  {f1:.4f}")
            if roc_auc is not None:
                logger.info(f"  ROC-AUC:   {roc_auc:.4f}")
            logger.info(f"  Training Time: {training_time:.2f}s")

            # Store results
            result = {
                "Model": model_name,
                "Accuracy": accuracy,
                "Precision": precision,
                "Recall": recall,
                "F1-Score": f1,
                "ROC-AUC": roc_auc,
                "Training Time (s)": training_time,
                "model_object": model,
            }

            logger.info(f"✓ {model_name} training completed")

            return result

    def train_all_models(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        models: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Train multiple models and compare results

        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            models: List of model names to train (None = all models)

        Returns:
            DataFrame with comparison results
        """
        logger.info("=" * 80)
        logger.info("TRAINING MODELS")
        logger.info("=" * 80)

        model_configs = self.get_model_configs()

        # Filter models if specified
        if models:
            model_configs = {k: v for k, v in model_configs.items() if k in models}

        self.results = []
        self.trained_models = {}

        for model_name, config in model_configs.items():
            result = self.train_single_model(
                model_name,
                config["class"],
                config["params"],
                X_train,
                y_train,
                X_test,
                y_test,
            )

            self.results.append(result)
            self.trained_models[model_name] = result["model_object"]

        logger.info("=" * 80)
        logger.info("ALL MODELS TRAINED")
        logger.info("=" * 80)

        # Create results dataframe
        results_df = pd.DataFrame([{k: v for k, v in r.items() if k != "model_object"} for r in self.results])
        results_df = results_df.sort_values("F1-Score", ascending=False)

        return results_df

    def get_best_model(self, metric: str = "F1-Score") -> Tuple[str, object, Dict]:
        """
        Get best model based on metric

        Args:
            metric: Metric to use for selection

        Returns:
            Tuple of (model_name, model_object, metrics_dict)
        """
        if not self.results:
            raise ValueError("No models trained yet. Call train_all_models first.")

        # Find best model
        best_result = max(self.results, key=lambda x: x[metric])
        best_model_name = best_result["Model"]
        best_model = best_result["model_object"]

        # Extract metrics
        metrics = {k: v for k, v in best_result.items() if k not in ["Model", "model_object"]}

        logger.info("=" * 80)
        logger.info("BEST MODEL SELECTION")
        logger.info("=" * 80)
        logger.info(f"\n🏆 Best Model: {best_model_name}")
        logger.info("\nPerformance Metrics:")
        for key, value in metrics.items():
            if pd.notna(value):
                logger.info(f"  {key}: {value:.4f}")

        return best_model_name, best_model, metrics

    def save_best_model(self, output_dir: str, metric: str = "F1-Score"):
        """
        Save best model and metadata

        Args:
            output_dir: Directory to save model
            metric: Metric to use for selection
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get best model
        best_model_name, best_model, metrics = self.get_best_model(metric)

        # Store for later access
        self.best_model_name = best_model_name
        self.best_score = metrics.get(metric, 0)

        # Save model
        model_filename = f'best_model_{best_model_name.replace(" ", "_").lower()}.pkl'
        model_path = output_path / model_filename
        joblib.dump(best_model, model_path)
        logger.info(f"✓ Best model saved to: {model_path}")

        # Save metadata
        metadata = {
            "model_name": best_model_name,
            "metrics": metrics,
            "trained_on": pd.Timestamp.now().isoformat(),
            "selection_metric": metric,
        }

        metadata_path = output_path / "best_model_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Model metadata saved to: {metadata_path}")

        return model_path, metadata_path

    def save_comparison_results(self, output_dir: str):
        """
        Save model comparison results

        Args:
            output_dir: Directory to save results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create results dataframe
        results_df = pd.DataFrame([{k: v for k, v in r.items() if k != "model_object"} for r in self.results])
        results_df = results_df.sort_values("F1-Score", ascending=False)

        # Save to CSV
        results_path = output_path / "model_comparison.csv"
        results_df.to_csv(results_path, index=False)
        logger.info(f"✓ Comparison results saved to: {results_path}")

        return results_path

    def create_training_summary(self, X_train: pd.DataFrame, X_test: pd.DataFrame, output_dir: str) -> str:
        """
        Create and save training summary

        Args:
            X_train: Training features
            X_test: Test features
            output_dir: Directory to save summary

        Returns:
            Path to summary file
        """
        output_path = Path(output_dir)

        # Get best model info
        best_model_name, _, metrics = self.get_best_model()

        # Create summary text
        roc_auc_value = metrics.get("ROC-AUC")
        roc_auc_str = f"{roc_auc_value:.4f}" if pd.notna(roc_auc_value) else "N/A"

        summary_text = f"""
MODEL TRAINING COMPLETED

Models Trained: {len(self.results)}
  {', '.join([r['Model'] for r in self.results])}

Best Model: {best_model_name}
  - Accuracy:  {metrics['Accuracy']:.4f}
  - Precision: {metrics['Precision']:.4f}
  - Recall:    {metrics['Recall']:.4f}
  - F1-Score:  {metrics['F1-Score']:.4f}
  - ROC-AUC:   {roc_auc_str}

Training Data:
  - Training samples: {len(X_train):,}
  - Test samples: {len(X_test):,}
  - Features: {X_train.shape[1]}

Saved Artifacts:
  - Best model: {output_path / f'best_model_{best_model_name.replace(" ", "_").lower()}.pkl'}
  - Model metadata: {output_path / 'best_model_metadata.json'}
  - Comparison results: {output_path / 'model_comparison.csv'}
  - All models logged to MLflow

✅ Ready for model evaluation!
"""

        # Save summary
        summary_path = output_path / "training_summary.txt"
        with open(summary_path, "w") as f:
            f.write(summary_text)

        logger.info(f"✓ Summary saved to {summary_path}")

        return str(summary_path)
