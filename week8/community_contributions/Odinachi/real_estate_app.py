import modal

app = modal.App("real-estate-predictor")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "gradio>=5.0,<6.0",
        "openai",
        "chromadb",
        "sentence-transformers",
        "datasets",
        "pandas",
        "numpy",
    )
)

secrets = [
    modal.Secret.from_name("huggingface-secret"),
    modal.Secret.from_name("my-openai-secret"),
]

COLLECTION_NAME = "real_estate"
BASE_MODEL = "gpt-4o-mini-2024-07-18"
FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:pillowcode:real-estate-predictor:DH3aSJlR"
HF_USERNAME = "odinachidavid"
RAG_DATASET_NAME = f"{HF_USERNAME}/real_estate_properties"

SYSTEM_PROMPT = (
    "You are a real estate expert assistant. You help users estimate property prices "
    "and recommend neighborhoods. When given property details, provide accurate price "
    "estimates with ranges. When asked about neighborhoods, give practical location advice. "
    "Be concise but informative."
)

PRICE_KEYWORDS = [
    "price", "cost", "worth", "value", "estimate", "market value",
    "how much", "budget", "afford", "pricing", "expensive", "cheap",
    "pay for", "listed at", "asking price",
]


@app.cls(image=image, secrets=secrets, timeout=900, scaledown_window=300)
class RealEstatePredictor:

    @modal.enter()
    def setup(self):
        import pandas as pd
        import os
        import chromadb
        from sentence_transformers import SentenceTransformer
        from datasets import load_dataset
        from openai import OpenAI

        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(COLLECTION_NAME)

        rag_hub = load_dataset(RAG_DATASET_NAME)
        rag_df = rag_hub["train"].to_pandas()

        def parse_price(p):
            if pd.isna(p):
                return 0.0
            return float(str(p).replace("$", "").replace(",", ""))

        batch_size = 500
        for i in range(0, len(rag_df), batch_size):
            batch = rag_df.iloc[i : i + batch_size]
            documents = batch["description"].tolist()
            vectors = self.encoder.encode(documents).astype(float).tolist()

            metadatas = []
            for _, row in batch.iterrows():
                metadatas.append({
                    "property_id": str(row["property_id"]),
                    "rooms": int(row["rooms"]),
                    "bathrooms": int(row["bathrooms"]),
                    "country": str(row.get("country", "")),
                    "state": str(row.get("state", "")),
                    "size": str(row.get("size", "")),
                    "property_type": str(row.get("property_type", "")),
                    "year_built": str(row.get("year_built", "")),
                    "condition": str(row.get("condition", "")),
                    "price": parse_price(row["price"]),
                    "price_range_low": parse_price(row.get("price_range_low")),
                    "price_range_high": parse_price(row.get("price_range_high")),
                })

            ids = [f"prop_{j}" for j in range(i, i + len(documents))]
            self.collection.add(
                ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas
            )

        print(f"ChromaDB ready with {self.collection.count():,} documents")

    def _find_similar(self, query: str, n: int = 5):
        vector = self.encoder.encode([query])
        results = self.collection.query(
            query_embeddings=vector.astype(float).tolist(), n_results=n
        )
        return results["documents"][0], results["metadatas"][0]

    def _build_context(self, documents, metadatas):
        lines = ["Here are similar properties from the market for reference:\n"]
        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            price = meta.get("price", 0)
            low = meta.get("price_range_low", 0)
            high = meta.get("price_range_high", 0)
            lines.append(
                f"Property {i}: {doc}\n"
                f"  Listed at ${price:,.0f} (range: ${low:,.0f} \u2013 ${high:,.0f})\n"
            )
        return "\n".join(lines)

    @staticmethod
    def _is_price_question(query: str) -> bool:
        q = query.lower()
        return any(kw in q for kw in PRICE_KEYWORDS)

    @modal.method()
    def predict(self, query: str) -> dict:
        is_pricing = self._is_price_question(query)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        rag_info = ""
        if is_pricing:
            docs, metas = self._find_similar(query, n=5)
            rag_context = self._build_context(docs, metas)
            user_content = f"{query}\n\n---\n{rag_context}"
            rag_info = rag_context
        else:
            user_content = query

        messages.append({"role": "user", "content": user_content})

        response = self.openai_client.chat.completions.create(
            model=FINE_TUNED_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )

        return {
            "answer": response.choices[0].message.content,
            "used_rag": is_pricing,
            "rag_context": rag_info,
        }


@app.function(
    image=image,
    secrets=secrets,
    timeout=3600,
    scaledown_window=300,
    max_containers=1,
)
@modal.web_server(port=7860, startup_timeout=600)
def web():
    import gradio as gr

    RealEstatePredictorCls = modal.Cls.from_name("real-estate-predictor", "RealEstatePredictor")
    predictor = RealEstatePredictorCls()

    def respond(message, history):
        try:
            result = predictor.predict.remote(message)
            answer = result["answer"]
            if result["used_rag"]:
                answer += "\n\n---\n*RAG retrieved 5 similar properties to inform this estimate.*"
            return answer
        except Exception as e:
            return f"Sorry, an error occurred: {e}. Please try again."

    with gr.Blocks(
        title="Real Estate Predictor",
        theme=gr.themes.Soft(primary_hue="emerald"),
    ) as demo:
        gr.Markdown(
            "# Real Estate Price Predictor\n"
            "### RAG-augmented, Fine-tuned GPT-4o-mini\n\n"
            "Ask about **property prices** or **neighborhood recommendations**.\n\n"
            "> **Note:** The first message may take 1-2 minutes while the AI model warms up."
        )
        gr.ChatInterface(
            fn=respond,
            type="messages",
            chatbot=gr.Chatbot(height=500, type="messages"),
            textbox=gr.Textbox(
                placeholder="Ask about property prices or neighborhoods...",
                container=False,
                scale=7,
            ),
            examples=[
                "What's a 2-bedroom apartment worth in Berlin, Germany?",
                "Estimate the market value of a 4-bed, 3-bath villa in Queensland, Australia. 350 sqm, built 2010, good condition.",
                "Can you suggest a good neighborhood in Ontario, Canada for a 3-bedroom townhouse?",
                "How much should I budget for a 5-bedroom home in suburban Colorado?",
            ],
            cache_examples=False,
        )

    demo.launch(server_name="0.0.0.0",server_port=7860,  show_error=True,)
