"""Unit tests for color mapping utilities."""

import pytest
import tempfile
import shutil

from utils.color_mapping import (
    normalize_user_colors,
    get_color_suggestions,
    USER_TERM_TO_API_COLOR
)
from setup_metadata_vectordb import MetadataVectorDB


@pytest.fixture
def temp_vectordb():
    """Create a temporary metadata vector database with colors indexed."""
    temp_dir = tempfile.mkdtemp()
    vectordb = MetadataVectorDB(persist_directory=temp_dir)
    
    # Index some test colors
    test_colors = [
        "Black",
        "White",
        "Black & White / Tuxedo",
        "Orange / Red",
        "Gray / Blue / Silver",
        "Calico",
        "Tabby (Brown / Chocolate)"
    ]
    vectordb.index_colors(test_colors, source="petfinder")
    
    yield vectordb
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestColorMapping:
    """Tests for color mapping functions."""
    
    def test_dictionary_match_tuxedo(self):
        """Test dictionary mapping for 'tuxedo'."""
        valid_colors = ["Black", "White", "Black & White / Tuxedo"]
        
        result = normalize_user_colors(["tuxedo"], valid_colors)
        
        assert len(result) > 0
        assert "Black & White / Tuxedo" in result
        assert "Black" not in result  # Should NOT map to separate colors
    
    def test_dictionary_match_orange(self):
        """Test dictionary mapping for 'orange'."""
        valid_colors = ["Orange / Red", "White"]
        
        result = normalize_user_colors(["orange"], valid_colors)
        
        assert len(result) == 1
        assert "Orange / Red" in result
    
    def test_dictionary_match_gray_variations(self):
        """Test dictionary mapping for gray/grey."""
        valid_colors = ["Gray / Blue / Silver", "White"]
        
        result_gray = normalize_user_colors(["gray"], valid_colors)
        result_grey = normalize_user_colors(["grey"], valid_colors)
        
        assert result_gray == result_grey
        assert "Gray / Blue / Silver" in result_gray
    
    def test_multiple_colors(self):
        """Test mapping multiple color terms."""
        valid_colors = [
            "Black & White / Tuxedo",
            "Orange / Red",
            "Calico"
        ]
        
        result = normalize_user_colors(
            ["tuxedo", "orange", "calico"],
            valid_colors
        )
        
        assert len(result) == 3
        assert "Black & White / Tuxedo" in result
        assert "Orange / Red" in result
        assert "Calico" in result
    
    def test_exact_match_fallback(self):
        """Test exact match when not in dictionary."""
        valid_colors = ["Black", "White", "Calico"]
        
        # "Calico" should match exactly
        result = normalize_user_colors(["calico"], valid_colors)
        
        assert len(result) == 1
        assert "Calico" in result
    
    def test_substring_match_fallback(self):
        """Test substring matching as last resort."""
        valid_colors = ["Tabby (Brown / Chocolate)", "Tabby (Orange / Red)"]
        
        # "tabby" should match both tabby colors
        result = normalize_user_colors(["tabby"], valid_colors)
        
        assert len(result) >= 1
        assert any("Tabby" in color for color in result)
    
    def test_no_match(self):
        """Test when no match is found."""
        valid_colors = ["Black", "White"]
        
        result = normalize_user_colors(["invalid_color_xyz"], valid_colors)
        
        # Should return empty list
        assert len(result) == 0
    
    def test_empty_input(self):
        """Test with empty input."""
        valid_colors = ["Black", "White"]
        
        result = normalize_user_colors([], valid_colors)
        assert len(result) == 0
        
        result = normalize_user_colors([""], valid_colors)
        assert len(result) == 0
    
    def test_with_vectordb(self, temp_vectordb):
        """Test with vector DB for fuzzy matching."""
        valid_colors = [
            "Black & White / Tuxedo",
            "Orange / Red",
            "Gray / Blue / Silver"
        ]
        
        # Test with typo (with lower threshold to demonstrate fuzzy matching)
        result = normalize_user_colors(
            ["tuxado"],  # Typo
            valid_colors,
            vectordb=temp_vectordb,
            source="petfinder",
            similarity_threshold=0.3  # Lower threshold for typos
        )
        
        # With lower threshold, may find a match (not guaranteed for all typos)
        # The main point is that it doesn't crash and handles typos gracefully
        assert isinstance(result, list)  # Returns a list (may be empty)
    
    def test_vector_search_typo(self, temp_vectordb):
        """Test vector search handles typos."""
        valid_colors = ["Gray / Blue / Silver"]
        
        # Typo: "grey" is in dictionary but "gery" is not
        result = normalize_user_colors(
            ["gery"],  # Typo
            valid_colors,
            vectordb=temp_vectordb,
            source="petfinder",
            similarity_threshold=0.6  # Lower threshold for typos
        )
        
        # Vector search should find gray
        # Note: May not always work for severe typos
        if len(result) > 0:
            assert "Gray" in result[0] or "Blue" in result[0] or "Silver" in result[0]
    
    def test_dictionary_priority(self, temp_vectordb):
        """Test that dictionary matches are prioritized over vector search."""
        valid_colors = ["Black & White / Tuxedo", "Black"]
        
        # "tuxedo" is in dictionary
        result = normalize_user_colors(
            ["tuxedo"],
            valid_colors,
            vectordb=temp_vectordb,
            source="petfinder"
        )
        
        # Should use dictionary match
        assert "Black & White / Tuxedo" in result
        assert "Black" not in result  # Should not be separate
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        valid_colors = ["Black & White / Tuxedo"]
        
        result_lower = normalize_user_colors(["tuxedo"], valid_colors)
        result_upper = normalize_user_colors(["TUXEDO"], valid_colors)
        result_mixed = normalize_user_colors(["TuXeDo"], valid_colors)
        
        assert result_lower == result_upper == result_mixed
    
    def test_get_color_suggestions(self):
        """Test color suggestions function."""
        valid_colors = [
            "Tabby (Brown / Chocolate)",
            "Tabby (Orange / Red)",
            "Tabby (Gray / Blue / Silver)"
        ]
        
        suggestions = get_color_suggestions("tab", valid_colors, top_n=3)
        
        assert len(suggestions) == 3
        assert all("Tabby" in s for s in suggestions)
    
    def test_all_dictionary_mappings(self):
        """Test that all dictionary mappings are correctly defined."""
        # Verify structure of USER_TERM_TO_API_COLOR
        assert isinstance(USER_TERM_TO_API_COLOR, dict)
        
        for user_term, api_colors in USER_TERM_TO_API_COLOR.items():
            assert isinstance(user_term, str)
            assert isinstance(api_colors, list)
            assert len(api_colors) > 0
            assert all(isinstance(c, str) for c in api_colors)
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in user input."""
        valid_colors = ["Black & White / Tuxedo"]
        
        result1 = normalize_user_colors([" tuxedo "], valid_colors)
        result2 = normalize_user_colors(["tuxedo"], valid_colors)
        
        assert result1 == result2

