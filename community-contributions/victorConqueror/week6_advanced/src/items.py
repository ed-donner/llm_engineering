"""
Enhanced Item class with additional features for improved price prediction
"""

from pydantic import BaseModel, Field
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self, List
import re


PREFIX = "Price is $"
QUESTION = "What does this cost to the nearest dollar?"


class Item(BaseModel):
    """
    Enhanced Item class with additional features for better price prediction
    """

    # Original fields
    title: str
    category: str
    price: float
    full: Optional[str] = None
    weight: Optional[float] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    id: Optional[int] = None

    # Enhanced features
    brand: Optional[str] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    has_dimensions: Optional[bool] = None
    is_premium: Optional[bool] = None
    embedding: Optional[List[float]] = None
    similar_prices: Optional[List[float]] = None
    price_bucket: Optional[str] = None
    
    # Computed features
    price_per_weight: Optional[float] = None
    text_quality_score: Optional[float] = None

    def extract_brand(self) -> str:
        """Extract brand name from summary"""
        if not self.summary:
            return "Unknown"
        
        # Look for "Brand: XYZ" pattern
        brand_match = re.search(r'Brand:\s*([A-Za-z0-9\s&\-]+)', self.summary)
        if brand_match:
            return brand_match.group(1).strip()
        
        # Look for brand in title (first word often)
        words = self.title.split()
        if words:
            return words[0]
        
        return "Unknown"

    def compute_text_features(self):
        """Compute text-based features"""
        if self.summary:
            self.word_count = len(self.summary.split())
            self.char_count = len(self.summary)
            
            # Check for premium keywords
            premium_keywords = ['premium', 'professional', 'deluxe', 'pro', 'elite', 'luxury']
            self.is_premium = any(keyword in self.summary.lower() for keyword in premium_keywords)
            
            # Check for dimensions
            self.has_dimensions = bool(re.search(r'\d+\s*x\s*\d+', self.summary))
            
            # Text quality score (simple heuristic)
            self.text_quality_score = min(self.word_count / 100.0, 1.0)

    def compute_derived_features(self):
        """Compute derived features"""
        if self.weight and self.weight > 0:
            self.price_per_weight = self.price / self.weight
        
        # Assign price bucket
        if self.price < 10:
            self.price_bucket = "budget"
        elif self.price < 50:
            self.price_bucket = "low"
        elif self.price < 100:
            self.price_bucket = "medium"
        elif self.price < 300:
            self.price_bucket = "high"
        else:
            self.price_bucket = "premium"

    def enhance(self):
        """Apply all enhancements to this item"""
        self.brand = self.extract_brand()
        self.compute_text_features()
        self.compute_derived_features()

    def make_prompt(self, text: str):
        """Create prompt for LLM"""
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.price)}.00"

    def test_prompt(self) -> str:
        """Get test prompt without answer"""
        return self.prompt.split(PREFIX)[0] + PREFIX if self.prompt else ""

    def get_feature_dict(self) -> dict:
        """Get dictionary of features for ML models"""
        return {
            'weight': self.weight or 0,
            'weight_unknown': 1 if not self.weight else 0,
            'word_count': self.word_count or 0,
            'char_count': self.char_count or 0,
            'has_dimensions': 1 if self.has_dimensions else 0,
            'is_premium': 1 if self.is_premium else 0,
            'text_quality_score': self.text_quality_score or 0,
            'price_per_weight': self.price_per_weight or 0,
        }

    def __repr__(self) -> str:
        return f"<{self.title} = ${self.price}>"

    @staticmethod
    def push_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):
        """Push Item lists to HuggingFace Hub"""
        DatasetDict(
            {
                "train": Dataset.from_list([item.model_dump() for item in train]),
                "validation": Dataset.from_list([item.model_dump() for item in val]),
                "test": Dataset.from_list([item.model_dump() for item in test]),
            }
        ).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct Items"""
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )
