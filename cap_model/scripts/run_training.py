#!/usr/bin/env python3
"""
Model Training Script
Trains multiple models and saves the best one using src modules
"""

import argparse
import sys
import warnings
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent  # noqa: E402
sys.path.insert(0, str(project_root))  # noqa: E402

import pandas as pd  # noqa: E402
from loguru import logger  # noqa: E402
from src.models.train import ModelTrainer  # noqa: E402
from src.utils.metrics import get_classification_report  # noqa: E402

# Import plotting functions
from src.utils.plotting import plot_confusion_matrix, plot_precision_recall_curve, plot_roc_curve  # noqa: E402

warnings.filterwarnings("ignore")


def main():
    """Run model training pipeline"""
    parser = argparse.ArgumentParser(description="Run Model Training")
    parser.add_argument(
        "--data-dir",
        default="data/processed",
        help="Processed data directory (default: data/processed)",
    )
    parser.add_argument(
        "--output-dir",
        default="models",
        help="Output directory for models (default: models)",
    )
    parser.add_argument(
        "--mlflow-uri",
        default="http://127.0.0.1:5000",
        help="MLflow tracking URI (default: http://127.0.0.1:5000)",
    )
    parser.add_argument("--models", nargs="+", help="Specific models to train (default: all)")
    parser.add_argument(
        "--metric",
        default="F1-Score",
        help="Metric for best model selection (default: F1-Score)",
    )
    parser.add_argument(
        "--auto-register",
        action="store_true",
        help="Automatically register best model to MLflow Production stage",
    )
    parser.add_argument(
        "--model-name",
        default="card_approval_model",
        help="Model name for MLflow registry (default: card_approval_model)",
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("MODEL TRAINING PIPELINE")
    logger.info("=" * 80)

    try:
        # 1. Load Processed Data
        logger.info("\n1. Loading processed data...")
        data_path = Path(args.data_dir)

        X_train = pd.read_csv(data_path / "X_train.csv")
        X_test = pd.read_csv(data_path / "X_test.csv")
        y_train = pd.read_csv(data_path / "y_train.csv")["Label"]
        y_test = pd.read_csv(data_path / "y_test.csv")["Label"]

        logger.info(f"✓ X_train: {X_train.shape}")
        logger.info(f"✓ X_test: {X_test.shape}")
        logger.info(f"✓ y_train: {y_train.shape} - Good: {(y_train == 1).sum():,}, Bad: {(y_train == 0).sum():,}")
        logger.info(f"✓ y_test: {y_test.shape} - Good: {(y_test == 1).sum():,}, Bad: {(y_test == 0).sum():,}")

        # 2. Train Models
        logger.info("\n2. Training models...")

        trainer = ModelTrainer(tracking_uri=args.mlflow_uri)
        models = args.models

        results_df = trainer.train_all_models(
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            models=models,
        )

        # 3. Display Results
        logger.info("\n3. Training results...")
        logger.info("\n" + "=" * 80)
        logger.info("MODEL COMPARISON")
        logger.info("=" * 80)
        print("\n" + results_df.to_string(index=False))

        # 4. Save Results
        logger.info("\n4. Saving results...")
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save best model
        best_model_path, metadata_path = trainer.save_best_model(args.output_dir, metric=args.metric)
        logger.info(f"✓ Best model saved to: {best_model_path}")
        logger.info(f"✓ Model metadata saved to: {metadata_path}")

        # Save comparison results
        trainer.save_comparison_results(args.output_dir)
        logger.info(f"✓ Comparison results saved to: {output_path / 'model_comparison.csv'}")

        # Save training summary
        trainer.create_training_summary(X_train, X_test, args.output_dir)
        logger.info(f"✓ Training summary saved to: {output_path / 'training_summary.txt'}")

        # 5. Generate Evaluation Visualizations
        logger.info("\n5. Generating evaluation visualizations...")

        # Load best model
        best_model = trainer.trained_models[trainer.best_model_name]

        # Generate predictions
        y_pred = best_model.predict(X_test)
        y_pred_proba = best_model.predict_proba(X_test)[:, 1] if hasattr(best_model, "predict_proba") else None

        # Create evaluation directory
        eval_dir = output_path / "evaluation"
        eval_dir.mkdir(exist_ok=True)

        # Generate and save visualizations
        plot_confusion_matrix(y_test, y_pred, save_path=str(eval_dir / "confusion_matrix.png"))
        logger.info(f"✓ Confusion matrix saved to: {eval_dir / 'confusion_matrix.png'}")

        if y_pred_proba is not None:
            plot_roc_curve(y_test, y_pred_proba, save_path=str(eval_dir / "roc_curve.png"))
            logger.info(f"✓ ROC curve saved to: {eval_dir / 'roc_curve.png'}")

            plot_precision_recall_curve(
                y_test,
                y_pred_proba,
                save_path=str(eval_dir / "precision_recall_curve.png"),
            )
            logger.info(f"✓ Precision-Recall curve saved to: {eval_dir / 'precision_recall_curve.png'}")

        # Save classification report
        report = get_classification_report(y_test, y_pred)
        report_path = eval_dir / "classification_report.txt"
        with open(report_path, "w") as f:
            f.write(report)
        logger.info(f"✓ Classification report saved to: {report_path}")

        # Display best model info
        logger.info("\n" + "=" * 80)
        logger.info(f"🏆 BEST MODEL: {trainer.best_model_name}")
        logger.info("=" * 80)
        logger.info(f"Metric ({args.metric}): {trainer.best_score}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ TRAINING & EVALUATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Results saved to: {args.output_dir}")
        logger.info(f"Evaluation plots: {eval_dir}")
        logger.info(f"MLflow UI: {args.mlflow_uri}")

        # Auto-register best model to Production
        if args.auto_register:
            logger.info("\n" + "=" * 80)
            logger.info("🚀 AUTO-REGISTERING BEST MODEL TO PRODUCTION")
            logger.info("=" * 80)

            try:
                from src.utils.mlflow_registry import MLflowRegistry

                registry = MLflowRegistry(tracking_uri=args.mlflow_uri)

                # Get the best run ID
                best_run_id = trainer.best_model_run_id

                # Register model
                registration_info = registry.register_model(run_id=best_run_id, model_name=args.model_name)

                model_version = registration_info["version"]

                # Add description to the registered version
                description = f"Auto-registered: {trainer.best_model_name} | {args.metric}={trainer.best_score}"
                registry.add_version_description(
                    model_name=args.model_name, version=model_version, description=description
                )

                # Transition to Production
                registry.transition_model_stage(model_name=args.model_name, version=model_version, stage="Production")

                logger.info(f"✅ Model registered: {args.model_name} v{model_version}")
                logger.info(f"✅ Transitioned to Production stage")
                logger.info(f"🎯 Run ID: {best_run_id}")

            except Exception as e:
                logger.warning(f"⚠️  Auto-registration failed: {e}")
                logger.info("You can manually register using:")
                logger.info(
                    f"  python scripts/register_model.py --run-id {trainer.best_model_run_id} --model-name {args.model_name} --stage Production"
                )

        return 0

    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
