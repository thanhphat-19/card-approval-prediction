"""
Unit tests for training/src/data/data_loader.py module.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from training.src.data.data_loader import DataLoader  # noqa: E402

# Add training/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "training"))


class TestDataLoader:
    """Tests for DataLoader class."""

    @pytest.fixture
    def data_loader(self):
        """Create DataLoader instance."""
        return DataLoader(raw_data_dir="data/raw")

    @pytest.fixture
    def sample_app_data(self):
        """Sample application data."""
        return pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "CODE_GENDER": ["M", "F", "M"],
                "AMT_INCOME_TOTAL": [100000, 150000, 80000],
                "NAME_INCOME_TYPE": ["Working", "Pensioner", "Working"],
            }
        )

    @pytest.fixture
    def sample_credit_data(self):
        """Sample credit record data."""
        return pd.DataFrame(
            {
                "ID": [1, 1, 2, 2, 3, 3],
                "MONTHS_BALANCE": [-1, -2, -1, -2, -1, -2],
                "STATUS": ["0", "0", "2", "3", "C", "X"],
            }
        )

    def test_init_sets_raw_data_dir(self, data_loader):
        """Test DataLoader sets raw_data_dir correctly."""
        assert data_loader.raw_data_dir == Path("data/raw")

    def test_init_with_custom_dir(self):
        """Test DataLoader with custom directory."""
        loader = DataLoader(raw_data_dir="/custom/path")
        assert loader.raw_data_dir == Path("/custom/path")

    @patch("pandas.read_csv")
    def test_load_raw_data(self, mock_read_csv, data_loader, sample_app_data, sample_credit_data):
        """Test load_raw_data loads both files."""
        mock_read_csv.side_effect = [sample_app_data, sample_credit_data]

        app_data, credit_data = data_loader.load_raw_data()

        assert len(app_data) == 3
        assert len(credit_data) == 6
        assert mock_read_csv.call_count == 2

    def test_create_target_variable(self, data_loader, sample_credit_data):
        """Test create_target_variable creates correct labels."""
        result = data_loader.create_target_variable(sample_credit_data)

        assert "ID" in result.columns
        assert "Label" in result.columns
        # ID 1 has all good status (0), ID 2 has bad (2,3), ID 3 has good (C,X)
        assert len(result) == 3

    def test_create_target_good_status(self, data_loader):
        """Test good status values are labeled as 1."""
        credit_data = pd.DataFrame(
            {
                "ID": [1, 1, 1],
                "MONTHS_BALANCE": [-1, -2, -3],
                "STATUS": ["0", "X", "C"],  # All good
            }
        )

        result = data_loader.create_target_variable(credit_data)

        assert result[result["ID"] == 1]["Label"].values[0] == 1

    def test_create_target_bad_status(self, data_loader):
        """Test bad status values are labeled as 0."""
        credit_data = pd.DataFrame(
            {
                "ID": [1, 1, 1],
                "MONTHS_BALANCE": [-1, -2, -3],
                "STATUS": ["2", "3", "4"],  # All bad
            }
        )

        result = data_loader.create_target_variable(credit_data)

        assert result[result["ID"] == 1]["Label"].values[0] == 0

    def test_merge_data(self, data_loader, sample_app_data):
        """Test merge_data merges correctly."""
        target_data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Label": [1, 0, 1],
            }
        )

        result = data_loader.merge_data(sample_app_data, target_data)

        assert len(result) == 3
        assert "Label" in result.columns
        assert "CODE_GENDER" in result.columns

    def test_merge_data_fills_missing(self, data_loader):
        """Test merge_data fills missing values when requested."""
        app_data = pd.DataFrame(
            {
                "ID": [1, 2],
                "CODE_GENDER": ["M", None],
            }
        )
        target_data = pd.DataFrame(
            {
                "ID": [1, 2],
                "Label": [1, 0],
            }
        )

        result = data_loader.merge_data(app_data, target_data, fill_missing=True)

        # None should be replaced with "Unknown"
        assert result["CODE_GENDER"].iloc[1] == "Unknown"

    def test_merge_data_inner_join(self, data_loader, sample_app_data):
        """Test merge_data uses inner join."""
        target_data = pd.DataFrame(
            {
                "ID": [1, 2],  # Missing ID 3
                "Label": [1, 0],
            }
        )

        result = data_loader.merge_data(sample_app_data, target_data)

        # Only IDs 1 and 2 should be in result
        assert len(result) == 2
        assert 3 not in result["ID"].values

    @patch.object(DataLoader, "load_raw_data")
    @patch.object(DataLoader, "create_target_variable")
    @patch.object(DataLoader, "merge_data")
    def test_load_and_prepare_data(
        self, mock_merge, mock_target, mock_load, data_loader, sample_app_data, sample_credit_data
    ):
        """Test load_and_prepare_data complete pipeline."""
        mock_load.return_value = (sample_app_data, sample_credit_data)
        mock_target.return_value = pd.DataFrame({"ID": [1, 2, 3], "Label": [1, 0, 1]})
        mock_merge.return_value = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "CODE_GENDER": ["M", "F", "M"],
                "Label": [1, 0, 1],
            }
        )

        X, y = data_loader.load_and_prepare_data()

        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert "ID" not in X.columns  # ID should be removed
        assert "Label" not in X.columns  # Label should be in y

    def test_load_and_prepare_removes_id(self, data_loader):
        """Test load_and_prepare_data removes ID column."""
        with patch.object(DataLoader, "load_raw_data") as mock_load, patch.object(
            DataLoader, "create_target_variable"
        ) as mock_target, patch.object(DataLoader, "merge_data") as mock_merge:
            mock_load.return_value = (
                pd.DataFrame({"ID": [1], "feat": [1]}),
                pd.DataFrame({"ID": [1], "STATUS": ["0"]}),
            )
            mock_target.return_value = pd.DataFrame({"ID": [1], "Label": [1]})
            mock_merge.return_value = pd.DataFrame({"ID": [1], "feat": [1], "Label": [1]})

            X, y = data_loader.load_and_prepare_data()

            assert "ID" not in X.columns
