import chromadb
from sentence_transformers import SentenceTransformer
from config import VECTOR_DB_PATH

encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
collection = client.get_or_create_collection("papers")


def find_similar(summary, k=3):

    vector = encoder.encode([summary]).tolist()

    results = collection.query(query_embeddings=vector, n_results=k)

    docs = results["documents"][0]

    return docs