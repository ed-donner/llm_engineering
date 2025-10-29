"""Fixed unit tests for data models."""

import pytest
from datetime import datetime
from models.cats import Cat, CatProfile, CatMatch, AdoptionAlert, SearchResult


class TestCat:
    """Tests for Cat model."""
    
    def test_cat_creation(self):
        """Test basic cat creation."""
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
            organization_name="Test Rescue",
            url="https://example.com/cat/12345"
        )
        
        assert cat.name == "Fluffy"
        assert cat.breed == "Persian"
        assert cat.age == "adult"
        assert cat.gender == "female"
        assert cat.size == "medium"
        assert cat.organization_name == "Test Rescue"
    
    def test_cat_with_optional_fields(self):
        """Test cat with all optional fields."""
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
            organization_name="Test Rescue",
            url="https://example.com/cat/12345",
            description="Very fluffy",
            primary_photo="http://example.com/photo.jpg",
            adoption_fee=150.00,
            good_with_children=True,
            good_with_dogs=False,
            good_with_cats=True
        )
        
        assert cat.description == "Very fluffy"
        assert cat.adoption_fee == 150.00
        assert cat.good_with_children is True
    
    def test_cat_from_json(self):
        """Test cat deserialization from JSON."""
        json_data = """
        {
            "id": "12345",
            "name": "Fluffy",
            "breed": "Persian",
            "age": "adult",
            "gender": "female",
            "size": "medium",
            "city": "New York",
            "state": "NY",
            "source": "petfinder",
            "organization_name": "Test Rescue",
            "url": "https://example.com/cat/12345"
        }
        """
        
        cat = Cat.model_validate_json(json_data)
        assert cat.name == "Fluffy"
        assert cat.id == "12345"


class TestCatProfile:
    """Tests for CatProfile model."""
    
    def test_profile_creation_minimal(self):
        """Test profile with minimal fields."""
        profile = CatProfile()
        
        assert profile.personality_description == ""  # Defaults to empty string
        assert profile.max_distance == 100
        assert profile.age_range is None  # No default
    
    def test_profile_creation_full(self):
        """Test profile with all fields."""
        profile = CatProfile(
            user_location="10001",
            max_distance=50,
            personality_description="friendly and playful",
            age_range=["young", "adult"],
            size=["small", "medium"],
            good_with_children=True,
            good_with_dogs=True,
            good_with_cats=False
        )
        
        assert profile.user_location == "10001"
        assert profile.max_distance == 50
        assert "young" in profile.age_range
        assert profile.good_with_children is True


class TestCatMatch:
    """Tests for CatMatch model."""
    
    def test_match_creation(self):
        """Test match creation."""
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
            organization_name="Test Rescue",
            url="https://example.com/cat/12345"
        )
        
        match = CatMatch(
            cat=cat,
            match_score=0.85,
            vector_similarity=0.9,
            attribute_match_score=0.8,
            explanation="Great personality match"
        )
        
        assert match.cat.name == "Fluffy"
        assert match.match_score == 0.85
        assert "personality" in match.explanation


class TestAdoptionAlert:
    """Tests for AdoptionAlert model."""
    
    def test_alert_creation(self):
        """Test alert creation."""
        cat_profile = CatProfile(
            user_location="10001",
            personality_description="friendly"
        )
        
        alert = AdoptionAlert(
            user_id=1,
            user_email="test@example.com",
            profile=cat_profile,  # Correct field name
            frequency="daily"
        )
        
        assert alert.user_email == "test@example.com"
        assert alert.frequency == "daily"
        assert alert.active is True


class TestSearchResult:
    """Tests for SearchResult model."""
    
    def test_search_result_creation(self):
        """Test search result creation."""
        profile = CatProfile(user_location="10001")
        
        result = SearchResult(
            matches=[],
            total_found=0,
            search_profile=profile,
            search_time=1.23,
            sources_queried=["petfinder"],
            duplicates_removed=0
        )
        
        assert result.total_found == 0
        assert result.search_time == 1.23
        assert "petfinder" in result.sources_queried

