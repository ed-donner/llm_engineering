"""
Build ChromaDB vector store for FrontierAgent RAG.
Run from week8: python community_contributions/winniekariuki/build_vectorstore.py
"""
import os
import sys
from pathlib import Path

# Paths: week8 for cwd, week6 for pricer
week8 = Path(__file__).resolve().parent.parent.parent
week6 = week8.parent / "week6"
sys.path.insert(0, str(week6))
sys.path.insert(0, str(week8))

from dotenv import load_dotenv
load_dotenv(override=True)

from huggingface_hub import login
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Use pricer Item if available, else load from datasets
try:
    from pricer.items import Item
    DATASET = "ed-donner/items_lite"
    train, val, test = Item.from_hub(DATASET)
    items = train + val + test  # Item has .summary, .price, .category

    def description(item):
        return item.summary if hasattr(item, 'summary') else str(item)
    def price(item):
        return item.price
    def category(item):
        return getattr(item, 'category', 'Electronics')
except ImportError:
    from datasets import load_dataset
    ds = load_dataset("ed-donner/items_lite")
    splits = ["train", "validation", "test"] if "validation" in ds else ["train", "val", "test"]
    items = []
    for s in splits:
        if s in ds:
            items.extend(list(ds[s]))

    def description(item):
        return item.get("summary", item.get("title", str(item)))
    def price(item):
        return float(item.get("price", 0))
    def category(item):
        return item.get("category", "Electronics")

DB = "products_vectorstore"
BATCH_SIZE = 256

if __name__ == "__main__":
    os.chdir(week8)  # DB lives in week8/ for deal_agent_framework
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        login(token=hf_token, add_to_git_credential=False)

    client = chromadb.PersistentClient(path=DB)
    if "products" in [c.name for c in client.list_collections()]:
        client.delete_collection("products")
    collection = client.create_collection("products", metadata={"hnsw:space": "cosine"})

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    docs = [description(item) for item in items]
    categories = [category(item) for item in items]
    prices = [price(item) for item in items]

    for i in tqdm(range(0, len(docs), BATCH_SIZE), desc="Adding to ChromaDB"):
        batch = docs[i : i + BATCH_SIZE]
        embeddings = model.encode(batch)
        ids = [f"doc_{i+j}" for j in range(len(batch))]
        metadatas = [
            {"category": c, "price": p} for c, p in zip(
                categories[i : i + BATCH_SIZE],
                prices[i : i + BATCH_SIZE],
            )
        ]
        collection.add(ids=ids, embeddings=embeddings.tolist(), documents=batch, metadatas=metadatas)

    print(f"Built {DB}/ with {len(docs):,} documents.")
