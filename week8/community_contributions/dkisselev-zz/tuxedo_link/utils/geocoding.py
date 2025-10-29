"""Geocoding utilities for location services."""

import requests
from typing import Optional, Tuple


def geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """
    Convert a location string (address, city, or ZIP) to latitude/longitude.
    
    Uses the free Nominatim API (OpenStreetMap).
    
    Args:
        location: Location string (address, city, ZIP code, etc.)
        
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    try:
        # Use Nominatim API (free, no API key required)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us,ca'  # Limit to US and Canada
        }
        headers = {
            'User-Agent': 'TuxedoLink/1.0'  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        if results and len(results) > 0:
            lat = float(results[0]['lat'])
            lon = float(results[0]['lon'])
            return lat, lon
        
        return None
        
    except Exception as e:
        print(f"Geocoding failed for '{location}': {e}")
        return None


def reverse_geocode(latitude: float, longitude: float) -> Optional[dict]:
    """
    Convert latitude/longitude to address information.
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        Dictionary with address components or None if failed
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json'
        }
        headers = {
            'User-Agent': 'TuxedoLink/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if 'address' in result:
            address = result['address']
            return {
                'city': address.get('city', address.get('town', address.get('village', ''))),
                'state': address.get('state', ''),
                'zip': address.get('postcode', ''),
                'country': address.get('country', ''),
                'display_name': result.get('display_name', '')
            }
        
        return None
        
    except Exception as e:
        print(f"Reverse geocoding failed for ({latitude}, {longitude}): {e}")
        return None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points in miles.
    
    Uses the Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in miles
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Earth's radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    
    return distance


def parse_location_input(location_input: str) -> Optional[Tuple[float, float]]:
    """
    Parse location input that might be coordinates or an address.
    
    Handles formats:
    - "lat,long" (e.g., "40.7128,-74.0060")
    - ZIP code (e.g., "10001")
    - City, State (e.g., "New York, NY")
    - Full address
    
    Args:
        location_input: Location string
        
    Returns:
        Tuple of (latitude, longitude) or None if parsing fails
    """
    # Try to parse as coordinates first
    if ',' in location_input:
        parts = location_input.split(',')
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                # Basic validation
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            except ValueError:
                pass  # Not coordinates, try geocoding
    
    # Fall back to geocoding
    return geocode_location(location_input)

