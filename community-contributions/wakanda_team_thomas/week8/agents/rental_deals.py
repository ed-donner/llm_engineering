import random
from pydantic import BaseModel
from typing import Optional


class ScrapedListing(BaseModel):
    title: str
    description: str
    url: str
    price: float  # USD
    city: str


class RentalDeal(BaseModel):
    title: str
    description: str
    url: str
    rent: float  # USD per month
    city: str
    bedrooms: int
    sqft: int


class DealSelection(BaseModel):
    reasoning: str
    deals: list[RentalDeal]


class RentalOpportunity(BaseModel):
    deal: RentalDeal
    estimated_fair_rent: float
    monthly_savings: float


# Mock data templates per city

NEIGHBORHOODS = {
    "New York": ["Harlem", "Brooklyn Heights", "Astoria", "East Village", "Washington Heights", "Bushwick", "Upper West Side"],
    "Lagos": ["Lekki", "Victoria Island", "Ikeja", "Yaba", "Surulere", "Ikoyi", "Ajah"],
    "Nairobi": ["Westlands", "Kilimani", "Lavington", "Karen", "Langata", "South B", "Kileleshwa"],
}

RENT_RANGES = {
    "New York": (1500, 5000),
    "Lagos": (300, 1800),
    "Nairobi": (200, 1000),
}

PROPERTY_TYPES = ["apartment", "studio", "condo", "townhouse", "flat"]

FEATURES = [
    "natural light", "hardwood floors", "modern kitchen", "balcony",
    "parking included", "near public transit", "rooftop access",
    "in-unit laundry", "gym access", "security guard", "backup generator",
    "water tank", "garden view", "quiet neighborhood", "pet friendly",
]


def _generate_listing(city: str) -> ScrapedListing:
    neighborhood = random.choice(NEIGHBORHOODS[city])
    lo, hi = RENT_RANGES[city]
    price = round(random.uniform(lo, hi), 2)
    bedrooms = random.randint(1, 4)
    sqft = random.randint(400, 2000)
    prop_type = random.choice(PROPERTY_TYPES)
    feats = random.sample(FEATURES, k=random.randint(2, 4))
    feat_text = ", ".join(feats)

    title = f"{bedrooms}BR {prop_type.title()} in {neighborhood}, {city}"
    description = (
        f"Beautiful {bedrooms}-bedroom {prop_type} in {neighborhood}. "
        f"{sqft} sqft. Features: {feat_text}. "
        f"Listed at ${price:,.2f}/month."
    )
    url = f"https://mock-rentals.example.com/{city.lower().replace(' ', '-')}/{neighborhood.lower().replace(' ', '-')}/{random.randint(1000, 9999)}"

    return ScrapedListing(
        title=title,
        description=description,
        url=url,
        price=price,
        city=city,
    )


def generate_mock_listings(city: str, count: int = 10) -> list[ScrapedListing]:
    if city not in NEIGHBORHOODS:
        raise ValueError(f"Unsupported city: {city}. Choose from {list(NEIGHBORHOODS.keys())}")
    return [_generate_listing(city) for _ in range(count)]


def scraped_to_deal(listing: ScrapedListing) -> RentalDeal:
    """Extract structured fields from a scraped listing."""
    # Parse bedrooms and sqft from description
    bedrooms = 1
    sqft = 600
    for word in listing.description.split():
        if word.endswith("-bedroom"):
            try:
                bedrooms = int(word.split("-")[0])
            except ValueError:
                pass
    for i, word in enumerate(listing.description.split()):
        if word == "sqft." or word == "sqft":
            try:
                prev = listing.description.split()[i - 1]
                sqft = int(prev)
            except (ValueError, IndexError):
                pass

    return RentalDeal(
        title=listing.title,
        description=listing.description,
        url=listing.url,
        rent=listing.price,
        city=listing.city,
        bedrooms=bedrooms,
        sqft=sqft,
    )


def fetch_all_listings(count_per_city: int = 10) -> list[ScrapedListing]:
    """Fetch mock listings from all three cities."""
    listings = []
    for city in NEIGHBORHOODS:
        listings.extend(generate_mock_listings(city, count=count_per_city))
    return listings
