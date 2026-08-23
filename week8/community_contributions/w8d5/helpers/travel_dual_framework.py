import os
import sys
import logging
import json
from typing import List, Tuple
from dotenv import load_dotenv
import chromadb
import numpy as np
from sklearn.manifold import TSNE

w8d5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)

from agents.travel_scanner_agent import TravelScannerAgent
from agents.travel_estimator_agent import TravelEstimatorAgent
from agents.travel_xgboost_agent import TravelXGBoostAgent
from agents.travel_messaging_agent import TravelMessagingAgent
from helpers.travel_deals import TravelOpportunity, TravelDeal

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


class TravelDualFramework:

    DB = "travel_vectorstore"
    LLM_MEMORY_FILE = "travel_memory_llm.json"
    XGB_MEMORY_FILE = "travel_memory_xgb.json"
    DEAL_THRESHOLD = 200.0

    def __init__(self):
        init_logging()
        load_dotenv()
        client = chromadb.PersistentClient(path=self.DB)
        self.collection = client.get_or_create_collection('travel_deals')
        
        self.llm_memory = self.read_memory(self.LLM_MEMORY_FILE)
        self.xgb_memory = self.read_memory(self.XGB_MEMORY_FILE)
        
        self.scanner = None
        self.llm_estimator = None
        self.xgb_estimator = None
        self.messenger = None

    def init_agents_as_needed(self):
        if not self.scanner:
            self.log("Initializing Travel Dual Estimation Framework")
            self.scanner = TravelScannerAgent()
            self.llm_estimator = TravelEstimatorAgent(self.collection)
            self.xgb_estimator = TravelXGBoostAgent(self.collection)
            self.messenger = TravelMessagingAgent()
            self.log("Travel Dual Framework ready")
        
    def read_memory(self, filename: str) -> List[TravelOpportunity]:
        if os.path.exists(filename):
            with open(filename, "r") as file:
                data = json.load(file)
            opportunities = [TravelOpportunity(**item) for item in data]
            return opportunities
        return []

    def write_memory(self, opportunities: List[TravelOpportunity], filename: str) -> None:
        data = [opportunity.dict() for opportunity in opportunities]
        with open(filename, "w") as file:
            json.dump(data, file, indent=2)

    def log(self, message: str):
        text = BG_BLUE + WHITE + "[Dual Framework] " + message + RESET
        logging.info(text)

    def run(self) -> Tuple[List[TravelOpportunity], List[TravelOpportunity]]:
        self.init_agents_as_needed()
        
        self.log("Starting dual estimation scan")
        deal_selection = self.scanner.scan()
        
        if not deal_selection or not deal_selection.deals:
            self.log("No deals found")
            return self.llm_memory, self.xgb_memory
        
        deals = deal_selection.deals
        self.log(f"Processing {len(deals)} deals with both estimators")
        
        llm_opportunities = []
        xgb_opportunities = []
        
        for deal in deals:
            llm_estimate = self.llm_estimator.estimate(deal.description)
            llm_discount = llm_estimate - deal.price
            
            if llm_discount >= self.DEAL_THRESHOLD:
                llm_opp = TravelOpportunity(
                    deal=deal,
                    estimate=llm_estimate,
                    discount=llm_discount
                )
                llm_opportunities.append(llm_opp)
                self.log(f"LLM found opportunity: {deal.destination} - ${llm_discount:.0f} savings")
                self.messenger.alert(llm_opp)
            
            xgb_estimate = self.xgb_estimator.estimate(deal.description)
            xgb_discount = xgb_estimate - deal.price
            
            if xgb_discount >= self.DEAL_THRESHOLD:
                xgb_opp = TravelOpportunity(
                    deal=deal,
                    estimate=xgb_estimate,
                    discount=xgb_discount
                )
                xgb_opportunities.append(xgb_opp)
                self.log(f"XGBoost found opportunity: {deal.destination} - ${xgb_discount:.0f} savings")
                self.messenger.alert(xgb_opp)
        
        if llm_opportunities:
            self.llm_memory.extend(llm_opportunities)
            self.write_memory(self.llm_memory, self.LLM_MEMORY_FILE)
        
        if xgb_opportunities:
            self.xgb_memory.extend(xgb_opportunities)
            self.write_memory(self.xgb_memory, self.XGB_MEMORY_FILE)
        
        self.log(f"Scan complete: {len(llm_opportunities)} LLM, {len(xgb_opportunities)} XGBoost opportunities")
        
        return self.llm_memory, self.xgb_memory

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
        return documents, reduced_vectors, colors, categories


if __name__=="__main__":
    framework = TravelDualFramework()
    framework.run()

