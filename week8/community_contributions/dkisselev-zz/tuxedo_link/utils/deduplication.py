"""Deduplication utilities for identifying duplicate cat listings."""

import hashlib
from typing import Tuple
import Levenshtein

from models.cats import Cat


def create_fingerprint(cat: Cat) -> str:
    """
    Create a fingerprint for a cat based on stable attributes.
    
    The fingerprint is a hash of:
    - Organization name (normalized)
    - Breed (normalized)
    - Age
    - Gender
    
    Args:
        cat: Cat object
        
    Returns:
        Fingerprint hash (16 characters)
    """
    components = [
        cat.organization_name.lower().strip(),
        cat.breed.lower().strip(),
        str(cat.age).lower(),
        cat.gender.lower()
    ]
    
    # Create hash from combined components
    combined = '|'.join(components)
    hash_obj = hashlib.sha256(combined.encode())
    
    # Return first 16 characters of hex digest
    return hash_obj.hexdigest()[:16]


def calculate_levenshtein_similarity(str1: str, str2: str) -> float:
    """
    Calculate normalized Levenshtein similarity between two strings.
    
    Similarity = 1 - (distance / max_length)
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score (0-1, where 1 is identical)
    """
    if not str1 or not str2:
        return 0.0
    
    # Normalize strings
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    # Handle identical strings
    if str1 == str2:
        return 1.0
    
    # Calculate Levenshtein distance
    distance = Levenshtein.distance(str1, str2)
    
    # Normalize by maximum possible distance
    max_length = max(len(str1), len(str2))
    
    if max_length == 0:
        return 1.0
    
    similarity = 1.0 - (distance / max_length)
    
    return max(0.0, similarity)


def calculate_text_similarity(cat1: Cat, cat2: Cat) -> Tuple[float, float]:
    """
    Calculate text similarity between two cats (name and description).
    
    Args:
        cat1: First cat
        cat2: Second cat
        
    Returns:
        Tuple of (name_similarity, description_similarity)
    """
    # Name similarity
    name_similarity = calculate_levenshtein_similarity(cat1.name, cat2.name)
    
    # Description similarity
    desc_similarity = calculate_levenshtein_similarity(
        cat1.description,
        cat2.description
    )
    
    return name_similarity, desc_similarity


def calculate_composite_score(
    name_similarity: float,
    description_similarity: float,
    image_similarity: float,
    name_weight: float = 0.4,
    description_weight: float = 0.3,
    image_weight: float = 0.3
) -> float:
    """
    Calculate a composite similarity score from multiple signals.
    
    Args:
        name_similarity: Name similarity (0-1)
        description_similarity: Description similarity (0-1)
        image_similarity: Image similarity (0-1)
        name_weight: Weight for name similarity
        description_weight: Weight for description similarity
        image_weight: Weight for image similarity
        
    Returns:
        Composite score (0-1)
    """
    # Ensure weights sum to 1
    total_weight = name_weight + description_weight + image_weight
    if total_weight == 0:
        return 0.0
    
    # Normalize weights
    name_weight /= total_weight
    description_weight /= total_weight
    image_weight /= total_weight
    
    # Calculate weighted score
    score = (
        name_similarity * name_weight +
        description_similarity * description_weight +
        image_similarity * image_weight
    )
    
    return score


def normalize_string(s: str) -> str:
    """
    Normalize a string for comparison.
    
    - Convert to lowercase
    - Strip whitespace
    - Remove extra spaces
    
    Args:
        s: String to normalize
        
    Returns:
        Normalized string
    """
    import re
    s = s.lower().strip()
    s = re.sub(r'\s+', ' ', s)  # Replace multiple spaces with single space
    return s


def calculate_breed_similarity(breed1: str, breed2: str) -> float:
    """
    Calculate breed similarity with special handling for mixed breeds.
    
    Args:
        breed1: First breed
        breed2: Second breed
        
    Returns:
        Similarity score (0-1)
    """
    breed1_norm = normalize_string(breed1)
    breed2_norm = normalize_string(breed2)
    
    # Exact match
    if breed1_norm == breed2_norm:
        return 1.0
    
    # Check if both are domestic shorthair/longhair (very common)
    domestic_variants = ['domestic short hair', 'domestic shorthair', 'dsh',
                        'domestic long hair', 'domestic longhair', 'dlh',
                        'domestic medium hair', 'domestic mediumhair', 'dmh']
    
    if breed1_norm in domestic_variants and breed2_norm in domestic_variants:
        return 0.9  # High similarity for domestic cats
    
    # Check for mix/mixed keywords
    mix_keywords = ['mix', 'mixed', 'tabby']
    breed1_has_mix = any(keyword in breed1_norm for keyword in mix_keywords)
    breed2_has_mix = any(keyword in breed2_norm for keyword in mix_keywords)
    
    if breed1_has_mix and breed2_has_mix:
        # Both are mixes, higher tolerance
        return calculate_levenshtein_similarity(breed1, breed2) * 0.9
    
    # Standard Levenshtein similarity
    return calculate_levenshtein_similarity(breed1, breed2)

