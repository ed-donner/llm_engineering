import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

from datasets import load_dataset
from parser import parse
from tqdm import tqdm

CHUNK_SIZE = 1000

cpu_count = os.cpu_count()
WORKERS = max(cpu_count - 1, 1)


class ShippingContractLoader:
    def __init__(self):
        self.dataset = None

    def from_datapoint(self, datapoint):
        """
        Try to create a ShippingContract from this datapoint
        Return the ShippingContract
        """
        return parse(datapoint)

    def from_chunk(self, chunk):
        """
        Create a list of ShippingContracts from this chunk of elements from the Dataset
        """
        batch = [self.from_datapoint(datapoint) for datapoint in chunk]
        return [contract for contract in batch if contract is not None]

    def chunk_generator(self):
        """
        Iterate over the Dataset, yielding chunks of datapoints at a time
        """
        size = len(self.dataset)
        for i in range(0, size, CHUNK_SIZE):
            yield self.dataset.select(range(i, min(i + CHUNK_SIZE, size)))

    def load_in_parallel(self, workers):
        """
        Use concurrent.futures to farm out the work to process chunks of datapoints -
        This speeds up processing significantly, but will tie up your computer while it's doing so!
        """
        results = []
        chunk_count = (len(self.dataset) // CHUNK_SIZE) + 1
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for batch in tqdm(
                pool.map(self.from_chunk, self.chunk_generator()), total=chunk_count
            ):
                results.extend(batch)
        return results

    def load(self, workers=WORKERS):
        """
        Load in this dataset; the workers parameter specifies how many processes
        should work on loading and scrubbing the data
        """
        start = datetime.now()
        print("Loading dataset", flush=True)
        self.dataset = load_dataset(
            "MongoDB/supply_chain_contracts_dataset_small",
            split="train",
            trust_remote_code=True,
        )
        results = self.load_in_parallel(workers)
        finish = datetime.now()
        print(
            f"Completed with {len(results):,} datapoints in {(finish - start).total_seconds() / 60:.1f} mins",
            flush=True,
        )
        return results
