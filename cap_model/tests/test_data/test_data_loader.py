"""
Unit tests for data loader
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.data_loader import DataLoader, load_sample_data


class TestDataLoader:
    """Test DataLoader functionality"""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            "data": {
                "raw_data_path": "data/raw/test_data.csv",
                "processed_data_path": "data/processed/test_data.csv",
                "test_size": 0.2,
                "validation_size": 0.1,
                "random_state": 42,
            },
            "features": {
                "numerical_features": ["age", "annual_income", "credit_score"],
                "categorical_features": ["employment_status", "housing_type"],
                "target": "approval_status",
            },
        }

    def test_load_sample_data(self):
        """Test sample data generation"""
        df = load_sample_data()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1000
        assert "approval_status" in df.columns
        assert df["approval_status"].isin([0, 1]).all()

    def test_data_loader_initialization(self, sample_config):
        """Test DataLoader initialization"""
        loader = DataLoader(sample_config)
        assert loader.config == sample_config

    def test_validate_data(self, sample_config):
        """Test data validation"""
        loader = DataLoader(sample_config)
        df = load_sample_data()

        # Should pass validation
        assert loader.validate_data(df) == True

        # Should fail with missing column
        df_incomplete = df.drop(columns=["age"])
        with pytest.raises(ValueError):
            loader.validate_data(df_incomplete)

    def test_split_data(self, sample_config):
        """Test data splitting"""
        loader = DataLoader(sample_config)
        df = load_sample_data()

        train_df, val_df, test_df = loader.split_data(df)

        # Check sizes
        assert len(train_df) > 0
        assert len(val_df) > 0
        assert len(test_df) > 0

        # Check total
        total = len(train_df) + len(val_df) + len(test_df)
        assert total == len(df)

        # Check no overlap
        train_idx = set(train_df.index)
        val_idx = set(val_df.index)
        test_idx = set(test_df.index)

        assert len(train_idx & val_idx) == 0
        assert len(train_idx & test_idx) == 0
        assert len(val_idx & test_idx) == 0
