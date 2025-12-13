"""
Visualization utilities
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def plot_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray, save_path: Optional[str] = None) -> plt.Figure:
    """
    Plot confusion matrix

    Args:
        y_true: True labels
        y_pred: Predicted labels
        save_path: Path to save figure (optional)

    Returns:
        Matplotlib figure
    """
    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        ax=ax,
        xticklabels=["Bad (0)", "Good (1)"],
        yticklabels=["Bad (0)", "Good (1)"],
    )
    ax.set_xlabel("Predicted", fontsize=12, fontweight="bold")
    ax.set_ylabel("Actual", fontsize=12, fontweight="bold")
    ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold", pad=15)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"✓ Confusion matrix saved to {save_path}")

    return fig


def plot_roc_curve(y_true: pd.Series, y_pred_proba: np.ndarray, save_path: Optional[str] = None) -> plt.Figure:
    """
    Plot ROC curve

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        save_path: Path to save figure (optional)

    Returns:
        Matplotlib figure
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    roc_auc = roc_auc_score(y_true, y_pred_proba)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color="#667eea", lw=3, label=f"ROC Curve (AUC = {roc_auc:.4f})")
    ax.plot([0, 1], [0, 1], color="#cccccc", lw=2, linestyle="--", label="Random Classifier")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate", fontsize=12, fontweight="bold")
    ax.set_ylabel("True Positive Rate", fontsize=12, fontweight="bold")
    ax.set_title("ROC Curve", fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="lower right", fontsize=11)
    ax.grid(alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"✓ ROC curve saved to {save_path}")

    return fig


def plot_precision_recall_curve(
    y_true: pd.Series, y_pred_proba: np.ndarray, save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot Precision-Recall curve

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        save_path: Path to save figure (optional)

    Returns:
        Matplotlib figure
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(recall, precision, color="#764ba2", lw=3, label="Precision-Recall Curve")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall", fontsize=12, fontweight="bold")
    ax.set_ylabel("Precision", fontsize=12, fontweight="bold")
    ax.set_title("Precision-Recall Curve", fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="lower left", fontsize=11)
    ax.grid(alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"✓ Precision-Recall curve saved to {save_path}")

    return fig


def plot_threshold_analysis(y_true: pd.Series, y_pred_proba: np.ndarray, save_path: Optional[str] = None) -> plt.Figure:
    """
    Plot metrics vs threshold

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        save_path: Path to save figure (optional)

    Returns:
        Matplotlib figure
    """
    thresholds = np.arange(0.1, 1.0, 0.01)
    precisions = []
    recalls = []
    f1_scores = []

    for threshold in thresholds:
        y_pred_thresh = (y_pred_proba >= threshold).astype(int)
        precisions.append(precision_score(y_true, y_pred_thresh, zero_division=0))
        recalls.append(recall_score(y_true, y_pred_thresh, zero_division=0))
        f1_scores.append(f1_score(y_true, y_pred_thresh, zero_division=0))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(thresholds, precisions, label="Precision", color="#667eea", lw=2)
    ax.plot(thresholds, recalls, label="Recall", color="#764ba2", lw=2)
    ax.plot(thresholds, f1_scores, label="F1-Score", color="#f093fb", lw=2)
    ax.set_xlabel("Threshold", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12, fontweight="bold")
    ax.set_title("Metrics vs Threshold", fontsize=14, fontweight="bold", pad=15)
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)

    # Find optimal threshold (max F1)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx]
    ax.axvline(
        x=optimal_threshold,
        color="red",
        linestyle="--",
        lw=2,
        label=f"Optimal Threshold = {optimal_threshold:.2f}",
    )
    ax.legend(fontsize=11)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"✓ Threshold analysis saved to {save_path}")

    logger.info(f"Optimal threshold (max F1): {optimal_threshold:.4f}")

    return fig


__all__ = [
    "plot_confusion_matrix",
    "plot_roc_curve",
    "plot_precision_recall_curve",
    "plot_threshold_analysis",
]
