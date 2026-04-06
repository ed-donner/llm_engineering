"""
Quick test script for backend implementation.

Run with: python test_backend.py
"""

import os
from dotenv import load_dotenv
from synth_data.backends import HuggingFaceAPIBackend, GenerationParams
from synth_data.config import configure_logging

# Load environment variables
load_dotenv()

# Configure logging
configure_logging("INFO")


def test_backend():
    """Test HuggingFace API backend."""
    print("\n" + "="*60)
    print("Testing HuggingFace API Backend")
    print("="*60 + "\n")

    # Get API key from environment
    api_key = os.getenv("HUGGINGFACE_API_KEY")

    if not api_key:
        print("ERROR: HUGGINGFACE_API_KEY not found in environment")
        print("Please set it in .env file or environment variables")
        return

    # Create backend
    print("1. Creating backend...")
    backend = HuggingFaceAPIBackend(api_key=api_key)
    print(f"   Model: {backend.model_id}")

    # Validate connection
    print("\n2. Validating connection...")
    is_valid = backend.validate_connection()
    print(f"   Connection valid: {is_valid}")

    if not is_valid:
        print("   ERROR: Cannot connect to API. Check your API key.")
        return

    # Define schema
    print("\n3. Defining schema...")
    schema = {
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
    print("   Schema defined with fields: name, age, email")

    # Generate data
    print("\n4. Generating 5 records...")
    params = GenerationParams(temperature=0.7, max_tokens=1024)

    result = backend.generate(
        schema=schema,
        num_records=5,
        params=params
    )

    # Display results
    print(f"\n5. Results:")
    print(f"   Success: {result.success}")
    print(f"   Records generated: {result.num_records}")

    if result.success and result.data:
        print(f"\n   Sample records:")
        for i, record in enumerate(result.data[:3], 1):
            print(f"   {i}. {record}")
    else:
        print(f"   Error: {result.error_message}")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_backend()
