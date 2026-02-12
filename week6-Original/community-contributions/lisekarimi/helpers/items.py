from typing import Optional  # A variable might be a certain type or None
from transformers import AutoTokenizer
import re

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"

MIN_TOKENS = 150 # Minimum tokens required to accept an item
MAX_TOKENS = 160 # We limit to 160 tokens so that after adding prompt text, the total stays around 180 tokens.

MIN_CHARS = 300 # Reject items with less than 300 characters
CEILING_CHARS = MAX_TOKENS * 7 # Truncate long text to about 1120 characters (approx 160 tokens)

class Item:
    """
    An Item is a cleaned, curated datapoint of a Product with a Price
    """
    
    # Load tokenizer for the model
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    
    # Define PRICE_LABEL and question for the training prompt
    PRICE_LABEL = "Price is $"
    QUESTION = "How much does this cost to the nearest dollar?"

    # A list of useless phrases to remove to reduce noise for price prediction
    REMOVALS = ['"Batteries Included?": "No"', '"Batteries Included?": "Yes"', '"Batteries Required?": "No"', '"Batteries Required?": "Yes"', "By Manufacturer", "Item", "Date First", "Package", ":", "Number of", "Best Sellers", "Number", "Product "]

    # Attributes for each item
    title: str
    price: float
    category: str
    token_count: int = 0 # How many tokens in the final prompt
    
    # Optional fields
    details: Optional[str] # The value can be a string or can be None
    prompt: Optional[str] = None
    include = False # Whether to keep the item or not

    def __init__(self, data, price):
        self.title = data['title']
        self.price = price
        self.parse(data)

    def scrub_details(self):
        """
        Removes useless phrases from details, which often has repeated specs or boilerplate text.
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
        Prepares the text, checks length, tokenizes it, and sets include = True if it’s valid.
        """
        # Builds a full contents string by combining description, features, and cleaned details.
        contents = '\n'.join(data['description'])
        if contents:
            contents += '\n'
        features = '\n'.join(data['features'])
        if features:
            contents += features + '\n'
        self.details = data['details']
        if self.details:
            contents += self.scrub_details() + '\n'

        # If content is long enough, trim it to max char limit before processing.
        if len(contents) > MIN_CHARS:
            contents = contents[:CEILING_CHARS]
            
            # Clean and tokenize text, then check token count.
            text = f"{self.scrub(self.title)}\n{self.scrub(contents)}"
            tokens = self.tokenizer.encode(text, add_special_tokens=False)
            
            if len(tokens) > MIN_TOKENS:  
                # Truncate tokens, decode them back and create the training prompt
                tokens = tokens[:MAX_TOKENS]
                text = self.tokenizer.decode(tokens)
                self.make_prompt(text)
                
                # Mark the item as valid and ready to be used in training
                self.include = True  # Only items with MIN_TOKENS <= tokens <= MAX_TOKENS are kept


    def make_prompt(self, text):
        """
        Builds the training prompt using the question, text, and price. Then counts the tokens.
        """
        self.prompt = f"{self.QUESTION}\n\n{text}\n\n"
        self.prompt += f"{self.PRICE_LABEL }{str(round(self.price))}.00"
        self.token_count = len(self.tokenizer.encode(self.prompt, add_special_tokens=False))

    def test_prompt(self):
        """
        Returns the prompt without the actual price, useful for testing/inference.
        """
        return self.prompt.split(self.PRICE_LABEL )[0] + self.PRICE_LABEL 

    def __repr__(self):
        """
        Defines how the Item object looks when printed — it shows the title and price.
        """
        return f"<{self.title} = ${self.price}>"

        

    
    