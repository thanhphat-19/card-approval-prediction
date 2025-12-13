"""
Metrics calculation utilities
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def calculate_metrics(y_true: pd.Series, y_pred: np.ndarray, y_pred_proba: Optional[np.ndarray] = None) -> Dict:
    """
    Calculate classification metrics

    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_pred_proba: Predicted probabilities (optional)

    Returns:
        Dictionary of metrics
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
    }

    if y_pred_proba is not None:
        metrics["roc_auc"] = roc_auc_score(y_true, y_pred_proba)

    return metrics


def get_classification_report(y_true: pd.Series, y_pred: np.ndarray, target_names: Optional[list] = None) -> str:
    """
    Generate classification report

    Args:
        y_true: True labels
        y_pred: Predicted labels
        target_names: Names of target classes (optional)

    Returns:
        Classification report string
    """
    if target_names is None:
        target_names = ["Bad (0)", "Good (1)"]

    report = classification_report(y_true, y_pred, target_names=target_names)
    return report


def find_optimal_threshold(y_true: pd.Series, y_pred_proba: np.ndarray, metric: str = "f1") -> float:
    """
    Find optimal classification threshold

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        metric: Metric to optimize ('f1', 'precision', 'recall')

    Returns:
        Optimal threshold value
    """
    logger.info(f"Finding optimal threshold for {metric}...")

    thresholds = np.arange(0.1, 1.0, 0.01)
    best_threshold = 0.5
    best_score = 0.0

    for threshold in thresholds:
        y_pred_thresh = (y_pred_proba >= threshold).astype(int)

        if metric == "f1":
            score = f1_score(y_true, y_pred_thresh, zero_division=0)
        elif metric == "precision":
            score = precision_score(y_true, y_pred_thresh, zero_division=0)
        elif metric == "recall":
            score = recall_score(y_true, y_pred_thresh, zero_division=0)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        if score > best_score:
            best_score = score
            best_threshold = threshold

    logger.info(f"Optimal threshold: {best_threshold:.4f} (best {metric}: {best_score:.4f})")

    return best_threshold


__all__ = [
    "calculate_metrics",
    "get_classification_report",
    "find_optimal_threshold",
]
