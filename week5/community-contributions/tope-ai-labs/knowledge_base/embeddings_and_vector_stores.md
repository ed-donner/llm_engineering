# Embeddings and Vector Stores

**Embeddings** are dense vector representations of text (or other data). Similar pieces of text get similar vectors, so we can find relevant content by comparing embeddings—e.g., with cosine similarity or Euclidean distance.

## How Embeddings Are Produced

Embedding models (e.g., OpenAI’s text-embedding-3, sentence-transformers like all-MiniLM-L6-v2) take text as input and output a fixed-size vector. They are trained so that semantically similar sentences have similar vectors. Dimensions are often 384, 768, or 1536, depending on the model.

## Vector Stores

A vector store is a database optimized for similarity search over embeddings. You insert (id, embedding, optional metadata and text), then query with an embedding and get the nearest neighbors. Examples include ChromaDB, Pinecone, Weaviate, and FAISS. ChromaDB is lightweight and can run locally, making it popular for prototyping and small-scale RAG.

## Use in RAG

In RAG, document chunks are embedded and stored. At query time, the question is embedded and the store returns the top-k most similar chunks. Those chunks form the context for the LLM. Choosing a good chunk size, overlap, and embedding model significantly affects retrieval quality and thus answer accuracy.
