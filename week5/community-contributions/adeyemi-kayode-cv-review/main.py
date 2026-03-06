"""CV Review RAG: run ingest once, then Gradio chatbot to ask questions about the resumes."""
import sys
import gradio as gr
from answer import answer_question

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--ingest":
        from ingest import fetch_documents, create_chunks, create_embeddings
        docs = fetch_documents()
        chunks = create_chunks(docs)
        create_embeddings(chunks)
        print("Done. Run without --ingest to start the chatbot.")
        sys.exit(0)

    def chat(message, history):
        if not message or not message.strip():
            return ""
        try:
            reply = answer_question(message.strip())
            return reply
        except Exception as e:
            return f"Error: {e}"

    gr.ChatInterface(
        chat,
        title="CV Review RAG",
        description="Ask about the candidates (e.g. 'Who has Python experience?', 'Compare backend skills').",
    ).launch(inbrowser=True)
