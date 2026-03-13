import faiss
import numpy as np


class StreamingVectorStore:
    """
    Temporary FAISS index built from streamed dataset samples.
    """

    def __init__(self, dim):

        self.index = faiss.IndexFlatL2(dim)
        self.texts = []

    def add(self, embeddings, texts):

        vectors = np.array(embeddings).astype("float32")

        self.index.add(vectors)
        self.texts.extend(texts)

    def search(self, query_embedding, k=3):

        vector = np.array([query_embedding]).astype("float32")

        _distances, indices = self.index.search(vector, k)

        return [self.texts[i] for i in indices[0]]