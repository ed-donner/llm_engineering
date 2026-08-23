# Retrieval Augmented Generation (RAG)

Retrieval Augmented Generation (RAG) is a technique used to improve the accuracy of large language models by retrieving relevant information from a knowledge base before generating an answer.

Instead of relying only on the model's training data, RAG allows the system to search a collection of documents and provide them as context to the model.

A typical RAG pipeline works as follows:

1. Load documents into the system.
2. Split documents into smaller chunks.
3. Convert the chunks into vector embeddings.
4. Store the embeddings in a vector database.
5. When a user asks a question, retrieve the most relevant chunks.
6. Send the retrieved context to the language model to generate an answer.

RAG is widely used in applications such as question answering systems, documentation assistants, and knowledge-based chatbots.