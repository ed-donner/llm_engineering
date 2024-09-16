from typing import Optional
from datetime import datetime
from tqdm import tqdm
from datasets import load_dataset
from transformers import AutoTokenizer
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
MIN_TOKENS = 150
MAX_TOKENS = 160
MIN_CHARS = 300
CEILING_CHARS = MAX_TOKENS * 7

class Item:
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    PREFIX = "Price is $"
    QUESTION = "How much does this cost to the nearest dollar?"

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


class ItemLoader:

    def __init__(self, name):
        self.name = name
        self.dataset = None

    def from_datapoint(self, datapoint):
        try:
            price_str = datapoint['price']
            if price_str:
                price = float(price_str)
                if price >= 0.5 and price <= 999.49:
                    item = Item(datapoint, price)
                    if item.include:
                        return item
        except ValueError:
            pass
        return None

    def from_chunk(self, chunk):
        batch = []
        for datapoint in chunk:
            result = self.from_datapoint(datapoint)
            if result:
                batch.append(result)
        return batch

    def make_chunks(self):
        print("Preparing data chunks...", end="", flush=True)
        size = len(self.dataset)
        chunks = []
        for i in range(0, size, 1000):
            chunks.append(self.dataset.select(range(i, min(i + 1000, size))))
        print(" done.", flush=True)
        return chunks

    def load_in_parallel(self, chunks, workers):
        results = []
        with ProcessPoolExecutor(max_workers=6) as pool:
            for batch in tqdm(pool.map(self.from_chunk, chunks), total=len(chunks)):
                results.extend(batch)
        for result in results:
            result.category = self.name
        return results
            
    def load(self, workers=8):
        start = datetime.now()
        print(f"Loading dataset {self.name}", flush=True)
        self.dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", f"raw_meta_{self.name}", split="full", trust_remote_code=True)
        chunks = self.make_chunks()
        results = self.load_in_parallel(chunks, workers)
        finish = datetime.now()
        print(f"Completed loading {self.name} with {len(results):,} datapoints in {(finish-start).total_seconds()/60:.1f} mins", flush=True)
        return results
        

    
    