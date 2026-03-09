# Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation is a technique that combines a large language model with an external knowledge base. Instead of relying only on the model’s internal knowledge, RAG retrieves relevant documents at query time and conditions the model’s answer on that context.

## Why RAG?

LLMs can hallucinate—generate plausible but incorrect information—and their knowledge is fixed at training time. RAG addresses this by grounding answers in retrieved documents. It also allows you to use private or up-to-date data (docs, manuals, support articles) without retraining the model.

## How RAG Works

1. **Indexing**: Documents are split into chunks, converted to vector embeddings, and stored in a vector database (e.g., ChromaDB, Pinecone).
2. **Retrieval**: When the user asks a question, the question is embedded and the database returns the most similar chunks (by cosine similarity or other metrics).
3. **Generation**: The retrieved chunks are passed to the LLM as context, and the model generates an answer based on that context and the user query.

## Best Practices

Chunk size and overlap affect retrieval quality. Embedding model choice matters for semantic match. It helps to include source metadata (e.g., filename, section) so the model can cite and so you can filter or rank results. Optionally, you can re-rank retrieved chunks before generation to improve relevance.
