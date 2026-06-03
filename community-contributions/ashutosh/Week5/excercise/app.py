import gradio as gr
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from answer import answer_question
from eval import evaluate_response

load_dotenv(override=True)


def format_context(context):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2><br>"

    for doc in context:
        source = doc.metadata.get("source", "Unknown")

        result += (
            f"<span style='color: #ff7800;'>"
            f"<b>Source:</b> {source}"
            f"</span><br><br>"
        )

        result += doc.page_content
        result += "<br><br><hr><br>"

    return result

def create_eval_chart(scores):
    metrics = [
        "Retrieval\nRelevance",
        "Faithfulness",
        "Completeness",
        "Answer\nRelevance",
    ]

    values = [
        scores["retrieval_relevance"].score,
        scores["faithfulness"].score,
        scores["completeness"].score,
        scores["answer_relevance"].score,
    ]

    fig, ax = plt.subplots(figsize=(7, 4))

    bars = ax.bar(metrics, values)

    # Add some headroom for labels
    ax.set_ylim(0, 1.15)

    ax.set_ylabel("Score")
    ax.set_title("Evaluation Scores", pad=15)

    # Light grid
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Remove top/right borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Display values above bars
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.03,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()

    return fig

def chat(history):
    last_message = history[-1]["content"]
    prior = history[:-1]

    answer, context = answer_question(
        last_message,
        prior,
    )

    history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    scores = evaluate_response(
        query=last_message,
        chunks=context,
        answer=answer,
    )

    chart = create_eval_chart(scores)

    return (
        history,
        chart,
        format_context(context),
    )


def main():

    def put_message_in_chatbot(message, history):
        return (
            "",
            history
            + [
                {
                    "role": "user",
                    "content": message,
                }
            ],
        )

    theme = gr.themes.Soft(
        font=["Inter", "system-ui", "sans-serif"]
    )

    with gr.Blocks(
        title="AiForAll Assistant",
        theme=theme,
    ) as ui:

        gr.Markdown(
            "# 🏢 AiForAll Expert Assistant\n"
            "Ask me anything about AiForAll!"
        )

        with gr.Row():

            # LEFT SIDE
            with gr.Column(scale=1):

                chatbot = gr.Chatbot(
                    label="💬 Conversation",
                    type="messages",
                    show_copy_button=True,
                )

                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about AiForAll...",
                    show_label=False,
                )

            # RIGHT SIDE
            with gr.Column(scale=1):

                eval_plot = gr.Plot(
                    label="📈 Evaluation Scores",
                )

                context_markdown = gr.Markdown(
                    value="*Retrieved context will appear here*",
                    label="📚 Retrieved Context",
                )

        (
            message.submit(
                put_message_in_chatbot,
                inputs=[message, chatbot],
                outputs=[message, chatbot],
            )
            .then(
                chat,
                inputs=chatbot,
                outputs=[
                    chatbot,
                    eval_plot,
                    context_markdown,
                ],
            )
        )

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()