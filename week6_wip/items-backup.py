from typing import Optional
from tqdm import tqdm
from datasets import load_dataset
from transformers import AutoTokenizer
import re

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
MIN_TOKENS = 100
MAX_TOKENS = 141

class Item:
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    PREFIX = "Price is $"

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

    
    def parse(self, data):
        self.text = self.title + '\n'
        self.text += '\n'.join(data['description'])+ '\n'
        self.details = data['details']
        if self.details:
            self.text += self.scrub_details() + '\n'
        features = '\n'.join(data['features'])
        if features:
            self.text += '\n' + features
        self.text = re.sub(r'[:\[\]"{}【】\s]+', ' ', self.text).strip()
        self.text = self.text.replace(" ,", ",").replace(",,,",",").replace(",,",",")
        tokens = self.tokenizer.encode(self.text, add_special_tokens=False)
        if len(tokens) > MIN_TOKENS:
            tokens = tokens[:MAX_TOKENS]
            self.text = self.tokenizer.decode(tokens)
            self.make_prompt()
            self.count_tokens()
            self.include = True

    def question(self):
        prompt = "How much is this?\n"
        prompt += f"{self.text}\n"
        return prompt

    def messages(self):
        return [
            {"role":"system", "content": "You estimate prices to the nearest dollar"},
            {"role":"user", "content": self.question()},
            {"role":"assistant", "content": f"{self.PREFIX}{str(round(self.price))}.00"}
        ]

    def make_prompt(self):
        prompt = self.tokenizer.apply_chat_template(self.messages(), tokenize=False, add_generation_prompt=False)
        groups = prompt.split('\n\n')
        self.prompt = groups[0]+'\n\n'+'\n\n'.join(groups[2:])

    def count_tokens(self):
        self.token_count = len(self.tokenizer.encode(self.prompt))

    def tokens_between(self, low, high):
        return self.token_count >= low and self.token_count < high

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