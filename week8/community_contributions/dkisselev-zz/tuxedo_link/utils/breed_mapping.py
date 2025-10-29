"""
Breed mapping utilities for cat APIs.

Handles mapping user breed terms to valid API breed values
using dictionary lookups, vector search, and exact matching.
"""

import logging
from typing import List, Optional, Dict

# Mapping of common user terms to API breed values
# These are fuzzy/colloquial terms that users might type
USER_TERM_TO_API_BREED: Dict[str, List[str]] = {
    # Common misspellings and variations
    "main coon": ["Maine Coon"],
    "maine": ["Maine Coon"],
    "ragdol": ["Ragdoll"],
    "siames": ["Siamese"],
    "persian": ["Persian"],
    "bengal": ["Bengal"],
    "british shorthair": ["British Shorthair"],
    "russian blue": ["Russian Blue"],
    "sphynx": ["Sphynx"],
    "sphinx": ["Sphynx"],
    "american shorthair": ["American Shorthair"],
    "scottish fold": ["Scottish Fold"],
    "abyssinian": ["Abyssinian"],
    "birman": ["Birman"],
    "burmese": ["Burmese"],
    "himalayan": ["Himalayan"],
    "norwegian forest": ["Norwegian Forest Cat"],
    "norwegian forest cat": ["Norwegian Forest Cat"],
    "oriental": ["Oriental"],
    "somali": ["Somali"],
    "turkish angora": ["Turkish Angora"],
    "turkish van": ["Turkish Van"],
    
    # Mixed breeds
    "mixed": ["Mixed Breed", "Domestic Short Hair", "Domestic Medium Hair", "Domestic Long Hair"],
    "mixed breed": ["Mixed Breed", "Domestic Short Hair", "Domestic Medium Hair", "Domestic Long Hair"],
    "domestic": ["Domestic Short Hair", "Domestic Medium Hair", "Domestic Long Hair"],
    "dsh": ["Domestic Short Hair"],
    "dmh": ["Domestic Medium Hair"],
    "dlh": ["Domestic Long Hair"],
    "tabby": ["Domestic Short Hair"],  # Tabby is a pattern, not a breed
    "tuxedo": ["Domestic Short Hair"],  # Tuxedo is a color, not a breed
}


def normalize_user_breeds(
    user_breeds: List[str], 
    valid_api_breeds: List[str],
    vectordb: Optional[object] = None,
    source: str = "petfinder",
    similarity_threshold: float = 0.7
) -> List[str]:
    """
    Normalize user breed preferences to valid API breed values.
    
    Uses 3-tier strategy:
    1. Dictionary lookup for common variations
    2. Vector DB semantic search for fuzzy matching
    3. Direct string matching as fallback
    
    Args:
        user_breeds: List of breed terms provided by the user
        valid_api_breeds: List of breeds actually accepted by the API
        vectordb: Optional MetadataVectorDB instance for semantic search
        source: API source (petfinder/rescuegroups) for vector filtering
        similarity_threshold: Minimum similarity score (0-1) for vector matches
        
    Returns:
        List of valid API breed strings
    """
    if not user_breeds:
        return []
    
    normalized_breeds = set()
    
    for user_term in user_breeds:
        if not user_term or not user_term.strip():
            continue
            
        user_term_lower = user_term.lower().strip()
        matched = False
        
        # Tier 1: Dictionary lookup (instant, common variations)
        if user_term_lower in USER_TERM_TO_API_BREED:
            mapped_breeds = USER_TERM_TO_API_BREED[user_term_lower]
            for mapped_breed in mapped_breeds:
                if mapped_breed in valid_api_breeds:
                    normalized_breeds.add(mapped_breed)
                    matched = True
            
            if matched:
                logging.info(f"🎯 Dictionary match: '{user_term}' → {list(mapped_breeds)}")
                continue
        
        # Tier 2: Vector DB semantic search (fuzzy matching, handles typos)
        if vectordb:
            try:
                matches = vectordb.search_breed(
                    user_term, 
                    n_results=1,
                    source_filter=source
                )
                
                if matches and matches[0]['similarity'] >= similarity_threshold:
                    best_match = matches[0]['breed']
                    similarity = matches[0]['similarity']
                    
                    if best_match in valid_api_breeds:
                        normalized_breeds.add(best_match)
                        logging.info(
                            f"🔍 Vector match: '{user_term}' → '{best_match}' "
                            f"(similarity: {similarity:.2f})"
                        )
                        matched = True
                        continue
            except Exception as e:
                logging.warning(f"Vector search failed for breed '{user_term}': {e}")
        
        # Tier 3: Direct string matching (exact or substring)
        if not matched:
            # Try exact match (case-insensitive)
            for valid_breed in valid_api_breeds:
                if valid_breed.lower() == user_term_lower:
                    normalized_breeds.add(valid_breed)
                    logging.info(f"✓ Exact match: '{user_term}' → '{valid_breed}'")
                    matched = True
                    break
            
            # Try substring match if exact didn't work
            if not matched:
                for valid_breed in valid_api_breeds:
                    if user_term_lower in valid_breed.lower():
                        normalized_breeds.add(valid_breed)
                        logging.info(f"≈ Substring match: '{user_term}' → '{valid_breed}'")
                        matched = True
        
        # Log if no match found
        if not matched:
            logging.warning(
                f"⚠️ No breed match found for '{user_term}'. "
                f"User will see broader results."
            )
    
    result = list(normalized_breeds)
    logging.info(f"Breed normalization complete: {user_breeds} → {result}")
    return result


def get_breed_suggestions(breed_term: str, valid_breeds: List[str], top_n: int = 5) -> List[str]:
    """
    Get breed suggestions for autocomplete or error messages.
    
    Args:
        breed_term: Partial or misspelled breed name
        valid_breeds: List of valid API breed values
        top_n: Number of suggestions to return
        
    Returns:
        List of suggested breed names
    """
    term_lower = breed_term.lower().strip()
    suggestions = []
    
    # Find breeds containing the term
    for breed in valid_breeds:
        if term_lower in breed.lower():
            suggestions.append(breed)
    
    return suggestions[:top_n]

