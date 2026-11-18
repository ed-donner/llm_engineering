import io
import os
import sys
import modal
from huggingface_hub import hf_hub_download
from datasets import load_dataset, Dataset, DatasetDict
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import StandardScaler
import torch
from pathlib import Path
import shutil
from xgboost import XGBRegressor
import numpy as np
import pandas as pd

from util import Tester

app = modal.App()

volume_name = "ed-donner-price-prediction"
volume = modal.Volume.from_name(volume_name, create_if_missing=True)

@app.function(
    image = modal.Image.debian_slim().pip_install(
        "huggingface_hub", "sentence-transformers", "torch", "datasets == 3.6.0"
    ),
    volumes = {"/mnt/data": volume},
    secrets = [modal.Secret.from_name("huggingface-secret")],
    gpu = "T4",
    timeout = 5*3600,
)
def run_embedding(dataset_name: str, embedding_model: str, batch_size: int = 64) -> tuple[str, str]:
    # get device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Download the dataset from Hugging Face
    dataset = load_dataset(dataset_name)
    
    # get the model from huggingface hub
    embeddings = SentenceTransformer(embedding_model).to(device)
    
    def embed_batch(batch):
        vectors = embeddings.encode(batch['prompt'])
        return {'embedding': vectors}

    for subset in ['train', 'test', 'val']:
        print(f"Embedding {subset} set...")
        dataset[subset] = dataset[subset].map(
            embed_batch,
            batched=True,
            batch_size = batch_size,
            desc= f"Embedding {subset} set",
        )
    
    # Save the dataset to a temporary directory
    file_name = dataset_name.split("/")[-1] + "_embedded_" + embedding_model.split("/")[-1]
    tmp_dir = Path("/tmp/data")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    file_path = tmp_dir / file_name
    dataset.save_to_disk(file_path)
    
    # Move the dataset to the volume
    volume_file_path = Path("/mnt/data") / file_name
    shutil.copytree(file_path, volume_file_path, dirs_exist_ok=True)
    
    volume.commit()

    return volume_name, file_name


@app.function(
    image = modal.Image.debian_slim().pip_install(
        "sentence-transformers", "torch", "datasets == 3.6.0", "plotly == 6.4.0", "xgboost == 3.1.1","numpy == 2.3.4", "scikit-learn == 1.7.2", "pandas == 2.3.3", "ipython == 9.7.0"
    ).add_local_python_source("util"),
    volumes = {"/mnt/data": volume},
    secrets = [modal.Secret.from_name("huggingface-secret")],
    timeout = 5*3600,
    nonpreemptible=True,
)
def train_evaluate_xgboost(file_name: str) -> list[dict]:
    # Load the dataset from the volume
    dataset_path = Path("/mnt/data") / file_name
    dataset = DatasetDict.load_from_disk(dataset_path)

    # Train and evaluate the XGBoost model
    # price string to float
    dataset = dataset.with_format("numpy")
    dataset = dataset.map(lambda x : {'completion': float(x['completion'])}, batched=False)

    # price normalization
    scaler = StandardScaler()
    scaler.fit(np.array(dataset['train']['completion']).reshape(-1, 1))

    def normalize(batch):
        arr = np.asarray(batch["completion"], dtype=np.float64).reshape(-1, 1)
        return {"completion": scaler.transform(arr).flatten().tolist()}

    train_dataset = dataset['train'].map(normalize, batched=True)
    val_dataset = dataset['val'].map(normalize, batched=True)

    X_train = np.asarray(train_dataset['embedding'], dtype=np.float32)
    y_train = train_dataset['completion']

    X_val = np.asarray(val_dataset['embedding'], dtype=np.float32)
    y_val = val_dataset['completion']

    model = XGBRegressor(
        n_estimators=5000,
        max_depth=8,
        learning_rate=1e-1,
        early_stopping_rounds=10,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=True,
    )
    
    def model_predict(item):
        inputs = item['embedding']
        
        prediction = model.predict(np.array([inputs], dtype=np.float32))
        return scaler.inverse_transform(np.array([prediction], dtype=np.float64)).flatten().tolist()[0]
    
    # Create a Tester instance
    tester = Tester(model_predict, dataset['test'], 200)
    
    tester.run()
    
    # save results
    result_df = pd.DataFrame({
        "title": tester.titles,
        "guess": tester.guesses,
        "truth": tester.truths,
        "error": tester.errors,
        "color": tester.colors,
    })
    result_df.to_csv(Path("/mnt/data") / "results.csv", index=False)
    

    return result_df.to_dict(orient="records")
