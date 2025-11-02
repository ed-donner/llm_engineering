import os
import sys
from dotenv import load_dotenv

project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '..', '..'))

from helpers.travel_deal_framework import TravelDealFramework

load_dotenv()

print("\nTesting Full Travel Deal Pipeline\n")

print("Initializing framework...")
framework = TravelDealFramework()
framework.init_agents_as_needed()

print("\nRunning one iteration...")
try:
    result = framework.run()
    print(f"\nPipeline completed")
    print(f"Memory now has {len(result)} opportunities")
    if result:
        latest = result[-1]
        print(f"\nLatest opportunity:")
        print(f"  Destination: {latest.deal.destination}")
        print(f"  Type: {latest.deal.deal_type}")
        print(f"  Price: ${latest.deal.price:.2f}")
        print(f"  Estimate: ${latest.estimate:.2f}")
        print(f"  Discount: ${latest.discount:.2f}")
except Exception as e:
    print(f"\nError during pipeline: {e}")
    import traceback
    traceback.print_exc()

print("\n")

