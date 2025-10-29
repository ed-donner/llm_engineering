from typing import Optional
from transformers import AutoTokenizer
import re
import os

# Try multiple model sources in order of preference
BASE_MODEL_OPTIONS = [
    "/root/.llama/checkpoints/Llama3.1-8B",  # Local llama-stack download
    "microsoft/DialoGPT-medium",  # Accessible alternative
    "gpt2"  # Fallback
]

BASE_MODEL = None

MIN_TOKENS = 150  # Any less than this, and we don't have enough useful content
MAX_TOKENS = 160  # Truncate after this many tokens. Then after adding in prompt text, we will get to around 180 tokens

MIN_CHARS = 300
CEILING_CHARS = MAX_TOKENS * 7

class Item:
    """
    An Item is a cleaned, curated datapoint of a Product with a Price
    Enhanced version with better error handling and alternative tokenizer
    """
    
    # Initialize tokenizer with fallback options
    tokenizer = None
    for model_path in BASE_MODEL_OPTIONS:
        try:
            if model_path.startswith("/") and not os.path.exists(model_path):
                continue  # Skip local paths that don't exist
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            BASE_MODEL = model_path
            print(f"✅ Successfully loaded tokenizer from: {model_path}")
            break
        except Exception as e:
            print(f"⚠️  Failed to load {model_path}: {e}")
            continue
    
    if tokenizer is None:
        print("❌ All tokenizer options failed. Using character-based fallback.")
        # Create a dummy tokenizer for fallback
        class DummyTokenizer:
            def encode(self, text, add_special_tokens=False):
                # Rough approximation: 1 token ≈ 4 characters
                return list(range(len(text) // 4))
            def decode(self, tokens):
                return "dummy text"
        tokenizer = DummyTokenizer()
        BASE_MODEL = "fallback"
    
    PREFIX = "Price is $"
    QUESTION = "How much does this cost to the nearest dollar?"
    REMOVALS = [
        '"Batteries Included?": "No"', 
        '"Batteries Included?": "Yes"', 
        '"Batteries Required?": "No"', 
        '"Batteries Required?": "Yes"', 
        "By Manufacturer", 
        "Item", 
        "Date First", 
        "Package", 
        ":", 
        "Number of", 
        "Best Sellers", 
        "Number", 
        "Product "
    ]

    title: str
    price: float
    category: str
    token_count: int = 0
    details: Optional[str]
    prompt: Optional[str] = None
    include = False

    def __init__(self, data, price):
        self.title = data['title']
        self.price = price
        self.parse(data)

    def scrub_details(self):
        """
        Clean up the details string by removing common text that doesn't add value
        """
        details = self.details
        for remove in self.REMOVALS:
            details = details.replace(remove, "")
        return details

    def scrub(self, stuff):
        """
        Clean up the provided text by removing unnecessary characters and whitespace
        Also remove words that are 7+ chars and contain numbers, as these are likely irrelevant product numbers
        """
        stuff = re.sub(r'[:\[\]"{}【】\s]+', ' ', stuff).strip()
        stuff = stuff.replace(" ,", ",").replace(",,,",",").replace(",,",",")
        words = stuff.split(' ')
        select = [word for word in words if len(word)<7 or not any(char.isdigit() for char in word)]
        return " ".join(select)
    
    def parse(self, data):
        """
        Parse this datapoint and if it fits within the allowed Token range,
        then set include to True
        """
        contents = '\n'.join(data['description'])
        if contents:
            contents += '\n'
        features = '\n'.join(data['features'])
        if features:
            contents += features + '\n'
        self.details = data['details']
        if self.details:
            contents += self.scrub_details() + '\n'
        if len(contents) > MIN_CHARS:
            contents = contents[:CEILING_CHARS]
            text = f"{self.scrub(self.title)}\n{self.scrub(contents)}"
            tokens = self.tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) > MIN_TOKENS:
                tokens = tokens[:MAX_TOKENS]
                text = self.tokenizer.decode(tokens)
                self.make_prompt(text)
                self.include = True

    def make_prompt(self, text):
        """
        Set the prompt instance variable to be a prompt appropriate for training
        """
        self.prompt = f"{self.QUESTION}\n\n{text}\n\n"
        self.prompt += f"{self.PREFIX}{str(round(self.price))}.00"
        self.token_count = len(self.tokenizer.encode(self.prompt, add_special_tokens=False))

    def test_prompt(self):
        """
        Return a prompt suitable for testing, with the actual price removed
        """
        return self.prompt.split(self.PREFIX)[0] + self.PREFIX

    def __repr__(self):
        """
        Return a String version of this Item
        """
        return f"<{self.title} = ${self.price}>"



