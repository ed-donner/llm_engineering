import hashlib
import pandas as pd

def hash_row(row: pd.Series) -> str:
    """Compute MD5 hash for a row to detect duplicates."""
    return hashlib.md5(str(tuple(row)).encode()).hexdigest()


def sample_reference(reference_df: pd.DataFrame, n_reference_rows: int) -> list:
    """Return a fresh sample of reference data for batch generation."""
    if reference_df is not None and not reference_df.empty:
        sample_df = reference_df.sample(min(n_reference_rows, len(reference_df)), replace=False)
        return sample_df.to_dict(orient="records")
    return []
