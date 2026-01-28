#!/usr/bin/env python3
"""
CI/CD Model Evaluation Script

"""

import argparse
import os
import sys
from pathlib import Path

import mlflow
import pandas as pd

# Reuse existing evaluation utilities from training module
from training.src.utils.metrics import calculate_metrics

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_mlflow_model(tracking_uri: str, model_name: str, stage: str):
    """
    Load the latest model from MLflow registry.

    Args:
        tracking_uri: MLflow tracking server URL
        model_name: Name of the registered model
        stage: Model stage (Production, Staging, etc.)

    Returns:
        Tuple of (model, version, run_id)
    """
    mlflow.set_tracking_uri(tracking_uri)
    client = mlflow.tracking.MlflowClient()

    # Get model versions
    filter_string = f"name='{model_name}'"
    model_versions = client.search_model_versions(filter_string=filter_string)

    # Filter by stage
    stage_versions = [v for v in model_versions if v.current_stage == stage]

    if not stage_versions:
        raise ValueError(f"No model found for '{model_name}' in '{stage}' stage")

    # Get latest version
    latest = sorted(stage_versions, key=lambda v: int(v.version), reverse=True)[0]
    version = latest.version
    run_id = latest.run_id

    print(f"📦 Loading model: {model_name} v{version} ({stage})")
    print(f"   Run ID: {run_id}")

    # Load model using native flavor for predict_proba support
    model_uri = f"models:/{model_name}/{version}"

    # Try native flavors first (for predict_proba support)
    flavor_loaders = [
        ("xgboost", mlflow.xgboost.load_model),
        ("lightgbm", mlflow.lightgbm.load_model),
        ("catboost", mlflow.catboost.load_model),
        ("sklearn", mlflow.sklearn.load_model),
    ]

    for flavor_name, loader_func in flavor_loaders:
        try:
            model = loader_func(model_uri)
            print(f"   Loaded with {flavor_name} flavor")
            return model, version, run_id
        except Exception:
            continue

    # Fallback to pyfunc
    model = mlflow.pyfunc.load_model(model_uri)
    print("   Loaded with pyfunc flavor")
    return model, version, run_id


def load_test_data(data_dir: str):
    """
    Load test data from processed directory.

    Args:
        data_dir: Path to processed data directory

    Returns:
        Tuple of (X_test, y_test)
    """
    data_path = Path(data_dir)

    X_test_path = data_path / "X_test.csv"
    y_test_path = data_path / "y_test.csv"

    if not X_test_path.exists():
        raise FileNotFoundError(f"Test features not found: {X_test_path}")
    if not y_test_path.exists():
        raise FileNotFoundError(f"Test labels not found: {y_test_path}")

    X_test = pd.read_csv(X_test_path)
    y_test = pd.read_csv(y_test_path).squeeze()

    print(f"📊 Loaded test data: {len(X_test)} samples")

    return X_test, y_test


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Evaluate model using shared metrics from training module.

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels

    Returns:
        Dictionary of metrics
    """
    y_pred = model.predict(X_test)
    y_pred_proba = None

    if hasattr(model, "predict_proba"):
        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
        except Exception:
            pass

    # Reuse the same metrics calculation from training
    return calculate_metrics(y_test, y_pred, y_pred_proba)


def main():
    parser = argparse.ArgumentParser(description="Evaluate MLflow model for CI/CD quality gate")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.90,
        help="F1 score threshold for passing (default: 0.90)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Path to processed data directory (default: data/processed)",
    )
    parser.add_argument(
        "--tracking-uri",
        type=str,
        default=os.environ.get("MLFLOW_TRACKING_URI"),
        help="MLflow tracking URI (default: from MLFLOW_TRACKING_URI env)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=os.environ.get("MODEL_NAME", "card_approval_model"),
        help="Model name in MLflow registry (default: card_approval_model)",
    )
    parser.add_argument(
        "--model-stage",
        type=str,
        default=os.environ.get("MODEL_STAGE", "Production"),
        help="Model stage to evaluate (default: Production)",
    )

    args = parser.parse_args()

    # Validate
    if not args.tracking_uri:
        print("❌ ERROR: MLFLOW_TRACKING_URI not set")
        sys.exit(1)

    print("=" * 60)
    print("🔍 CI/CD MODEL EVALUATION")
    print("=" * 60)
    print(f"   MLflow URI: {args.tracking_uri}")
    print(f"   Model: {args.model_name} ({args.model_stage})")
    print(f"   Threshold: F1 >= {args.threshold}")
    print("=" * 60)

    try:
        # Load model from MLflow
        model, version, run_id = load_mlflow_model(
            args.tracking_uri,
            args.model_name,
            args.model_stage,
        )

        # Load test data
        X_test, y_test = load_test_data(args.data_dir)

        # Evaluate using shared metrics
        print("\n📈 Evaluating model...")
        metrics = evaluate_model(model, X_test, y_test)

        # Print results
        print("\n" + "=" * 60)
        print("📊 EVALUATION RESULTS")
        print("=" * 60)
        for metric_name, value in metrics.items():
            status = "✅" if metric_name == "f1_score" and value >= args.threshold else "  "
            print(f"   {status} {metric_name}: {value:.4f}")

        # Quality gate check
        f1 = metrics["f1_score"]
        print("\n" + "=" * 60)

        if f1 >= args.threshold:
            print(f"✅ PASSED: F1 score ({f1:.4f}) >= threshold ({args.threshold})")
            print("   Model is ready for deployment!")
            print("=" * 60)
            sys.exit(0)
        else:
            print(f"❌ FAILED: F1 score ({f1:.4f}) < threshold ({args.threshold})")
            print("   Model does not meet quality requirements!")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
