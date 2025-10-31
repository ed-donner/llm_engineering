#!/usr/bin/env python3
"""
Build a ChromaDB vector store ('products_vectorstore') with product documents and embeddings.
Streaming from McAuley-Lab/Amazon-Reviews-2023 raw_meta_* datasets.
"""

from itertools import islice
from typing import List, Dict, Iterable

import argparse
import chromadb
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from logging_utils import init_logger
import config as cfg

logger = init_logger("DealIntel.BuildVectorStore")

def text_for(dp: Dict) -> str:
    """
    Construct product text from typical raw_meta_* fields: title + description + features + details.
    """
    title = dp.get("title") or ""
    description = "\n".join(dp.get("description") or [])
    features = "\n".join(dp.get("features") or [])
    details = (dp.get("details") or "").strip()
    parts = [title, description, features, details]
    return "\n".join([p for p in parts if p])

def stream_category(category: str) -> Iterable[Dict]:
    """
    Stream datapoints from raw_meta_{category}.
    """
    ds = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_meta_{category}",
        split="full",
        trust_remote_code=True,
        streaming=True,
    )
    return ds

def build(categories: List[str], max_items_per_category: int, batch_size: int):
    logger.info(f"Initializing DB at '{cfg.DB_PATH}' collection '{cfg.COLLECTION_NAME}'")
    client = chromadb.PersistentClient(path=cfg.DB_PATH)
    collection = client.get_or_create_collection(cfg.COLLECTION_NAME)

    logger.info(f"Loading embedding model '{cfg.MODEL_NAME}'")
    model = SentenceTransformer(cfg.MODEL_NAME)

    total_added = 0
    for category in categories:
        logger.info(f"Category {category}: targeting up to {max_items_per_category} items")
        stream = stream_category(category)
        limited = islice(stream, max_items_per_category)

        buffer_docs: List[str] = []
        buffer_embeddings: List[List[float]] = []
        buffer_metadatas: List[Dict] = []
        buffer_ids: List[str] = []
        count = 0

        for dp in tqdm(limited, total=max_items_per_category, desc=f"{category}"):
            price = dp.get("price")
            if not price:
                continue
            try:
                price_val = float(price)
            except Exception:
                continue

            doc = text_for(dp)
            if not doc or len(doc) < 50:
                continue

            buffer_docs.append(doc)
            buffer_metadatas.append({"price": price_val, "category": category})
            buffer_ids.append(f"{category}-{dp.get('asin', str(count))}")
            count += 1

            if len(buffer_docs) >= batch_size:
                embeddings = model.encode(buffer_docs, show_progress_bar=False)
                buffer_embeddings = [emb.tolist() for emb in embeddings]
                collection.add(
                    ids=buffer_ids,
                    documents=buffer_docs,
                    metadatas=buffer_metadatas,
                    embeddings=buffer_embeddings,
                )
                total_added += len(buffer_docs)
                buffer_docs.clear()
                buffer_embeddings.clear()
                buffer_metadatas.clear()
                buffer_ids.clear()

        if buffer_docs:
            embeddings = model.encode(buffer_docs, show_progress_bar=False)
            buffer_embeddings = [emb.tolist() for emb in embeddings]
            collection.add(
                ids=buffer_ids,
                documents=buffer_docs,
                metadatas=buffer_metadatas,
                embeddings=buffer_embeddings,
            )
            total_added += len(buffer_docs)

        logger.info(f"Category {category}: added {count} items")

    logger.info(f"Completed build. Total items added: {total_added}")

def main():
    parser = argparse.ArgumentParser(description="Build ChromaDB vector store")
    parser.add_argument("--categories", nargs="*", default=cfg.CATEGORIES, help="Categories to ingest")
    parser.add_argument("--max-per-category", type=int, default=cfg.MAX_ITEMS_PER_CATEGORY)
    parser.add_argument("--batch-size", type=int, default=cfg.BATCH_SIZE)
    args = parser.parse_args()

    build(args.categories, args.max_per_category, args.batch_size)

if __name__ == "__main__":
    main()