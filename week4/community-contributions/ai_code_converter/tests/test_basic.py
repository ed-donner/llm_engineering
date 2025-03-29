"""Basic tests for CodeXchange AI application."""

import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai_code_converter.config import SUPPORTED_LANGUAGES, DOCUMENT_STYLES


def test_supported_languages():
    """Test that supported languages configuration is valid."""
    assert isinstance(SUPPORTED_LANGUAGES, list)
    assert len(SUPPORTED_LANGUAGES) > 0
    assert "Python" in SUPPORTED_LANGUAGES


def test_document_styles():
    """Test that document styles configuration is valid."""
    assert isinstance(DOCUMENT_STYLES, dict)
    assert len(DOCUMENT_STYLES) > 0
    
    # Check that each language has at least one document style
    for language in SUPPORTED_LANGUAGES:
        assert language in DOCUMENT_STYLES, f"{language} missing from document styles"
        assert isinstance(DOCUMENT_STYLES[language], list)
        assert len(DOCUMENT_STYLES[language]) > 0
