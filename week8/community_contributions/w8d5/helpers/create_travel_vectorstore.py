import os
import random
from dotenv import load_dotenv
from huggingface_hub import login
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm

load_dotenv(override=True)
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', 'your-key-if-not-using-env')

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

DB = "travel_vectorstore"
CATEGORIES = ['Flights', 'Hotels', 'Car_Rentals', 'Vacation_Packages', 'Cruises', 'Activities']

AIRLINES = ['American Airlines', 'Delta', 'United', 'Southwest', 'JetBlue', 'Spirit', 'Frontier', 'Alaska Airlines', 'Emirates', 'British Airways', 'Air France', 'Lufthansa', 'Qatar Airways']
CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Miami', 'San Francisco', 'Boston', 'Seattle', 'Denver', 'Atlanta', 'Las Vegas', 'Orlando', 'Phoenix', 'London', 'Paris', 'Tokyo', 'Dubai', 'Singapore', 'Sydney', 'Rome']
HOTELS = ['Hilton', 'Marriott', 'Hyatt', 'Holiday Inn', 'Best Western', 'Sheraton', 'Ritz-Carlton', 'Four Seasons', 'Westin', 'Radisson']
CLASSES = ['Economy', 'Premium Economy', 'Business', 'First Class']
CAR_COMPANIES = ['Hertz', 'Enterprise', 'Avis', 'Budget', 'National', 'Alamo']
CAR_TYPES = ['Compact', 'Sedan', 'SUV', 'Luxury', 'Van']

def generate_flight_description():
    airline = random.choice(AIRLINES)
    source = random.choice(CITIES)
    dest = random.choice([c for c in CITIES if c != source])
    flight_class = random.choice(CLASSES)
    stops = random.choice(['non-stop', 'one-stop', 'two-stops'])
    duration = f"{random.randint(1, 15)} hours {random.randint(0, 59)} minutes"
    
    description = f"{airline} {flight_class} {stops} flight from {source} to {dest}. "
    description += f"Flight duration approximately {duration}. "
    
    if random.random() > 0.5:
        description += f"Includes {random.randint(1, 2)} checked bag"
        if random.random() > 0.5:
            description += "s"
        description += ". "
    
    if flight_class in ['Business', 'First Class']:
        description += random.choice(['Priority boarding included. ', 'Lounge access available. ', 'Lie-flat seats. '])
    
    price = random.randint(150, 2500) if flight_class == 'Economy' else random.randint(800, 8000)
    return description, price

def generate_hotel_description():
    hotel = random.choice(HOTELS)
    city = random.choice(CITIES)
    stars = random.randint(2, 5)
    room_type = random.choice(['Standard Room', 'Deluxe Room', 'Suite', 'Executive Suite'])
    nights = random.randint(1, 7)
    
    description = f"{hotel} {stars}-star hotel in {city}. {room_type} for {nights} night"
    if nights > 1:
        description += "s"
    description += ". "
    
    amenities = []
    if random.random() > 0.3:
        amenities.append('Free WiFi')
    if random.random() > 0.5:
        amenities.append('Breakfast included')
    if random.random() > 0.6:
        amenities.append('Pool access')
    if random.random() > 0.7:
        amenities.append('Gym')
    if random.random() > 0.8:
        amenities.append('Spa services')
    
    if amenities:
        description += f"Amenities: {', '.join(amenities)}. "
    
    price_per_night = random.randint(80, 500) if stars <= 3 else random.randint(200, 1200)
    total_price = price_per_night * nights
    
    return description, total_price

def generate_car_rental_description():
    company = random.choice(CAR_COMPANIES)
    car_type = random.choice(CAR_TYPES)
    city = random.choice(CITIES)
    days = random.randint(1, 14)
    
    description = f"{company} car rental in {city}. {car_type} class vehicle for {days} day"
    if days > 1:
        description += "s"
    description += ". "
    
    if random.random() > 0.6:
        description += "Unlimited mileage included. "
    if random.random() > 0.5:
        description += "Airport pickup available. "
    if random.random() > 0.7:
        description += "GPS navigation included. "
    
    daily_rate = {'Compact': random.randint(25, 45), 'Sedan': random.randint(35, 65), 'SUV': random.randint(50, 90), 'Luxury': random.randint(80, 200), 'Van': random.randint(60, 100)}
    total_price = daily_rate[car_type] * days
    
    return description, total_price

def generate_vacation_package_description():
    city = random.choice(CITIES)
    nights = random.randint(3, 10)
    
    description = f"All-inclusive vacation package to {city} for {nights} nights. "
    description += f"Includes round-trip {random.choice(CLASSES)} flights, {random.choice(HOTELS)} hotel accommodation, "
    
    extras = []
    if random.random() > 0.3:
        extras.append('daily breakfast')
    if random.random() > 0.5:
        extras.append('airport transfers')
    if random.random() > 0.6:
        extras.append('city tour')
    if random.random() > 0.7:
        extras.append('travel insurance')
    
    if extras:
        description += f"and {', '.join(extras)}. "
    
    base_price = random.randint(800, 4000)
    return description, base_price

def generate_cruise_description():
    destinations = [', '.join(random.sample(['Caribbean', 'Mediterranean', 'Alaska', 'Hawaii', 'Baltic Sea', 'South Pacific'], k=random.randint(2, 4)))]
    nights = random.choice([3, 5, 7, 10, 14])
    
    description = f"{nights}-night cruise visiting {destinations[0]}. "
    description += f"All meals and entertainment included. "
    
    cabin_type = random.choice(['Interior cabin', 'Ocean view cabin', 'Balcony cabin', 'Suite'])
    description += f"{cabin_type}. "
    
    if random.random() > 0.5:
        description += "Unlimited beverage package available. "
    if random.random() > 0.6:
        description += "Shore excursions at each port. "
    
    base_price = random.randint(500, 5000)
    return description, base_price

def generate_activity_description():
    city = random.choice(CITIES)
    activities = ['City sightseeing tour', 'Museum pass', 'Adventure sports package', 'Wine tasting tour', 'Cooking class', 'Hot air balloon ride', 'Snorkeling excursion', 'Helicopter tour', 'Spa day package', 'Theme park tickets']
    activity = random.choice(activities)
    
    description = f"{activity} in {city}. "
    
    if 'tour' in activity.lower():
        description += f"Duration: {random.randint(2, 8)} hours. "
    if random.random() > 0.5:
        description += "Hotel pickup included. "
    if random.random() > 0.6:
        description += "Small group experience. "
    
    price = random.randint(30, 500)
    return description, price

GENERATORS = {
    'Flights': generate_flight_description,
    'Hotels': generate_hotel_description,
    'Car_Rentals': generate_car_rental_description,
    'Vacation_Packages': generate_vacation_package_description,
    'Cruises': generate_cruise_description,
    'Activities': generate_activity_description
}

print("Generating synthetic travel dataset...")
travel_data = []

items_per_category = 3334
for category in CATEGORIES:
    print(f"Generating {category}...")
    generator = GENERATORS[category]
    for _ in range(items_per_category):
        description, price = generator()
        travel_data.append((description, float(price), category))

random.shuffle(travel_data)
print(f"Generated {len(travel_data)} travel deals")

print("\nInitializing SentenceTransformer model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

print(f"Connecting to ChromaDB at {DB}...")
client = chromadb.PersistentClient(path=DB)

collection_name = "travel_deals"
existing_collections = [col.name for col in client.list_collections()]
if collection_name in existing_collections:
    client.delete_collection(collection_name)
    print(f"Deleted existing collection: {collection_name}")

collection = client.create_collection(collection_name)
print(f"Created new collection: {collection_name}")

print("\nCreating embeddings and adding to ChromaDB...")
for i in tqdm(range(0, len(travel_data), 1000)):
    batch = travel_data[i:i+1000]
    documents = [desc for desc, _, _ in batch]
    vectors = model.encode(documents).astype(float).tolist()
    metadatas = [{"category": cat, "price": price} for _, price, cat in batch]
    ids = [f"travel_{j}" for j in range(i, i+len(batch))]
    
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=vectors,
        metadatas=metadatas
    )

total_items = collection.count()
print(f"\nVectorstore created successfully with {total_items} travel deals")

result = collection.get(include=['metadatas'], limit=total_items)
categories = [m['category'] for m in result['metadatas']]
prices = [m['price'] for m in result['metadatas']]
category_counts = {}
for cat in categories:
    category_counts[cat] = category_counts.get(cat, 0) + 1

print("\nCategory distribution:")
for category, count in sorted(category_counts.items()):
    print(f"  {category}: {count}")

avg_price = sum(prices) / len(prices) if prices else 0
print(f"\nAverage price: ${avg_price:.2f}")
print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
