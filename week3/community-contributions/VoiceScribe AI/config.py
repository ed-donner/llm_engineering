"""
Configuration file for VoiceScribe AI
Customize models and settings here
"""

# ============================================
# Model Configuration
# ============================================

# Whisper Model Options:
# - "openai/whisper-tiny.en" - Fastest, least accurate (~1GB)
# - "openai/whisper-base.en" - Fast, decent accuracy (~1.5GB)
# - "openai/whisper-small.en" - Balanced (~2.5GB)
# - "openai/whisper-medium.en" - Good accuracy, slower (~5GB) [DEFAULT]
# - "openai/whisper-large" - Best accuracy, slowest (~10GB)
WHISPER_MODEL = "openai/whisper-medium.en"

# Summarization Model Options:
# - "facebook/bart-large-cnn" - Good quality summaries [DEFAULT]
# - "google/pegasus-xsum" - Alternative summarization
# - "t5-base" - Lighter weight option
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"

# QA Model Options:
# - "google/flan-t5-base" - Good balance [DEFAULT]
# - "google/flan-t5-large" - Better quality, slower
# - "google/flan-t5-small" - Faster, less accurate
QA_MODEL = "google/flan-t5-base"

# Embeddings Model Options:
# - "sentence-transformers/all-MiniLM-L6-v2" - Fast, good quality [DEFAULT]
# - "sentence-transformers/all-mpnet-base-v2" - Better quality, slower
EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ============================================
# Processing Configuration
# ============================================

# Maximum audio length in seconds (0 = no limit)
MAX_AUDIO_LENGTH = 0

# Chunk size for text splitting (for RAG)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Number of key points to extract
NUM_KEY_POINTS = 5

# Summary length settings
SUMMARY_MAX_LENGTH = 200
SUMMARY_MIN_LENGTH = 50

# ============================================
# RAG Configuration
# ============================================

# Number of chunks to retrieve for Q&A
RAG_TOP_K = 3

# Vector store type
# - "FAISS" - Fast and efficient [DEFAULT]
# - "Chroma" - Alternative (requires chromadb)
VECTOR_STORE_TYPE = "FAISS"

# ============================================
# UI Configuration
# ============================================

# Gradio interface settings
SHARE_INTERFACE = True  # Create public shareable link
SERVER_PORT = 7860
SERVER_NAME = "0.0.0.0"  # "0.0.0.0" for external access, "127.0.0.1" for local only

# Theme options:
# - "default" - Gradio default theme
# - "soft" - Soft theme
# - "compact" - Compact layout
UI_THEME = "default"

# ============================================
# Performance Settings
# ============================================

# Force CPU (set to True to disable GPU)
FORCE_CPU = False

# Batch size for processing (lower if out of memory)
BATCH_SIZE = 8

# Number of beams for summarization (higher = better quality, slower)
NUM_BEAMS = 4

# ============================================
# Advanced Settings
# ============================================

# Enable verbose logging
VERBOSE = False

# Cache directory for models
CACHE_DIR = None  # None = use default HuggingFace cache

# Enable gradient checkpointing (saves memory, slower)
GRADIENT_CHECKPOINTING = False

# ============================================
# Feature Flags
# ============================================

# Enable/disable features
ENABLE_TRANSCRIPTION = True
ENABLE_SUMMARIZATION = True
ENABLE_KEY_POINTS = True
ENABLE_QA = True
ENABLE_SEARCH = True
