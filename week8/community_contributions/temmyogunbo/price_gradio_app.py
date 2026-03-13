"""
Gradio app for price estimation using the Ensemble Agent.

Run from the temmyogunbo folder:
  uv run python price_gradio_app.py

Prerequisites:
  - Deploy the pricer service: uv run modal deploy -m pricer_service
  - Set HF_TOKEN in .env for Hugging Face (and Chroma population on first run)
  - OpenAI API key for the Frontier Agent (gpt-5.1)
"""

import os
import sys
from pathlib import Path

# Use temmyogunbo's agents folder

from dotenv import load_dotenv
load_dotenv(override=True)

import gradio as gr
import chromadb
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from huggingface_hub import login

from agents.items import Item
from agents.ensemble_agent import EnsembleAgent

DB = "products_vectorstore"
COLLECTION_NAME = "products"
LITE_MODE = False


def setup_collection():
    """Initialize ChromaDB client and get or create the products collection."""
    client = chromadb.PersistentClient(path=DB)
    collection_name = COLLECTION_NAME
    existing_collection_names = [c.name for c in client.list_collections()]

    if collection_name not in existing_collection_names:
        collection = client.create_collection(collection_name)
        print("Populating Chroma vectorstore (this may take a few minutes on first run)...")
        encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        username = "ed-donner"
        dataset = f"{username}/items_lite" if LITE_MODE else f"{username}/items_full"
        train, _, _ = Item.from_hub(dataset)
        for i in tqdm(range(0, len(train), 1000)):
            documents = [item.summary for item in train[i : i + 1000]]
            vectors = encoder.encode(documents).astype(float).tolist()
            metadatas = [{"category": item.category, "price": item.price} for item in train[i : i + 1000]]
            ids = [f"doc_{j}" for j in range(i, min(i + 1000, len(train)))]
            ids = ids[: len(documents)]
            collection.add(ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas)
        print("Vectorstore populated.")
    else:
        collection = client.get_or_create_collection(collection_name)

    return collection


def estimate_price(description: str, ensemble_agent: EnsembleAgent) -> str:
    """Get price estimate from the Ensemble Agent."""
    if not description or not description.strip():
        return "Please describe an item to get a price estimate."
    try:
        price = ensemble_agent.price(description.strip())
        return f"**Estimated price: ${price:,.2f}**"
    except Exception as e:
        return f"Error: {str(e)}"


def create_app():
    """Create and launch the Gradio interface."""
    print("Logging in to Hugging Face...")
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        login(token=hf_token, add_to_git_credential=False)

    print("Setting up Chroma vectorstore...")
    collection = setup_collection()

    def predict(description: str):
        """Generator that shows loading state, disables button, then returns result."""
        ensemble_agent = EnsembleAgent(collection)
        print("Ensemble Agent initialized.")
        # Show loading feedback and disable button immediately
        yield "⏳ **Estimating price...** (This may take a few seconds)", gr.update(interactive=False)
        # Run the actual estimation
        result = estimate_price(description, ensemble_agent)
        # Show result and re-enable button
        yield result, gr.update(interactive=True)

    with gr.Blocks(title="Price Estimator", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🏷️ Price Estimator

            Describe any product and get an AI-powered price estimate using the **Ensemble Agent** —
            combining a fine-tuned specialist model with RAG-augmented frontier LLM predictions.
            """
        )
        with gr.Row():
            with gr.Column(scale=2):
                item_input = gr.Textbox(
                    label="Describe the item",
                    placeholder="e.g., iPhone 16 Pro Max 256GB, or Quadcast HyperX condenser mic...",
                    lines=3,
                )
                submit_btn = gr.Button("Get Price Estimate", variant="primary")
            with gr.Column(scale=1):
                output = gr.Markdown(label="Estimated Price")

        submit_btn.click(
            fn=predict,
            inputs=item_input,
            outputs=[output, submit_btn],
        )

        gr.Examples(
            examples=[
                ["iPhone 16 Pro Max 256GB"],
                ["Quadcast HyperX condenser mic, connects via usb-c for crystal clear audio"],
                ["Sony WH-1000XM5 wireless noise-cancelling headphones"],
            ],
            inputs=item_input,
            label="Try these examples",
        )

    return demo


if __name__ == "__main__":
    demo = create_app()
    demo.launch(inbrowser=True)
