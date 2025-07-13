from datetime import datetime
from tqdm import tqdm
from datasets import load_dataset, Dataset, Features, Value, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from items import Item
import json

CHUNK_SIZE = 1000
MIN_PRICE = 0.5
MAX_PRICE = 999.49

class ItemLoader:


    def __init__(self, name):
        self.name = name
        self.dataset = None

    def from_datapoint(self, datapoint):
        """
        Try to create an Item from this datapoint
        Return the Item if successful, or None if it shouldn't be included
        """
        try:
            price_str = datapoint['price']
            if price_str:
                price = float(price_str)
                if MIN_PRICE <= price <= MAX_PRICE:
                    item = Item(datapoint, price)
                    return item if item.include else None
        except ValueError:
            return None

    def from_chunk(self, chunk):
        """
        Create a list of Items from this chunk of elements from the Dataset
        """
        batch = []
        for datapoint in chunk:
            result = self.from_datapoint(datapoint)
            if result:
                batch.append(result)
        return batch

    def chunk_generator(self):
        """
        Iterate over the Dataset, yielding chunks of datapoints at a time
        """
        if self.dataset is None:
            raise ValueError("Dataset is not loaded. Please load the dataset before calling load_in_parallel.")
        size = len(self.dataset)
        for i in range(0, size, CHUNK_SIZE):
            yield self.dataset.select(range(i, min(i + CHUNK_SIZE, size)))

    def load_in_parallel(self, workers):
        """
        Use concurrent.futures to farm out the work to process chunks of datapoints -
        This speeds up processing significantly, but will tie up your computer while it's doing so!
        """
        results = []
        if self.dataset is None:
            raise ValueError("Dataset is not loaded. Please load the dataset before calling load_in_parallel.")
        chunk_count = (len(self.dataset) // CHUNK_SIZE) + 1
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for batch in tqdm(pool.map(self.from_chunk, self.chunk_generator()), total=chunk_count):
                results.extend(batch)
        for result in results:
            result.category = self.name
        return results

    def process_line(self, line: str):
        """
        Function to process a single line of JSON data.
        This function will be executed in parallel.
        """
        try:
            json_data = json.loads(line.strip())
            if 'price' in json_data and json_data['price'] is None:
                json_data['price'] = 0.0
            return json_data
        except json.JSONDecodeError as e:
            print(f"Skipping malformed JSON line: {line.strip()} - Error: {e}")
            return None # Or handle the error differently


    def load_data(self, max_workers =8):
        features = Features({
            'main_category': Value('string'),
            'title': Value('string'),
            'average_rating': Value(dtype='float64'),
            'rating_number': Value(dtype='int64'),
            'features': Sequence(Value('string')),
            'description': Sequence(Value('string')),
            'price': Value(dtype='float64'),
            'images': Sequence(Value('string')),
            'videos': Sequence(Value('string')),
            'store': Value('string'),
            'categories': Sequence(Value('string')),
            'details': Value( ('string') ),
            'parent_asin': Value('string'),
            'bought_together': Value('string')
        })
        root = "/Developer/github/llm_engineering_datasets/"
        file = f"{root}Amazon-Reviews-2023/raw/meta_categories/meta_{self.name}.jsonl"
        parsed_objects = []
        with open(file, 'r') as fp:
            lines = fp.readlines()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # executor.map applies the process_line function to each line in 'lines'
                # in parallel. It returns results in the order the inputs were submitted.
                results = executor.map(self.process_line, lines)

                for obj in results:
                    if obj is not None: # Only append if processing was successful
                        parsed_objects.append(obj)
            
        return Dataset.from_list(parsed_objects, features=features )

    

    def load(self, workers=8):
        """
        Load in this dataset; the workers parameter specifies how many processes
        should work on loading and scrubbing the data
        """
        start = datetime.now()
        print(f"Loading dataset {self.name}", flush=True)
        #self.dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", f"raw_meta_{self.name}", split="full", trust_remote_code=True)
        self.dataset = self.load_data(workers)
        results = self.load_in_parallel(workers)
        finish = datetime.now()
        print(f"Completed {self.name} with {len(results):,} datapoints in {(finish-start).total_seconds()/60:.1f} mins", flush=True)
        return results
        
 
    
    