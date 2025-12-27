import os

import kaggle


def download_dataset():
    DATASET = "rikdifos/credit-card-approval-prediction"
    TARGET_DIR = "../cap_model/data/raw"

    print(f"[INFO] Creating target directory: {TARGET_DIR}")
    os.makedirs(TARGET_DIR, exist_ok=True)

    print(f"[INFO] Downloading dataset: {DATASET}")
    kaggle.api.dataset_download_files(dataset=DATASET, path=TARGET_DIR, unzip=True)

    print(f"[DONE] Dataset downloaded and extracted to: {TARGET_DIR}")


if __name__ == "__main__":
    download_dataset()
