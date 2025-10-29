"""Integration tests for alert management system."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from database.manager import DatabaseManager
from models.cats import AdoptionAlert, CatProfile


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Unlink so DatabaseManager can initialize it
    Path(db_path).unlink()
    
    db_manager = DatabaseManager(db_path)
    
    yield db_manager
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_profile():
    """Create a sample cat profile for testing."""
    return CatProfile(
        user_location="New York, NY",
        max_distance=25,
        age_range=["young", "adult"],
        good_with_children=True,
        good_with_dogs=False,
        good_with_cats=True,
        personality_description="Friendly and playful",
        special_requirements=[]
    )


class TestAlertManagement:
    """Tests for alert management without user authentication."""
    
    def test_create_alert_without_user(self, temp_db, sample_profile):
        """Test creating an alert without user authentication."""
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=sample_profile,
            frequency="daily",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        
        assert alert_id is not None
        assert alert_id > 0
    
    def test_get_alert_by_id(self, temp_db, sample_profile):
        """Test retrieving an alert by ID."""
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=sample_profile,
            frequency="weekly",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        retrieved_alert = temp_db.get_alert(alert_id)
        
        assert retrieved_alert is not None
        assert retrieved_alert.id == alert_id
        assert retrieved_alert.user_email == "test@example.com"
        assert retrieved_alert.frequency == "weekly"
        assert retrieved_alert.profile.user_location == "New York, NY"
    
    def test_get_alerts_by_email(self, temp_db, sample_profile):
        """Test retrieving all alerts for a specific email."""
        email = "user@example.com"
        
        # Create multiple alerts for the same email
        for freq in ["daily", "weekly", "immediately"]:
            alert = AdoptionAlert(
                user_email=email,
                profile=sample_profile,
                frequency=freq,
                active=True
            )
            temp_db.create_alert(alert)
        
        # Create alert for different email
        other_alert = AdoptionAlert(
            user_email="other@example.com",
            profile=sample_profile,
            frequency="daily",
            active=True
        )
        temp_db.create_alert(other_alert)
        
        # Retrieve alerts for specific email
        alerts = temp_db.get_alerts_by_email(email)
        
        assert len(alerts) == 3
        assert all(a.user_email == email for a in alerts)
    
    def test_get_all_alerts(self, temp_db, sample_profile):
        """Test retrieving all alerts in the database."""
        # Create alerts for different emails
        for email in ["user1@test.com", "user2@test.com", "user3@test.com"]:
            alert = AdoptionAlert(
                user_email=email,
                profile=sample_profile,
                frequency="daily",
                active=True
            )
            temp_db.create_alert(alert)
        
        all_alerts = temp_db.get_all_alerts()
        
        assert len(all_alerts) == 3
        assert len(set(a.user_email for a in all_alerts)) == 3
    
    def test_get_active_alerts(self, temp_db, sample_profile):
        """Test retrieving only active alerts."""
        # Create active alerts
        for i in range(3):
            alert = AdoptionAlert(
                user_email=f"user{i}@test.com",
                profile=sample_profile,
                frequency="daily",
                active=True
            )
            temp_db.create_alert(alert)
        
        # Create inactive alert
        inactive_alert = AdoptionAlert(
            user_email="inactive@test.com",
            profile=sample_profile,
            frequency="weekly",
            active=False
        )
        alert_id = temp_db.create_alert(inactive_alert)
        
        # Deactivate it
        temp_db.update_alert(alert_id, active=False)
        
        active_alerts = temp_db.get_active_alerts()
        
        # Should only get the 3 active alerts
        assert len(active_alerts) == 3
        assert all(a.active for a in active_alerts)
    
    def test_update_alert_frequency(self, temp_db, sample_profile):
        """Test updating alert frequency."""
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=sample_profile,
            frequency="daily",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        
        # Update frequency
        temp_db.update_alert(alert_id, frequency="weekly")
        
        updated_alert = temp_db.get_alert(alert_id)
        assert updated_alert.frequency == "weekly"
    
    def test_update_alert_last_sent(self, temp_db, sample_profile):
        """Test updating alert last_sent timestamp."""
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=sample_profile,
            frequency="daily",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        
        # Update last_sent
        now = datetime.now()
        temp_db.update_alert(alert_id, last_sent=now)
        
        updated_alert = temp_db.get_alert(alert_id)
        assert updated_alert.last_sent is not None
        # Compare with some tolerance
        assert abs((updated_alert.last_sent - now).total_seconds()) < 2
    
    def test_update_alert_match_ids(self, temp_db, sample_profile):
        """Test updating alert last_match_ids."""
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=sample_profile,
            frequency="daily",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        
        # Update match IDs
        match_ids = ["cat-123", "cat-456", "cat-789"]
        temp_db.update_alert(alert_id, last_match_ids=match_ids)
        
        updated_alert = temp_db.get_alert(alert_id)
        assert updated_alert.last_match_ids == match_ids
    
    def test_toggle_alert_active_status(self, temp_db, sample_profile):
        """Test toggling alert active/inactive."""
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=sample_profile,
            frequency="daily",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        
        # Deactivate
        temp_db.update_alert(alert_id, active=False)
        assert temp_db.get_alert(alert_id).active is False
        
        # Reactivate
        temp_db.update_alert(alert_id, active=True)
        assert temp_db.get_alert(alert_id).active is True
    
    def test_delete_alert(self, temp_db, sample_profile):
        """Test deleting an alert."""
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=sample_profile,
            frequency="daily",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        
        # Verify alert exists
        assert temp_db.get_alert(alert_id) is not None
        
        # Delete alert
        temp_db.delete_alert(alert_id)
        
        # Verify alert is gone
        assert temp_db.get_alert(alert_id) is None
    
    def test_multiple_alerts_same_email(self, temp_db, sample_profile):
        """Test creating multiple alerts for the same email address."""
        email = "test@example.com"
        
        # Create alerts with different frequencies
        for freq in ["immediately", "daily", "weekly"]:
            alert = AdoptionAlert(
                user_email=email,
                profile=sample_profile,
                frequency=freq,
                active=True
            )
            temp_db.create_alert(alert)
        
        alerts = temp_db.get_alerts_by_email(email)
        
        assert len(alerts) == 3
        frequencies = {a.frequency for a in alerts}
        assert frequencies == {"immediately", "daily", "weekly"}
    
    def test_alert_profile_persistence(self, temp_db):
        """Test that complex profile data persists correctly."""
        complex_profile = CatProfile(
            user_location="San Francisco, CA",
            max_distance=50,
            age_range=["kitten", "young"],
            size=["small", "medium"],
            preferred_breeds=["Siamese", "Persian"],
            good_with_children=True,
            good_with_dogs=True,
            good_with_cats=False,
            special_needs_ok=False,
            personality_description="Calm and affectionate lap cat"
        )
        
        alert = AdoptionAlert(
            user_email="test@example.com",
            profile=complex_profile,
            frequency="daily",
            active=True
        )
        
        alert_id = temp_db.create_alert(alert)
        retrieved_alert = temp_db.get_alert(alert_id)
        
        # Verify all profile fields persisted correctly
        assert retrieved_alert.profile.user_location == "San Francisco, CA"
        assert retrieved_alert.profile.max_distance == 50
        assert retrieved_alert.profile.age_range == ["kitten", "young"]
        assert retrieved_alert.profile.size == ["small", "medium"]
        assert retrieved_alert.profile.gender == ["female"]
        assert retrieved_alert.profile.breed == ["Siamese", "Persian"]
        assert retrieved_alert.profile.good_with_children is True
        assert retrieved_alert.profile.good_with_dogs is True
        assert retrieved_alert.profile.good_with_cats is False
        assert retrieved_alert.profile.personality_description == "Calm and affectionate lap cat"
        assert retrieved_alert.profile.special_requirements == ["indoor-only", "senior-friendly"]

