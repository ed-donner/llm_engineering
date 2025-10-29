"""Pydantic models for cat adoption data."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Cat(BaseModel):
    """Model representing a cat available for adoption."""
    
    # Basic information
    id: str = Field(..., description="Unique identifier from source")
    name: str = Field(..., description="Cat's name")
    breed: str = Field(..., description="Primary breed")
    breeds_secondary: Optional[List[str]] = Field(default=None, description="Secondary breeds")
    age: str = Field(..., description="Age category: kitten, young, adult, senior")
    size: str = Field(..., description="Size: small, medium, large")
    gender: str = Field(..., description="Gender: male, female, unknown")
    description: str = Field(default="", description="Full description of the cat")
    
    # Location information
    organization_name: str = Field(..., description="Rescue organization name")
    organization_id: Optional[str] = Field(default=None, description="Organization ID")
    city: Optional[str] = Field(default=None, description="City")
    state: Optional[str] = Field(default=None, description="State/Province")
    zip_code: Optional[str] = Field(default=None, description="ZIP/Postal code")
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate")
    country: Optional[str] = Field(default="US", description="Country code")
    distance: Optional[float] = Field(default=None, description="Distance from user in miles")
    
    # Behavioral attributes
    good_with_children: Optional[bool] = Field(default=None, description="Good with children")
    good_with_dogs: Optional[bool] = Field(default=None, description="Good with dogs")
    good_with_cats: Optional[bool] = Field(default=None, description="Good with cats")
    special_needs: bool = Field(default=False, description="Has special needs")
    
    # Media
    photos: List[str] = Field(default_factory=list, description="List of photo URLs")
    primary_photo: Optional[str] = Field(default=None, description="Primary photo URL")
    videos: List[str] = Field(default_factory=list, description="List of video URLs")
    
    # Metadata
    source: str = Field(..., description="Source: petfinder, rescuegroups")
    url: str = Field(..., description="Direct URL to listing")
    adoption_fee: Optional[float] = Field(default=None, description="Adoption fee in dollars")
    contact_email: Optional[str] = Field(default=None, description="Contact email")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone")
    fetched_at: datetime = Field(default_factory=datetime.now, description="When data was fetched")
    
    # Deduplication
    fingerprint: Optional[str] = Field(default=None, description="Computed fingerprint for deduplication")
    
    # Additional attributes
    declawed: Optional[bool] = Field(default=None, description="Is declawed")
    spayed_neutered: Optional[bool] = Field(default=None, description="Is spayed/neutered")
    house_trained: Optional[bool] = Field(default=None, description="Is house trained")
    coat_length: Optional[str] = Field(default=None, description="Coat length: short, medium, long")
    colors: List[str] = Field(default_factory=list, description="Coat colors")
    
    @field_validator('age')
    @classmethod
    def validate_age(cls, v: str) -> str:
        """Validate age category."""
        valid_ages = ['kitten', 'young', 'adult', 'senior', 'unknown']
        if v.lower() not in valid_ages:
            return 'unknown'
        return v.lower()
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v: str) -> str:
        """Validate size category."""
        valid_sizes = ['small', 'medium', 'large', 'unknown']
        if v.lower() not in valid_sizes:
            return 'unknown'
        return v.lower()
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        """Validate gender."""
        valid_genders = ['male', 'female', 'unknown']
        if v.lower() not in valid_genders:
            return 'unknown'
        return v.lower()


class CatProfile(BaseModel):
    """Model representing user preferences for cat adoption."""
    
    # Hard constraints
    age_range: Optional[List[str]] = Field(
        default=None, 
        description="Acceptable age categories: kitten, young, adult, senior"
    )
    size: Optional[List[str]] = Field(
        default=None,
        description="Acceptable sizes: small, medium, large"
    )
    max_distance: Optional[int] = Field(
        default=100,
        description="Maximum distance in miles"
    )
    good_with_children: Optional[bool] = Field(
        default=None,
        description="Must be good with children"
    )
    good_with_dogs: Optional[bool] = Field(
        default=None,
        description="Must be good with dogs"
    )
    good_with_cats: Optional[bool] = Field(
        default=None,
        description="Must be good with cats"
    )
    special_needs_ok: bool = Field(
        default=True,
        description="Open to special needs cats"
    )
    
    # Soft preferences (for vector search)
    personality_description: str = Field(
        default="",
        description="Free-text description of desired personality and traits"
    )
    
    # Breed preferences
    preferred_breeds: Optional[List[str]] = Field(
        default=None,
        description="Preferred breeds"
    )
    
    # Location
    user_location: Optional[str] = Field(
        default=None,
        description="User location (ZIP code, city, or lat,long)"
    )
    user_latitude: Optional[float] = Field(default=None, description="User latitude")
    user_longitude: Optional[float] = Field(default=None, description="User longitude")
    
    # Additional preferences
    gender_preference: Optional[str] = Field(
        default=None,
        description="Preferred gender: male, female, or None for no preference"
    )
    coat_length_preference: Optional[List[str]] = Field(
        default=None,
        description="Preferred coat lengths: short, medium, long"
    )
    color_preferences: Optional[List[str]] = Field(
        default=None,
        description="Preferred colors"
    )
    must_be_declawed: Optional[bool] = Field(default=None, description="Must be declawed")
    must_be_spayed_neutered: Optional[bool] = Field(default=None, description="Must be spayed/neutered")
    
    @field_validator('age_range')
    @classmethod
    def validate_age_range(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate age range values."""
        if v is None:
            return None
        valid_ages = {'kitten', 'young', 'adult', 'senior'}
        return [age.lower() for age in v if age.lower() in valid_ages]
    
    @field_validator('size')
    @classmethod
    def validate_size_list(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate size values."""
        if v is None:
            return None
        valid_sizes = {'small', 'medium', 'large'}
        return [size.lower() for size in v if size.lower() in valid_sizes]


class CatMatch(BaseModel):
    """Model representing a matched cat with scoring details."""
    
    cat: Cat = Field(..., description="The matched cat")
    match_score: float = Field(..., description="Overall match score (0-1)")
    vector_similarity: float = Field(..., description="Vector similarity score (0-1)")
    attribute_match_score: float = Field(..., description="Attribute match score (0-1)")
    explanation: str = Field(default="", description="Human-readable match explanation")
    matching_attributes: List[str] = Field(
        default_factory=list,
        description="List of matching attributes"
    )
    missing_attributes: List[str] = Field(
        default_factory=list,
        description="List of desired but missing attributes"
    )


class AdoptionAlert(BaseModel):
    """Model representing a scheduled adoption alert."""
    
    id: Optional[int] = Field(default=None, description="Alert ID (assigned by database)")
    user_email: str = Field(..., description="User email for notifications")
    profile: CatProfile = Field(..., description="Search profile")
    frequency: str = Field(..., description="Frequency: immediately, daily, weekly")
    last_sent: Optional[datetime] = Field(default=None, description="Last notification sent")
    active: bool = Field(default=True, description="Is alert active")
    created_at: datetime = Field(default_factory=datetime.now, description="When alert was created")
    last_match_ids: List[str] = Field(
        default_factory=list,
        description="IDs of cats from last notification (to avoid duplicates)"
    )
    
    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        """Validate frequency value."""
        valid_frequencies = ['immediately', 'daily', 'weekly']
        if v.lower() not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        return v.lower()


class SearchResult(BaseModel):
    """Model representing search results returned to UI."""
    
    matches: List[CatMatch] = Field(..., description="List of matched cats")
    total_found: int = Field(..., description="Total cats found before filtering")
    search_profile: CatProfile = Field(..., description="Search profile used")
    search_time: float = Field(..., description="Search time in seconds")
    sources_queried: List[str] = Field(..., description="Sources that were queried")
    duplicates_removed: int = Field(default=0, description="Number of duplicates removed")

