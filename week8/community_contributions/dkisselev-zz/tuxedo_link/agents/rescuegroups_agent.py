"""RescueGroups.org API agent for fetching cat adoption listings."""

import os
import time
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from models.cats import Cat
from .agent import Agent, timed


class RescueGroupsAgent(Agent):
    """Agent for interacting with RescueGroups.org API."""
    
    name = "RescueGroups Agent"
    color = Agent.MAGENTA
    
    BASE_URL = "https://api.rescuegroups.org/v5"
    
    # Rate limiting
    MAX_REQUESTS_PER_SECOND = 0.5  # Be conservative
    MAX_RESULTS_PER_PAGE = 100
    
    # Cache for valid colors and breeds
    _valid_colors_cache: Optional[List[str]] = None
    _valid_breeds_cache: Optional[List[str]] = None
    
    def __init__(self):
        """Initialize the RescueGroups agent with API credentials."""
        load_dotenv()
        
        self.api_key = os.getenv('RESCUEGROUPS_API_KEY')
        
        if not self.api_key:
            self.log_warning("RESCUEGROUPS_API_KEY not set - agent will not function")
            self.api_key = None
        
        self.last_request_time: float = 0
        
        self.log("RescueGroups Agent initialized")
    
    def get_valid_colors(self) -> List[str]:
        """
        Fetch valid colors from RescueGroups API.
        
        Returns:
            List of valid color strings
        """
        if not self.api_key:
            return []
        
        # Use class-level cache
        if RescueGroupsAgent._valid_colors_cache is not None:
            return RescueGroupsAgent._valid_colors_cache
        
        try:
            self.log("Fetching valid cat colors from RescueGroups API...")
            
            # Correct endpoint for colors
            url = f"{self.BASE_URL}/public/animals/colors"
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/vnd.api+json'
            }
            
            # Add limit parameter to get all colors (no max limit for static data per docs)
            params = {'limit': 1000}
            
            self._rate_limit()
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            colors = [item['attributes']['name'] for item in data.get('data', [])]
            
            # Cache the results
            RescueGroupsAgent._valid_colors_cache = colors
            
            self.log(f"✓ Fetched {len(colors)} valid colors from RescueGroups")
            return colors
            
        except Exception as e:
            self.log_error(f"Failed to fetch valid colors: {e}")
            # Return empty list - planning agent will handle gracefully
            return []
    
    def get_valid_breeds(self) -> List[str]:
        """
        Fetch valid cat breeds from RescueGroups API.
        
        Returns:
            List of valid breed strings
        """
        if not self.api_key:
            return []
        
        # Use class-level cache
        if RescueGroupsAgent._valid_breeds_cache is not None:
            return RescueGroupsAgent._valid_breeds_cache
        
        try:
            self.log("Fetching valid cat breeds from RescueGroups API...")
            
            # Correct endpoint for breeds
            url = f"{self.BASE_URL}/public/animals/breeds"
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/vnd.api+json'
            }
            
            # Add limit parameter to get all breeds (no max limit for static data per docs)
            params = {'limit': 1000}
            
            self._rate_limit()
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            breeds = [item['attributes']['name'] for item in data.get('data', [])]
            
            # Cache the results
            RescueGroupsAgent._valid_breeds_cache = breeds
            
            self.log(f"✓ Fetched {len(breeds)} valid breeds from RescueGroups")
            return breeds
            
        except Exception as e:
            self.log_error(f"Failed to fetch valid breeds: {e}")
            # Return empty list - planning agent will handle gracefully
            return []
    
    def _rate_limit(self) -> None:
        """Implement rate limiting to respect API limits."""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.MAX_REQUESTS_PER_SECOND
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an authenticated POST request to RescueGroups API.
        
        Args:
            endpoint: API endpoint (e.g., "/animals/search")
            data: Request payload
            
        Returns:
            JSON response data
        """
        if not self.api_key:
            raise ValueError("RescueGroups API key not configured")
        
        self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/vnd.api+json'
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.log_error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.log_error(f"Response: {e.response.text[:500]}")
            raise
    
    def _parse_cat(self, animal_data: Dict[str, Any]) -> Cat:
        """
        Parse RescueGroups API animal data into Cat model.
        
        Args:
            animal_data: Animal data from RescueGroups API
            
        Returns:
            Cat object
        """
        attributes = animal_data.get('attributes', {})
        
        # Basic info
        cat_id = f"rescuegroups_{animal_data['id']}"
        name = attributes.get('name', 'Unknown')
        
        # Breed info
        primary_breed = attributes.get('breedPrimary', 'Unknown')
        secondary_breed = attributes.get('breedSecondary')
        secondary_breeds = [secondary_breed] if secondary_breed else []
        
        # Age mapping
        age_str = attributes.get('ageGroup', '').lower()
        age_map = {
            'baby': 'kitten',
            'young': 'young',
            'adult': 'adult',
            'senior': 'senior'
        }
        age = age_map.get(age_str, 'unknown')
        
        # Size mapping  
        size_str = attributes.get('sizeGroup', '').lower()
        size_map = {
            'small': 'small',
            'medium': 'medium',
            'large': 'large'
        }
        size = size_map.get(size_str, 'unknown')
        
        # Gender mapping
        gender_str = attributes.get('sex', '').lower()
        gender_map = {
            'male': 'male',
            'female': 'female'
        }
        gender = gender_map.get(gender_str, 'unknown')
        
        # Description
        description = attributes.get('descriptionText', '')
        if not description:
            description = f"{name} is a {age} {primary_breed} looking for a home."
        
        # Location info
        location = attributes.get('location', {}) or {}
        city = location.get('citytown')
        state = location.get('stateProvince')
        zip_code = location.get('postalcode')
        
        # Organization
        org_name = attributes.get('orgName', 'Unknown Organization')
        org_id = attributes.get('orgID')
        
        # Attributes - map RescueGroups boolean fields
        good_with_children = attributes.get('isKidsGood')
        good_with_dogs = attributes.get('isDogsGood')
        good_with_cats = attributes.get('isCatsGood')
        special_needs = attributes.get('isSpecialNeeds', False)
        
        # Photos
        pictures = attributes.get('pictureThumbnailUrl', [])
        if isinstance(pictures, str):
            pictures = [pictures] if pictures else []
        elif not pictures:
            pictures = []
        
        photos = [pic for pic in pictures if pic]
        primary_photo = photos[0] if photos else None
        
        # Contact info
        contact_email = attributes.get('emailAddress')
        contact_phone = attributes.get('phoneNumber')
        
        # Colors
        color_str = attributes.get('colorDetails', '')
        colors = [c.strip() for c in color_str.split(',') if c.strip()] if color_str else []
        
        # Coat
        coat_str = attributes.get('coatLength', '').lower()
        coat_map = {
            'short': 'short',
            'medium': 'medium',
            'long': 'long'
        }
        coat_length = coat_map.get(coat_str)
        
        # URL
        url = attributes.get('url', f"https://rescuegroups.org/animal/{animal_data['id']}")
        
        # Additional attributes
        declawed = attributes.get('isDeclawed')
        spayed_neutered = attributes.get('isAltered')
        house_trained = attributes.get('isHousetrained')
        
        return Cat(
            id=cat_id,
            name=name,
            breed=primary_breed,
            breeds_secondary=secondary_breeds,
            age=age,
            size=size,
            gender=gender,
            description=description,
            organization_name=org_name,
            organization_id=org_id,
            city=city,
            state=state,
            zip_code=zip_code,
            country='US',
            good_with_children=good_with_children,
            good_with_dogs=good_with_dogs,
            good_with_cats=good_with_cats,
            special_needs=special_needs,
            photos=photos,
            primary_photo=primary_photo,
            source='rescuegroups',
            url=url,
            contact_email=contact_email,
            contact_phone=contact_phone,
            declawed=declawed,
            spayed_neutered=spayed_neutered,
            house_trained=house_trained,
            coat_length=coat_length,
            colors=colors,
            fetched_at=datetime.now()
        )
    
    @timed
    def search_cats(
        self,
        location: Optional[str] = None,
        distance: int = 100,
        age: Optional[List[str]] = None,
        size: Optional[List[str]] = None,
        gender: Optional[str] = None,
        color: Optional[List[str]] = None,
        breed: Optional[List[str]] = None,
        good_with_children: Optional[bool] = None,
        good_with_dogs: Optional[bool] = None,
        good_with_cats: Optional[bool] = None,
        limit: int = 100
    ) -> List[Cat]:
        """
        Search for cats on RescueGroups.
        
        Args:
            location: ZIP code or city/state
            distance: Search radius in miles (default: 100)
            age: List of age categories: kitten, young, adult, senior
            size: List of sizes: small, medium, large
            gender: Gender filter: male, female
            color: List of colors (e.g., ["black", "white", "tuxedo"])
            breed: List of breed names (e.g., ["Siamese", "Maine Coon"])
            good_with_children: Filter for cats good with children
            good_with_dogs: Filter for cats good with dogs
            good_with_cats: Filter for cats good with other cats
            limit: Maximum number of results (default: 100)
            
        Returns:
            List of Cat objects
        """
        if not self.api_key:
            self.log_warning("RescueGroups API key not configured, returning empty results")
            return []
        
        color_str = f" with colors {color}" if color else ""
        breed_str = f" breeds {breed}" if breed else ""
        self.log(f"Searching RescueGroups for cats near {location}{color_str}{breed_str}")
        
        self.log(f"DEBUG: RescueGroups search params - location: {location}, distance: {distance}, age: {age}, size: {size}, gender: {gender}, color: {color}, breed: {breed}")
        
        # Build filter criteria
        filters = [
            {
                "fieldName": "species.singular",
                "operation": "equals",
                "criteria": "cat"
            },
            {
                "fieldName": "statuses.name",
                "operation": "equals",
                "criteria": "Available"
            }
        ]
        
        # Location filter - DISABLED: RescueGroups v5 API doesn't support location filtering
        # Their API returns animals from all locations, filtering must be done client-side
        if location:
            self.log(f"NOTE: RescueGroups doesn't support location filters. Will return all results.")
        
        # Age filter
        if age:
            age_map = {
                'kitten': 'Baby',
                'young': 'Young',
                'adult': 'Adult',
                'senior': 'Senior'
            }
            rg_ages = [age_map.get(a, a.capitalize()) for a in age]
            for rg_age in rg_ages:
                filters.append({
                    "fieldName": "animals.ageGroup",
                    "operation": "equals",
                    "criteria": rg_age
                })
        
        # Size filter
        if size:
            size_map = {
                'small': 'Small',
                'medium': 'Medium',
                'large': 'Large'
            }
            for s in size:
                rg_size = size_map.get(s, s.capitalize())
                filters.append({
                    "fieldName": "animals.sizeGroup",
                    "operation": "equals",
                    "criteria": rg_size
                })
        
        # Gender filter
        if gender:
            filters.append({
                "fieldName": "animals.sex",
                "operation": "equals",
                "criteria": gender.capitalize()
            })
        
        # Color filter - DISABLED: RescueGroups v5 API field name for color is unclear
        # Filtering by color will be done client-side with returned data
        if color:
            self.log(f"NOTE: Color filtering for RescueGroups will be done client-side: {color}")
        
        # Breed filter - DISABLED: RescueGroups v5 API breed filtering is not reliable
        # Filtering by breed will be done client-side with returned data
        if breed:
            self.log(f"NOTE: Breed filtering for RescueGroups will be done client-side: {breed}")
        
        # Behavioral filters - DISABLED: RescueGroups v5 API doesn't support behavioral filters
        # These fields exist in response data but cannot be used as filter criteria
        # Client-side filtering will be applied to returned results
        if good_with_children:
            self.log(f"NOTE: good_with_children filtering will be done client-side")
        
        if good_with_dogs:
            self.log(f"NOTE: good_with_dogs filtering will be done client-side")
        
        if good_with_cats:
            self.log(f"NOTE: good_with_cats filtering will be done client-side")
        
        # Build request payload
        payload = {
            "data": {
                "filters": filters,
                "filterProcessing": "1"  # AND logic
            }
        }
        
        # Add pagination
        if limit:
            payload["data"]["limit"] = min(limit, self.MAX_RESULTS_PER_PAGE)
        
        self.log(f"DEBUG: RescueGroups filters: {len(filters)} filters applied")
        
        try:
            response = self._make_request("/public/animals/search/available/cats", payload)
            
            self.log(f"DEBUG: RescueGroups API Response - Found {len(response.get('data', []))} animals")
            
            # Parse response
            data = response.get('data', [])
            cats = []
            
            for animal_data in data:
                try:
                    cat = self._parse_cat(animal_data)
                    cats.append(cat)
                except Exception as e:
                    self.log_warning(f"Failed to parse cat {animal_data.get('id')}: {e}")
            
            self.log(f"Search complete: found {len(cats)} cats")
            return cats
            
        except Exception as e:
            self.log_error(f"Search failed: {e}")
            return []

