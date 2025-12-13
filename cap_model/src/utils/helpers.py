"""
Utility functions for card approval prediction
"""

import json
from pathlib import Path
from typing import List

import pandas as pd
import yaml
from loguru import logger


# File I/O operations
def load_config(config_path: str) -> dict:
    """Load YAML configuration file"""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def save_config(config: dict, output_path: str):
    """Save configuration to YAML file"""
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
    """Create directory if it doesn't exist"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


def print_data_summary(df: pd.DataFrame):
    """Print comprehensive data summary"""
    logger.info("=" * 80)
    logger.info("DATA SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Shape: {df.shape} | Rows: {df.shape[0]:,} | Columns: {df.shape[1]}")

    missing = df.isnull().sum()
    if missing.sum() > 0:
        logger.info(f"Missing Values: {missing[missing > 0].to_dict()}")

    logger.info(f"Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")


def validate_features(df: pd.DataFrame, required_features: List[str]) -> bool:
    """Validate that DataFrame contains required features"""
    missing = set(required_features) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    return True
