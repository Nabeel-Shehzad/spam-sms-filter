"""
Entry point to run the full ML training pipeline.

Usage:
    python run_training.py

Steps:
    1. Downloads dataset if not present
    2. Preprocesses all messages
    3. Trains Naive Bayes, SVM, and LSTM models
    4. Saves best model + vectorizers to models/
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "SMSSpamCollection.tsv")


def main():
    # Step 1: Download dataset if missing
    if not os.path.exists(DATA_PATH):
        print("Dataset not found. Downloading...")
        from data.download_dataset import download
        download()
    else:
        print(f"Dataset found: {DATA_PATH}")

    # Step 2-6: Run full training pipeline
    from backend.ml.train import run_training
    run_training()


if __name__ == "__main__":
    main()
