"""Configuration settings for Week 7 fine-tuning project"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for the project"""
    
    # HuggingFace
    HF_TOKEN = os.getenv('HF_TOKEN')
    HF_USERNAME = "ed-donner"  # Dataset owner
    
    # Training Mode
    LITE_MODE = os.getenv('LITE_MODE', 'True').lower() == 'true'
    
    # Datasets
    @property
    def DATASET_NAME(self):
        return f"{self.HF_USERNAME}/items_lite" if self.LITE_MODE else f"{self.HF_USERNAME}/items_full"
    
    @property
    def PROMPTS_DATASET_NAME(self):
        return f"{self.HF_USERNAME}/items_prompts_lite" if self.LITE_MODE else f"{self.HF_USERNAME}/items_prompts_full"
    
    # Model Settings
    BASE_MODEL = "meta-llama/Llama-3.2-3B"
    
    # Token Settings
    MAX_TOKENS = 110  # Cutoff for product descriptions
    MAX_SEQ_LENGTH = 256  # Maximum sequence length for training
    
    # QLoRA Settings
    @property
    def LORA_RANK(self):
        return 16 if self.LITE_MODE else 32
    
    @property
    def LORA_ALPHA(self):
        return 32 if self.LITE_MODE else 64
    
    LORA_DROPOUT = 0.05
    LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]
    
    # Training Settings
    LEARNING_RATE = 2e-4
    
    @property
    def BATCH_SIZE(self):
        return 4 if self.LITE_MODE else 8
    
    GRADIENT_ACCUMULATION_STEPS = 4
    
    @property
    def NUM_EPOCHS(self):
        return 3 if self.LITE_MODE else 5
    
    WARMUP_STEPS = 100
    SAVE_STEPS = 500
    LOGGING_STEPS = 10
    
    # Evaluation Settings
    EVAL_SIZE = 200  # Number of test samples to evaluate
    
    # Prompt Template
    QUESTION = "What does this cost to the nearest dollar?"
    PREFIX = "Price is $"
    
    @classmethod
    def get_prompt_template(cls, summary: str, price: float = None) -> str:
        """Generate prompt for training or inference"""
        prompt = f"{cls.QUESTION}\n\n{summary}\n\n{cls.PREFIX}"
        if price is not None:
            prompt += f"{round(price)}.00"
        return prompt
    
    @classmethod
    def display(cls):
        """Display current configuration"""
        config = cls()
        print("=" * 60)
        print("WEEK 7 FINE-TUNING CONFIGURATION")
        print("=" * 60)
        print(f"Mode: {'LITE' if config.LITE_MODE else 'FULL'}")
        print(f"Dataset: {config.DATASET_NAME}")
        print(f"Base Model: {config.BASE_MODEL}")
        print(f"LoRA Rank: {config.LORA_RANK}")
        print(f"LoRA Alpha: {config.LORA_ALPHA}")
        print(f"Batch Size: {config.BATCH_SIZE}")
        print(f"Epochs: {config.NUM_EPOCHS}")
        print(f"Learning Rate: {config.LEARNING_RATE}")
        print(f"Max Tokens: {config.MAX_TOKENS}")
        print("=" * 60)


# Create singleton instance
config = Config()
