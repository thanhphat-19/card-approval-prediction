"""
Main training script for card approval prediction model
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.data_loader import DataLoader, load_sample_data
from features.feature_engineering import FeatureEngineer
from models.evaluate import ModelEvaluator
from models.train import train_with_mlflow


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def main(args):
    """Main training pipeline"""

    print("=" * 80)
    print("CARD APPROVAL PREDICTION - MODEL TRAINING")
    print("=" * 80)

    # 1. Load configuration
    print(f"\n1. Loading configuration from {args.config}")
    config = load_config(args.config)

    # 2. Load data
    print("\n2. Loading data...")
    data_loader = DataLoader(config)

    # Check if data file exists, if not create sample data
    data_path = Path(config["data"]["raw_data_path"])
    if not data_path.exists():
        print(f"   Data file not found at {data_path}")
        print("   Generating sample data for demonstration...")
        df = load_sample_data()
        data_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(data_path, index=False)
        print(f"   ✓ Sample data saved to {data_path}")
    else:
        df = data_loader.load_raw_data()

    # Validate data
    data_loader.validate_data(df)

    # Split data
    train_df, val_df, test_df = data_loader.split_data(df)

    # Save processed splits
    data_loader.save_processed_data(train_df, val_df, test_df)

    # 3. Feature engineering
    print("\n3. Feature engineering...")
    feature_engineer = FeatureEngineer(config)

    # Fit and transform training data
    X_train, y_train, feature_names = feature_engineer.fit_transform(train_df)

    # Transform validation and test data
    X_val, y_val = feature_engineer.transform(val_df)
    X_test, y_test = feature_engineer.transform(test_df)

    # Save feature engineering pipeline
    feature_engineer.save()

    # 4. Train model with MLflow
    print("\n4. Training model...")

    run_name = args.run_name or f"{config['model']['type']}-{config['seed']}"

    model = train_with_mlflow(
        config=config,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        feature_names=feature_names,
        run_name=run_name,
    )

    # 5. Evaluate model
    print("\n5. Evaluating model...")
    evaluator = ModelEvaluator(config)

    metrics = evaluator.generate_evaluation_report(
        model=model,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        feature_names=feature_names,
        output_dir=config["output"]["figures_dir"],
    )

    # 6. Summary
    print("\n" + "=" * 80)
    print("TRAINING COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nTest Set Performance:")
    for metric_name, value in metrics.items():
        if "test" in metric_name:
            print(f"  {metric_name}: {value:.4f}")

    print(f"\nOutputs saved to:")
    print(f"  - Model: models/{config['model']['type']}/")
    print(f"  - Figures: {config['output']['figures_dir']}")
    print(f"  - Preprocessors: models/preprocessors/")

    if args.track_mlflow:
        print(f"\nView results in MLflow UI:")
        print(f"  {config['mlflow']['tracking_uri']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train card approval prediction model")
    parser.add_argument(
        "--config",
        type=str,
        default="src/config/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument("--run-name", type=str, default=None, help="MLflow run name")
    parser.add_argument(
        "--track-mlflow", action="store_true", help="Enable MLflow tracking"
    )

    args = parser.parse_args()

    main(args)
