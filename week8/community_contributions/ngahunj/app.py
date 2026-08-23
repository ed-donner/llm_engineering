"""
Gradio UI for manual RAG pipeline
"""

import gradio as gr

from .ingest import (
    create_embeddings,
    create_llm,
    load_or_create_vectorstore,
    create_retriever,
    rag_pipeline,
)


def initialize_rag():
    llm = create_llm()

    embeddings = create_embeddings()

    vectorstore = load_or_create_vectorstore(embeddings)

    retriever = create_retriever(vectorstore)

    return llm, retriever


def chat_response(message, history, query_type):
    chat_history = list(history) if history else []

    if query_type == "RAG":
        result = rag_pipeline(
            llm,
            retriever,
            message,
            chat_history,
        )

        response_text = result["answer"]

        if result.get("source_documents"):
            sources = []
            seen = set()

            for doc in result["source_documents"]:
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", "unknown")

                key = f"{source}:{page}"

                if key not in seen:
                    sources.append(f"- {source}, page {page}")
                    seen.add(key)

            if sources:
                response_text += "\n\nSources:\n" + "\n".join(sources)

    else:
        result = llm.invoke(message)

        response_text = result.content

    return response_text


llm, retriever = initialize_rag()


with gr.Blocks() as demo:
    gr.Markdown("# RAG-Powered Document Chat")

    rag_enabled = gr.Checkbox(
        value=True,
        label="Enable RAG",
    )

    chatbot = gr.Chatbot()

    context_box = gr.Textbox(
        label="Retrieved Context",
        interactive=False,
        visible=True,
        lines=5,
    )

    with gr.Row():
        msg = gr.Textbox(label="Query", scale=8)

        with gr.Column(scale=1):
            submit = gr.Button("Submit")
            clear = gr.Button("Clear")

    def respond(message, chat_history, is_rag_enabled):
        if not message:
            return "", chat_history, "", is_rag_enabled

        query_type = "RAG" if is_rag_enabled else "Vanilla"

        bot_message = chat_response(
            message,
            chat_history,
            query_type,
        )

        new_history = list(chat_history)

        new_history.append((message, bot_message))

        context = ""

        if is_rag_enabled:
            docs = retriever.invoke(message)

            context = "\n\n".join(doc.page_content for doc in docs)

        return "", new_history, context, is_rag_enabled

    def update_context_visibility(is_rag_enabled):
        return gr.update(
            visible=is_rag_enabled,
            value="" if not is_rag_enabled else None,
        )

    msg.submit(
        respond,
        [msg, chatbot, rag_enabled],
        [msg, chatbot, context_box, rag_enabled],
    )

    submit.click(
        respond,
        [msg, chatbot, rag_enabled],
        [msg, chatbot, context_box, rag_enabled],
    )

    clear.click(
        lambda: [[], "", True],
        None,
        [chatbot, context_box, rag_enabled],
        queue=False,
    )

    rag_enabled.change(
        update_context_visibility,
        rag_enabled,
        context_box,
    )

    gr.Examples(
        examples=[
            "Tell me about Arcee Fusion.",
            "How does deepseek-R1 differ from deepseek-v3?",
            "What is DELLA merging?",
        ],
        inputs=msg,
    )


if __name__ == "__main__":
    demo.launch()
