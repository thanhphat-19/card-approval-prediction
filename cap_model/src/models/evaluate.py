"""
Model evaluation module
"""

from pathlib import Path
from typing import Any, Dict, Tuple

import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


class ModelEvaluator:
    """Evaluate classification model performance"""

    def __init__(self, config: dict):
        """
        Initialize ModelEvaluator

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.metrics = {}

    def evaluate(
        self, model: Any, X: np.ndarray, y: np.ndarray, dataset_name: str = "test"
    ) -> Dict[str, float]:
        """
        Evaluate model performance

        Args:
            model: Trained model
            X: Feature matrix
            y: True labels
            dataset_name: Name of dataset (train/val/test)

        Returns:
            Dictionary of metrics
        """
        print(f"\n{'='*60}")
        print(f"EVALUATING MODEL ON {dataset_name.upper()} SET")
        print(f"{'='*60}")

        # Get predictions
        y_pred = model.predict(X)
        y_pred_proba = (
            model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else y_pred
        )

        # Calculate metrics
        metrics = {
            f"{dataset_name}_accuracy": accuracy_score(y, y_pred),
            f"{dataset_name}_precision": precision_score(y, y_pred, zero_division=0),
            f"{dataset_name}_recall": recall_score(y, y_pred, zero_division=0),
            f"{dataset_name}_f1_score": f1_score(y, y_pred, zero_division=0),
        }

        # Add ROC-AUC if probabilities available
        if hasattr(model, "predict_proba"):
            metrics[f"{dataset_name}_roc_auc"] = roc_auc_score(y, y_pred_proba)

        # Print metrics
        print("\nMetrics:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.4f}")

        # Store for later use
        self.metrics.update(metrics)

        # Log to MLflow if enabled
        if mlflow.active_run() and self.config["mlflow"]["log_metrics"]:
            mlflow.log_metrics(metrics)

        return metrics

    def print_classification_report(
        self, model: Any, X: np.ndarray, y: np.ndarray, target_names: list = None
    ):
        """
        Print detailed classification report

        Args:
            model: Trained model
            X: Feature matrix
            y: True labels
            target_names: Names of target classes
        """
        y_pred = model.predict(X)

        if target_names is None:
            target_names = ["Rejected", "Approved"]

        print("\nClassification Report:")
        print("=" * 60)
        print(classification_report(y, y_pred, target_names=target_names))

    def plot_confusion_matrix(
        self, model: Any, X: np.ndarray, y: np.ndarray, save_path: str = None
    ) -> plt.Figure:
        """
        Plot confusion matrix

        Args:
            model: Trained model
            X: Feature matrix
            y: True labels
            save_path: Path to save figure

        Returns:
            Matplotlib figure
        """
        y_pred = model.predict(X)
        cm = confusion_matrix(y, y_pred)

        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["Rejected", "Approved"],
            yticklabels=["Rejected", "Approved"],
            ax=ax,
        )
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title("Confusion Matrix")

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✓ Confusion matrix saved to {save_path}")

            # Log to MLflow
            if mlflow.active_run() and self.config["mlflow"]["save_confusion_matrix"]:
                mlflow.log_artifact(save_path)

        return fig

    def plot_roc_curve(
        self, model: Any, X: np.ndarray, y: np.ndarray, save_path: str = None
    ) -> plt.Figure:
        """
        Plot ROC curve

        Args:
            model: Trained model
            X: Feature matrix
            y: True labels
            save_path: Path to save figure

        Returns:
            Matplotlib figure
        """
        if not hasattr(model, "predict_proba"):
            print("Model does not support probability predictions")
            return None

        y_pred_proba = model.predict_proba(X)[:, 1]
        fpr, tpr, thresholds = roc_curve(y, y_pred_proba)
        roc_auc = roc_auc_score(y, y_pred_proba)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(
            fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.3f})"
        )
        ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("Receiver Operating Characteristic (ROC) Curve")
        ax.legend(loc="lower right")
        ax.grid(alpha=0.3)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✓ ROC curve saved to {save_path}")

            # Log to MLflow
            if mlflow.active_run() and self.config["mlflow"]["save_roc_curve"]:
                mlflow.log_artifact(save_path)

        return fig

    def plot_precision_recall_curve(
        self, model: Any, X: np.ndarray, y: np.ndarray, save_path: str = None
    ) -> plt.Figure:
        """
        Plot Precision-Recall curve

        Args:
            model: Trained model
            X: Feature matrix
            y: True labels
            save_path: Path to save figure

        Returns:
            Matplotlib figure
        """
        if not hasattr(model, "predict_proba"):
            print("Model does not support probability predictions")
            return None

        y_pred_proba = model.predict_proba(X)[:, 1]
        precision, recall, thresholds = precision_recall_curve(y, y_pred_proba)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(recall, precision, color="darkorange", lw=2)
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title("Precision-Recall Curve")
        ax.grid(alpha=0.3)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✓ Precision-Recall curve saved to {save_path}")

        return fig

    def plot_feature_importance(
        self, model: Any, feature_names: list, top_n: int = 20, save_path: str = None
    ) -> plt.Figure:
        """
        Plot feature importance

        Args:
            model: Trained model
            feature_names: List of feature names
            top_n: Number of top features to show
            save_path: Path to save figure

        Returns:
            Matplotlib figure
        """
        # Get feature importance
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_[0])
        else:
            print("Model does not have feature importance")
            return None

        # Create DataFrame
        feature_imp = (
            pd.DataFrame({"feature": feature_names, "importance": importances})
            .sort_values("importance", ascending=False)
            .head(top_n)
        )

        # Plot
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.barplot(data=feature_imp, y="feature", x="importance", ax=ax)
        ax.set_title(f"Top {top_n} Feature Importances")
        ax.set_xlabel("Importance")
        ax.set_ylabel("Feature")

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✓ Feature importance plot saved to {save_path}")

            # Log to MLflow
            if mlflow.active_run() and self.config["mlflow"]["save_feature_importance"]:
                mlflow.log_artifact(save_path)

        return fig

    def generate_evaluation_report(
        self,
        model: Any,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: list,
        output_dir: str = "outputs/",
    ):
        """
        Generate complete evaluation report with all plots and metrics

        Args:
            model: Trained model
            X_train, y_train: Training data
            X_val, y_val: Validation data
            X_test, y_test: Test data
            feature_names: List of feature names
            output_dir: Output directory for plots
        """
        print(f"\n{'='*60}")
        print("GENERATING EVALUATION REPORT")
        print(f"{'='*60}")

        output_path = Path(output_dir)
        figures_path = output_path / "figures"
        figures_path.mkdir(parents=True, exist_ok=True)

        # Evaluate on all sets
        self.evaluate(model, X_train, y_train, "train")
        self.evaluate(model, X_val, y_val, "val")
        self.evaluate(model, X_test, y_test, "test")

        # Print classification report
        print("\n" + "=" * 60)
        print("TEST SET CLASSIFICATION REPORT")
        print("=" * 60)
        self.print_classification_report(model, X_test, y_test)

        # Generate plots
        print("\nGenerating visualizations...")

        self.plot_confusion_matrix(
            model, X_test, y_test, save_path=str(figures_path / "confusion_matrix.png")
        )

        self.plot_roc_curve(
            model, X_test, y_test, save_path=str(figures_path / "roc_curve.png")
        )

        self.plot_precision_recall_curve(
            model,
            X_test,
            y_test,
            save_path=str(figures_path / "precision_recall_curve.png"),
        )

        self.plot_feature_importance(
            model, feature_names, save_path=str(figures_path / "feature_importance.png")
        )

        plt.close("all")  # Close all figures

        # Save metrics to file
        metrics_path = output_path / "metrics"
        metrics_path.mkdir(parents=True, exist_ok=True)

        metrics_df = pd.DataFrame([self.metrics])
        metrics_df.to_csv(metrics_path / "metrics.csv", index=False)

        print(f"\n✓ Evaluation report generated in {output_path}")
        print(f"  - Figures: {figures_path}")
        print(f"  - Metrics: {metrics_path}")

        return self.metrics
