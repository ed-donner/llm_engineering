from datetime import datetime # Measure how long loading takes
from tqdm import tqdm # Shows a progress bar while processing data
from datasets import load_dataset # Load a dataset from Hugging Face Hub
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor # For parallel processing (speed)
from items import Item

CHUNK_SIZE = 1000 # Process the dataset in chunks of 1000 datapoints at a time (for efficiency)
MIN_PRICE = 0.5
MAX_PRICE = 999.49
WORKER = 4 # Set the number of workers here

class ItemLoader:

    def __init__(self, name):
        """
        Initialize the loader with a dataset name.
        """
        self.name = name # Store the category name
        self.dataset = None #Placeholder for the dataset (we load it later in load())

    def process_chunk(self, chunk):
        """
        Convert a chunk of datapoints into valid Item objects.
        """
        batch = [] # Initialize the list to hold valid items

        # Loop through each datapoint in the chunk
        for datapoint in chunk:
            try:
                # Extract price from datapoint
                price_str = datapoint['price']
                if price_str:
                    price = float(price_str)

                    # Check if price is within valid range
                    if MIN_PRICE <= price <= MAX_PRICE:
                        item = Item(datapoint, price)

                        # Keep only valid items
                        if item.include:
                            batch.append(item)
            except ValueError:
                continue # Skip datapoints with invalid price format
        return batch # Return the list of valid items


    def load_in_parallel(self, workers):
        """
        Split the dataset into chunks and process them in parallel.
        """
        results = []
        size = len(self.dataset)
        chunk_count = (size // CHUNK_SIZE) + 1
    
        # Build chunks directly here (no separate function)
        chunks = [
            self.dataset.select(range(i, min(i + CHUNK_SIZE, size)))
            for i in range(0, size, CHUNK_SIZE)
        ]

        # Process chunks in parallel using multiple CPU cores
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for batch in tqdm(pool.map(self.process_chunk, chunks), total=chunk_count):
                results.extend(batch)

        # Add the category name to each result
        for result in results:
            result.category = self.name
    
        return results

            
    def load(self, workers=WORKER):
        """
        Load and process the dataset, returning valid items.
        """
        # Record start time
        start = datetime.now()
    
        # Print loading message
        print(f"Loading dataset {self.name}", flush=True)
    
        # Load dataset from Hugging Face (based on category name)
        self.dataset = load_dataset(
            "McAuley-Lab/Amazon-Reviews-2023",
            f"raw_meta_{self.name}",
            split="full",
            trust_remote_code=True
        )
    
        # Process the dataset in parallel and collect valid items
        results = self.load_in_parallel(workers)
    
        # Record end time and print summary
        finish = datetime.now()
        print(
            f"Completed {self.name} with {len(results):,} datapoints in {(finish-start).total_seconds()/60:.1f} mins",
            flush=True
        )
    
        # Return the list of valid items
        return results


    
    