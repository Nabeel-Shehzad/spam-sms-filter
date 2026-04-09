"""
Downloads the UCI SMS Spam Collection dataset and saves it to data/raw/.
Dataset source: UCI Machine Learning Repository
"""

import urllib.request
import zipfile
import os
import shutil

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"


def download():
    os.makedirs(RAW_DIR, exist_ok=True)
    zip_path = os.path.join(RAW_DIR, "smsspamcollection.zip")

    print("Downloading UCI SMS Spam Collection...")
    urllib.request.urlretrieve(URL, zip_path)

    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(RAW_DIR)

    # The extracted file is named 'SMSSpamCollection' (no extension, tab-separated)
    src = os.path.join(RAW_DIR, "SMSSpamCollection")
    dst = os.path.join(RAW_DIR, "SMSSpamCollection.tsv")
    if os.path.exists(src):
        shutil.move(src, dst)

    os.remove(zip_path)
    print(f"Dataset saved to: {dst}")


if __name__ == "__main__":
    download()
