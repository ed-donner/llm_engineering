"""Convert structured housing data to natural language prompts."""
import pandas as pd

SYSTEM_PROMPT = """
You are a real estate appraiser. Based on property details, estimate the market price.
You only respond with the price, no other text.
"""


def create_description(row: pd.Series) -> str:
    """Convert a row of structured data to natural language description.
    
    Example output:
    "A 3 bedroom, 2 bathroom house with 1,850 square feet on a 0.25 acre lot 
    located in Austin, Texas, 78701."
    """
    bed = int(row['bed']) if pd.notna(row['bed']) else None
    bath = row['bath'] if pd.notna(row['bath']) else None
    sqft = int(row['house_size']) if pd.notna(row['house_size']) else None
    acres = row['acre_lot'] if pd.notna(row['acre_lot']) else None
    city = row['city'] if pd.notna(row['city']) else "Unknown"
    state = row['state'] if pd.notna(row['state']) else ""
    zip_code = row['zip_code'] if pd.notna(row['zip_code']) else ""

    parts = []

    if bed and bath:
        parts.append(f"A {bed} bedroom, {bath} bathroom house")
    elif bed:
        parts.append(f"A {bed} bedroom house")
    else:
        parts.append("A house")

    if sqft:
        parts.append(f"with {sqft:,} square feet")
    if acres and acres > 0:
        parts.append(f"on a {acres} acre lot")

    location_parts = [city, state]
    if zip_code:
        try:
            location_parts.append(str(int(float(zip_code))))
        except (ValueError, TypeError):
            pass
    location = ", ".join(filter(None, location_parts))
    if location:
        parts.append(f"located in {location}")

    return " ".join(parts) + "."


def format_for_inference(description: str) -> list[dict]:
    """Create messages for LLM inference."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"What is the estimated price of this property?\n\n{description}"}
    ]


def format_for_finetuning(row: pd.Series) -> dict:
    """Format for LLaMA 3.2 fine-tuning (chat template).
    
    Returns a dict with 'text' key containing the full training example
    in LLaMA 3.2 chat format.
    """
    description = create_description(row)
    price = row['price']

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"What is the estimated price of this property?\n\n{description}"},
            {"role": "assistant", "content": f"${price:,.0f}"}
        ]
    }
