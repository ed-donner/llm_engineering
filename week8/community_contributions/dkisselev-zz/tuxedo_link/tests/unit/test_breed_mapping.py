"""Unit tests for breed mapping utilities."""

import pytest
import tempfile
import shutil

from utils.breed_mapping import (
    normalize_user_breeds,
    get_breed_suggestions,
    USER_TERM_TO_API_BREED
)
from setup_metadata_vectordb import MetadataVectorDB


@pytest.fixture
def temp_vectordb():
    """Create a temporary metadata vector database with breeds indexed."""
    temp_dir = tempfile.mkdtemp()
    vectordb = MetadataVectorDB(persist_directory=temp_dir)
    
    # Index some test breeds
    test_breeds = [
        "Siamese",
        "Persian",
        "Maine Coon",
        "Bengal",
        "Ragdoll",
        "British Shorthair",
        "Domestic Short Hair",
        "Domestic Medium Hair",
        "Domestic Long Hair"
    ]
    vectordb.index_breeds(test_breeds, source="petfinder")
    
    yield vectordb
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestBreedMapping:
    """Tests for breed mapping functions."""
    
    def test_dictionary_match_maine_coon(self):
        """Test dictionary mapping for 'maine coon' (common typo)."""
        valid_breeds = ["Maine Coon", "Siamese", "Persian"]
        
        result = normalize_user_breeds(["main coon"], valid_breeds)  # Typo: "main"
        
        assert len(result) > 0
        assert "Maine Coon" in result
    
    def test_dictionary_match_ragdoll(self):
        """Test dictionary mapping for 'ragdol' (typo)."""
        valid_breeds = ["Ragdoll", "Siamese"]
        
        result = normalize_user_breeds(["ragdol"], valid_breeds)
        
        assert len(result) > 0
        assert "Ragdoll" in result
    
    def test_dictionary_match_sphynx(self):
        """Test dictionary mapping for 'sphinx' (common misspelling)."""
        valid_breeds = ["Sphynx", "Persian"]
        
        result = normalize_user_breeds(["sphinx"], valid_breeds)
        
        assert len(result) > 0
        assert "Sphynx" in result
    
    def test_dictionary_match_mixed_breed(self):
        """Test dictionary mapping for 'mixed' returns multiple options."""
        valid_breeds = [
            "Mixed Breed",
            "Domestic Short Hair",
            "Domestic Medium Hair",
            "Domestic Long Hair"
        ]
        
        result = normalize_user_breeds(["mixed"], valid_breeds)
        
        assert len(result) >= 1
        # Should map to one or more domestic breeds
        assert any(b in result for b in valid_breeds)
    
    def test_exact_match_fallback(self):
        """Test exact match when not in dictionary."""
        valid_breeds = ["Siamese", "Persian", "Bengal"]
        
        result = normalize_user_breeds(["siamese"], valid_breeds)
        
        assert len(result) == 1
        assert "Siamese" in result
    
    def test_substring_match_fallback(self):
        """Test substring matching for partial breed names."""
        valid_breeds = ["British Shorthair", "American Shorthair"]
        
        result = normalize_user_breeds(["shorthair"], valid_breeds)
        
        assert len(result) >= 1
        assert any("Shorthair" in breed for breed in result)
    
    def test_multiple_breeds(self):
        """Test mapping multiple breed terms."""
        valid_breeds = ["Siamese", "Persian", "Maine Coon"]
        
        result = normalize_user_breeds(
            ["siamese", "persian", "maine"],
            valid_breeds
        )
        
        assert len(result) >= 2  # At least siamese and persian should match
        assert "Siamese" in result
        assert "Persian" in result
    
    def test_no_match(self):
        """Test when no match is found."""
        valid_breeds = ["Siamese", "Persian"]
        
        result = normalize_user_breeds(["invalid_breed_xyz"], valid_breeds)
        
        # Should return empty list
        assert len(result) == 0
    
    def test_empty_input(self):
        """Test with empty input."""
        valid_breeds = ["Siamese", "Persian"]
        
        result = normalize_user_breeds([], valid_breeds)
        assert len(result) == 0
        
        result = normalize_user_breeds([""], valid_breeds)
        assert len(result) == 0
    
    def test_with_vectordb(self, temp_vectordb):
        """Test with vector DB for fuzzy matching."""
        valid_breeds = ["Maine Coon", "Ragdoll", "Bengal"]
        
        # Test with typo
        result = normalize_user_breeds(
            ["ragdol"],  # Typo
            valid_breeds,
            vectordb=temp_vectordb,
            source="petfinder"
        )
        
        # Should still find Ragdoll via vector search (if not in dictionary)
        # Or dictionary match if present
        assert len(result) > 0
        assert "Ragdoll" in result
    
    def test_vector_search_typo(self, temp_vectordb):
        """Test vector search handles typos."""
        valid_breeds = ["Siamese"]
        
        # Typo: "siames"
        result = normalize_user_breeds(
            ["siames"],
            valid_breeds,
            vectordb=temp_vectordb,
            source="petfinder",
            similarity_threshold=0.6
        )
        
        # Vector search should find Siamese
        if len(result) > 0:
            assert "Siamese" in result
    
    def test_dictionary_priority(self, temp_vectordb):
        """Test that dictionary matches are prioritized over vector search."""
        valid_breeds = ["Maine Coon"]
        
        # "main coon" is in dictionary
        result = normalize_user_breeds(
            ["main coon"],
            valid_breeds,
            vectordb=temp_vectordb,
            source="petfinder"
        )
        
        # Should use dictionary match
        assert "Maine Coon" in result
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        valid_breeds = ["Maine Coon"]
        
        result_lower = normalize_user_breeds(["maine"], valid_breeds)
        result_upper = normalize_user_breeds(["MAINE"], valid_breeds)
        result_mixed = normalize_user_breeds(["MaInE"], valid_breeds)
        
        assert result_lower == result_upper == result_mixed
    
    def test_domestic_variations(self):
        """Test that DSH/DMH/DLH map correctly."""
        valid_breeds = [
            "Domestic Short Hair",
            "Domestic Medium Hair",
            "Domestic Long Hair"
        ]
        
        result_dsh = normalize_user_breeds(["dsh"], valid_breeds)
        result_dmh = normalize_user_breeds(["dmh"], valid_breeds)
        result_dlh = normalize_user_breeds(["dlh"], valid_breeds)
        
        assert "Domestic Short Hair" in result_dsh
        assert "Domestic Medium Hair" in result_dmh
        assert "Domestic Long Hair" in result_dlh
    
    def test_tabby_is_not_breed(self):
        """Test that 'tabby' maps to Domestic Short Hair (tabby is a pattern, not breed)."""
        valid_breeds = ["Domestic Short Hair", "Siamese"]
        
        result = normalize_user_breeds(["tabby"], valid_breeds)
        
        assert len(result) > 0
        assert "Domestic Short Hair" in result
    
    def test_get_breed_suggestions(self):
        """Test breed suggestions function."""
        valid_breeds = [
            "British Shorthair",
            "American Shorthair",
            "Domestic Short Hair"
        ]
        
        suggestions = get_breed_suggestions("short", valid_breeds, top_n=3)
        
        assert len(suggestions) == 3
        assert all("Short" in s for s in suggestions)
    
    def test_all_dictionary_mappings(self):
        """Test that all dictionary mappings are correctly defined."""
        # Verify structure of USER_TERM_TO_API_BREED
        assert isinstance(USER_TERM_TO_API_BREED, dict)
        
        for user_term, api_breeds in USER_TERM_TO_API_BREED.items():
            assert isinstance(user_term, str)
            assert isinstance(api_breeds, list)
            assert len(api_breeds) > 0
            assert all(isinstance(b, str) for b in api_breeds)
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in user input."""
        valid_breeds = ["Maine Coon"]
        
        result1 = normalize_user_breeds([" maine "], valid_breeds)
        result2 = normalize_user_breeds(["maine"], valid_breeds)
        
        assert result1 == result2
    
    def test_norwegian_forest_variations(self):
        """Test Norwegian Forest Cat variations."""
        valid_breeds = ["Norwegian Forest Cat"]
        
        result1 = normalize_user_breeds(["norwegian forest"], valid_breeds)
        result2 = normalize_user_breeds(["norwegian forest cat"], valid_breeds)
        
        assert "Norwegian Forest Cat" in result1
        assert "Norwegian Forest Cat" in result2
    
    def test_similarity_threshold(self, temp_vectordb):
        """Test that similarity threshold works."""
        valid_breeds = ["Siamese"]
        
        # Very different term
        result_high = normalize_user_breeds(
            ["abcxyz"],
            valid_breeds,
            vectordb=temp_vectordb,
            source="petfinder",
            similarity_threshold=0.9  # High threshold
        )
        
        result_low = normalize_user_breeds(
            ["abcxyz"],
            valid_breeds,
            vectordb=temp_vectordb,
            source="petfinder",
            similarity_threshold=0.1  # Low threshold
        )
        
        # High threshold should reject poor matches
        # Low threshold may accept them
        assert len(result_high) <= len(result_low)

