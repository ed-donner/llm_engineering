#!/usr/bin/env python3
"""
Download tope-ai-labs data from Google Drive and extract into the current directory.
Requires: pip install gdown
Run from the tope-ai-labs folder.

To use: set GOOGLE_DRIVE_FILE_ID below to the ID from your shareable link, then run:
  python download_data.py
"""
import os
import sys
import zipfile
from pathlib import Path

# Replace with the file ID from your Google Drive shareable link.
# Link format: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
GOOGLE_DRIVE_FILE_ID = "YOUR_FILE_ID_HERE"
ZIP_NAME = "tope-ai-labs-data.zip"


def main():
    if GOOGLE_DRIVE_FILE_ID == "YOUR_FILE_ID_HERE":
        print("Please set GOOGLE_DRIVE_FILE_ID in this script to your Google Drive file ID.")
        print("Get it from the shareable link: https://drive.google.com/file/d/<FILE_ID>/view?usp=sharing")
        sys.exit(1)

    try:
        import gdown
    except ImportError:
        print("Install gdown first: pip install gdown")
        sys.exit(1)

    here = Path(__file__).resolve().parent
    zip_path = here / ZIP_NAME

    print(f"Downloading {ZIP_NAME} from Google Drive...")
    url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_FILE_ID}"
    gdown.download(url, str(zip_path), quiet=False, fuzzy=True)

    if not zip_path.exists():
        print("Download failed.")
        sys.exit(1)

    print(f"Extracting to {here}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(here)
    zip_path.unlink()
    print("Done. You can run the notebook now.")


if __name__ == "__main__":
    main()
