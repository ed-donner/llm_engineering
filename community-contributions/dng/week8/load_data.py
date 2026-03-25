import os

import chromadb
from dotenv import load_dotenv
from huggingface_hub import login
from items import Item
from sentence_transformers import SentenceTransformer
from tqdm.notebook import tqdm

load_dotenv(override=True)
DB = "products_vectorstore"


def load_items():
    hf_token = os.environ["HF_TOKEN"]
    login(token=hf_token, add_to_git_credential=False)
    username = "ed-donner"
    dataset = f"{username}/items_lite"

    train, val, test = Item.from_hub(dataset)

    print(
        f"Loaded {len(train):,} training items, {len(val):,} validation items, {len(test):,} test items"
    )
    client = chromadb.PersistentClient(path=DB)
    encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Check if the collection exists; if not, create it

    collection_name = "products"
    existing_collection_names = [
        collection.name for collection in client.list_collections()
    ]

    if collection_name not in existing_collection_names:
        collection = client.create_collection(collection_name)
        for i in tqdm(range(0, len(train), 1000)):
            documents = [item.summary for item in train[i : i + 1000]]
            vectors = encoder.encode(documents).astype(float).tolist()
            metadatas = [
                {"category": item.category, "price": item.price}
                for item in train[i : i + 1000]
            ]
            ids = [f"doc_{j}" for j in range(i, i + 1000)]
            ids = ids[: len(documents)]
            collection.add(
                ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas
            )

    collection = client.get_or_create_collection(collection_name)
    return collection
