import os
import sys
from dotenv import load_dotenv

project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '..', '..'))

from agents.travel_estimator_agent import TravelEstimatorAgent
from agents.travel_xgboost_agent import TravelXGBoostAgent
import chromadb

load_dotenv()

print("\nTesting Dual Estimation (LLM vs XGBoost)\n")

client = chromadb.PersistentClient(path='travel_vectorstore')
collection = client.get_collection('travel_deals')

print("Initializing agents...")
llm_agent = TravelEstimatorAgent(collection)
xgb_agent = TravelXGBoostAgent(collection)

test_cases = [
    "Round trip flight from New York to London, Economy class, non-stop",
    "5-star Marriott hotel in Paris, 3 nights, Suite with breakfast included",
    "7-night Caribbean cruise, Balcony cabin, all meals included",
    "Hertz SUV rental in Los Angeles for 5 days with unlimited mileage",
    "All-inclusive vacation package to Dubai for 7 nights with Business class flights"
]

print("\n" + "="*80)
print(f"{'Travel Deal Description':<60} {'LLM Est.':<12} {'XGB Est.':<12}")
print("="*80)

for desc in test_cases:
    llm_est = llm_agent.estimate(desc)
    xgb_est = xgb_agent.estimate(desc)
    
    short_desc = desc[:57] + "..." if len(desc) > 60 else desc
    print(f"{short_desc:<60} ${llm_est:>9.2f}  ${xgb_est:>9.2f}")

print("="*80)
print("\nDual estimation test complete!")
print("\nKey Observations:")
print("- LLM: Uses semantic understanding + RAG context")
print("- XGBoost: Uses pattern recognition from embeddings")
print("- Both trained on same 20K travel deals dataset")

