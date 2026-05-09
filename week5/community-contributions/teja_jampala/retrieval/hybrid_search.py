import os
import chromadb
from retrieval.synonym_expander import expand_query
from ingestion.embedder import get_embedding

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

print("📦 Chroma path:", CHROMA_DIR)


def keyword_score(doc, q):
    return sum(1 for t in q.split() if t in doc.lower())


def hybrid_search(query, top_k=10):
    q = expand_query(query)

    embedding = get_embedding(q)

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_collection("mapping_docs")

    res = col.query(query_embeddings=[embedding], n_results=20)

    docs = res["documents"][0]
    metas = res["metadatas"][0]

    print("🔍 SEARCH RESULTS RAW:", metas)

    sql_results = []
    mapping_results = []

    for d, m in zip(docs, metas):
        score = keyword_score(d, q)

        record = {
            "document": d,
            "metadata": m,
            "score": score
        }

        if m.get("type") == "sql":
            sql_results.append(record)
        elif m.get("type") == "mapping":
            mapping_results.append(record)

    # 🔥 Sort individually
    sql_results.sort(key=lambda x: x["score"], reverse=True)
    mapping_results.sort(key=lambda x: x["score"], reverse=True)

    # 🔥 BALANCE OUTPUT (IMPORTANT)
    final = []

    # take top mapping first
    final.extend(mapping_results[:top_k // 2])

    # then SQL
    final.extend(sql_results[:top_k // 2])

    # fallback if one is empty
    if not final:
        all_results = sql_results + mapping_results
        all_results.sort(key=lambda x: x["score"], reverse=True)
        final = all_results[:top_k]

    return [{"document": r["document"], "metadata": r["metadata"]} for r in final]