#!/usr/bin/env python3
"""
Data Preprocessing Script
Handles feature engineering and data preparation using src modules
"""

import argparse
import sys
import warnings
from pathlib import Path

from loguru import logger
from src.data.data_loader import DataLoader
from src.features.feature_engineering import FeatureEngineer

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


warnings.filterwarnings("ignore")


def main():
    """Run preprocessing pipeline"""
    parser = argparse.ArgumentParser(description="Run Data Preprocessing")
    parser.add_argument(
        "--raw-data-dir",
        default="data/raw",
        help="Raw data directory (default: data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Output directory for processed data (default: data/processed)",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set size (default: 0.2)")
    parser.add_argument(
        "--pca-components",
        type=int,
        default=5,
        help="Number of PCA components (default: 5)",
    )
    parser.add_argument("--no-smote", action="store_true", help="Disable SMOTE resampling")
    parser.add_argument("--no-pca", action="store_true", help="Disable PCA")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("DATA PREPROCESSING PIPELINE")
    logger.info("=" * 80)

    try:
        # 1. Load Data
        logger.info("\n1. Loading data...")
        loader = DataLoader(raw_data_dir=args.raw_data_dir)
        X, y = loader.load_and_prepare_data()

        logger.info(f"✓ Features: {X.shape}")
        logger.info(f"✓ Target: {y.shape}")
        logger.info(f"  Good (1): {(y == 1).sum():,} ({(y == 1).sum() / len(y) * 100:.2f}%)")
        logger.info(f"  Bad (0): {(y == 0).sum():,} ({(y == 0).sum() / len(y) * 100:.2f}%)")

        # 2. Feature Engineering
        logger.info("\n2. Running feature engineering pipeline...")
        engineer = FeatureEngineer(random_state=args.random_state)

        result = engineer.full_pipeline(
            X=X,
            y=y,
            apply_smote=not args.no_smote,
            apply_pca_transform=not args.no_pca,
            n_components=args.pca_components,
            test_size=args.test_size,
            save_preprocessors=True,
            output_dir=args.output_dir,
        )

        # 3. Display Results
        logger.info("\n3. Pipeline results...")
        logger.info(f"✓ X_train: {result['X_train'].shape}")
        logger.info(f"✓ X_test: {result['X_test'].shape}")
        logger.info(f"✓ y_train: {result['y_train'].shape}")
        logger.info(f"✓ y_test: {result['y_test'].shape}")

        logger.info("\n📊 Training set distribution:")
        logger.info(
            f"  Good (1): {(result['y_train'] == 1).sum():,} ({(result['y_train'] == 1).sum() / len(result['y_train']) * 100:.2f}%)"
        )
        logger.info(
            f"  Bad (0): {(result['y_train'] == 0).sum():,} ({(result['y_train'] == 0).sum() / len(result['y_train']) * 100:.2f}%)"
        )

        logger.info("\n📊 Test set distribution:")
        logger.info(
            f"  Good (1): {(result['y_test'] == 1).sum():,} ({(result['y_test'] == 1).sum() / len(result['y_test']) * 100:.2f}%)"
        )
        logger.info(
            f"  Bad (0): {(result['y_test'] == 0).sum():,} ({(result['y_test'] == 0).sum() / len(result['y_test']) * 100:.2f}%)"
        )

        # 4. Save Processed Data
        logger.info("\n4. Saving processed data...")
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        result["X_train"].to_csv(output_path / "X_train.csv", index=False)
        result["X_test"].to_csv(output_path / "X_test.csv", index=False)
        result["y_train"].to_csv(output_path / "y_train.csv", index=False)
        result["y_test"].to_csv(output_path / "y_test.csv", index=False)

        logger.info(f"✓ Saved to {output_path}:")
        logger.info(f"  - X_train.csv ({result['X_train'].shape[0]} x {result['X_train'].shape[1]})")
        logger.info(f"  - X_test.csv ({result['X_test'].shape[0]} x {result['X_test'].shape[1]})")
        logger.info(f"  - y_train.csv ({len(result['y_train'])} samples)")
        logger.info(f"  - y_test.csv ({len(result['y_test'])} samples)")
        logger.info("  - scaler.pkl")
        if not args.no_pca:
            logger.info("  - pca.pkl")

        logger.info("\n" + "=" * 80)
        logger.info("✅ PREPROCESSING COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Results saved to: {args.output_dir}")

        return 0

    except Exception as e:
        logger.error(f"❌ Preprocessing failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
