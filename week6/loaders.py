from datetime import datetime
from tqdm import tqdm
from datasets import load_dataset
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from items import Item

CHUNK_SIZE = 1000
MIN_PRICE = 0.5
MAX_PRICE = 999.49

class ItemLoader:


    def __init__(self, name):
        self.name = name
        self.dataset = None

    def from_datapoint(self, datapoint):
        """
        Intenta crear un elemento a partir de este punto de datos
        Devuelve el elemento si se realiza correctamente o Ninguno si no se debe incluir
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
        Crea una lista de elementos a partir de este fragmento de elementos del conjunto de datos
        """
        batch = []
        for datapoint in chunk:
            result = self.from_datapoint(datapoint)
            if result:
                batch.append(result)
        return batch

    def chunk_generator(self):
        """
        Iterar sobre el conjunto de datos, generando fragmentos de puntos de datos a la vez
        """
        size = len(self.dataset)
        for i in range(0, size, CHUNK_SIZE):
            yield self.dataset.select(range(i, min(i + CHUNK_SIZE, size)))

    def load_in_parallel(self, workers):
        """
        Utiliza concurrent.futures para subcontratar el trabajo de procesamiento de fragmentos de puntos de datos. 
        Esto acelera significativamente el procesamiento, pero ocupará espacio en su computadora mientras lo hace.
        """
        results = []
        chunk_count = (len(self.dataset) // CHUNK_SIZE) + 1
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for batch in tqdm(pool.map(self.from_chunk, self.chunk_generator()), total=chunk_count):
                results.extend(batch)
        for result in results:
            result.category = self.name
        return results
            
    def load(self, workers=8):
        """
        Cargar en este conjunto de datos; el parámetro de trabajadores especifica cuántos procesos
        deben trabajar en la carga y limpieza de los datos
        """
        start = datetime.now()
        print(f"Cargando dataset {self.name}", flush=True)
        self.dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", f"raw_meta_{self.name}", split="full", trust_remote_code=True)
        results = self.load_in_parallel(workers)
        finish = datetime.now()
        print(f"Completado {self.name} con {len(results):,} datapoints en {(finish-start).total_seconds()/60:.1f} mins", flush=True)
        return results
        

    
    