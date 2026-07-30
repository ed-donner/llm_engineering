"""Main entry point for the RAG pipeline.

Run from the repository root, since the knowledge-base and ChromaDB paths in
config.py are relative to the current working directory:

    python community-contributions/isg-hybrid-rag/main.py

Set REBUILD_DATABASE = True in config.py to re-chunk and re-embed the
knowledge base before answering.
"""
from config import REBUILD_DATABASE
from document_loader import fetch_documents
from chunking import create_chunks, make_prompt, make_messages
from embedding import create_embeddings
from answer import answer_question


def main():
    if REBUILD_DATABASE:
        print("Loading documents...")
        documents = fetch_documents()
        print(f"Total documents loaded: {len(documents)}")

        print("\nSample prompt:")
        print(make_prompt(documents[0]))

        print("\nSample message:")
        print(make_messages(documents[0]))

        print("\nChunk the entire set of documents")
        chunks = create_chunks(documents)

        print("\nCreating embeddings")
        create_embeddings(chunks)

    # Q&A loop
    question = "Who went to Manchester University?"
    print(f"\nQuestion: {question}")
    answer, _ = answer_question(question, [])
    print(answer)


if __name__ == "__main__":
    main()
