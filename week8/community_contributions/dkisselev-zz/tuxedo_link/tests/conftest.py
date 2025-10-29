"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from database.manager import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temp path but don't create the file yet
    # This allows DatabaseManager to initialize it properly
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.unlink(path)  # Remove empty file so DatabaseManager can initialize it
    
    db = DatabaseManager(path)  # Tables are created automatically in __init__
    
    yield db
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def sample_cat_data():
    """Sample cat data for testing."""
    return {
        "id": "test123",
        "name": "Test Cat",
        "breed": "Persian",
        "age": "adult",
        "gender": "female",
        "size": "medium",
        "city": "Test City",
        "state": "TS",
        "source": "test",
        "organization_name": "Test Rescue",
        "url": "https://example.com/cat/test123"
    }

