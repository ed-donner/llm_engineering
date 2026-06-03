from pydantic import BaseModel
from datasets import load_dataset
from typing import Optional, List

PREFIX = "Price is $"
QUESTION = "What is the fair market value of this used car to the nearest dollar?"

class Item(BaseModel):
    """
    An Item is a data-point representing a used car with a price.
    """
    title: str
    category: str
    price: float
    full: Optional[str] = None
    weight: Optional[float] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    id: Optional[int] = None

    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.price)}.00"

    def test_prompt(self) -> str:
        return self.prompt.split(PREFIX)[0] + PREFIX

    def __repr__(self) -> str:
        return f"<{self.title} = ${self.price}>"

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[List['Item'], List['Item'], List['Item']]:
        """
        Load a used car dataset from Hugging Face (HF) and map it to our Item schema.
        We use 'Carson-Shively/used-car-price' as it is a standard automotive dataset.
        """
        ds = load_dataset(dataset_name, split="train")
        ds = ds.shuffle(seed=42)
        
        items = []
        for row in ds:
            make = row.get("Make", "Unknown Make")
            model = row.get("Model", "Unknown Model")
            year = row.get("Year", "Unknown Year")
            mileage = row.get("Mileage", "Unknown Mileage")
            price = float(row.get("Price", 0.0))
            
            if price <= 0:
                continue
                
            summary = f"{year} {make} {model} with {mileage} miles. Good condition used car."
            
            item = cls(
                title=f"{year} {make} {model}",
                category="Automotive",
                price=price,
                summary=summary
            )
            items.append(item)
            
            # Capping at 10,000 for high-speed local processing
            if len(items) >= 10000:
                break
                
        train_size = int(len(items) * 0.8)
        val_size = int(len(items) * 0.1)
        
        train = items[:train_size]
        val = items[train_size:train_size + val_size]
        test = items[train_size + val_size:]
        
        return train, val, test