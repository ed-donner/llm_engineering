"""
Configuration for the Investment Research system.
Paths are relative to the haastrupea directory.
"""

import os

# Base directory: week8/community_contributions/haastrupea
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "research_vectorstore")
COLLECTION_NAME = "filings"
MEMORY_FILENAME = os.path.join(BASE_DIR, "research_memory.json")
KNOWLEDGE_BASE = os.path.join(BASE_DIR, "knowledge_base", "filings")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Default watched tickers for MVP
DEFAULT_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA"]
