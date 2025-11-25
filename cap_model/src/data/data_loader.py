"""
Data loading and preprocessing module
"""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


class DataLoader:
    """Load and prepare credit card application data"""

    def __init__(self, config: dict):
        """
        Initialize DataLoader

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.data_path = Path(config["data"]["raw_data_path"])

    def load_raw_data(self) -> pd.DataFrame:
        """
        Load raw data from CSV

        Returns:
            DataFrame with raw data
        """
        print(f"Loading data from {self.data_path}")

        try:
            df = pd.read_csv(self.data_path)
            print(f"Loaded {len(df)} records with {len(df.columns)} features")
            return df
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Data file not found: {self.data_path}\n"
                f"Please place your dataset in {self.data_path}"
            )

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate data quality

        Args:
            df: Input DataFrame

        Returns:
            True if data is valid
        """
        # Check for required columns
        required_cols = (
            self.config["features"]["numerical_features"]
            + self.config["features"]["categorical_features"]
            + [self.config["features"]["target"]]
        )

        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Check for completely empty features
        empty_cols = df.columns[df.isnull().all()].tolist()
        if empty_cols:
            print(f"Warning: Completely empty columns: {empty_cols}")

        # Check target distribution
        target_col = self.config["features"]["target"]
        print(f"\nTarget distribution:")
        print(df[target_col].value_counts(normalize=True))

        return True

    def split_data(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, and test sets

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        test_size = self.config["data"]["test_size"]
        val_size = self.config["data"]["validation_size"]
        random_state = self.config["data"]["random_state"]
        target_col = self.config["features"]["target"]

        # First split: train+val vs test
        train_val_df, test_df = train_test_split(
            df, test_size=test_size, random_state=random_state, stratify=df[target_col]
        )

        # Second split: train vs val
        val_size_adjusted = val_size / (1 - test_size)
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_size_adjusted,
            random_state=random_state,
            stratify=train_val_df[target_col],
        )

        print(f"\nData split:")
        print(f"  Train: {len(train_df)} samples ({len(train_df)/len(df)*100:.1f}%)")
        print(f"  Val:   {len(val_df)} samples ({len(val_df)/len(df)*100:.1f}%)")
        print(f"  Test:  {len(test_df)} samples ({len(test_df)/len(df)*100:.1f}%)")

        return train_df, val_df, test_df

    def save_processed_data(
        self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame
    ):
        """
        Save processed data splits

        Args:
            train_df: Training data
            val_df: Validation data
            test_df: Test data
        """
        output_dir = Path(self.config["data"]["processed_data_path"]).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        train_df.to_csv(output_dir / "train.csv", index=False)
        val_df.to_csv(output_dir / "val.csv", index=False)
        test_df.to_csv(output_dir / "test.csv", index=False)

        print(f"\nSaved processed data to {output_dir}")


def load_sample_data() -> pd.DataFrame:
    """
    Generate sample credit card application data for testing

    Returns:
        DataFrame with sample data
    """
    np.random.seed(42)
    n_samples = 1000

    # Generate synthetic data
    data = {
        "age": np.random.randint(18, 70, n_samples),
        "annual_income": np.random.randint(20000, 200000, n_samples),
        "credit_score": np.random.randint(300, 850, n_samples),
        "employment_years": np.random.randint(0, 40, n_samples),
        "debt_to_income_ratio": np.random.uniform(0, 1, n_samples),
        "num_existing_credit_cards": np.random.randint(0, 10, n_samples),
        "total_credit_limit": np.random.randint(0, 100000, n_samples),
        "employment_status": np.random.choice(
            ["employed", "self_employed", "unemployed"], n_samples
        ),
        "housing_type": np.random.choice(
            ["own", "rent", "mortgage", "other"], n_samples
        ),
        "education_level": np.random.choice(
            ["high_school", "bachelor", "master", "phd"], n_samples
        ),
        "marital_status": np.random.choice(
            ["single", "married", "divorced", "widowed"], n_samples
        ),
    }

    df = pd.DataFrame(data)

    # Generate target based on features (simplified logic)
    df["approval_score"] = (
        (df["credit_score"] / 850) * 0.4
        + (df["annual_income"] / 200000) * 0.3
        + (1 - df["debt_to_income_ratio"]) * 0.2
        + (df["employment_years"] / 40) * 0.1
    )

    # Convert to binary approval
    df["approval_status"] = (df["approval_score"] > 0.5).astype(int)
    df = df.drop("approval_score", axis=1)

    return df
