"""
Model evaluation module
"""

import json
from pathlib import Path
from typing import Dict, Optional

import joblib
import pandas as pd
from loguru import logger
from src.utils.metrics import calculate_metrics, get_classification_report
from src.utils.plotting import plot_confusion_matrix, plot_precision_recall_curve, plot_roc_curve


class ModelEvaluator:
    """Handle model evaluation and visualization"""

    def __init__(self):
        """Initialize ModelEvaluator"""
        self.metrics = {}
        self.predictions = {}

    def evaluate_model(
        self,
        model,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        output_dir: Optional[str] = None,
        save_plots: bool = True,
    ) -> Dict:
        """
        Complete model evaluation pipeline

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            output_dir: Directory to save outputs (optional)
            save_plots: Whether to save plots

        Returns:
            Dictionary of evaluation results
        """
        logger.info("=" * 80)
        logger.info("MODEL EVALUATION")
        logger.info("=" * 80)

        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

        self.predictions = {
            "y_true": y_test,
            "y_pred": y_pred,
            "y_pred_proba": y_pred_proba,
        }

        # Calculate metrics
        metrics = calculate_metrics(y_test, y_pred, y_pred_proba)
        self.metrics = metrics

        logger.info("=" * 80)
        logger.info("EVALUATION METRICS")
        logger.info("=" * 80)
        for key, value in metrics.items():
            logger.info(f"  {key}: {value:.4f}")

        # Classification report
        report = get_classification_report(y_test, y_pred)
        logger.info("=" * 80)
        logger.info("CLASSIFICATION REPORT")
        logger.info("=" * 80)
        logger.info(f"\n{report}")

        # Create output directory if needed
        if save_plots and output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Plot confusion matrix
            plot_confusion_matrix(y_test, y_pred, save_path=output_path / "confusion_matrix.png")

            # Plot ROC curve
            if y_pred_proba is not None:
                plot_roc_curve(y_test, y_pred_proba, save_path=output_path / "roc_curve.png")

                # Plot Precision-Recall curve
                plot_precision_recall_curve(
                    y_test,
                    y_pred_proba,
                    save_path=output_path / "precision_recall_curve.png",
                )

            # Save classification report
            report_path = output_path / "classification_report.txt"
            with open(report_path, "w") as f:
                f.write(report)
            logger.info(f"✓ Classification report saved to {report_path}")

            # Save metrics
            metrics_path = output_path / "evaluation_metrics.json"
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"✓ Metrics saved to {metrics_path}")

        logger.info("=" * 80)
        logger.info("EVALUATION COMPLETED")
        logger.info("=" * 80)

        return {
            "metrics": metrics,
            "classification_report": report,
            "predictions": self.predictions,
        }

    def load_and_evaluate_model(
        self,
        model_path: str,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        output_dir: Optional[str] = None,
    ) -> Dict:
        """
        Load model from disk and evaluate

        Args:
            model_path: Path to saved model
            X_test: Test features
            y_test: Test labels
            output_dir: Directory to save outputs (optional)

        Returns:
            Dictionary of evaluation results
        """
        logger.info(f"Loading model from {model_path}")
        model = joblib.load(model_path)

        return self.evaluate_model(model, X_test, y_test, output_dir)

    def compare_models(self, models: Dict, X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
        """Compare multiple models"""
        logger.info("=" * 80)
        logger.info("COMPARING MODELS")
        logger.info("=" * 80)

        results = []
        for model_name, model in models.items():
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

            metrics_dict = calculate_metrics(y_test, y_pred, y_pred_proba)
            metrics_dict["Model"] = model_name
            results.append(metrics_dict)

            logger.info(f"\n{model_name}:")
            for key, value in metrics_dict.items():
                if key != "Model" and pd.notna(value):
                    logger.info(f"  {key}: {value:.4f}")

        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values("f1_score", ascending=False)

        logger.info("=" * 80)
        logger.info("COMPARISON COMPLETED")
        logger.info("=" * 80)

        return results_df
