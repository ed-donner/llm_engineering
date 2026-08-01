# ─────────────────────────────────────────
# modules/zillow_fetcher.py
# ─────────────────────────────────────────
import requests
import sys
import os
import re

# Fix path issue
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))

from config import HEADERS, RAPIDAPI_HOST

# ─────────────────────────────────────────
# Extract ZPID from Zillow URL
# ─────────────────────────────────────────
def extract_zpid(zillow_url):
    """Extract ZPID from Zillow URL"""
    match = re.search(r'/(\d+)_zpid', zillow_url)
    if match:
        zpid = match.group(1)
        print(f"✅ ZPID extracted: {zpid}")
        return zpid
    else:
        print("❌ Could not extract ZPID from URL")
        return None

# ─────────────────────────────────────────
# Fetch by ZPID
# ─────────────────────────────────────────
def fetch_by_zpid(zpid):
    """Fetch property data using ZPID"""
    print(f"\n🔍 Fetching property by ZPID: {zpid}")

    api_url = f"https://{RAPIDAPI_HOST}/property/all"
    params  = {"zpid": zpid}

    try:
        response = requests.get(
            api_url,
            headers=HEADERS,
            params=params,
            timeout=15
        )

        if response.status_code == 200:
            print("✅ Data fetched successfully!")
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ─────────────────────────────────────────
# Fetch by Zillow URL
# ─────────────────────────────────────────
def fetch_by_url(zillow_url):
    """Fetch property data using Zillow URL"""
    print(f"\n🔍 Fetching property data by URL...")

    zpid = extract_zpid(zillow_url)

    if not zpid:
        print("❌ Could not extract ZPID!")
        return None

    return fetch_by_zpid(zpid)

# ─────────────────────────────────────────
# Search by Location
# ─────────────────────────────────────────
def search_by_location(location, filters=None):
    """
    Search properties by location
    Args:
        location (str): City, State or Address
        filters (dict): Optional filters
    Returns:
        dict: Search results or None if failed
    """
    print(f"\n🔍 Searching properties in: {location}")

    api_url = f"https://{RAPIDAPI_HOST}/search/address"

    # Default payload
    payload = {
        "page": 1,
        "status": "for_sale",
        "min_price": None,
        "max_price": None,
        "min_beds": None,
        "min_baths": None,
        "min_sqft": None,
        "max_sqft": None,
        "min_lot_size": None,
        "year_built_min": None,
        "year_built_max": None,
        "has_pool": None,
        "has_garage": None,
        "keywords": None,
        "single_story": None,
        "has_3d_tour": None,
        "has_open_house": None,
        "is_coming_soon": None,
        "is_foreclosure": None,
        "is_fsbo": None,
        "is_new_construction": None,
        "has_basement": None,
        "has_ac": None,
        "is_waterfront": None,
        "parking_spots": None,
        "days_on_zillow": None,
        "min_school_rating": None,
        "is_55_plus": None,
        "max_hoa": None,
        "only_price_reduction": None,
        "location": location
    }

    # Apply custom filters if provided
    if filters:
        payload.update(filters)

    try:
        response = requests.post(
            api_url,
            headers=HEADERS,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            print("✅ Search successful!")
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ─────────────────────────────────────────
# Fetch by Address
# ─────────────────────────────────────────
def fetch_by_address(address):
    """
    Fetch specific property by address
    Args:
        address (str): Full property address
    Returns:
        dict: Property data or None if failed
    """
    print(f"\n🔍 Searching for: {address}")

    # Search by address
    results = search_by_location(address)

    if results and 'listings' in results:
        listings = results['listings']

        if listings and len(listings) > 0:
            # Get first matching result
            first = listings[0]
            zpid  = first.get('zpid')

            print(f"✅ Found property!")
            print(f"📍 Address : {first.get('address')}")
            print(f"💰 Price   : ${first.get('price'):,}")
            print(f"🔑 ZPID    : {zpid}")

            # Fetch full details
            return fetch_by_zpid(zpid)
        else:
            print("⚠️ No listings found!")
            return None
    else:
        print("⚠️ No results found!")
        return None