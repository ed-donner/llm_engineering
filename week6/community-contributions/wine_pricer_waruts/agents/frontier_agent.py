import re
from typing import List, Dict
import anthropic
from litellm import completion
from sentence_transformers import SentenceTransformer
from agents.agent import Agent


class FrontierAgent(Agent):
    """
    An Agent that prices a wine with a frontier model, helped by RAG:
    it looks up the 5 most similar wines in the Qdrant vector store and shows their prices to the model
    """

    name = "Frontier Agent"
    color = Agent.BLUE

    # Any model name starting with "claude" is called through the Anthropic SDK.
    # Anything else goes through LiteLLM, for example "groq/qwen/qwen3.8-27b"
    MODEL = "claude-sonnet-5"
    COLLECTION = "wines"

    def __init__(self, client, model: str = None):
        """
        Set up this instance by connecting to the model provider and to the Qdrant vector store,
        and by loading the vector encoding model
        :param client: an open QdrantClient
        """
        self.log("Initializing Frontier Agent")
        self.client = client
        self.MODEL = model or self.MODEL
        self.claude = anthropic.Anthropic()
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.log(f"Frontier Agent is ready with {self.MODEL}")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """
        Create context that can be inserted into the prompt
        :param similars: similar wines to the one being estimated
        :param prices: prices of the similar wines
        :return: text to insert in the prompt that provides context
        """
        message = "For context, here are some other wines that might be similar to the wine you need to estimate.\n\n"
        for similar, price in zip(similars, prices):
            message += f"Potentially related wine:\n{similar}\nPrice is ${price:.2f}\n\n"
        return message

    def messages_for(
        self, description: str, similars: List[str], prices: List[float]
    ) -> List[Dict[str, str]]:
        """
        Create the message list to send to the model
        :param description: a description of the wine
        :param similars: similar wines to this one
        :param prices: prices of similar wines
        """
        message = f"Estimate the price of this bottle of wine in US dollars. Respond with the price, no explanation\n\n{description}\n\n"
        message += self.make_context(similars, prices)
        return [{"role": "user", "content": message}]

    def find_similars(self, description: str):
        """
        Return a list of wines similar to the given one by looking in the Qdrant vector store
        """
        self.log("Frontier Agent is performing a RAG search of the Qdrant store to find 5 similar wines")
        vector = self.encoder.encode(description)
        results = self.client.query_points(
            self.COLLECTION, query=vector.tolist(), limit=5, with_payload=True
        ).points
        documents = [point.payload["summary"] for point in results]
        prices = [point.payload["price"] for point in results]
        self.log("Frontier Agent has found similar wines")
        return documents, prices

    def get_price(self, s) -> float:
        """
        A utility that plucks a floating point number out of a string
        """
        s = (s or "").replace("$", "").replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def ask(self, messages: List[Dict[str, str]]) -> str:
        """
        Send the messages to the model and return its reply as text
        """
        if self.MODEL.startswith("claude"):
            response = self.claude.messages.create(
                model=self.MODEL,
                max_tokens=16000,
                messages=messages,
                extra_body={"output_config": {"effort": "low"}},
            )
            if response.stop_reason == "refusal":
                return "0"
            return next((block.text for block in response.content if block.type == "text"), "0")
        response = completion(model=self.MODEL, messages=messages, reasoning_effort="none")
        return response.choices[0].message.content

    def price(self, description: str) -> float:
        """
        Estimate the price of the described wine, by looking up 5 similar wines
        and including them in the prompt to give context
        :param description: a description of the wine
        :return: an estimate of the price
        """
        documents, prices = self.find_similars(description)
        self.log(f"Frontier Agent is about to call {self.MODEL} with context including 5 similar wines")
        reply = self.ask(self.messages_for(description, documents, prices))
        result = self.get_price(reply)
        self.log(f"Frontier Agent completed - predicting ${result:.2f}")
        return result
