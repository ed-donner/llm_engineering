from rag.streaming_datasets import StreamingDatasetLoader
from rag.embedding_model import EmbeddingModel
from rag.streaming_vector_store import StreamingVectorStore


class StreamingRAG:

    def __init__(self):

        self.loader = StreamingDatasetLoader()
        self.embedder = EmbeddingModel()

    def retrieve(self, query, dataset):

        sentences = self.loader.sample_sentences(dataset, n=25)

        embeddings = self.embedder.embed(sentences)

        dim = len(embeddings[0])

        store = StreamingVectorStore(dim)

        store.add(embeddings, sentences)

        query_emb = self.embedder.embed([query])[0]

        results = store.search(query_emb)

        return results