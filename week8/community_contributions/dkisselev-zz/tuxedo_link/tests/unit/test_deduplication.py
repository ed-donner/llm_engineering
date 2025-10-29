"""Fixed unit tests for deduplication utilities."""

import pytest
from models.cats import Cat
from utils.deduplication import create_fingerprint, calculate_levenshtein_similarity, calculate_composite_score


class TestFingerprinting:
    """Tests for fingerprint generation."""
    
    def test_fingerprint_basic(self):
        """Test basic fingerprint generation."""
        cat = Cat(
            id="12345",
            name="Fluffy",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="petfinder",
            organization_name="Happy Paws Rescue",
            url="https://example.com/cat/12345"
        )
        
        fingerprint = create_fingerprint(cat)
        
        assert fingerprint is not None
        assert isinstance(fingerprint, str)
        # Fingerprint is a hash, so just verify it's a 16-character hex string
        assert len(fingerprint) == 16
        assert all(c in '0123456789abcdef' for c in fingerprint)
    
    def test_fingerprint_consistency(self):
        """Test that same cat produces same fingerprint."""
        cat1 = Cat(
            id="12345",
            name="Fluffy",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="petfinder",
            organization_name="Happy Paws",
            url="https://example.com/cat/12345"
        )
        
        cat2 = Cat(
            id="67890",
            name="Fluffy McGee",  # Different name
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="Boston",  # Different city
            state="MA",
            source="rescuegroups",  # Different source
            organization_name="Happy Paws",
            url="https://example.com/cat/67890"
        )
        
        # Should have same fingerprint (stable attributes match)
        assert create_fingerprint(cat1) == create_fingerprint(cat2)
    
    def test_fingerprint_difference(self):
        """Test that different cats produce different fingerprints."""
        cat1 = Cat(
            id="12345",
            name="Fluffy",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="petfinder",
            organization_name="Happy Paws",
            url="https://example.com/cat/12345"
        )
        
        cat2 = Cat(
            id="67890",
            name="Fluffy",
            breed="Persian",
            age="young",  # Different age
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="petfinder",
            organization_name="Happy Paws",
            url="https://example.com/cat/67890"
        )
        
        # Should have different fingerprints
        assert create_fingerprint(cat1) != create_fingerprint(cat2)


class TestLevenshteinSimilarity:
    """Tests for Levenshtein similarity calculation."""
    
    def test_identical_strings(self):
        """Test identical strings return 1.0."""
        similarity = calculate_levenshtein_similarity("Fluffy", "Fluffy")
        assert similarity == 1.0
    
    def test_completely_different_strings(self):
        """Test completely different strings return low score."""
        similarity = calculate_levenshtein_similarity("Fluffy", "12345")
        assert similarity < 0.2
    
    def test_similar_strings(self):
        """Test similar strings return high score."""
        similarity = calculate_levenshtein_similarity("Fluffy", "Fluffy2")
        assert similarity > 0.8
    
    def test_case_insensitive(self):
        """Test that comparison is case-insensitive."""
        similarity = calculate_levenshtein_similarity("Fluffy", "fluffy")
        assert similarity == 1.0
    
    def test_empty_strings(self):
        """Test empty strings - both empty is 0.0 similarity."""
        similarity = calculate_levenshtein_similarity("", "")
        assert similarity == 0.0  # Empty strings return 0.0 in implementation
        
        similarity = calculate_levenshtein_similarity("Fluffy", "")
        assert similarity == 0.0


class TestCompositeScore:
    """Tests for composite score calculation."""
    
    def test_composite_score_all_high(self):
        """Test composite score when all similarities are high."""
        score = calculate_composite_score(
            name_similarity=0.9,
            description_similarity=0.9,
            image_similarity=0.9,
            name_weight=0.4,
            description_weight=0.3,
            image_weight=0.3
        )
        
        assert score > 0.85
        assert score <= 1.0
    
    def test_composite_score_weighted(self):
        """Test that weights affect composite score correctly."""
        # Name has 100% weight
        score = calculate_composite_score(
            name_similarity=0.5,
            description_similarity=1.0,
            image_similarity=1.0,
            name_weight=1.0,
            description_weight=0.0,
            image_weight=0.0
        )
        
        assert score == 0.5
    
    def test_composite_score_zero_image(self):
        """Test composite score when no image similarity."""
        score = calculate_composite_score(
            name_similarity=0.9,
            description_similarity=0.9,
            image_similarity=0.0,
            name_weight=0.4,
            description_weight=0.3,
            image_weight=0.3
        )
        
        # Should still compute based on name and description
        assert score > 0.5
        assert score < 0.9
    
    def test_composite_score_bounds(self):
        """Test that composite score is always between 0 and 1."""
        score = calculate_composite_score(
            name_similarity=1.0,
            description_similarity=1.0,
            image_similarity=1.0,
            name_weight=0.4,
            description_weight=0.3,
            image_weight=0.3
        )
        
        assert 0.0 <= score <= 1.0


class TestTextSimilarity:
    """Integration tests for text similarity (name + description)."""
    
    def test_similar_cats_high_score(self):
        """Test that similar cats get high similarity scores."""
        cat1 = Cat(
            id="12345",
            name="Fluffy",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="petfinder",
            organization_name="Test Rescue",
            url="https://example.com/cat/12345",
            description="A very friendly and playful cat that loves to cuddle"
        )
        
        cat2 = Cat(
            id="67890",
            name="Fluffy",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="rescuegroups",
            organization_name="Test Rescue",
            url="https://example.com/cat/67890",
            description="Very friendly playful cat who loves cuddling"
        )
        
        name_sim = calculate_levenshtein_similarity(cat1.name, cat2.name)
        desc_sim = calculate_levenshtein_similarity(
            cat1.description or "",
            cat2.description or ""
        )
        
        assert name_sim == 1.0
        assert desc_sim > 0.7
    
    def test_different_cats_low_score(self):
        """Test that different cats get low similarity scores."""
        cat1 = Cat(
            id="12345",
            name="Fluffy",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="petfinder",
            organization_name="Test Rescue",
            url="https://example.com/cat/12345",
            description="Playful kitten"
        )
        
        cat2 = Cat(
            id="67890",
            name="Rex",
            breed="Siamese",
            age="young",
            gender="male",
            size="large",
            city="Boston",
            state="MA",
            source="rescuegroups",
            organization_name="Other Rescue",
            url="https://example.com/cat/67890",
            description="Calm senior cat"
        )
        
        name_sim = calculate_levenshtein_similarity(cat1.name, cat2.name)
        desc_sim = calculate_levenshtein_similarity(
            cat1.description or "",
            cat2.description or ""
        )
        
        assert name_sim < 0.3
        assert desc_sim < 0.5

