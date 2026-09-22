"""
Run the Real Estate Comps Agent.
Usage (from project root or week8):
  uv run python community_contributions/adams-bolaji/run_comps_agent.py

Prerequisites:
  1. Build the vector store: uv run python community_contributions/adams-bolaji/build_vectorstore.py
  2. Set OPENAI_API_KEY in .env
  3. Optional: PUSHOVER_USER and PUSHOVER_TOKEN for push notifications
"""
import sys
from pathlib import Path

ADAMS = Path(__file__).resolve().parent
WEEK8 = ADAMS.parent.parent  # week8/
if str(WEEK8) not in sys.path:
    sys.path.insert(0, str(WEEK8))
if str(ADAMS) not in sys.path:
    sys.path.insert(0, str(ADAMS))


def main():
    from real_estate_comps_framework import RealEstateCompsFramework

    framework = RealEstateCompsFramework()
    opportunities = framework.run()
    print(f"\nTotal opportunities in memory: {len(opportunities)}")
    for i, opp in enumerate(opportunities[-5:], 1):
        print(f"  {i}. {opp.listing.product_description[:50]}... | discount ${opp.discount:,.0f}")


if __name__ == "__main__":
    main()
