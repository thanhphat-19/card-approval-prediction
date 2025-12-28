"""
Utility functions for card approval prediction
"""
from pathlib import Path

import yaml


def load_config(config_path: str) -> dict:
    """Load YAML configuration file"""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def save_config(config: dict, output_path: str):
    """Save configuration to YAML file"""
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def ensure_dir(directory: str):
    """Create directory if it doesn't exist"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent
