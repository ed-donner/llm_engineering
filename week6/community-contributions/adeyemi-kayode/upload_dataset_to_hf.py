"""
Upload the Africa flight price CSV to Hugging Face as a dataset.
Run once (with HF_TOKEN set or `huggingface-cli login`) so the notebook can load
the data with: load_dataset("Karosi/africa-flight-prices")
"""
from pathlib import Path

import pandas as pd
from datasets import Dataset

HF_DATASET_ID = "Karosi/africa-flight-prices"

def main():
    data_path = Path(__file__).parent / "data" / "flight_prices_africa.csv"
    df = pd.read_csv(data_path)
    df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
    dataset = Dataset.from_pandas(df)
    dataset.push_to_hub(HF_DATASET_ID)
    print(f"Uploaded to https://huggingface.co/datasets/{HF_DATASET_ID}")

if __name__ == "__main__":
    main()
