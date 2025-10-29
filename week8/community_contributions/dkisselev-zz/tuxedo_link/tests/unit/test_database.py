"""Fixed unit tests for database manager."""

import pytest
from models.cats import Cat, CatProfile, AdoptionAlert


class TestDatabaseInitialization:
    """Tests for database initialization."""
    
    def test_database_creation(self, temp_db):
        """Test that database is created with tables."""
        assert temp_db.db_path.endswith('.db')
        
        # Check that tables exist
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row['name'] for row in cursor.fetchall()}
        
        assert 'alerts' in tables
        assert 'cats_cache' in tables
    
    def test_get_connection(self, temp_db):
        """Test database connection."""
        with temp_db.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1


class TestCatCaching:
    """Tests for cat caching operations."""
    
    def test_cache_cat(self, temp_db, sample_cat_data):
        """Test caching a cat."""
        from utils.deduplication import create_fingerprint
        
        cat = Cat(**sample_cat_data)
        cat.fingerprint = create_fingerprint(cat)  # Generate fingerprint
        temp_db.cache_cat(cat, None)
        
        # Verify cat was cached
        cats = temp_db.get_all_cached_cats()
        assert len(cats) == 1
        assert cats[0].name == "Test Cat"
    
    def test_cache_cat_with_embedding(self, temp_db, sample_cat_data):
        """Test caching a cat with image embedding."""
        import numpy as np
        from utils.deduplication import create_fingerprint
        
        cat = Cat(**sample_cat_data)
        cat.fingerprint = create_fingerprint(cat)  # Generate fingerprint
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        temp_db.cache_cat(cat, embedding)
        
        # Verify embedding was saved
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT image_embedding FROM cats_cache WHERE id = ?",
                (cat.id,)
            )
            row = cursor.fetchone()
            assert row['image_embedding'] is not None
    
    def test_get_cats_by_fingerprint(self, temp_db):
        """Test retrieving cats by fingerprint."""
        cat1 = Cat(
            id="test1",
            name="Cat 1",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="Test City",
            state="TS",
            source="test",
            organization_name="Test Rescue",
            url="https://example.com/cat/test1",
            fingerprint="test_fingerprint"
        )
        
        cat2 = Cat(
            id="test2",
            name="Cat 2",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="Test City",
            state="TS",
            source="test",
            organization_name="Test Rescue",
            url="https://example.com/cat/test2",
            fingerprint="test_fingerprint"
        )
        
        temp_db.cache_cat(cat1, None)
        temp_db.cache_cat(cat2, None)
        
        results = temp_db.get_cats_by_fingerprint("test_fingerprint")
        assert len(results) == 2
    
    def test_mark_as_duplicate(self, temp_db):
        """Test marking a cat as duplicate."""
        from utils.deduplication import create_fingerprint
        
        cat1 = Cat(
            id="original",
            name="Original",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="Test City",
            state="TS",
            source="test",
            organization_name="Test Rescue",
            url="https://example.com/cat/original"
        )
        cat1.fingerprint = create_fingerprint(cat1)
        
        cat2 = Cat(
            id="duplicate",
            name="Duplicate",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="Test City",
            state="TS",
            source="test",
            organization_name="Test Rescue",
            url="https://example.com/cat/duplicate"
        )
        cat2.fingerprint = create_fingerprint(cat2)
        
        temp_db.cache_cat(cat1, None)
        temp_db.cache_cat(cat2, None)
        
        temp_db.mark_as_duplicate("duplicate", "original")
        
        # Check duplicate is marked
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_duplicate, duplicate_of FROM cats_cache WHERE id = ?",
                ("duplicate",)
            )
            row = cursor.fetchone()
            assert row['is_duplicate'] == 1
            assert row['duplicate_of'] == "original"
    
    def test_get_cache_stats(self, temp_db):
        """Test getting cache statistics."""
        from utils.deduplication import create_fingerprint
        
        cat1 = Cat(
            id="test1",
            name="Cat 1",
            breed="Persian",
            age="adult",
            gender="female",
            size="medium",
            city="Test City",
            state="TS",
            source="petfinder",
            organization_name="Test Rescue",
            url="https://example.com/cat/test1"
        )
        cat1.fingerprint = create_fingerprint(cat1)
        
        cat2 = Cat(
            id="test2",
            name="Cat 2",
            breed="Siamese",
            age="young",
            gender="male",
            size="small",
            city="Test City",
            state="TS",
            source="rescuegroups",
            organization_name="Other Rescue",
            url="https://example.com/cat/test2"
        )
        cat2.fingerprint = create_fingerprint(cat2)
        
        temp_db.cache_cat(cat1, None)
        temp_db.cache_cat(cat2, None)
        
        stats = temp_db.get_cache_stats()
        
        assert stats['total_unique'] == 2
        assert stats['sources'] == 2
        assert 'petfinder' in stats['by_source']
        assert 'rescuegroups' in stats['by_source']


class TestAlertManagement:
    """Tests for alert management operations."""
    
    def test_create_alert(self, temp_db):
        """Test creating an alert."""
        profile = CatProfile(user_location="10001")
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=profile,
            frequency="daily"
        )
        
        alert_id = temp_db.create_alert(alert)
        
        assert alert_id is not None
        assert alert_id > 0
    
    def test_get_alerts_by_email(self, temp_db):
        """Test retrieving alerts by email."""
        profile = CatProfile(user_location="10001")
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=profile,
            frequency="daily"
        )
        
        temp_db.create_alert(alert)
        
        alerts = temp_db.get_alerts_by_email("test@example.com")
        
        assert len(alerts) > 0
        assert alerts[0].user_email == "test@example.com"

