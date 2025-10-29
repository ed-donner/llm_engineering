"""
Color mapping utilities for cat APIs.

Handles mapping user color terms to valid API color values
using dictionary lookups, vector search, and exact matching.
"""

import logging
from typing import List, Dict, Optional

# Mapping of common user terms to Petfinder API color values
# Based on actual Petfinder API color list
USER_TERM_TO_API_COLOR: Dict[str, List[str]] = {
    # Tuxedo/Bicolor patterns
    "tuxedo": ["Black & White / Tuxedo"],
    "black and white": ["Black & White / Tuxedo"],
    "black & white": ["Black & White / Tuxedo"],
    "bicolor": ["Black & White / Tuxedo"],  # Most common bicolor
    
    # Solid colors
    "black": ["Black"],
    "white": ["White"],
    
    # Orange variations
    "orange": ["Orange / Red"],
    "red": ["Orange / Red"],
    "ginger": ["Orange / Red"],
    "orange and white": ["Orange & White"],
    "orange & white": ["Orange & White"],
    
    # Gray variations
    "gray": ["Gray / Blue / Silver"],
    "grey": ["Gray / Blue / Silver"],
    "silver": ["Gray / Blue / Silver"],
    "blue": ["Gray / Blue / Silver"],
    "gray and white": ["Gray & White"],
    "grey and white": ["Gray & White"],
    
    # Brown/Chocolate
    "brown": ["Brown / Chocolate"],
    "chocolate": ["Brown / Chocolate"],
    
    # Cream/Ivory
    "cream": ["Cream / Ivory"],
    "ivory": ["Cream / Ivory"],
    "buff": ["Buff / Tan / Fawn"],
    "tan": ["Buff / Tan / Fawn"],
    "fawn": ["Buff / Tan / Fawn"],
    
    # Patterns
    "calico": ["Calico"],
    "dilute calico": ["Dilute Calico"],
    "tortoiseshell": ["Tortoiseshell"],
    "tortie": ["Tortoiseshell"],
    "dilute tortoiseshell": ["Dilute Tortoiseshell"],
    "torbie": ["Torbie"],
    
    # Tabby patterns
    "tabby": ["Tabby (Brown / Chocolate)", "Tabby (Gray / Blue / Silver)", "Tabby (Orange / Red)"],
    "brown tabby": ["Tabby (Brown / Chocolate)"],
    "gray tabby": ["Tabby (Gray / Blue / Silver)"],
    "grey tabby": ["Tabby (Gray / Blue / Silver)"],
    "orange tabby": ["Tabby (Orange / Red)"],
    "red tabby": ["Tabby (Orange / Red)"],
    "tiger": ["Tabby (Tiger Striped)"],
    "tiger striped": ["Tabby (Tiger Striped)"],
    "leopard": ["Tabby (Leopard / Spotted)"],
    "spotted": ["Tabby (Leopard / Spotted)"],
    
    # Point colors (Siamese-type)
    "blue point": ["Blue Point"],
    "chocolate point": ["Chocolate Point"],
    "cream point": ["Cream Point"],
    "flame point": ["Flame Point"],
    "lilac point": ["Lilac Point"],
    "seal point": ["Seal Point"],
    
    # Other
    "smoke": ["Smoke"],
    "blue cream": ["Blue Cream"],
}


def normalize_user_colors(
    user_colors: List[str], 
    valid_api_colors: List[str],
    vectordb: Optional[object] = None,
    source: str = "petfinder",
    similarity_threshold: float = 0.7
) -> List[str]:
    """
    Normalize user color preferences to valid API color values.
    
    Uses 3-tier strategy:
    1. Dictionary lookup for common color terms
    2. Vector DB semantic search for fuzzy matching
    3. Direct string matching as fallback
    
    Args:
        user_colors: List of color terms provided by the user
        valid_api_colors: List of colors actually accepted by the API
        vectordb: Optional MetadataVectorDB instance for semantic search
        source: API source (petfinder/rescuegroups) for vector filtering
        similarity_threshold: Minimum similarity score (0-1) for vector matches
        
    Returns:
        List of valid API color strings
    """
    if not user_colors:
        return []
    
    normalized_colors = set()
    
    for user_term in user_colors:
        if not user_term or not user_term.strip():
            continue
            
        user_term_lower = user_term.lower().strip()
        matched = False
        
        # Tier 1: Dictionary lookup (instant, common color terms)
        if user_term_lower in USER_TERM_TO_API_COLOR:
            mapped_colors = USER_TERM_TO_API_COLOR[user_term_lower]
            for mapped_color in mapped_colors:
                if mapped_color in valid_api_colors:
                    normalized_colors.add(mapped_color)
                    matched = True
            
            if matched:
                logging.info(f"🎯 Dictionary match: '{user_term}' → {list(mapped_colors)}")
                continue
        
        # Tier 2: Vector DB semantic search (fuzzy matching, handles typos)
        if vectordb:
            try:
                matches = vectordb.search_color(
                    user_term, 
                    n_results=1,
                    source_filter=source
                )
                
                if matches and matches[0]['similarity'] >= similarity_threshold:
                    best_match = matches[0]['color']
                    similarity = matches[0]['similarity']
                    
                    if best_match in valid_api_colors:
                        normalized_colors.add(best_match)
                        logging.info(
                            f"🔍 Vector match: '{user_term}' → '{best_match}' "
                            f"(similarity: {similarity:.2f})"
                        )
                        matched = True
                        continue
            except Exception as e:
                logging.warning(f"Vector search failed for color '{user_term}': {e}")
        
        # Tier 3: Direct string matching (exact or substring)
        if not matched:
            # Try exact match (case-insensitive)
            for valid_color in valid_api_colors:
                if valid_color.lower() == user_term_lower:
                    normalized_colors.add(valid_color)
                    logging.info(f"✓ Exact match: '{user_term}' → '{valid_color}'")
                    matched = True
                    break
            
            # Try substring match if exact didn't work
            if not matched:
                for valid_color in valid_api_colors:
                    if user_term_lower in valid_color.lower():
                        normalized_colors.add(valid_color)
                        logging.info(f"≈ Substring match: '{user_term}' → '{valid_color}'")
                        matched = True
        
        # Log if no match found
        if not matched:
            logging.warning(
                f"⚠️ No color match found for '{user_term}'. "
                f"User will see broader results."
            )
    
    result = list(normalized_colors)
    logging.info(f"Color normalization complete: {user_colors} → {result}")
    return result


def get_color_suggestions(color_term: str, valid_colors: List[str], top_n: int = 5) -> List[str]:
    """
    Get color suggestions for autocomplete or error messages.
    
    Args:
        color_term: Partial or misspelled color name
        valid_colors: List of valid API color values
        top_n: Number of suggestions to return
        
    Returns:
        List of suggested color names
    """
    term_lower = color_term.lower().strip()
    suggestions = []
    
    # Find colors containing the term
    for color in valid_colors:
        if term_lower in color.lower():
            suggestions.append(color)
    
    return suggestions[:top_n]


def get_color_help_text(valid_colors: List[str]) -> str:
    """
    Generate help text for valid colors.
    
    Args:
        valid_colors: List of valid API colors
        
    Returns:
        Formatted string describing valid colors
    """
    if not valid_colors:
        return "No color information available."
    
    return f"Valid colors: {', '.join(valid_colors)}"

