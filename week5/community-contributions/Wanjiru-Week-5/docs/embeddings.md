# Vector Embeddings

Vector embeddings are numerical representations of text that capture semantic meaning.

When text is converted into embeddings, each sentence or document becomes a vector of numbers. Similar texts will have vectors that are close to each other in vector space.

For example:
- "What is artificial intelligence?" 
- "Explain AI."

These two sentences would have very similar embeddings.

Embeddings allow systems to perform semantic search, meaning they can find relevant information even when the exact words do not match.

Embedding models such as `all-MiniLM-L6-v2` or OpenAI embedding models are commonly used in RAG systems.