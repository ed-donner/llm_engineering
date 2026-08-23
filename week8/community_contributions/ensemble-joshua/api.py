from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import chromadb

from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.random_forest_agent import RandomForestAgent
from agents.ensemble_agent import EnsembleAgent
from deal_agent_framework import DealAgentFramework


class PriceRequest(BaseModel):
    description: str


class DealScanResponse(BaseModel):
    opportunities: list


DB_PATH = os.path.join(os.path.dirname(__file__), "../../products_vectorstore")
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection("products")

app = FastAPI(title="Week8 Pricer API", version="1.0.0")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/price/specialist")
def price_specialist(body: PriceRequest):
    if not body.description:
        raise HTTPException(400, "description is required")
    agent = SpecialistAgent()
    price = float(agent.price(body.description))
    return {"price": price, "agent": "specialist"}


@app.post("/price/frontier")
def price_frontier(body: PriceRequest):
    if not body.description:
        raise HTTPException(400, "description is required")
    agent = FrontierAgent(collection)
    price = float(agent.price(body.description))
    return {"price": price, "agent": "frontier"}


@app.post("/price/random_forest")
def price_random_forest(body: PriceRequest):
    if not body.description:
        raise HTTPException(400, "description is required")
    agent = RandomForestAgent()
    price = float(agent.price(body.description))
    return {"price": price, "agent": "random_forest"}


@app.post("/price/ensemble")
def price_ensemble(body: PriceRequest):
    if not body.description:
        raise HTTPException(400, "description is required")
    agent = EnsembleAgent(collection)
    price = float(agent.price(body.description))
    return {"price": price, "agent": "ensemble"}


@app.post("/deals/scan")
def deals_scan():
    framework = DealAgentFramework()
    opportunities = framework.run()
    return {"count": len(opportunities), "opportunities": [o.dict() for o in opportunities]}


