"""Configuration settings for Week 8 multi-agent system"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for the multi-agent system"""
    
    # API Keys
    HF_TOKEN = os.getenv('HF_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MODAL_TOKEN_ID = os.getenv('MODAL_TOKEN_ID')
    MODAL_TOKEN_SECRET = os.getenv('MODAL_TOKEN_SECRET')
    PUSHOVER_USER = os.getenv('PUSHOVER_USER')
    PUSHOVER_TOKEN = os.getenv('PUSHOVER_TOKEN')
    
    # Mode Settings
    LITE_MODE = os.getenv('LITE_MODE', 'False').lower() == 'true'
    USE_MODAL = os.getenv('USE_MODAL', 'False').lower() == 'true'
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'False').lower() == 'true'
    
    # Model Settings
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    FRONTIER_MODEL = os.getenv('FRONTIER_MODEL', 'gpt-5.1')
    SPECIALIST_MODEL = os.getenv('SPECIALIST_MODEL', 'meta-llama/Llama-3.2-3B')
    
    # Dataset Settings
    HF_USERNAME = "ed-donner"
    
    @property
    def DATASET_NAME(self):
        return f"{self.HF_USERNAME}/items_lite" if self.LITE_MODE else f"{self.HF_USERNAME}/items_full"
    
    # RAG Settings
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './data/products_vectorstore')
    TOP_K_SIMILAR = int(os.getenv('TOP_K_SIMILAR', '5'))
    
    # Ensemble Settings
    USE_CONFIDENCE_WEIGHTING = os.getenv('USE_CONFIDENCE_WEIGHTING', 'True').lower() == 'true'
    DEFAULT_FRONTIER_WEIGHT = float(os.getenv('DEFAULT_FRONTIER_WEIGHT', '0.8'))
    DEFAULT_SPECIALIST_WEIGHT = float(os.getenv('DEFAULT_SPECIALIST_WEIGHT', '0.1'))
    DEFAULT_NEURAL_WEIGHT = float(os.getenv('DEFAULT_NEURAL_WEIGHT', '0.1'))
    
    # Evaluation Settings
    EVAL_SIZE = 200
    
    # Prompt Templates
    PRICE_QUESTION = "What does this cost to the nearest dollar?"
    PRICE_PREFIX = "Price is $"
    
    @classmethod
    def display(cls):
        """Display current configuration"""
        config = cls()
        print("=" * 60)
        print("WEEK 8 MULTI-AGENT SYSTEM CONFIGURATION")
        print("=" * 60)
        print(f"Mode: {'LITE' if config.LITE_MODE else 'FULL'}")
        print(f"Dataset: {config.DATASET_NAME}")
        print(f"Use Modal: {config.USE_MODAL}")
        print(f"Notifications: {config.ENABLE_NOTIFICATIONS}")
        print(f"Embedding Model: {config.EMBEDDING_MODEL}")
        print(f"Frontier Model: {config.FRONTIER_MODEL}")
        print(f"Vector DB: {config.VECTOR_DB_PATH}")
        print(f"Top-K Similar: {config.TOP_K_SIMILAR}")
        print(f"Confidence Weighting: {config.USE_CONFIDENCE_WEIGHTING}")
        print("=" * 60)
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        config = cls()
        errors = []
        
        if not config.HF_TOKEN:
            errors.append("HF_TOKEN not set")
        if not config.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY not set")
        
        if config.USE_MODAL:
            if not config.MODAL_TOKEN_ID:
                errors.append("MODAL_TOKEN_ID not set (required when USE_MODAL=True)")
            if not config.MODAL_TOKEN_SECRET:
                errors.append("MODAL_TOKEN_SECRET not set (required when USE_MODAL=True)")
        
        if config.ENABLE_NOTIFICATIONS:
            if not config.PUSHOVER_USER:
                errors.append("PUSHOVER_USER not set (required when ENABLE_NOTIFICATIONS=True)")
            if not config.PUSHOVER_TOKEN:
                errors.append("PUSHOVER_TOKEN not set (required when ENABLE_NOTIFICATIONS=True)")
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ Configuration valid")
        return True


# Create singleton instance
config = Config()
