"""
Utility functions for card approval prediction
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import yaml


def setup_logging(log_file: str = None, level: int = logging.INFO):
    """
    Setup logging configuration

    Args:
        log_file: Path to log file (optional)
        level: Logging level
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if log_file:
        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
    else:
        logging.basicConfig(level=level, format=log_format)


def load_config(config_path: str) -> dict:
    """
    Load YAML configuration file

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def save_config(config: dict, output_path: str):
    """
    Save configuration to YAML file

    Args:
        config: Configuration dictionary
        output_path: Output file path
    """
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def load_json(file_path: str) -> dict:
    """Load JSON file"""
    with open(file_path, "r") as f:
        return json.load(f)


def save_json(data: dict, file_path: str):
    """Save dictionary to JSON file"""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def ensure_dir(directory: str):
    """
    Create directory if it doesn't exist

    Args:
        directory: Directory path
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


def format_metrics(metrics: Dict[str, float], precision: int = 4) -> str:
    """
    Format metrics dictionary for display

    Args:
        metrics: Dictionary of metrics
        precision: Number of decimal places

    Returns:
        Formatted string
    """
    lines = []
    for key, value in metrics.items():
        if isinstance(value, float):
            lines.append(f"{key}: {value:.{precision}f}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def calculate_class_weights(y: np.ndarray) -> Dict[int, float]:
    """
    Calculate class weights for imbalanced datasets

    Args:
        y: Target array

    Returns:
        Dictionary of class weights
    """
    unique, counts = np.unique(y, return_counts=True)
    total = len(y)

    weights = {}
    for cls, count in zip(unique, counts):
        weights[cls] = total / (len(unique) * count)

    return weights


def get_threshold_metrics(
    y_true: np.ndarray, y_pred_proba: np.ndarray, thresholds: List[float] = None
) -> pd.DataFrame:
    """
    Calculate metrics at different probability thresholds

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        thresholds: List of thresholds to evaluate

    Returns:
        DataFrame with metrics for each threshold
    """
    from sklearn.metrics import f1_score, precision_score, recall_score

    if thresholds is None:
        thresholds = np.arange(0.1, 1.0, 0.1)

    results = []
    for threshold in thresholds:
        y_pred = (y_pred_proba >= threshold).astype(int)

        results.append(
            {
                "threshold": threshold,
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1_score": f1_score(y_true, y_pred, zero_division=0),
            }
        )

    return pd.DataFrame(results)


def find_optimal_threshold(
    y_true: np.ndarray, y_pred_proba: np.ndarray, metric: str = "f1_score"
) -> float:
    """
    Find optimal probability threshold based on a metric

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
        metric: Metric to optimize ('f1_score', 'precision', 'recall')

    Returns:
        Optimal threshold
    """
    thresholds = np.arange(0.1, 1.0, 0.01)
    metrics_df = get_threshold_metrics(y_true, y_pred_proba, thresholds)

    optimal_idx = metrics_df[metric].idxmax()
    optimal_threshold = metrics_df.loc[optimal_idx, "threshold"]

    return optimal_threshold


def print_data_summary(df: pd.DataFrame):
    """
    Print comprehensive data summary

    Args:
        df: Input DataFrame
    """
    print("\n" + "=" * 80)
    print("DATA SUMMARY")
    print("=" * 80)

    print(f"\nShape: {df.shape}")
    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]}")

    print("\nColumn Types:")
    print(df.dtypes.value_counts())

    print("\nMissing Values:")
    missing = df.isnull().sum()
    if missing.sum() > 0:
        missing_pct = (missing / len(df) * 100).round(2)
        missing_df = pd.DataFrame(
            {"count": missing[missing > 0], "percentage": missing_pct[missing > 0]}
        ).sort_values("count", ascending=False)
        print(missing_df)
    else:
        print("No missing values")

    print("\nMemory Usage:")
    print(f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")


def validate_features(df: pd.DataFrame, required_features: List[str]) -> bool:
    """
    Validate that DataFrame contains required features

    Args:
        df: Input DataFrame
        required_features: List of required feature names

    Returns:
        True if all features present

    Raises:
        ValueError if features missing
    """
    missing = set(required_features) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    return True


def create_directory_structure(base_path: str):
    """
    Create standard project directory structure

    Args:
        base_path: Base directory path
    """
    directories = [
        "data/raw",
        "data/processed",
        "data/features",
        "data/external",
        "models/baseline",
        "models/experimental",
        "models/production",
        "models/preprocessors",
        "outputs/figures",
        "outputs/reports",
        "outputs/metrics",
        "experiments/configs",
        "notebooks",
        "tests",
    ]

    for directory in directories:
        ensure_dir(Path(base_path) / directory)

    print(f"✓ Created directory structure in {base_path}")
