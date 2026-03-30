import chromadb
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
from tqdm import tqdm

encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./vectorstore/chroma_db")

collection = client.get_or_create_collection("papers")

dataset = load_dataset("ccdv/arxiv-summarization")

rows = dataset["train"].select(range(5000))

for i, row in tqdm(enumerate(rows)):

    text = row["abstract"]

    vector = encoder.encode([text]).tolist()

    collection.add(
        ids=[str(i)],
        documents=[text],
        embeddings=vector
    )