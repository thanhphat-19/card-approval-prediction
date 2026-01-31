"""
Unit tests for training/src/utils/model_configs.py module.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add training/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "training"))

from src.utils.model_configs import MODEL_CLASSES, get_model_configs  # noqa: E402


class TestModelClasses:
    """Tests for MODEL_CLASSES constant."""

    def test_model_classes_defined(self):
        """Test MODEL_CLASSES contains expected models."""
        expected_models = ["AdaBoost", "XGBoost", "LightGBM", "CatBoost", "Naive Bayes"]

        for model_name in expected_models:
            assert model_name in MODEL_CLASSES
            assert MODEL_CLASSES[model_name] is not None


class TestGetModelConfigs:
    """Tests for get_model_configs function."""

    @patch("src.utils.model_configs.load_config")
    def test_loads_from_default_config(self, mock_load_config):
        """Test get_model_configs loads from default config path."""
        mock_load_config.return_value = {
            "model": {"hyperparameters": {"XGBoost": {"max_depth": 6, "learning_rate": 0.1}}}
        }

        get_model_configs()

        # Should call load_config
        mock_load_config.assert_called_once()

    @patch("src.utils.model_configs.load_config")
    def test_returns_model_with_class_and_params(self, mock_load_config):
        """Test returns models with class and params structure."""
        mock_load_config.return_value = {"model": {"hyperparameters": {"XGBoost": {"max_depth": 6}}}}

        result = get_model_configs()

        assert "XGBoost" in result
        assert "class" in result["XGBoost"]
        assert "params" in result["XGBoost"]
        assert result["XGBoost"]["params"]["max_depth"] == 6

    @patch("src.utils.model_configs.load_config")
    def test_filters_specific_models(self, mock_load_config):
        """Test filters to specific models when requested."""
        mock_load_config.return_value = {
            "model": {"hyperparameters": {"XGBoost": {"max_depth": 6}, "LightGBM": {"num_leaves": 31}}}
        }

        result = get_model_configs(models=["XGBoost"])

        assert "XGBoost" in result
        assert "LightGBM" not in result

    @patch("src.utils.model_configs.load_config")
    def test_handles_none_params(self, mock_load_config):
        """Test handles None params gracefully."""
        mock_load_config.return_value = {"model": {"hyperparameters": {"Naive Bayes": None}}}

        result = get_model_configs()

        assert "Naive Bayes" in result
        assert result["Naive Bayes"]["params"] == {}

    @patch("src.utils.model_configs.load_config")
    def test_uses_custom_config_path(self, mock_load_config):
        """Test uses custom config path when provided."""
        mock_load_config.return_value = {"model": {"hyperparameters": {}}}

        custom_path = "/custom/config.yaml"
        get_model_configs(config_path=custom_path)

        # Should call with custom path
        mock_load_config.assert_called_once_with(custom_path)

    @patch("src.utils.model_configs.load_config")
    def test_returns_empty_when_no_hyperparameters(self, mock_load_config):
        """Test returns empty dict when no hyperparameters configured."""
        mock_load_config.return_value = {"model": {}}

        result = get_model_configs()

        assert result == {}

    @patch("src.utils.model_configs.load_config")
    def test_returns_multiple_models(self, mock_load_config):
        """Test returns all configured models."""
        mock_load_config.return_value = {
            "model": {
                "hyperparameters": {
                    "XGBoost": {"max_depth": 6},
                    "LightGBM": {"num_leaves": 31},
                    "CatBoost": {"iterations": 100},
                }
            }
        }

        result = get_model_configs()

        assert len(result) == 3
        assert all(name in result for name in ["XGBoost", "LightGBM", "CatBoost"])
