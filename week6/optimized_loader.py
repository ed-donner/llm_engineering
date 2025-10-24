from datetime import datetime
from tqdm import tqdm
from datasets import load_dataset
from concurrent.futures import ProcessPoolExecutor, as_completed
from items import Item
import os

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Number of datapoints to process in each batch/chunk
# Larger chunks = fewer overhead, but more memory per worker
CHUNK_SIZE = 1000

# Price filtering boundaries - items outside this range are excluded
MIN_PRICE = 0.5      # Minimum price threshold in dollars
MAX_PRICE = 999.49   # Maximum price threshold in dollars


# ============================================================================
# ITEMLOADER CLASS
# ============================================================================

class ItemLoader:
    """
    Loads and processes Amazon product data from the McAuley-Lab dataset.
    
    This class handles:
    - Loading datasets from HuggingFace
    - Filtering items by price range
    - Parallel processing for performance
    - Converting raw datapoints into Item objects
    """

    def __init__(self, name):
        """
        Initialize the ItemLoader for a specific product category.
        
        Args:
            name (str): The category name (e.g., 'Electronics', 'Books')
                       This corresponds to the dataset split name
        """
        self.name = name          # Store category name for later use
        self.dataset = None       # Will hold the loaded HuggingFace dataset


    def from_datapoint(self, datapoint):
        """
        Convert a single raw datapoint into an Item object with validation.
        
        Process:
        1. Extract and parse the price field
        2. Validate price is within acceptable range
        3. Create Item object and check if it should be included
        4. Return Item or None based on validation results
        
        Args:
            datapoint (dict): Raw data dictionary from the dataset
            
        Returns:
            Item or None: Valid Item object, or None if datapoint should be excluded
        """
        try:
            # Extract price string from datapoint (may be None or invalid)
            price_str = datapoint['price']
            
            # Only process if price exists (not None or empty string)
            if price_str:
                # Convert string to float (may raise ValueError)
                price = float(price_str)
                
                # Check if price falls within acceptable range
                if MIN_PRICE <= price <= MAX_PRICE:
                    # Create Item object with datapoint and parsed price
                    item = Item(datapoint, price)
                    
                    # Return item only if its include flag is True
                    # (Item class may have additional validation logic)
                    return item if item.include else None
                    
        except (ValueError, KeyError, TypeError):
            # ValueError: invalid price string (e.g., "N/A", "free")
            # KeyError: 'price' field missing from datapoint
            # TypeError: unexpected data type
            # In all cases, silently skip this datapoint
            return None
        
        # Return None if price is invalid or out of range
        return None


    def from_chunk(self, chunk):
        """
        Process a chunk of datapoints into a list of valid Item objects.
        
        This method is designed to be called by parallel workers.
        Each worker processes one chunk independently.
        
        Args:
            chunk: Iterable of datapoints (subset of the dataset)
            
        Returns:
            list[Item]: All valid Items from this chunk
        """
        batch = []  # Accumulator for valid items
        
        # Iterate through each datapoint in this chunk
        for datapoint in chunk:
            # Try to create an Item from this datapoint
            result = self.from_datapoint(datapoint)
            
            # Only add to batch if result is not None
            if result:
                batch.append(result)
                
        return batch


    def chunk_generator(self):
        """
        Generate chunks of the dataset for parallel processing.
        
        Yields sequential chunks of CHUNK_SIZE datapoints at a time.
        This is memory-efficient as it doesn't load entire dataset into RAM.
        
        Yields:
            Dataset: A subset of self.dataset containing up to CHUNK_SIZE items
        """
        size = len(self.dataset)  # Total number of datapoints
        
        # Generate range indices in steps of CHUNK_SIZE
        for i in range(0, size, CHUNK_SIZE):
            # Calculate end index (handles last chunk which may be smaller)
            end_idx = min(i + CHUNK_SIZE, size)
            
            # Use dataset.select() to get a view of this chunk
            # This is efficient and doesn't duplicate data in memory
            yield self.dataset.select(range(i, end_idx))


    def load_in_parallel(self, workers):
        """
        Process all dataset chunks in parallel using multiple worker processes.
        
        Uses ProcessPoolExecutor for true parallel execution (bypasses Python GIL).
        Shows progress bar via tqdm for user feedback.
        
        Args:
            workers (int): Number of parallel worker processes to use
            
        Returns:
            list[Item]: All valid Items from the entire dataset
        """
        results = []  # Will store all Items from all workers
        
        # Calculate total number of chunks for progress bar
        chunk_count = (len(self.dataset) // CHUNK_SIZE) + 1
        
        # Create a process pool with specified number of workers
        # ProcessPoolExecutor uses separate processes (not threads) for true parallelism
        with ProcessPoolExecutor(max_workers=workers) as pool:
            # Submit all chunks to the pool and process them in parallel
            # pool.map() returns results in order, tqdm shows progress
            for batch in tqdm(
                pool.map(self.from_chunk, self.chunk_generator()),
                total=chunk_count,
                desc=f"Processing {self.name}",
                unit="chunk"
            ):
                # Each batch is a list of Items from one chunk
                # Extend our results list with items from this batch
                results.extend(batch)
        
        # After all parallel processing is complete, set the category on all items
        # This must happen after pool.map() to avoid pickling issues
        for result in results:
            result.category = self.name
            
        return results


    def load(self, workers=None):
        """
        Main entry point: Load and process the complete dataset.
        
        Steps:
        1. Download/load dataset from HuggingFace
        2. Process in parallel with multiple workers
        3. Filter and validate all datapoints
        4. Return list of valid Item objects
        
        Args:
            workers (int, optional): Number of parallel processes to use.
                                    If None, auto-calculates based on CPU cores.
                                    For M3 Max (14-core): defaults to 12 workers
                                    (leaves 2 cores for system operations)
        
        Returns:
            list[Item]: All valid Items from the dataset
        """
        # Auto-calculate optimal worker count if not specified
        if workers is None:
            # Get CPU count (14 for M3 Max)
            cpu_count = os.cpu_count() or 8
            
            # Use 85% of cores (12 for 14-core M3 Max)
            # Leaves headroom for system processes and avoids thrashing
            workers = max(1, int(cpu_count * 0.85))
        
        # Record start time for performance tracking
        start = datetime.now()
        
        # Print status message (flush ensures immediate output)
        print(f"Loading dataset {self.name} with {workers} workers", flush=True)
        
        # Load the dataset from HuggingFace Hub
        # - "McAuley-Lab/Amazon-Reviews-2023": Dataset repository
        # - f"raw_meta_{self.name}": Specific category subset
        # - split="full": Load complete dataset (not train/test split)
        # - trust_remote_code=True: Allow custom dataset loading code
        self.dataset = load_dataset(
            "McAuley-Lab/Amazon-Reviews-2023",
            f"raw_meta_{self.name}",
            split="full",
            trust_remote_code=True
        )
        
        # Process dataset in parallel
        results = self.load_in_parallel(workers)
        
        # Calculate elapsed time
        finish = datetime.now()
        elapsed_minutes = (finish - start).total_seconds() / 60
        
        # Print completion summary with statistics
        print(
            f"✓ Completed {self.name}: "
            f"{len(results):,} items loaded "
            f"in {elapsed_minutes:.1f} minutes "
            f"({len(results)/elapsed_minutes:.0f} items/min)",
            flush=True
        )
        
        return results


# ============================================================================
# OPTIMIZATION NOTES FOR M3 MAX
# ============================================================================
# 
# Your M3 Max specifications:
# - 14-core CPU (10 performance + 4 efficiency cores)
# - 36GB unified memory
# - 30-core GPU (not used here)
#
# Optimizations applied:
# 1. Default workers = 12 (85% of 14 cores)
#    - Leaves 2 cores for macOS system tasks and dataset I/O
#    - Prevents CPU thrashing and maintains system responsiveness
#
# 2. ProcessPoolExecutor instead of ThreadPoolExecutor
#    - Bypasses Python's Global Interpreter Lock (GIL)
#    - True parallel CPU usage across all cores
#
# 3. CHUNK_SIZE = 1000
#    - Good balance for your 36GB RAM
#    - Small enough for even distribution across workers
#    - Large enough to minimize overhead
#
# 4. Memory considerations:
#    - Each worker gets its own memory space
#    - With 36GB RAM, 12 workers is safe even for large datasets
#    - Monitor with Activity Monitor if processing very large categories
#
# Performance tuning tips:
# - For small datasets (<100K items): Use fewer workers (4-6)
# - For huge datasets (>5M items): Can try 13 workers if system is idle
# - If memory issues occur: Reduce CHUNK_SIZE to 500
# ============================================================================
