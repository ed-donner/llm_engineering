import gradio as gr
from dotenv import load_dotenv

from implementation.answer import answer_question

# Carga variables de entorno (.env), por ejemplo API keys
load_dotenv(override=True)


def format_context(context):
    # Construye el panel HTML con los fragmentos recuperados por RAG
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in context:
        # Muestra la fuente del chunk para trazabilidad
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata['source']}</span>\n\n"
        # Muestra contenido del chunk
        result += doc.page_content + "\n\n"
    return result


def chat(history):
    # Toma el ultimo mensaje del usuario y el historial previo
    last_message = history[-1]["content"]
    prior = history[:-1]
    # Llama al motor RAG: devuelve respuesta + contexto usado
    answer, context = answer_question(last_message, prior)
    # Inserta respuesta del asistente en el historial del chat
    history.append({"role": "assistant", "content": answer})
    # Actualiza chat y panel de contexto
    return history, format_context(context)


def main():
    # Handler del submit: agrega mensaje del usuario al chatbot
    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    # Tema visual base de Gradio
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Insurellm Expert Assistant", theme=theme) as ui:
        gr.Markdown("# ðŸ¢ Insurellm Expert Assistant\nAsk me anything about Insurellm!")

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="ðŸ’¬ Conversation", height=600, type="messages", show_copy_button=True
                )
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about Insurellm...",
                    show_label=False,
                )

            with gr.Column(scale=1):
                context_markdown = gr.Markdown(
                    label="ðŸ“š Retrieved Context",
                    value="*Retrieved context will appear here*",
                    container=True,
                    height=600,
                )

        # Flujo en dos pasos:
        # 1) agrega mensaje del usuario al chat
        # 2) ejecuta RAG y refresca respuesta + contexto
        message.submit(
            put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
        ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])

    # Lanza la app y abre navegador automaticamente
    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
