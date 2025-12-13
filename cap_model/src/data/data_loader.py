"""
Data loading and target creation module
"""

from pathlib import Path
from typing import Tuple

import pandas as pd
from loguru import logger


class DataLoader:
    """Handle data loading and initial processing"""

    def __init__(self, raw_data_dir: str = "data/raw"):
        """
        Initialize DataLoader

        Args:
            raw_data_dir: Directory containing raw data files
        """
        self.raw_data_dir = Path(raw_data_dir)

    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load application and credit record data

        Returns:
            Tuple of (application_data, credit_data)
        """
        logger.info("Loading raw data...")

        app_path = self.raw_data_dir / "application_record.csv"
        credit_path = self.raw_data_dir / "credit_record.csv"

        app_data = pd.read_csv(app_path)
        credit_data = pd.read_csv(credit_path)

        logger.info(f"Application Records: {app_data.shape[0]:,} rows, {app_data.shape[1]} columns")
        logger.info(f"Credit Records: {credit_data.shape[0]:,} rows, {credit_data.shape[1]} columns")
        logger.info(f"Unique Applicants: {app_data['ID'].nunique():,}")

        return app_data, credit_data

    def create_target_variable(self, credit_data: pd.DataFrame) -> pd.DataFrame:
        """
        Create target variable from credit status

        Status mapping:
        - Good (1): Status in ['0', 'X', 'C']
        - Bad (0): Status in ['2', '3', '4', '5'] (overdue more than 60 days)

        Args:
            credit_data: Credit record DataFrame

        Returns:
            DataFrame with ID and Label columns
        """
        logger.info("Creating target variable...")

        # Create Good/Bad labels from STATUS
        credit_data = credit_data.copy()
        credit_data["Good or Bad"] = credit_data["STATUS"].apply(lambda x: "Good" if x in ["0", "X", "C"] else "Bad")

        # Group by ID and get dominant label
        credit_goods_bads = credit_data.groupby(["ID", "Good or Bad"]).size().to_frame("size")
        credit_goods_bads.reset_index(inplace=True)

        idx = credit_goods_bads.groupby("ID")["size"].idxmax()
        max_goods_bads = credit_goods_bads.loc[idx]

        # Convert to binary (1=Good, 0=Bad)
        max_goods_bads["Label"] = max_goods_bads["Good or Bad"].apply(lambda x: 1 if x == "Good" else 0)
        max_goods_bads = max_goods_bads[["ID", "Label"]].reset_index(drop=True)

        logger.info(f"Created target labels for {len(max_goods_bads):,} customers")
        logger.info(
            f"Good (1): {(max_goods_bads['Label'] == 1).sum():,} ({(max_goods_bads['Label'] == 1).sum() / len(max_goods_bads) * 100:.1f}%)"
        )
        logger.info(
            f"Bad (0): {(max_goods_bads['Label'] == 0).sum():,} ({(max_goods_bads['Label'] == 0).sum() / len(max_goods_bads) * 100:.1f}%)"
        )

        return max_goods_bads

    def merge_data(
        self,
        app_data: pd.DataFrame,
        target_data: pd.DataFrame,
        fill_missing: bool = True,
    ) -> pd.DataFrame:
        """
        Merge application data with target labels

        Args:
            app_data: Application record DataFrame
            target_data: Target labels DataFrame (ID, Label)
            fill_missing: Whether to fill missing values

        Returns:
            Merged DataFrame
        """
        logger.info("Merging application and target data...")

        # Fill missing values if requested
        if fill_missing:
            app_data = app_data.copy()
            app_data.fillna("Unknown", inplace=True)
            logger.info("Filled missing values with 'Unknown'")

        # Merge data
        merged_data = pd.merge(app_data, target_data, how="inner", on="ID")

        logger.info(f"Merged dataset: {len(merged_data):,} rows, {merged_data.shape[1]} columns")
        logger.info("Target Distribution After Merge:")
        logger.info(
            f"  Good (1): {(merged_data['Label'] == 1).sum():,} ({(merged_data['Label'] == 1).sum() / len(merged_data) * 100:.2f}%)"
        )
        logger.info(
            f"  Bad (0): {(merged_data['Label'] == 0).sum():,} ({(merged_data['Label'] == 0).sum() / len(merged_data) * 100:.2f}%)"
        )
        logger.info(f"  Imbalance Ratio: {(merged_data['Label'] == 1).sum() / (merged_data['Label'] == 0).sum():.2f}:1")

        return merged_data

    def load_and_prepare_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Complete pipeline: load raw data, create target, and merge

        Returns:
            Tuple of (features_df, target_series)
        """
        # Load raw data
        app_data, credit_data = self.load_raw_data()

        # Create target
        target_data = self.create_target_variable(credit_data)

        # Merge data
        merged_data = self.merge_data(app_data, target_data)

        # Separate features and target
        X = merged_data.drop("Label", axis=1)
        y = merged_data["Label"]

        # Remove ID column - it's just an identifier, not a predictive feature
        if "ID" in X.columns:
            X = X.drop("ID", axis=1)
            logger.info("Removed ID column from features")

        logger.info(f"Final features shape: {X.shape}")
        logger.info(f"Final target shape: {y.shape}")

        return X, y
