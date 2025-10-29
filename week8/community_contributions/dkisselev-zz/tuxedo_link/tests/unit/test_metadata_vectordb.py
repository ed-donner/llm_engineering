"""Unit tests for metadata vector database."""

import pytest
import tempfile
import shutil
from pathlib import Path

from setup_metadata_vectordb import MetadataVectorDB


@pytest.fixture
def temp_vectordb():
    """Create a temporary metadata vector database."""
    temp_dir = tempfile.mkdtemp()
    vectordb = MetadataVectorDB(persist_directory=temp_dir)
    
    yield vectordb
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestMetadataVectorDB:
    """Tests for MetadataVectorDB class."""
    
    def test_initialization(self, temp_vectordb):
        """Test vector DB initializes correctly."""
        assert temp_vectordb is not None
        assert temp_vectordb.colors_collection is not None
        assert temp_vectordb.breeds_collection is not None
    
    def test_index_colors(self, temp_vectordb):
        """Test indexing colors."""
        colors = ["Black", "White", "Black & White / Tuxedo", "Orange / Red"]
        
        temp_vectordb.index_colors(colors, source="petfinder")
        
        # Check indexed
        stats = temp_vectordb.get_stats()
        assert stats['colors_count'] == len(colors)
        
        # Should not re-index same source
        temp_vectordb.index_colors(colors, source="petfinder")
        stats = temp_vectordb.get_stats()
        assert stats['colors_count'] == len(colors)  # Should not double
    
    def test_index_breeds(self, temp_vectordb):
        """Test indexing breeds."""
        breeds = ["Siamese", "Persian", "Maine Coon", "Bengal"]
        
        temp_vectordb.index_breeds(breeds, source="petfinder")
        
        # Check indexed
        stats = temp_vectordb.get_stats()
        assert stats['breeds_count'] == len(breeds)
    
    def test_search_color_exact(self, temp_vectordb):
        """Test searching for exact color match."""
        colors = ["Black", "White", "Black & White / Tuxedo"]
        temp_vectordb.index_colors(colors, source="petfinder")
        
        # Search for exact match
        results = temp_vectordb.search_color("tuxedo", source_filter="petfinder")
        
        assert len(results) > 0
        assert results[0]['color'] == "Black & White / Tuxedo"
        assert results[0]['similarity'] > 0.5  # Should be reasonable similarity
    
    def test_search_color_fuzzy(self, temp_vectordb):
        """Test searching for color with typo."""
        colors = ["Black & White / Tuxedo", "Orange / Red", "Gray / Blue / Silver"]
        temp_vectordb.index_colors(colors, source="petfinder")
        
        # Search with typo
        results = temp_vectordb.search_color("tuxado", source_filter="petfinder")  # typo: tuxado
        
        assert len(results) > 0
        # Should still find tuxedo
        assert "Tuxedo" in results[0]['color'] or "tuxado" in results[0]['color'].lower()
    
    def test_search_breed_exact(self, temp_vectordb):
        """Test searching for exact breed match."""
        breeds = ["Siamese", "Persian", "Maine Coon"]
        temp_vectordb.index_breeds(breeds, source="petfinder")
        
        results = temp_vectordb.search_breed("siamese", source_filter="petfinder")
        
        assert len(results) > 0
        assert results[0]['breed'] == "Siamese"
        assert results[0]['similarity'] > 0.9  # Should be very high for exact match
    
    def test_search_breed_fuzzy(self, temp_vectordb):
        """Test searching for breed with typo."""
        breeds = ["Maine Coon", "Ragdoll", "British Shorthair"]
        temp_vectordb.index_breeds(breeds, source="petfinder")
        
        # Typo: "main coon" instead of "Maine Coon"
        results = temp_vectordb.search_breed("main coon", source_filter="petfinder")
        
        assert len(results) > 0
        assert "Maine" in results[0]['breed'] or "Coon" in results[0]['breed']
    
    def test_multiple_sources(self, temp_vectordb):
        """Test indexing from multiple sources."""
        petfinder_colors = ["Black", "White", "Tabby"]
        rescuegroups_colors = ["Black", "Grey", "Calico"]
        
        temp_vectordb.index_colors(petfinder_colors, source="petfinder")
        temp_vectordb.index_colors(rescuegroups_colors, source="rescuegroups")
        
        # Should have both indexed
        stats = temp_vectordb.get_stats()
        assert stats['colors_count'] == len(petfinder_colors) + len(rescuegroups_colors)
        
        # Search with source filter
        results = temp_vectordb.search_color("black", source_filter="petfinder")
        assert len(results) > 0
        assert results[0]['source'] == "petfinder"
    
    def test_empty_search(self, temp_vectordb):
        """Test searching with empty string."""
        colors = ["Black", "White"]
        temp_vectordb.index_colors(colors, source="petfinder")
        
        results = temp_vectordb.search_color("", source_filter="petfinder")
        assert len(results) == 0
        
        results = temp_vectordb.search_color(None, source_filter="petfinder")
        assert len(results) == 0
    
    def test_no_match(self, temp_vectordb):
        """Test search that returns no good matches."""
        colors = ["Black", "White"]
        temp_vectordb.index_colors(colors, source="petfinder")
        
        # Search for something very different
        results = temp_vectordb.search_color("xyzabc123", source_filter="petfinder")
        
        # Will return something (nearest neighbor) but with low similarity
        if len(results) > 0:
            assert results[0]['similarity'] < 0.5  # Low similarity
    
    def test_n_results(self, temp_vectordb):
        """Test returning multiple results."""
        colors = ["Black", "White", "Black & White / Tuxedo", "Gray / Blue / Silver"]
        temp_vectordb.index_colors(colors, source="petfinder")
        
        # Get top 3 results
        results = temp_vectordb.search_color("black", n_results=3, source_filter="petfinder")
        
        assert len(results) <= 3
        # First should be best match
        assert "Black" in results[0]['color']

