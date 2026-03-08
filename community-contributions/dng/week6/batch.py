import json
import pickle
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, retry_if_result, wait_fixed
from tqdm.notebook import tqdm

load_dotenv(override=True)
client = OpenAI()

MODEL = "gpt-5-nano-2025-08-07"
BATCHES_FOLDER = "batches"
OUTPUT_FOLDER = "output"
state = Path("batches.pkl")

SYSTEM_PROMPT = """Create a concise description of the relationship between the shipping cost, type of goods, and the weight of the shipment. Respond only in this format. Do not include part numbers.
Type of goods: eg Electronics, Furniture, Clothing, etc.
Weight: eg 100kg, 200kg, etc.
Shipping cost: eg $100, $200, etc."""


class Batch:
    BATCH_SIZE = 200

    batches = []

    def __init__(self, contracts, start, end):
        self.contracts = contracts
        self.start = start
        self.end = end
        self.filename = f"{start}_{end}.jsonl"
        self.file_id = None
        self.batch_id = None
        self.output_file_id = None
        self.done = False
        self.output = Path(OUTPUT_FOLDER)
        self.batches = Path(BATCHES_FOLDER)
        self.output.mkdir(parents=True, exist_ok=True)
        self.batches.mkdir(parents=True, exist_ok=True)

    def make_jsonl(self, contract):
        body = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": contract.full},
            ],
            "reasoning_effort": "low",
        }
        line = {
            "custom_id": str(contract.contract_number),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body,
        }
        return json.dumps(line)

    def make_file(self):
        batch_file = self.batches / self.filename
        with batch_file.open("w") as f:
            for contract in self.contracts[self.start : self.end]:
                f.write(self.make_jsonl(contract))
                f.write("\n")

    def send_file(self):
        batch_file = self.batches / self.filename
        with batch_file.open("rb") as f:
            response = client.files.create(file=f, purpose="batch")
        self.file_id = response.id

    def submit_batch(self):
        response = client.batches.create(
            completion_window="24h",
            endpoint="/v1/chat/completions",
            input_file_id=self.file_id,
        )
        self.batch_id = response.id

    def is_ready(self):
        response = client.batches.retrieve(self.batch_id)
        status = response.status
        if status == "completed":
            self.output_file_id = response.output_file_id
        return status == "completed"

    def fetch_output(self):
        output_file = str(self.output / self.filename)
        response = client.files.content(self.output_file_id)
        response.write_to_file(output_file)

    def apply_output(self):
        output_file = str(self.output / self.filename)
        with open(output_file, "r") as f:
            for line in f:
                json_line = json.loads(line)
                id = json_line["custom_id"]
                summary = json_line["response"]["body"]["choices"][0]["message"][
                    "content"
                ]
                index = [contract.contract_number for contract in self.contracts].index(
                    id
                )
                self.contracts[index].summary = summary
        self.done = True

    @classmethod
    def create(cls, contracts):
        for start in range(0, len(contracts), cls.BATCH_SIZE):
            end = min(start + cls.BATCH_SIZE, len(contracts))
            batch = Batch(contracts, start, end)
            cls.batches.append(batch)
        print(f"Created {len(cls.batches)} batches")

    @classmethod
    def run(cls):
        for batch in tqdm(cls.batches):
            batch.make_file()
            batch.send_file()
            batch.submit_batch()
        print(f"Submitted {len(cls.batches)} batches")

    @classmethod
    @retry(
        retry=retry_if_result(lambda result: not result),
        wait=wait_fixed(60),
    )
    def fetch(cls):
        for batch in tqdm(cls.batches):
            if not batch.done:
                if batch.is_ready():
                    batch.fetch_output()
                    batch.apply_output()
        finished = [batch for batch in cls.batches if batch.done]
        print(f"Finished {len(finished)} of {len(cls.batches)} batches")
        return all(batch.done for batch in cls.batches)

    @classmethod
    def save(cls):
        contracts = cls.batches[0].contracts
        for batch in cls.batches:
            batch.contracts = None
        with state.open("wb") as f:
            pickle.dump(cls.batches, f)
        for batch in cls.batches:
            batch.contracts = contracts
        print(f"Saved {len(cls.batches)} batches")

    @classmethod
    def load(cls, contracts):
        with state.open("rb") as f:
            cls.batches = pickle.load(f)
        for batch in cls.batches:
            batch.contracts = contracts
        print(f"Loaded {len(cls.batches)} batches")
