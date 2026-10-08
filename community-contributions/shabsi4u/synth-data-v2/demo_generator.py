"""
Demo script showing how to use the GeneratorService.

This demonstrates the complete workflow from configuration to data generation.
Run with: uv run python demo_generator.py
"""

import os
import json
from dotenv import load_dotenv

from synth_data.backends import HuggingFaceAPIBackend
from synth_data.services import GeneratorService
from synth_data.backends.base import GenerationParams

# Load environment variables
load_dotenv()


def demo_basic_generation():
    """Demonstrate basic data generation."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Data Generation")
    print("="*60)

    # Get API key from environment
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        print("Error: HUGGINGFACE_API_KEY not set in .env file")
        print("Please add your API key to .env file:")
        print("  HUGGINGFACE_API_KEY=hf_xxx")
        return

    # Step 1: Create backend
    print("\n1. Creating HuggingFace API backend...")
    backend = HuggingFaceAPIBackend(
        api_key=api_key,
        model_id="meta-llama/Llama-3.2-3B-Instruct"
    )

    # Step 2: Create generator service
    print("2. Creating GeneratorService...")
    service = GeneratorService(
        backend=backend,
        save_to_db=True  # Enable database persistence
    )

    # Step 3: Define schema
    print("3. Defining schema...")
    schema = {
        "name": {
            "type": "string",
            "description": "Person's full name"
        },
        "age": {
            "type": "integer",
            "description": "Age between 25 and 45"
        },
        "occupation": {
            "type": "string",
            "description": "Job title or profession"
        }
    }
    print(f"   Schema: {json.dumps(schema, indent=2)}")

    # Step 4: Generate data with progress callback
    print("\n4. Generating 5 synthetic records...")

    def show_progress(current, total):
        """Display progress bar."""
        percent = (current / total) * 100
        bar_length = 40
        filled = int(bar_length * current / total)
        bar = "█" * filled + "-" * (bar_length - filled)
        print(f"\r   Progress: [{bar}] {percent:.0f}%", end="", flush=True)

    try:
        result = service.generate(
            schema=schema,
            num_records=5,
            on_progress=show_progress
        )

        print()  # New line after progress bar

        # Step 5: Display results
        if result["success"]:
            print("\n5. Generation successful!")
            print(f"   Generation ID: {result['generation_id']}")
            print(f"   Records generated: {result['num_records']}")
            print(f"   Backend used: {result['backend']}")

            print("\n   Generated data:")
            for i, record in enumerate(result["data"], 1):
                print(f"   {i}. {record}")

        else:
            print(f"\nGeneration failed: {result['error_message']}")

    finally:
        service.close()


def demo_history_retrieval():
    """Demonstrate history retrieval."""
    print("\n" + "="*60)
    print("DEMO 2: Generation History")
    print("="*60)

    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        print("Skipping (no API key)")
        return

    backend = HuggingFaceAPIBackend(api_key=api_key)
    service = GeneratorService(backend=backend, save_to_db=True)

    try:
        # Get recent history
        print("\n1. Retrieving recent generation history...")
        history = service.get_history(limit=5)

        if not history:
            print("   No generation history found")
        else:
            print(f"   Found {len(history)} recent generations:")
            for gen in history:
                status = "✓" if gen["success"] else "✗"
                print(f"   {status} ID {gen['id']}: "
                      f"{gen['num_records']} records "
                      f"({gen['created_at']})")

    finally:
        service.close()


def demo_custom_parameters():
    """Demonstrate custom generation parameters."""
    print("\n" + "="*60)
    print("DEMO 3: Custom Generation Parameters")
    print("="*60)

    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        print("Skipping (no API key)")
        return

    backend = HuggingFaceAPIBackend(api_key=api_key)
    service = GeneratorService(backend=backend, save_to_db=False)

    # Use custom parameters for more creative output
    params = GenerationParams(
        temperature=0.9,  # Higher = more creative/random
        max_tokens=1000,
        top_p=0.95
    )

    schema = {
        "product_name": {
            "type": "string",
            "description": "Creative product name"
        },
        "tagline": {
            "type": "string",
            "description": "Catchy marketing tagline"
        }
    }

    print("\n1. Generating with high temperature (0.9) for creativity...")
    print(f"   Parameters: {params}")

    try:
        result = service.generate(
            schema=schema,
            num_records=3,
            params=params
        )

        if result["success"]:
            print("\n2. Creative results:")
            for i, record in enumerate(result["data"], 1):
                print(f"   {i}. {record['product_name']}")
                print(f"      '{record['tagline']}'")
                print()

    finally:
        service.close()


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n" + "="*60)
    print("DEMO 4: Error Handling")
    print("="*60)

    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        print("Skipping (no API key)")
        return

    backend = HuggingFaceAPIBackend(api_key=api_key)
    service = GeneratorService(backend=backend, save_to_db=True)

    print("\n1. Attempting generation with invalid schema...")

    # Invalid schema (empty)
    try:
        result = service.generate(schema={}, num_records=5)
        print("   Unexpected: should have raised error")
    except Exception as e:
        print(f"   ✓ Caught error: {type(e).__name__}: {e}")

    # Valid schema but check if failure is saved
    print("\n2. Valid schema but simulating API failure...")
    print("   (Failed generations are saved to database for debugging)")

    service.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("GeneratorService Demo")
    print("="*60)
    print("\nThis demo shows how to use the GeneratorService to generate")
    print("synthetic data and manage generation history.")

    # Check for API key first
    if not os.getenv("HUGGINGFACE_API_KEY"):
        print("\n⚠️  WARNING: HUGGINGFACE_API_KEY not found in environment")
        print("\nTo run these demos:")
        print("1. Create a .env file in the project root")
        print("2. Add: HUGGINGFACE_API_KEY=hf_your_key_here")
        print("3. Run again: uv run python demo_generator.py")
        exit(1)

    # Run demos
    demo_basic_generation()
    demo_history_retrieval()
    demo_custom_parameters()
    demo_error_handling()

    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)
    print("\nNext steps:")
    print("- Check the generated synth_data.db database")
    print("- Run tests: uv run pytest tests/test_generator.py -v")
    print("- Build the Streamlit UI (next phase)")
    print()
