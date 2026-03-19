"""
Load job postings from HuggingFace datasets.
Uses lukebarousse/data_jobs - 785K+ data analytics job postings from 2023.
"""

from datetime import datetime
from tqdm import tqdm
from datasets import load_dataset
from job_salary.parser import parse

CHUNK_SIZE = 5_000


class JobLoader:
    """Load and parse job postings from HuggingFace."""

    def __init__(self, split: str = "train", stream: bool = False):
        """
        Args:
            split: Dataset split - "train" loads full dataset (streaming if large)
            stream: If True, use streaming for large datasets
        """
        self.split = split
        self.stream = stream
        self.dataset = None

    def load(self, max_rows: int | None = None) -> list:
        """
        Load job postings from lukebarousse/data_jobs.
        Only keeps rows with valid salary_year_avg.
        """
        start = datetime.now()
        print("Loading lukebarousse/data_jobs...", flush=True)

        if self.stream:
            self.dataset = load_dataset(
                "lukebarousse/data_jobs",
                split=self.split,
                streaming=True,
                trust_remote_code=True,
            )
            results = self._load_streaming(max_rows)
        else:
            # Load in chunks to manage memory (dataset is 785K rows)
            ds = load_dataset("lukebarousse/data_jobs", split=self.split, trust_remote_code=True)
            total = min(len(ds), max_rows) if max_rows else len(ds)
            results = []
            for i in tqdm(range(0, total, CHUNK_SIZE), desc="Parsing"):
                end = min(i + CHUNK_SIZE, total)
                chunk = ds.select(range(i, end))
                for j in range(len(chunk)):
                    job = parse(chunk[j])
                    if job is not None:
                        results.append(job)

        finish = datetime.now()
        print(
            f"Completed with {len(results):,} jobs in {(finish - start).total_seconds() / 60:.1f} mins",
            flush=True,
        )
        return results

    def _load_streaming(self, max_rows: int | None) -> list:
        results = []
        for i, row in enumerate(tqdm(self.dataset)):
            if max_rows and i >= max_rows:
                break
            job = parse(dict(row))
            if job is not None:
                results.append(job)
        return results
