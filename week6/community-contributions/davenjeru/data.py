"""Data loading, filtering, and train/val/test splitting."""
import kagglehub
import pandas as pd
from sklearn.model_selection import train_test_split
import os

PRICE_MIN = 50_000
PRICE_MAX = 2_000_000


def load_raw_data() -> pd.DataFrame:
    """Load USA Real Estate dataset from Kaggle.
    
    Downloads the dataset and finds the CSV file automatically.
    """
    dataset_path = kagglehub.dataset_download("ahmedshahriarsakib/usa-real-estate-dataset")
    
    csv_files = [f for f in os.listdir(dataset_path) if f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {dataset_path}")
    
    csv_path = os.path.join(dataset_path, csv_files[0])
    print(f"Loading data from: {csv_path}")
    
    return pd.read_csv(csv_path)


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply quality filters: price range, non-null required fields."""
    filtered = df[
        (df['price'] >= PRICE_MIN) & 
        (df['price'] <= PRICE_MAX) &
        (df['bed'].notna()) &
        (df['bath'].notna()) &
        (df['house_size'].notna())
    ].copy()
    
    filtered = filtered.drop_duplicates(
        subset=['bed', 'bath', 'house_size', 'city', 'state', 'price']
    )
    
    return filtered


def create_splits(
    df: pd.DataFrame, 
    train_size: int = 500, 
    val_size: int = 50, 
    test_size: int = 50,
    random_state: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified sampling by price bucket, return train/val/test DataFrames."""
    df = df.copy()
    
    df['price_bucket'] = pd.qcut(
        df['price'], q=10, labels=False, duplicates='drop'
    )
    
    total_needed = train_size + val_size + test_size
    samples_per_bucket = total_needed // 10 + 1
    
    sampled = df.groupby('price_bucket', group_keys=False).apply(
        lambda x: x.sample(
            n=min(len(x), samples_per_bucket), 
            random_state=random_state
        )
    )
    
    sampled = sampled.drop(columns=['price_bucket'])
    
    train_val, test = train_test_split(
        sampled, 
        test_size=test_size, 
        random_state=random_state
    )
    train, val = train_test_split(
        train_val, 
        test_size=val_size, 
        random_state=random_state
    )
    
    return (
        train.reset_index(drop=True), 
        val.reset_index(drop=True), 
        test.reset_index(drop=True)
    )
