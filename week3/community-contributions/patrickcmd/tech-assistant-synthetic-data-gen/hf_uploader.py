import pandas as pd
from datasets import Dataset
from huggingface_hub import login


def upload_to_huggingface(
    df: pd.DataFrame,
    hf_username: str,
    hf_token: str,
    dataset_name: str,
) -> str:
    """
    Upload a DataFrame to HuggingFace Hub.

    Returns:
        URL of the uploaded dataset.
    """
    login(token=hf_token)

    repo_id = f"{hf_username}/{dataset_name}"
    dataset = Dataset.from_pandas(df)
    dataset.push_to_hub(repo_id, private=False)

    return f"https://huggingface.co/datasets/{repo_id}"