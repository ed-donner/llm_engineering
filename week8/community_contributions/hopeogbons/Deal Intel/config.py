#!/usr/bin/env python3
"""
Centralized configuration for Deal Intel.
"""

import os
from typing import List

# Vector store
DB_PATH = os.getenv("DEAL_INTEL_DB_PATH", "products_vectorstore")
COLLECTION_NAME = os.getenv("DEAL_INTEL_COLLECTION", "products")

# Embedding model
MODEL_NAME = os.getenv("DEAL_INTEL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Categories (kept consistent with framework plot colors)
CATEGORIES: List[str] = [
    "Appliances",
    "Automotive",
    "Cell_Phones_and_Accessories",
    "Electronics",
    "Musical_Instruments",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Toys_and_Games",
]

# Data limits
MAX_ITEMS_PER_CATEGORY = int(os.getenv("DEAL_INTEL_MAX_ITEMS", "2500"))
BATCH_SIZE = int(os.getenv("DEAL_INTEL_BATCH_SIZE", "500"))

# Training limits
RF_MAX_DATAPOINTS = int(os.getenv("DEAL_INTEL_RF_MAX_DATAPOINTS", "10000"))
ENSEMBLE_SAMPLE_SIZE = int(os.getenv("DEAL_INTEL_ENSEMBLE_SAMPLE_SIZE", "200"))