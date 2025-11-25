"""
Prediction script for card approval model
"""

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.feature_engineering import FeatureEngineer
from utils.helpers import ensure_dir, load_config


def load_model_and_preprocessor(model_path: str, preprocessor_path: str, config: dict):
    """
    Load trained model and feature preprocessor

    Args:
        model_path: Path to trained model
        preprocessor_path: Path to preprocessor
        config: Configuration dictionary

    Returns:
        Tuple of (model, feature_engineer)
    """
    print(f"Loading model from {model_path}")
    model = joblib.load(model_path)

    print(f"Loading preprocessor from {preprocessor_path}")
    feature_engineer = FeatureEngineer(config)
    feature_engineer.load(preprocessor_path)

    return model, feature_engineer


def predict_single(
    applicant_data: dict, model, feature_engineer: FeatureEngineer
) -> dict:
    """
    Make prediction for a single applicant

    Args:
        applicant_data: Dictionary with applicant features
        model: Trained model
        feature_engineer: Fitted FeatureEngineer

    Returns:
        Dictionary with prediction results
    """
    # Convert to DataFrame
    df = pd.DataFrame([applicant_data])

    # Transform features
    X, _ = feature_engineer.transform(df)

    # Make prediction
    prediction = model.predict(X)[0]

    # Get probability if available
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        approval_proba = proba[1]
        rejection_proba = proba[0]
    else:
        approval_proba = float(prediction)
        rejection_proba = 1 - approval_proba

    result = {
        "prediction": "Approved" if prediction == 1 else "Rejected",
        "prediction_label": int(prediction),
        "approval_probability": float(approval_proba),
        "rejection_probability": float(rejection_proba),
        "confidence": float(max(approval_proba, rejection_proba)),
    }

    return result


def predict_batch(
    input_file: str, output_file: str, model, feature_engineer: FeatureEngineer
):
    """
    Make predictions for batch of applicants

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        model: Trained model
        feature_engineer: Fitted FeatureEngineer
    """
    print(f"\nLoading data from {input_file}")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} records")

    # Transform features
    print("Transforming features...")

    # Add dummy target if not present (required for transform)
    if feature_engineer.target not in df.columns:
        df[feature_engineer.target] = 0

    X, _ = feature_engineer.transform(df)

    # Make predictions
    print("Making predictions...")
    predictions = model.predict(X)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X)
        df["approval_probability"] = probabilities[:, 1]
        df["rejection_probability"] = probabilities[:, 0]

    df["prediction"] = predictions
    df["prediction_label"] = ["Approved" if p == 1 else "Rejected" for p in predictions]

    # Remove dummy target
    df = df.drop(columns=[feature_engineer.target])

    # Save results
    ensure_dir(Path(output_file).parent)
    df.to_csv(output_file, index=False)

    print(f"\n✓ Predictions saved to {output_file}")
    print(f"\nPrediction Summary:")
    print(df["prediction_label"].value_counts())


def main(args):
    """Main prediction pipeline"""

    print("=" * 80)
    print("CARD APPROVAL PREDICTION - INFERENCE")
    print("=" * 80)

    # Load configuration
    config = load_config(args.config)

    # Load model and preprocessor
    model, feature_engineer = load_model_and_preprocessor(
        args.model_path, args.preprocessor_path, config
    )

    if args.mode == "single":
        # Single prediction example
        print("\nSingle Prediction Mode")
        print("-" * 40)

        # Example applicant data
        applicant_data = {
            "age": 35,
            "annual_income": 75000,
            "credit_score": 720,
            "employment_years": 5,
            "debt_to_income_ratio": 0.3,
            "num_existing_credit_cards": 3,
            "total_credit_limit": 25000,
            "employment_status": "employed",
            "housing_type": "own",
            "education_level": "bachelor",
            "marital_status": "married",
        }

        print("\nApplicant Data:")
        for key, value in applicant_data.items():
            print(f"  {key}: {value}")

        result = predict_single(applicant_data, model, feature_engineer)

        print("\nPrediction Result:")
        print("-" * 40)
        print(f"Decision: {result['prediction']}")
        print(f"Approval Probability: {result['approval_probability']:.2%}")
        print(f"Rejection Probability: {result['rejection_probability']:.2%}")
        print(f"Confidence: {result['confidence']:.2%}")

    elif args.mode == "batch":
        # Batch predictions
        if not args.input_file:
            raise ValueError("--input-file required for batch mode")

        output_file = args.output_file or args.input_file.replace(
            ".csv", "_predictions.csv"
        )

        predict_batch(args.input_file, output_file, model, feature_engineer)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Make predictions with trained card approval model"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="src/config/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="models/xgboost/model.pkl",
        help="Path to trained model",
    )
    parser.add_argument(
        "--preprocessor-path",
        type=str,
        default="models/preprocessors",
        help="Path to preprocessor directory",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "batch"],
        default="single",
        help="Prediction mode",
    )
    parser.add_argument(
        "--input-file", type=str, help="Input CSV file for batch predictions"
    )
    parser.add_argument(
        "--output-file", type=str, help="Output CSV file for predictions"
    )

    args = parser.parse_args()

    main(args)
