import random
from datasets import Dataset
from huggingface_hub import login

NEIGHBORHOODS = {
    "New York": ["Harlem", "Brooklyn Heights", "Astoria", "East Village", "Washington Heights",
                 "Bushwick", "Upper West Side", "Chelsea", "Williamsburg", "SoHo",
                 "Lower East Side", "Midtown", "Hell's Kitchen", "Park Slope", "Tribeca"],
    "Lagos": ["Lekki", "Victoria Island", "Ikeja", "Yaba", "Surulere", "Ikoyi", "Ajah",
              "Gbagada", "Magodo", "Maryland", "Ogba", "Festac", "Banana Island",
              "Anthony Village", "Ogudu"],
    "Nairobi": ["Westlands", "Kilimani", "Lavington", "Karen", "Langata", "South B",
                "Kileleshwa", "Runda", "Muthaiga", "Parklands", "South C", "Hurlingham",
                "Upperhill", "Ngong Road", "Riverside"],
}

RENT_RANGES = {
    "New York": (1500, 5000),
    "Lagos": (300, 1800),
    "Nairobi": (200, 1000),
}

SQFT_RANGES = {
    1: (350, 700),
    2: (600, 1200),
    3: (900, 1800),
    4: (1200, 2500),
}

PROPERTY_TYPES = ["apartment", "studio", "condo", "townhouse", "flat"]

FEATURES = [
    "natural light", "hardwood floors", "modern kitchen", "balcony",
    "parking included", "near public transit", "rooftop access",
    "in-unit laundry", "gym access", "security guard", "backup generator",
    "water tank", "garden view", "quiet neighborhood", "pet friendly",
    "air conditioning", "high ceilings", "walk-in closet", "dishwasher",
    "concierge", "swimming pool", "furnished", "unfurnished",
    "recently renovated", "open floor plan", "city view",
]


def generate_listing(city: str) -> dict:
    neighborhood = random.choice(NEIGHBORHOODS[city])
    bedrooms = random.randint(1, 4)
    lo, hi = RENT_RANGES[city]

    # Scale rent by bedrooms
    base_rent = random.uniform(lo, hi)
    rent = round(base_rent * (1 + (bedrooms - 1) * 0.3), 2)

    sqft_lo, sqft_hi = SQFT_RANGES[bedrooms]
    sqft = random.randint(sqft_lo, sqft_hi)

    prop_type = random.choice(PROPERTY_TYPES)
    feats = random.sample(FEATURES, k=random.randint(2, 5))
    feat_text = ", ".join(feats)

    title = f"{bedrooms}BR {prop_type.title()} in {neighborhood}, {city}"
    description = (
        f"Beautiful {bedrooms}-bedroom {prop_type} in {neighborhood}. "
        f"{sqft} sqft. Features: {feat_text}. "
        f"Available now."
    )

    return {
        "title": title,
        "description": description,
        "city": city,
        "rent": rent,
        "bedrooms": bedrooms,
        "sqft": sqft,
    }


def curate_dataset(count_per_city: int = 5000) -> Dataset:
    rows = []
    for city in NEIGHBORHOODS:
        for _ in range(count_per_city):
            rows.append(generate_listing(city))
    random.shuffle(rows)
    return Dataset.from_list(rows)


if __name__ == "__main__":
    # Login to HuggingFace (uses HF_TOKEN env var or prompts for token)
    login()

    print("Generating dataset...")
    dataset = curate_dataset(count_per_city=5000)
    print(f"Created {len(dataset)} listings.")
    print(f"\nSample:\n{dataset[0]}")
    print(f"\nColumn types: {dataset.features}")

    print("\nPushing to HuggingFace...")
    dataset.push_to_hub("Gasmyr/rental-prices")
    print("Done! Dataset available at https://huggingface.co/datasets/Gasmyr/rental-prices")
