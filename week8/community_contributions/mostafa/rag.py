import chromadb
from chromadb.utils import embedding_functions
import os
import glob
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Paths
KB_DIR = "kb_articles"
CHROMA_PATH = "./chroma_data"
COLLECTION_NAME = "security_kb"

# Embedding function using sentence-transformers
# encoder = embedding_functions.SentenceTransformerEmbeddingFunction(
    # model_name="sentence-transformers/all-MiniLM-L6-v2"
# )

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)

encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_collection(rebuild=False):
    """Get or create the persistent Chroma collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return collection

def load_articles_to_chroma():
    """Read all .txt and .md files from KB_DIR and add to Chroma."""
    collection = get_collection(rebuild=True)
    docs = []
    metadatas = []
    ids = []
    file_paths = glob.glob(os.path.join(KB_DIR, "*.txt")) + glob.glob(os.path.join(KB_DIR, "*.md"))

    for i, filepath in tqdm(
        enumerate(file_paths), 
        total=len(glob.glob(os.path.join(KB_DIR, "*.txt")) + glob.glob(os.path.join(KB_DIR, "*.md"))),
        desc="Loading articles to Chroma"
    ):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        chunks = text_splitter.split_text(content)  
        for j, chunk in enumerate(chunks):
            metadata = {
                "source": os.path.basename(filepath), 
                "length": len(chunk),
                "chunk_index": j
            }
            docs.append(chunk)
            metadatas.append(metadata)
            ids.append(f"chunk_{i}_{j}")
    
    embeddings = encoder.encode(docs).astype(float).tolist()
    if docs:
        collection.add(ids=ids, documents=docs, embeddings=embeddings, metadatas=metadatas)
        print(collection.get(include=["documents", "embeddings", "metadatas"]))
        print(f"Loaded {len(docs)} articles into Chroma.")
    else:
        print("No articles found in", KB_DIR)
    

def retrieve_context(query, n_results=5):
    """Retrieve top-k articles related to the query."""
    vector = encoder.encode(query)
    collection = get_collection()  # In practice, you'd cache the collection.
    results = collection.query(query_embeddings=[vector.astype(float).tolist()], n_results=n_results)
    return results
    # results['documents'] is a list of lists
    # return results['documents'][0] if results['documents'] else []

if __name__ == "__main__":
    load_articles_to_chroma()