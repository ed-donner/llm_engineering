import re
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from agents.agent import Agent
from agents.rental_deals import RentalDeal


class RentalFrontierAgent(Agent):
    """Estimates fair rent using RAG — retrieves similar listings from Chroma and prompts GPT."""

    name = "Frontier"
    color = "green"

    SYSTEM_PROMPT = """You are a rental market expert. Based on similar rental listings provided as context,
estimate the fair monthly rent in USD for the given property. Reply with a single number — the estimated
monthly rent in USD. Do not include currency symbols or explanations."""

    def __init__(self, collection):
        self.client = OpenAI()
        self.collection = collection
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def estimate(self, deal: RentalDeal) -> float:
        self.log(f"Estimating fair rent for: {deal.title}")
        context = self._retrieve_similar(deal)
        estimate = self._ask_gpt(deal, context)
        self.log(f"Estimated fair rent: ${estimate:,.2f}/month")
        return estimate

    def _retrieve_similar(self, deal: RentalDeal, n_results: int = 5) -> str:
        query_text = f"{deal.bedrooms}BR {deal.sqft}sqft in {deal.city}. {deal.description}"
        embedding = self.model.encode(query_text).tolist()

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        context_parts = []
        for doc, meta in zip(documents, metadatas):
            rent = meta.get("rent", "unknown")
            context_parts.append(f"- {doc} (Rent: ${rent}/month)")

        context = "\n".join(context_parts)
        self.log(f"Retrieved {len(documents)} similar listings from vector DB.")
        return context

    def _ask_gpt(self, deal: RentalDeal, context: str) -> float:
        user_prompt = (
            f"Similar rental listings:\n{context}\n\n"
            f"Estimate the fair monthly rent for this property:\n"
            f"Title: {deal.title}\n"
            f"City: {deal.city}\n"
            f"Bedrooms: {deal.bedrooms}\n"
            f"Size: {deal.sqft} sqft\n"
            f"Description: {deal.description}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        reply = response.choices[0].message.content.strip()
        numbers = re.findall(r"[\d,]+\.?\d*", reply.replace(",", ""))
        if numbers:
            return float(numbers[0])
        self.log("Could not parse estimate, returning listed rent.")
        return deal.rent
