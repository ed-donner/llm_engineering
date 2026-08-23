import os
import sys
import logging
import json
from typing import List, Optional
from dotenv import load_dotenv
import chromadb
import numpy as np
from sklearn.manifold import TSNE

w8d5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)

from agents.travel_planning_agent import TravelPlanningAgent
from helpers.travel_deals import TravelOpportunity

BG_BLUE = '\033[44m'
WHITE = '\033[37m'
RESET = '\033[0m'

CATEGORIES = ['Flights', 'Hotels', 'Car_Rentals', 'Vacation_Packages', 'Cruises', 'Activities']
COLORS = ['red', 'blue', 'green', 'orange', 'purple', 'cyan']

def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [Travel Agents] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

class TravelDealFramework:

    DB = "travel_vectorstore"
    MEMORY_FILENAME = "travel_memory.json"

    def __init__(self):
        init_logging()
        load_dotenv()
        client = chromadb.PersistentClient(path=self.DB)
        self.memory = self.read_memory()
        self.collection = client.get_or_create_collection('travel_deals')
        self.planner = None

    def init_agents_as_needed(self):
        if not self.planner:
            self.log("Initializing Travel Agent Framework")
            self.planner = TravelPlanningAgent(self.collection)
            self.log("Travel Agent Framework ready")
        
    def read_memory(self) -> List[TravelOpportunity]:
        if os.path.exists(self.MEMORY_FILENAME):
            with open(self.MEMORY_FILENAME, "r") as file:
                data = json.load(file)
            opportunities = [TravelOpportunity(**item) for item in data]
            return opportunities
        return []

    def write_memory(self) -> None:
        data = [opportunity.dict() for opportunity in self.memory]
        with open(self.MEMORY_FILENAME, "w") as file:
            json.dump(data, file, indent=2)

    def log(self, message: str):
        text = BG_BLUE + WHITE + "[Travel Framework] " + message + RESET
        logging.info(text)

    def run(self) -> List[TravelOpportunity]:
        self.init_agents_as_needed()
        logging.info("Starting Travel Planning Agent")
        results = self.planner.plan(memory=self.memory)
        logging.info(f"Travel Planning Agent completed with {len(results) if results else 0} results")
        if results:
            self.memory.extend(results)
            self.write_memory()
        return self.memory

    @classmethod
    def get_plot_data(cls, max_datapoints=10000):
        client = chromadb.PersistentClient(path=cls.DB)
        collection = client.get_or_create_collection('travel_deals')
        result = collection.get(include=['embeddings', 'documents', 'metadatas'], limit=max_datapoints)
        vectors = np.array(result['embeddings'])
        documents = result['documents']
        categories = [metadata['category'] for metadata in result['metadatas']]
        colors = [COLORS[CATEGORIES.index(c)] for c in categories]
        tsne = TSNE(n_components=3, random_state=42, n_jobs=-1)
        reduced_vectors = tsne.fit_transform(vectors)
        return documents, reduced_vectors, colors

if __name__=="__main__":
    TravelDealFramework().run()

