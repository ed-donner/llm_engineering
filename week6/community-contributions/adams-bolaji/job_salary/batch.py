"""
Batch API client for LLM-based job description rewriting.
Uses Groq batch API (same pattern as pricer).
"""

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
BATCHES_FOLDER = "batches"
OUTPUT_FOLDER = "output"
state = Path("batches.pkl")

SYSTEM_PROMPT = """Create a concise job posting summary. Respond only in this format.
Title: Standardized job title
Role: eg Data Scientist, ML Engineer
Company: Company name
Location: City, Country
Schedule: Full-time, Part-time, etc.
Remote: Yes/No
Skills: Comma-separated key skills (max 10)
Experience: Junior, Mid, Senior, or Executive"""


class Batch:
    BATCH_SIZE = 1_000
    batches = []

    def __init__(self, jobs, start, end, lite):
        self.jobs = jobs
        self.start = start
        self.end = end
        self.filename = f"{start}_{end}.jsonl"
        self.file_id = None
        self.batch_id = None
        self.output_file_id = None
        self.done = False
        folder = Path("lite") if lite else Path("full")
        self.batches = folder / BATCHES_FOLDER
        self.output = folder / OUTPUT_FOLDER
        self.batches.mkdir(parents=True, exist_ok=True)
        self.output.mkdir(parents=True, exist_ok=True)

    def make_jsonl(self, job):
        body = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": job.full},
            ],
            "reasoning_effort": "low",
        }
        line = {
            "custom_id": str(job.id),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body,
        }
        return json.dumps(line)

    def make_file(self):
        batch_file = self.batches / self.filename
        with batch_file.open("w") as f:
            for job in self.jobs[self.start : self.end]:
                f.write(self.make_jsonl(job))
                f.write("\n")

    def send_file(self):
        batch_file = self.batches / self.filename
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
        status = response.status
        if status == "completed":
            self.output_file_id = response.output_file_id
        return status == "completed"

    def fetch_output(self):
        output_file = str(self.output / self.filename)
        response = groq.files.content(self.output_file_id)
        response.write_to_file(output_file)

    def apply_output(self):
        output_file = str(self.output / self.filename)
        with open(output_file, "r") as f:
            for line in f:
                json_line = json.loads(line)
                id = int(json_line["custom_id"])
                summary = json_line["response"]["body"]["choices"][0]["message"]["content"]
                self.jobs[id].summary = summary
        self.done = True

    @classmethod
    def create(cls, jobs, lite):
        Batch.batches = []
        for start in range(0, len(jobs), cls.BATCH_SIZE):
            end = min(start + cls.BATCH_SIZE, len(jobs))
            batch = Batch(jobs, start, end, lite)
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
    def fetch(cls):
        for batch in tqdm(cls.batches):
            if not batch.done:
                if batch.is_ready():
                    batch.fetch_output()
                    batch.apply_output()
        finished = [batch for batch in cls.batches if batch.done]
        print(f"Finished {len(finished)} of {len(cls.batches)} batches")
