"""
Custom exceptions for synthetic data generator.

This module defines the exception hierarchy for handling various
error conditions throughout the application.
"""


class SynthDataError(Exception):
    """Base exception for synthetic data generator."""
    pass


class APIKeyError(SynthDataError):
    """Raised when API key is missing or invalid."""
    pass


class SchemaValidationError(SynthDataError):
    """Raised when schema validation fails."""
    pass


class GenerationError(SynthDataError):
    """Raised when data generation fails."""
    pass


class BackendError(SynthDataError):
    """Raised when backend operation fails."""
    pass
