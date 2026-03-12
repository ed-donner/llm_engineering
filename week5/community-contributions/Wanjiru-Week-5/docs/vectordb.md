# Vector Databases

A vector database stores embeddings and allows efficient similarity search.

Instead of searching for exact keywords, vector databases compare the distance between embeddings to find the most semantically similar content.

Common vector databases include:
- Chroma
- Pinecone
- Weaviate
- FAISS

In a RAG system, embeddings of document chunks are stored in a vector database. When a question is asked, the system converts the question into an embedding and retrieves the most similar chunks.

These retrieved chunks are then used as context for the language model.