import glob
import json
from src.processing.chunker import PharmaChunker
from src.retrieval.vector_store import PharmaVectorStore
from src.processing.summarizer import PharmaSummarizer

def ingest_all_raw_data():
    """
    Ingests all the raw data stored in the data/raw directory
    """
    files = glob.glob("data/raw/*.json")
    chunks = []
    summaries = []
    chunker = PharmaChunker()
    vectorstore = PharmaVectorStore()
    summarizer = PharmaSummarizer()
    #loop through the files
    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
            chunks.extend(chunker.chunk_drug_label(data))
    #summarize the chunks
    for chunk in chunks:
        summaries.append(summarizer.summarize(chunk.page_content, chunk.metadata['section']))
    #add the chunks to the vector store
    vectorstore.add_chunks(chunks, summaries)
    
   
if __name__ == "__main__":
    ingest_all_raw_data()