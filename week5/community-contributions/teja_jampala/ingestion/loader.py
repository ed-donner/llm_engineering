import sys
import os
import hashlib
import shutil
import time

# ✅ Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chromadb
from ingestion.parser import parse_files
from ingestion.embedder import get_embedding
from ingestion.file_tracker import load_hash, save_hash
from ingestion.sql_lineage_parser import process_sql_file
from retrieval.graph_store import graph

# -------------------------------
# BASE PATHS
# -------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# -------------------------------
# HELPER: Normalize records
# -------------------------------
def normalize_record(record):
    """
    Supports:
    - (doc, meta)
    - {"text": ..., "metadata": ...}
    """
    if isinstance(record, tuple) and len(record) == 2:
        return record

    elif isinstance(record, dict):
        return record.get("text", ""), record.get("metadata", {})

    else:
        return None, None


# -------------------------------
# MAIN LOADER
# -------------------------------
def load_all(data_path=None):

    if data_path is None:
        data_path = DATA_DIR

    print(f"📂 Loading data from: {data_path}")

    # -------------------------------
    # RESET CHROMA (FRESH LOAD)
    # -------------------------------
    if os.path.exists(CHROMA_DIR):
        print("🧹 Deleting existing ChromaDB...")

    try:
        shutil.rmtree(CHROMA_DIR)
        time.sleep(1)  # 🔥 allow OS to release lock
    except Exception as e:
        print(f"⚠️ Delete failed: {e}")

    print("📁 Exists after delete:", os.path.exists(CHROMA_DIR))    

    # recreate clean dir
    os.makedirs(CHROMA_DIR, exist_ok=True)

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    print("Collections:", client.list_collections())
    col = client.get_or_create_collection("mapping_docs")
    

    # -------------------------------
    # HASH TRACKING
    # -------------------------------
    old_hash = load_hash()
    new_hash = {}
    seen_ids = set()

    docs, metas, ids, embeds = [], [], [], []

    # -------------------------------
    # 1️⃣ LOAD MAPPING FILES
    # -------------------------------
    print("📊 Parsing mapping files...")

    try:
        mapping_records = parse_files(data_path)

        print(f"📊 Mapping records count: {len(mapping_records)}")

        for record in mapping_records:

            doc, meta = normalize_record(record)

            if not doc:
                print(f"⚠️ Skipping invalid mapping record: {record}")
                continue

            hid = hashlib.md5(doc.encode()).hexdigest()

            if hid in old_hash or hid in seen_ids:
                continue

            seen_ids.add(hid)
            new_hash[hid] = True

            docs.append(doc)
            metas.append(meta)
            ids.append(hid)
            embeds.append(get_embedding(doc))

    except Exception as e:
        print(f"❌ Error parsing mapping files: {e}")

    # -------------------------------
    # 2️⃣ LOAD SQL FILES
    # -------------------------------
    print("🧠 Parsing SQL files...")

    for file in os.listdir(data_path):

        if not file.endswith(".sql"):
            continue

        path = os.path.join(data_path, file)

        try:
            sql_records, lineage, table = process_sql_file(path)

            # ✅ Add lineage to graph
            graph.add_sql_lineage(lineage, table)

            for record in sql_records:

                doc, meta = normalize_record(record)

                if not doc:
                    print(f"⚠️ Skipping invalid SQL record: {record}")
                    continue

                hid = hashlib.md5(doc.encode()).hexdigest()

                if hid in old_hash or hid in seen_ids:
                    continue

                seen_ids.add(hid)
                new_hash[hid] = True

                docs.append(doc)
                metas.append(meta)
                ids.append(hid)
                embeds.append(get_embedding(doc))

        except Exception as e:
            print(f"❌ Error processing SQL file {file}: {e}") 

    # -------------------------------
    # 3️⃣ INSERT INTO CHROMA
    # -------------------------------
    if docs:
        print(f"🚀 Inserting {len(docs)} new records...")

        col.add(
            documents=docs,
            metadatas=metas,
            ids=ids,
            embeddings=embeds
        )

    else:
        print("✅ No new records to insert")

    # -------------------------------
    # SAVE HASH STATE
    # -------------------------------
    save_hash(new_hash)

    print("✅ Data loading complete!")

# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    load_all()