# Learning Notes

## Retrieval Augmented Generation (RAG)
RAG combines vector search with large language models.

Steps:
1. Split documents into chunks
2. Generate embeddings
3. Store in a vector database
4. Retrieve relevant chunks
5. Provide them as context to an LLM

Benefits:
- Reduces hallucinations
- Allows models to use private data

Common vector databases:
- Chroma
- Pinecone
- Weaviate
- FAISS

## AI Agents
AI agents are systems where an LLM can:
- Plan tasks
- Use tools
- Take actions
- Maintain memory