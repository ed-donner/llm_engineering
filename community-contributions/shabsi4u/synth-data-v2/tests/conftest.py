"""
Pytest fixtures for testing.

Shared fixtures used across test modules.
"""

import pytest
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from synth_data.database.models import Base
from synth_data.database.service import DatabaseService


@pytest.fixture
def mock_database(db_session):
    """
    Provide a DatabaseService instance with in-memory database.

    Uses the db_session fixture to create a DatabaseService that
    operates on an in-memory SQLite database, ensuring test isolation.

    Returns:
        DatabaseService configured with in-memory database
    """
    return DatabaseService(session=db_session)


@pytest.fixture
def sample_schema() -> Dict[str, Any]:
    """Provide a sample schema for testing."""
    return {
        "name": {
            "type": "string",
            "description": "Person's full name"
        },
        "age": {
            "type": "integer",
            "description": "Age between 18 and 80"
        },
        "email": {
            "type": "string",
            "description": "Email address"
        }
    }


@pytest.fixture(scope="function")
def db_session():
    """
    Provide a clean in-memory database session for each test.

    Creates a fresh SQLite in-memory database for each test function,
    ensuring test isolation. The session is automatically closed after
    the test completes.

    Yields:
        SQLAlchemy Session connected to in-memory database
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Cleanup
    session.close()


@pytest.fixture
def mock_api_key() -> str:
    """Provide a mock API key for testing."""
    return "hf_test_key_12345"


@pytest.fixture
def sample_json_response() -> str:
    """Provide a sample JSON response."""
    return '''[
        {"name": "John Doe", "age": 30, "email": "john@example.com"},
        {"name": "Jane Smith", "age": 25, "email": "jane@example.com"}
    ]'''


@pytest.fixture
def sample_json_with_markdown() -> str:
    """Provide JSON response wrapped in markdown."""
    return '''```json
    [
        {"name": "John Doe", "age": 30, "email": "john@example.com"},
        {"name": "Jane Smith", "age": 25, "email": "jane@example.com"}
    ]
    ```'''
