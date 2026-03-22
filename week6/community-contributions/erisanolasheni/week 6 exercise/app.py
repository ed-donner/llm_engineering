"""Gradio UI for Week 6 Price is Right. Run: gradio app.py (from this directory)."""
import os
import gradio as gr

from pricers import zero_shot_predict, fine_tuned_predict

FINE_TUNED_MODEL_NAME = os.environ.get("WEEK6_FINE_TUNED_MODEL", "")


def predict_price(description: str, model_choice: str):
    if not description or not description.strip():
        return "Enter a product description."
    try:
        if model_choice == "Fine-tuned":
            if not FINE_TUNED_MODEL_NAME:
                return "Set WEEK6_FINE_TUNED_MODEL to use the fine-tuned model."
            price = fine_tuned_predict(description, model=FINE_TUNED_MODEL_NAME)
        else:
            price = zero_shot_predict(description)
        return f"${price:,.2f}"
    except Exception as e:
        return f"Error: {e}"


demo = gr.Interface(
    fn=predict_price,
    inputs=[
        gr.Textbox(placeholder="Paste product title/description here...", label="Product description", lines=4),
        gr.Radio(choices=["Zero-shot", "Fine-tuned"], value="Zero-shot", label="Model"),
    ],
    outputs=gr.Textbox(label="Predicted price"),
    title="Price is Right — Week 6",
    description="Predict product price from description using zero-shot or fine-tuned model.",
)

if __name__ == "__main__":
    demo.launch()
