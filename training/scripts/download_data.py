import argparse
import os

import kaggle


def download_dataset(output_dir: str = "data/raw") -> None:
    """Download and extract the credit card approval dataset."""
    dataset = "rikdifos/credit-card-approval-prediction"

    print(f"[INFO] Creating target directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"[INFO] Downloading dataset: {dataset}")
    kaggle.api.dataset_download_files(dataset=dataset, path=output_dir, unzip=True)

    print(f"[DONE] Dataset downloaded and extracted to: {output_dir}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Download Credit Card Approval dataset")
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Output directory for raw data (default: data/raw)",
    )
    args = parser.parse_args()

    download_dataset(args.output_dir)
    return 0


if __name__ == "__main__":
    exit(main())
