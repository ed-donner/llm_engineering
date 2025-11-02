import os
import sys
from dotenv import load_dotenv

project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '..', '..'))

from helpers.travel_deals import ScrapedTravelDeal
from agents.travel_scanner_agent import TravelScannerAgent
from agents.travel_estimator_agent import TravelEstimatorAgent

load_dotenv()

print("\nTesting Travel Deal Hunter Components\n")

print("1. RSS Feed Scraping")
deals = ScrapedTravelDeal.fetch(show_progress=False)
print(f"Fetched {len(deals)} deals from RSS feeds")
if deals:
    print(f"Sample: {deals[0].title[:60]}...")


print("\n2. OpenAI Connection")
if os.getenv("OPENAI_API_KEY"):
    print("OPENAI_API_KEY found")
else:
    print("OPENAI_API_KEY not found - set in .env file")

print("\n3. Scanner Agent")
scanner = TravelScannerAgent()
print("Scanner agent initialized")

print("\n4. Deal Scanning")
try:
    selection = scanner.scan(memory=[])
    if selection and selection.deals:
        print(f"Scanner found {len(selection.deals)} processed deals")
        print(f"Sample: {selection.deals[0].destination} - ${selection.deals[0].price}")
    else:
        print("No deals returned")
except Exception as e:
    print(f"Error: {e}")

print("\n5. ChromaDB Access")
import chromadb
try:
    db_path = "travel_vectorstore"
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection('travel_deals')
    count = collection.count()
    print(f"ChromaDB connected - {count} travel items in collection")
except Exception as e:
    print(f"Error: {e}")

print("\n6. Estimator Check using travel vectorstore")
try:
    estimator = TravelEstimatorAgent(collection)
    sample = "Non-stop economy flight from New York to London, duration 7 hours"
    estimate = estimator.estimate(sample)
    print(f"Estimate: ${estimate:.2f}")
except Exception as e:
    print(f"Error: {e}")

print("\nComponent tests complete")

