#!/usr/bin/env python3
"""
Download model artifacts from MLflow for embedding into Docker image.

This script downloads the production model from MLflow registry to a local
directory, which can then be baked into the Docker image at build time.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import mlflow


def download_model(
    tracking_uri: str,
    model_name: str,
    stage: str,
    output_dir: str,
) -> dict:
    """
    Download model artifacts from MLflow registry.

    Args:
        tracking_uri: MLflow tracking server URL
        model_name: Name of the registered model
        stage: Model stage (Production, Staging, etc.)
        output_dir: Local directory to save model artifacts

    Returns:
        Dictionary with model metadata (version, run_id, etc.)
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
    source = latest.source

    print(f"📦 Found model: {model_name} v{version} ({stage})", file=sys.stderr)
    print(f"   Run ID: {run_id}", file=sys.stderr)
    print(f"   Source: {source}", file=sys.stderr)

    # Prepare output directory
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Download model artifacts
    model_uri = f"models:/{model_name}/{version}"
    print(f"\n⬇️  Downloading model artifacts to: {output_path}", file=sys.stderr)

    # Download the model using mlflow
    local_path = mlflow.artifacts.download_artifacts(
        artifact_uri=model_uri,
        dst_path=str(output_path),
    )

    print(f"✅ Model downloaded to: {local_path}", file=sys.stderr)

    # Also download preprocessing artifacts from the same run
    print(f"\n⬇️  Downloading preprocessing artifacts from run: {run_id}", file=sys.stderr)
    try:
        preprocessing_path = output_path / "preprocessing"
        preprocessing_path.mkdir(parents=True, exist_ok=True)

        # Download preprocessing artifacts
        mlflow.artifacts.download_artifacts(
            run_id=run_id,
            artifact_path="preprocessing",
            dst_path=str(preprocessing_path.parent),
        )
        print(f"Preprocessing artifacts downloaded", file=sys.stderr)
    except Exception as e:
        print(f"Could not download preprocessing artifacts: {e}", file=sys.stderr)
        print("   Preprocessing will use MLflow at runtime if needed", file=sys.stderr)

    # Save model metadata
    metadata = {
        "model_name": model_name,
        "version": version,
        "run_id": run_id,
        "stage": stage,
        "source": source,
    }

    metadata_path = output_path / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"📝 Metadata saved to: {metadata_path}", file=sys.stderr)

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Download model from MLflow for Docker image embedding")
    parser.add_argument(
        "--tracking-uri",
        type=str,
        default=os.environ.get("MLFLOW_TRACKING_URI"),
        help="MLflow tracking URI",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=os.environ.get("MODEL_NAME", "card_approval_model"),
        help="Model name in MLflow registry",
    )
    parser.add_argument(
        "--model-stage",
        type=str,
        default=os.environ.get("MODEL_STAGE", "Production"),
        help="Model stage to download",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Output directory for model artifacts (default: models)",
    )
    parser.add_argument(
        "--output-env-file",
        type=str,
        default=None,
        help="Output file for environment variables (for CI/CD)",
    )

    args = parser.parse_args()

    if not args.tracking_uri:
        print("❌ ERROR: MLFLOW_TRACKING_URI not set", file=sys.stderr)
        sys.exit(1)

    print("=" * 60, file=sys.stderr)
    print("📥 MODEL DOWNLOAD FOR DOCKER BUILD", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"   MLflow URI: {args.tracking_uri}", file=sys.stderr)
    print(f"   Model: {args.model_name} ({args.model_stage})", file=sys.stderr)
    print(f"   Output: {args.output_dir}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    try:
        metadata = download_model(
            tracking_uri=args.tracking_uri,
            model_name=args.model_name,
            stage=args.model_stage,
            output_dir=args.output_dir,
        )

        # Output for CI/CD
        if args.output_env_file:
            env_path = Path(args.output_env_file)
            env_path.parent.mkdir(parents=True, exist_ok=True)
            with open(env_path, "w") as f:
                f.write(f"MODEL_VERSION={metadata['version']}\n")
                f.write(f"MODEL_RUN_ID={metadata['run_id']}\n")
            print(f"📝 Environment file written to: {env_path}", file=sys.stderr)

        print("\n" + "=" * 60, file=sys.stderr)
        print("✅ MODEL DOWNLOAD COMPLETE", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"   Version: {metadata['version']}", file=sys.stderr)
        print(f"   Run ID: {metadata['run_id']}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
