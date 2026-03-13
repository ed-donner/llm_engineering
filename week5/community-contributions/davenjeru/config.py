"""
Configuration constants for the Recipe RAG System.
"""

# Kaggle dataset configuration
KAGGLE_DATASET = "thedevastator/better-recipes-for-a-better-life"
CSV_FILENAME = "recipes.csv"

# Directory paths
OUTPUT_DIR = "knowledge"
VECTOR_DB_DIR = "vector_db"

# Model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gpt-3.5-turbo"

# Default number of recipes to load
DEFAULT_NUM_RECIPES = 100
