import json
import logging
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
from agents.rental_deals import RentalOpportunity
from agents.rental_scanner_agent import RentalScannerAgent
from agents.rental_frontier_agent import RentalFrontierAgent
from agents.rental_specialist_agent import RentalSpecialistAgent
from agents.rental_ensemble_agent import RentalEnsembleAgent
from agents.rental_messaging_agent import RentalMessagingAgent
from agents.rental_autonomous_agent import RentalAutonomousAgent

logger = logging.getLogger(__name__)

MEMORY_FILE = "rental_memory.json"
DB_PATH = "rental_vectorstore"


class RentalAgentFramework:
    """Orchestrates all agents, manages Chroma vector DB and persistent memory."""

    def __init__(self):
        logger.info("Initializing Rental Agent Framework...")

        # Vector database
        self.chroma_client = chromadb.PersistentClient(path=DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection("rental_listings")
        logger.info(f"Chroma collection loaded: {self.collection.count()} documents.")

        # Agents
        self.scanner = RentalScannerAgent()
        self.frontier = RentalFrontierAgent(collection=self.collection)
        self.specialist = RentalSpecialistAgent()
        self.ensemble = RentalEnsembleAgent(
            frontier=self.frontier,
            specialist=self.specialist,
        )
        self.messenger = RentalMessagingAgent()
        self.autonomous = RentalAutonomousAgent(
            scanner=self.scanner,
            ensemble=self.ensemble,
            messenger=self.messenger,
        )

        # Memory
        self.memory = self._load_memory()
        logger.info("Framework ready.")

    def run(self) -> list[RentalOpportunity]:
        """Run the autonomous agent and return discovered opportunities."""
        opportunities = self.autonomous.run()
        self._save_to_memory(opportunities)
        return opportunities

    def _load_memory(self) -> dict:
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"alerted_urls": []}

    def _save_to_memory(self, opportunities: list[RentalOpportunity]):
        for opp in opportunities:
            url = opp.deal.url
            if url not in self.memory["alerted_urls"]:
                self.memory["alerted_urls"].append(url)
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.memory, f, indent=2)
        logger.info(f"Memory updated: {len(self.memory['alerted_urls'])} deals tracked.")

    def plot_data(self) -> dict:
        """Generate 3D scatter plot data from the vector database."""
        result = self.collection.get(include=["embeddings", "metadatas", "documents"])
        if result["embeddings"] is None or len(result["embeddings"]) == 0:
            return {"x": [], "y": [], "z": [], "text": [], "color": []}

        embeddings = np.array(result["embeddings"])
        metadatas = result["metadatas"]
        documents = result["documents"]

        # Reduce to 3D with PCA for speed
        from sklearn.decomposition import PCA
        pca = PCA(n_components=3)
        coords = pca.fit_transform(embeddings)

        city_colors = {"New York": "red", "Lagos": "green", "Nairobi": "blue"}
        colors = [city_colors.get(m.get("city", ""), "gray") for m in metadatas]
        labels = [d[:60] for d in documents]

        return {
            "x": coords[:, 0].tolist(),
            "y": coords[:, 1].tolist(),
            "z": coords[:, 2].tolist(),
            "text": labels,
            "color": colors,
        }
