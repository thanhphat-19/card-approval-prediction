#!/usr/bin/env python3
"""
Exploratory Data Analysis Script
Performs EDA and generates visualizations using src modules
"""

import argparse
import sys
import warnings
from pathlib import Path

from loguru import logger
from src.data.data_loader import DataLoader

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

warnings.filterwarnings("ignore")


def main():
    """Run EDA pipeline"""
    parser = argparse.ArgumentParser(description="Run Exploratory Data Analysis")
    parser.add_argument(
        "--raw-data-dir",
        default="data/raw",
        help="Raw data directory (default: data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/eda",
        help="Output directory for EDA results (default: outputs/eda)",
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("EXPLORATORY DATA ANALYSIS PIPELINE")
    logger.info("=" * 80)

    try:
        # Create output directory
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Load Data
        logger.info("\n1. Loading data...")
        loader = DataLoader(raw_data_dir=args.raw_data_dir)
        app_data, credit_data = loader.load_raw_data()

        logger.info(f"✓ Application Records: {app_data.shape[0]:,} rows, {app_data.shape[1]} columns")
        logger.info(f"✓ Credit Records: {credit_data.shape[0]:,} rows, {credit_data.shape[1]} columns")

        # 2. Create Target Variable
        logger.info("\n2. Creating target variable...")
        target_data = loader.create_target_variable(credit_data)

        logger.info(f"✓ Created target labels for {len(target_data):,} customers")
        logger.info(
            f"  Good (1): {(target_data['Label'] == 1).sum():,} ({(target_data['Label'] == 1).sum() / len(target_data) * 100:.1f}%)"
        )
        logger.info(
            f"  Bad (0):  {(target_data['Label'] == 0).sum():,} ({(target_data['Label'] == 0).sum() / len(target_data) * 100:.1f}%)"
        )

        # 3. Merge Data
        logger.info("\n3. Merging application and credit data...")
        app_data_filled = app_data.fillna("Unknown")
        data = app_data_filled.merge(target_data, how="inner", on="ID")

        logger.info(f"✓ Merged dataset: {len(data):,} rows, {data.shape[1]} columns")
        logger.info(f"  Good (1): {(data['Label'] == 1).sum():,} ({(data['Label'] == 1).sum() / len(data) * 100:.2f}%)")
        logger.info(f"  Bad (0):  {(data['Label'] == 0).sum():,} ({(data['Label'] == 0).sum() / len(data) * 100:.2f}%)")
        logger.info(f"  Imbalance Ratio: {(data['Label'] == 1).sum() / (data['Label'] == 0).sum():.2f}:1")

        # 4. Basic Statistics
        logger.info("\n4. Data summary...")
        logger.info(f"✓ Shape: {data.shape}")
        logger.info(f"✓ Columns: {list(data.columns)}")
        logger.info(f"✓ Missing values: {data.isnull().sum().sum()}")
        logger.info(f"✓ Duplicates: {data.duplicated().sum()}")

        # 5. Save summary
        logger.info("\n5. Saving EDA results...")
        summary_path = output_path / "eda_summary.txt"
        with open(summary_path, "w") as f:
            f.write("EXPLORATORY DATA ANALYSIS SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Application Records: {app_data.shape[0]:,}\n")
            f.write(f"Credit Records: {credit_data.shape[0]:,}\n")
            f.write(f"Merged Records: {len(data):,}\n\n")
            f.write(f"Target Distribution:\n")
            f.write(
                f"  Good (1): {(data['Label'] == 1).sum():,} ({(data['Label'] == 1).sum() / len(data) * 100:.2f}%)\n"
            )
            f.write(
                f"  Bad (0): {(data['Label'] == 0).sum():,} ({(data['Label'] == 0).sum() / len(data) * 100:.2f}%)\n"
            )
            f.write(f"  Imbalance Ratio: {(data['Label'] == 1).sum() / (data['Label'] == 0).sum():.2f}:1\n\n")
            f.write(f"Data Info:\n")
            f.write(f"  Shape: {data.shape}\n")
            f.write(f"  Missing values: {data.isnull().sum().sum()}\n")
            f.write(f"  Duplicates: {data.duplicated().sum()}\n")

        logger.info(f"✓ Summary saved to {summary_path}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ EDA COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Results saved to: {args.output_dir}")

        return 0

    except Exception as e:
        logger.error(f"❌ EDA failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
