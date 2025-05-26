# Ragnarok Online Trade Dataset

This directory contains datasets generated for the Ragnarok Online Trade Buddy project. The datasets are used to train and inform an LLM agent that helps suggest trading options between players.

## Dataset Format

The datasets are stored in CSV format with the following columns:

- Item Name: Name of the item in Ragnarok Online
- Item ID: Unique identifier for the item (format: #XXXX-abc123)
- Item Description: Detailed description of the item and its properties
- Item Price: Price in zeny (in-game currency)
- Item Type: Category of the item (e.g., Accessory, Consumable, Currency, Armor)
- Willing to Trade For: Boolean indicating if the item can be traded for other items

## Usage

The datasets can be loaded into a pandas DataFrame using:

```python
import pandas as pd

# Load the dataset
df = pd.read_csv('ragnarok_items.csv')

# Example: Filter items by type
armor_items = df[df['Item Type'] == 'Armor']

# Example: Find items within a price range
affordable_items = df[df['Item Price'] <= 1000]
```

## Dataset Generation

The datasets are generated using the `products_dataset_generator.ipynb` notebook, which uses the Mistral-7B-Instruct model to create realistic Ragnarok Online items with appropriate attributes and prices.

## Updates

Each dataset file includes a timestamp in its name to track different versions. The latest dataset is always named `ragnarok_items_latest.csv`. 