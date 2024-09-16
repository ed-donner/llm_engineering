from typing import Optional
from tqdm import tqdm
from datasets import load_dataset
from transformers import AutoTokenizer
import re

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
MIN_TOKENS = 150
MAX_TOKENS = 160
MIN_CHARS = 300
CEILING_CHARS = MAX_TOKENS * 7

class Item:
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    eos = tokenizer.eos_token
    bos = tokenizer.bos_token
    PREFIX = "Price is $"
    QUESTION = "How much does this cost to the nearest dollar?"

    title: str
    price: float
    category: str
    token_count: int = 0
    text: Optional[str]
    details: Optional[str]
    prompt: Optional[str] = None
    include = False

    def __init__(self, data, price, category):
        self.title = data['title']
        self.price = price
        self.category = category
        self.parse(data)

    def scrub_details(self):
        details = self.details
        removals = ['"Batteries Included?": "No"', '"Batteries Included?": "Yes"', '"Batteries Required?": "No"', '"Batteries Required?": "Yes"', "By Manufacturer", "Item", "Date First", "Package", ":", "Number of", "Best Sellers", "Number", "Product "]
        for remove in removals:
            details = details.replace(remove, "")
        return details

    def scrub(self, stuff):
        stuff = re.sub(r'[:\[\]"{}【】\s]+', ' ', stuff).strip()
        stuff = stuff.replace(" ,", ",").replace(",,,",",").replace(",,",",")
        words = stuff.split(' ')
        select = [word for word in words if len(word)<7 or not any(char.isdigit() for char in word)]
        return " ".join(select)
    
    def parse(self, data):
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
            text = f"{self.scrub(self.title)}\n{self.scrub(contents[:CEILING_CHARS])}"
            tokens = self.tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) > MIN_TOKENS:
                tokens = tokens[:MAX_TOKENS]
                text = self.tokenizer.decode(tokens)
                self.make_prompt(text)
                self.include = True

    def make_prompt(self, text):
        self.prompt = f"{self.QUESTION}\n\n{text}\n\n"
        self.prompt += f"{self.PREFIX}{str(round(self.price))}.00"
        self.token_count = len(self.tokenizer.encode(self.prompt, add_special_tokens=False))

    def test_prompt(self):
        return self.prompt.split(self.PREFIX)[0] + self.PREFIX

def read_dataset(name):
    print(f"Loading dataset {name}", flush=True)
    dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", f"raw_meta_{name}", split="full", trust_remote_code=True)
    results = []
    for data in dataset:
        try:
            price_str = data['price']
            if price_str:
                price = float(price_str)
                if price >= 0.5 and price <= 999.49:
                    item = Item(data, price, name)
                    if item.include:
                        results.append(item)
        except ValueError:
            pass
    print(f"Completed loading {name} with {len(results):,} datapoints", flush=True)
    del dataset
    return results