"""
Quick test script for database implementation.

Run with: python test_database.py
"""

from synth_data.database import DatabaseService
from synth_data.config import configure_logging

# Configure logging
configure_logging("INFO")


def test_database():
    """Test DatabaseService functionality."""
    print("\n" + "="*60)
    print("Testing Database Service")
    print("="*60 + "\n")

    # Create service (will create synth_data.db in current directory)
    print("1. Creating database service...")
    service = DatabaseService()
    print("   Database initialized: synth_data.db")

    # Define test schema
    print("\n2. Defining test schema...")
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
    print("   Schema: name, age, email")

    # Save successful generation
    print("\n3. Saving successful generation...")
    test_data = [
        {"name": "Alice Johnson", "age": 28, "email": "alice@example.com"},
        {"name": "Bob Smith", "age": 35, "email": "bob@example.com"},
        {"name": "Carol White", "age": 42, "email": "carol@example.com"}
    ]

    gen_id_1 = service.save_generation(
        schema=schema,
        model_backend="huggingface",
        num_records=3,
        data=test_data,
        success=True
    )
    print(f"   Saved generation ID: {gen_id_1}")

    # Save failed generation
    print("\n4. Saving failed generation...")
    gen_id_2 = service.save_generation(
        schema=schema,
        model_backend="huggingface",
        num_records=5,
        data=None,
        success=False,
        error_message="API timeout error"
    )
    print(f"   Saved failed generation ID: {gen_id_2}")

    # Retrieve by ID
    print("\n5. Retrieving generation by ID...")
    generation = service.get_generation(gen_id_1)
    if generation:
        print(f"   ID: {generation.id}")
        print(f"   Backend: {generation.model_backend}")
        print(f"   Records: {generation.num_records}")
        print(f"   Success: {generation.success}")
        print(f"   Created: {generation.created_at}")

    # Get recent generations
    print("\n6. Getting recent generations...")
    recent = service.get_recent_generations(limit=5)
    print(f"   Found {len(recent)} generations:")
    for gen in recent:
        status = "SUCCESS" if gen.success else "FAILED"
        print(f"   - ID {gen.id}: {gen.num_records} records, "
              f"{gen.model_backend}, {status}")

    # Filter successful only
    print("\n7. Getting successful generations only...")
    successful = service.get_recent_generations(success_only=True)
    print(f"   Found {len(successful)} successful generations")

    # Count generations
    print("\n8. Counting generations...")
    total = service.count_generations()
    hf_count = service.count_generations(backend="huggingface")
    print(f"   Total generations: {total}")
    print(f"   HuggingFace generations: {hf_count}")

    # Convert to dict
    print("\n9. Converting to dictionary...")
    gen_dict = generation.to_dict()
    print(f"   Dictionary keys: {list(gen_dict.keys())}")

    # Cleanup
    print("\n10. Cleaning up...")
    service.close()
    print("   Database service closed")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)
    print("\nDatabase file created: synth_data.db")
    print("You can inspect it with: sqlite3 synth_data.db")
    print("Or delete it with: rm synth_data.db\n")


if __name__ == "__main__":
    test_database()
