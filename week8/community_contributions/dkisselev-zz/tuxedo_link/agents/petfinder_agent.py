"""Petfinder API agent for fetching cat adoption listings."""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from models.cats import Cat
from .agent import Agent, timed


class PetfinderAgent(Agent):
    """Agent for interacting with Petfinder API v2."""
    
    name = "Petfinder Agent"
    color = Agent.CYAN
    
    BASE_URL = "https://api.petfinder.com/v2"
    TOKEN_URL = f"{BASE_URL}/oauth2/token"
    ANIMALS_URL = f"{BASE_URL}/animals"
    TYPES_URL = f"{BASE_URL}/types"
    
    # Rate limiting
    MAX_REQUESTS_PER_SECOND = 1
    MAX_RESULTS_PER_PAGE = 100
    MAX_TOTAL_RESULTS = 1000
    
    # Cache for valid colors and breeds (populated on first use)
    _valid_colors_cache: Optional[List[str]] = None
    _valid_breeds_cache: Optional[List[str]] = None
    
    def __init__(self):
        """Initialize the Petfinder agent with API credentials."""
        load_dotenv()
        
        self.api_key = os.getenv('PETFINDER_API_KEY')
        self.api_secret = os.getenv('PETFINDER_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("PETFINDER_API_KEY and PETFINDER_SECRET must be set in environment")
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.last_request_time: float = 0
        
        self.log("Petfinder Agent initialized")
    
    def get_valid_colors(self) -> List[str]:
        """
        Fetch valid colors for cats from Petfinder API.
        
        Returns:
            List of valid color strings accepted by the API
        """
        # Use class-level cache
        if PetfinderAgent._valid_colors_cache is not None:
            return PetfinderAgent._valid_colors_cache
        
        try:
            self.log("Fetching valid cat colors from Petfinder API...")
            url = f"{self.TYPES_URL}/cat"
            token = self._get_access_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            colors = data.get('type', {}).get('colors', [])
            
            # Cache the results
            PetfinderAgent._valid_colors_cache = colors
            
            self.log(f"✓ Fetched {len(colors)} valid colors from Petfinder")
            self.log(f"Valid colors: {', '.join(colors[:10])}...")
            
            return colors
        except Exception as e:
            self.log_error(f"Failed to fetch valid colors: {e}")
            # Return common colors as fallback
            fallback = ["Black", "White", "Orange", "Gray", "Brown", "Cream", "Tabby"]
            self.log(f"Using fallback colors: {fallback}")
            return fallback
    
    def get_valid_breeds(self) -> List[str]:
        """
        Fetch valid cat breeds from Petfinder API.
        
        Returns:
            List of valid breed strings accepted by the API
        """
        # Use class-level cache
        if PetfinderAgent._valid_breeds_cache is not None:
            return PetfinderAgent._valid_breeds_cache
        
        try:
            self.log("Fetching valid cat breeds from Petfinder API...")
            url = f"{self.TYPES_URL}/cat/breeds"
            token = self._get_access_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            breeds = [breed['name'] for breed in data.get('breeds', [])]
            
            # Cache the results
            PetfinderAgent._valid_breeds_cache = breeds
            
            self.log(f"✓ Fetched {len(breeds)} valid breeds from Petfinder")
            
            return breeds
        except Exception as e:
            self.log_error(f"Failed to fetch valid breeds: {e}")
            # Return common breeds as fallback
            fallback = ["Domestic Short Hair", "Domestic Medium Hair", "Domestic Long Hair", "Siamese", "Persian", "Maine Coon"]
            self.log(f"Using fallback breeds: {fallback}")
            return fallback
    
    def _rate_limit(self) -> None:
        """Implement rate limiting to respect API limits."""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.MAX_REQUESTS_PER_SECOND
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _get_access_token(self) -> str:
        """
        Get or refresh the OAuth access token.
        
        Returns:
            Access token string
        """
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # Request new token
        self.log("Requesting new access token from Petfinder")
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiration (subtract 60 seconds for safety)
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            self.log(f"Access token obtained, expires at {self.token_expires_at}")
            return self.access_token
            
        except Exception as e:
            self.log_error(f"Failed to get access token: {e}")
            raise
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an authenticated request to Petfinder API with rate limiting.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response data
        """
        self._rate_limit()
        
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token might be invalid, clear it and retry once
                self.log_warning("Token invalid, refreshing and retrying")
                self.access_token = None
                token = self._get_access_token()
                headers['Authorization'] = f'Bearer {token}'
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            else:
                raise
    
    def _parse_cat(self, animal_data: Dict[str, Any]) -> Cat:
        """
        Parse Petfinder API animal data into Cat model.
        
        Args:
            animal_data: Animal data from Petfinder API
            
        Returns:
            Cat object
        """
        # Basic info
        cat_id = f"petfinder_{animal_data['id']}"
        name = animal_data.get('name', 'Unknown')
        
        # Breed info
        breeds = animal_data.get('breeds', {})
        primary_breed = breeds.get('primary', 'Unknown')
        secondary_breed = breeds.get('secondary')
        secondary_breeds = [secondary_breed] if secondary_breed else []
        
        # Age mapping
        age_map = {
            'Baby': 'kitten',
            'Young': 'young',
            'Adult': 'adult',
            'Senior': 'senior'
        }
        age = age_map.get(animal_data.get('age', 'Unknown'), 'unknown')
        
        # Size mapping
        size_map = {
            'Small': 'small',
            'Medium': 'medium',
            'Large': 'large'
        }
        size = size_map.get(animal_data.get('size', 'Unknown'), 'unknown')
        
        # Gender mapping
        gender_map = {
            'Male': 'male',
            'Female': 'female',
            'Unknown': 'unknown'
        }
        gender = gender_map.get(animal_data.get('gender', 'Unknown'), 'unknown')
        
        # Description
        description = animal_data.get('description', '')
        if not description:
            description = f"{name} is a {age} {primary_breed} looking for a home."
        
        # Location info
        contact = animal_data.get('contact', {})
        address = contact.get('address', {})
        
        organization_id = animal_data.get('organization_id')
        city = address.get('city')
        state = address.get('state')
        zip_code = address.get('postcode')
        
        # Attributes
        attributes = animal_data.get('attributes', {})
        environment = animal_data.get('environment', {})
        
        # Photos
        photos_data = animal_data.get('photos', [])
        photos = [p['large'] or p['medium'] or p['small'] for p in photos_data if p]
        primary_photo = photos[0] if photos else None
        
        # Videos
        videos_data = animal_data.get('videos', [])
        videos = [v.get('embed') for v in videos_data if v.get('embed')]
        
        # Contact info
        contact_email = contact.get('email')
        contact_phone = contact.get('phone')
        
        # Colors
        colors_data = animal_data.get('colors', {})
        colors = [c for c in [colors_data.get('primary'), colors_data.get('secondary'), colors_data.get('tertiary')] if c]
        
        # Coat length
        coat = animal_data.get('coat')
        coat_map = {
            'Short': 'short',
            'Medium': 'medium',
            'Long': 'long'
        }
        coat_length = coat_map.get(coat) if coat else None
        
        # URL
        url = animal_data.get('url', f"https://www.petfinder.com/cat/{animal_data['id']}")
        
        return Cat(
            id=cat_id,
            name=name,
            breed=primary_breed,
            breeds_secondary=secondary_breeds,
            age=age,
            size=size,
            gender=gender,
            description=description,
            organization_name=animal_data.get('organization_id', 'Unknown Organization'),
            organization_id=organization_id,
            city=city,
            state=state,
            zip_code=zip_code,
            country='US',
            distance=animal_data.get('distance'),
            good_with_children=environment.get('children'),
            good_with_dogs=environment.get('dogs'),
            good_with_cats=environment.get('cats'),
            special_needs=attributes.get('special_needs', False),
            photos=photos,
            primary_photo=primary_photo,
            videos=videos,
            source='petfinder',
            url=url,
            contact_email=contact_email,
            contact_phone=contact_phone,
            declawed=attributes.get('declawed'),
            spayed_neutered=attributes.get('spayed_neutered'),
            house_trained=attributes.get('house_trained'),
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
        Search for cats on Petfinder.
        
        Args:
            location: ZIP code or "city, state" (e.g., "10001" or "New York, NY")
            distance: Search radius in miles (default: 100)
            age: List of age categories: baby, young, adult, senior
            size: List of sizes: small, medium, large
            gender: Gender filter: male, female
            color: List of colors (e.g., ["black", "white", "tuxedo"])
            breed: List of breed names (e.g., ["Siamese", "Maine Coon"])
            good_with_children: Filter for cats good with children
            good_with_dogs: Filter for cats good with dogs
            good_with_cats: Filter for cats good with other cats
            limit: Maximum number of results (default: 100, max: 1000)
            
        Returns:
            List of Cat objects
        """
        color_str = f" with colors {color}" if color else ""
        self.log(f"Searching for cats near {location} within {distance} miles{color_str}")
        
        # Build query parameters
        params: Dict[str, Any] = {
            'type': 'cat',
            'limit': min(self.MAX_RESULTS_PER_PAGE, limit),
            'sort': 'recent'
        }
        
        self.log(f"DEBUG: Initial params: {params}")
        
        if location:
            params['location'] = location
            params['distance'] = distance
        
        if age:
            # Map our age categories to Petfinder's
            age_map = {
                'kitten': 'baby',
                'young': 'young',
                'adult': 'adult',
                'senior': 'senior'
            }
            petfinder_ages = [age_map.get(a, a) for a in age]
            params['age'] = ','.join(petfinder_ages)
        
        if size:
            params['size'] = ','.join(size)
        
        if gender:
            params['gender'] = gender
        
        if color:
            params['color'] = ','.join(color)
        
        if breed:
            params['breed'] = ','.join(breed)
        
        if good_with_children is not None:
            params['good_with_children'] = str(good_with_children).lower()
        
        if good_with_dogs is not None:
            params['good_with_dogs'] = str(good_with_dogs).lower()
        
        if good_with_cats is not None:
            params['good_with_cats'] = str(good_with_cats).lower()
        
        self.log(f"DEBUG: ====== PETFINDER API CALL ======")
        self.log(f"DEBUG: Final API params: {params}")
        self.log(f"DEBUG: ================================")
        
        # Fetch results with pagination
        cats = []
        page = 1
        total_pages = 1
        
        while page <= total_pages and len(cats) < min(limit, self.MAX_TOTAL_RESULTS):
            params['page'] = page
            
            try:
                data = self._make_request(self.ANIMALS_URL, params)
                
                self.log(f"DEBUG: API Response - Total results: {data.get('pagination', {}).get('total_count', 'unknown')}")
                self.log(f"DEBUG: API Response - Animals in this page: {len(data.get('animals', []))}")
                
                # Parse animals
                animals = data.get('animals', [])
                for animal_data in animals:
                    try:
                        cat = self._parse_cat(animal_data)
                        cats.append(cat)
                    except Exception as e:
                        self.log_warning(f"Failed to parse cat {animal_data.get('id')}: {e}")
                
                # Check pagination
                pagination = data.get('pagination', {})
                total_pages = pagination.get('total_pages', 1)
                
                self.log(f"Fetched page {page}/{total_pages}, {len(animals)} cats")
                
                page += 1
                
            except Exception as e:
                self.log_error(f"Failed to fetch page {page}: {e}")
                break
        
        self.log(f"Search complete: found {len(cats)} cats")
        return cats[:limit]  # Ensure we don't exceed limit

