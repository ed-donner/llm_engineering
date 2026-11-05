import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
import json
import pickle
from tqdm.notebook import tqdm

load_dotenv(override=True)
groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-20b"
BATCHES_FOLDER = Path("batches")
OUTPUT_FOLDER = Path("output")
state = Path("batches.pkl")

SYSTEM_PROMPT = """Create a concise description of a wine. Respond only in this format, in plain text.
Wine: Short name with the winery, wine name and grape, plus the vintage year if one is given
Style: Colour and body, eg Red, full-bodied
Origin: Region, Country
Points: The points score exactly as given
Tasting: 1 sentence on the aromas, flavours and structure
Verdict: 1 sentence on what the reviewer thinks of the wine and when to drink it, using only what the review says
Use only facts from the text. Do not add praise or ageing potential that the review does not mention.
Never mention the price, the cost, value for money or whether it is a bargain."""


class Batch:
    BATCH_SIZE = 1_000

    batches = []

    def __init__(self, items, start, end):
        self.items = items
        self.start = start
        self.end = end
        self.filename = f"{start}_{end}.jsonl"
        self.file_id = None
        self.batch_id = None
        self.output_file_id = None
        self.status = None
        self.done = False
        BATCHES_FOLDER.mkdir(parents=True, exist_ok=True)
        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    def make_jsonl(self, item):
        body = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": item.full},
            ],
            "reasoning_effort": "low",
        }
        line = {
            "custom_id": str(item.id),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body,
        }
        return json.dumps(line)

    def make_file(self):
        batch_file = BATCHES_FOLDER / self.filename
        with batch_file.open("w", encoding="utf-8") as f:
            for item in self.items[self.start : self.end]:
                f.write(self.make_jsonl(item))
                f.write("\n")

    def send_file(self):
        batch_file = BATCHES_FOLDER / self.filename
        with batch_file.open("rb") as f:
            response = groq.files.create(file=f, purpose="batch")
        self.file_id = response.id

    def submit_batch(self):
        response = groq.batches.create(
            completion_window="24h",
            endpoint="/v1/chat/completions",
            input_file_id=self.file_id,
        )
        self.batch_id = response.id

    def is_ready(self):
        response = groq.batches.retrieve(self.batch_id)
        self.status = response.status
        if self.status == "completed":
            self.output_file_id = response.output_file_id
        return self.status == "completed"

    def fetch_output(self):
        output_file = OUTPUT_FOLDER / self.filename
        response = groq.files.content(self.output_file_id)
        response.write_to_file(output_file)

    def apply_output(self):
        output_file = OUTPUT_FOLDER / self.filename
        with output_file.open("r", encoding="utf-8") as f:
            for line in f:
                json_line = json.loads(line)
                id = int(json_line["custom_id"])
                response = json_line.get("response") or {}
                if response.get("status_code") == 200:
                    summary = response["body"]["choices"][0]["message"]["content"]
                    self.items[id].summary = summary
        self.done = True

    @classmethod
    def create(cls, items):
        cls.batches = []
        for start in range(0, len(items), cls.BATCH_SIZE):
            end = min(start + cls.BATCH_SIZE, len(items))
            cls.batches.append(Batch(items, start, end))
        print(f"Created {len(cls.batches)} batches")

    @classmethod
    def run(cls):
        for batch in tqdm(cls.batches):
            batch.make_file()
            batch.send_file()
            batch.submit_batch()
        print(f"Submitted {len(cls.batches)} batches")

    @classmethod
    def fetch(cls):
        for batch in tqdm(cls.batches):
            if not batch.done:
                if batch.is_ready():
                    batch.fetch_output()
                    batch.apply_output()
        finished = [batch for batch in cls.batches if batch.done]
        print(f"Finished {len(finished)} of {len(cls.batches)} batches")
        waiting = [batch for batch in cls.batches if not batch.done]
        if waiting:
            statuses = {}
            for batch in waiting:
                statuses[batch.status] = statuses.get(batch.status, 0) + 1
            print(f"Still waiting: {statuses}")

    @classmethod
    def save(cls):
        items = cls.batches[0].items
        for batch in cls.batches:
            batch.items = None
        with state.open("wb") as f:
            pickle.dump(cls.batches, f)
        for batch in cls.batches:
            batch.items = items
        print(f"Saved {len(cls.batches)} batches")

    @classmethod
    def load(cls, items):
        with state.open("rb") as f:
            cls.batches = pickle.load(f)
        for batch in cls.batches:
            batch.items = items
        print(f"Loaded {len(cls.batches)} batches")
