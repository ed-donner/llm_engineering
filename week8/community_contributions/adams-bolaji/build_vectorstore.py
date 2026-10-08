"""
Build the Chroma vector store of sold properties (comps) for RAG retrieval.
Run from project root or week8: uv run python community_contributions/adams-bolaji/build_vectorstore.py
"""
import json
import sys
from pathlib import Path

# Add week8 and adams-bolaji to path
WEEK8 = Path(__file__).resolve().parent.parent.parent
ADAMS = Path(__file__).resolve().parent
if str(WEEK8) not in sys.path:
    sys.path.insert(0, str(WEEK8))
if str(ADAMS) not in sys.path:
    sys.path.insert(0, str(ADAMS))

from models import SoldProperty
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

DB_PATH = ADAMS / "real_estate_vectorstore"
COLLECTION_NAME = "sold_properties"
DATA_PATH = ADAMS / "data" / "sold_properties.json"


def normalize_property(raw: dict) -> SoldProperty:
    """Convert raw JSON (beds/baths/price or full schema) to SoldProperty."""
    # Handle alternate field names
    bedrooms = raw.get("bedrooms") or raw.get("beds", 0)
    bathrooms = float(raw.get("bathrooms") or raw.get("baths", 0))
    sale_price = float(raw.get("sale_price") or raw.get("price", 0))
    city = raw.get("city", "Austin")
    state = raw.get("state", "TX")
    zip_code = raw.get("zip_code", "78700")
    address = raw.get("address", "")
    sale_date = raw.get("sale_date", "2024-01-01")
    year_built = raw.get("year_built")
    description = raw.get("description", "")

    return SoldProperty(
        address=address,
        city=city,
        state=state,
        zip_code=str(zip_code),
        bedrooms=int(bedrooms),
        bathrooms=bathrooms,
        sqft=int(raw.get("sqft", 0)),
        lot_sqft=raw.get("lot_sqft"),
        year_built=year_built,
        sale_price=sale_price,
        sale_date=str(sale_date),
        description=description or "",
    )


def main():
    print("Loading sold properties...")
    with open(DATA_PATH) as f:
        raw_list = json.load(f)

    properties = [normalize_property(p) for p in raw_list]
    print(f"Loaded {len(properties)} properties")

    client = chromadb.PersistentClient(path=str(DB_PATH))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)
    encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    print("Encoding and adding to Chroma...")
    documents = [p.to_document() for p in properties]
    vectors = encoder.encode(documents).astype(float).tolist()
    metadatas = [{"sale_price": p.sale_price, "address": p.address} for p in properties]
    ids = [f"prop_{i}" for i in range(len(properties))]

    collection.add(ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas)
    print(f"Vector store built at {DB_PATH} with {len(properties)} comps")


if __name__ == "__main__":
    main()
