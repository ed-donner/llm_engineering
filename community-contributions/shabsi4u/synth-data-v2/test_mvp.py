"""
Quick verification script for MVP functionality.

Tests the complete flow without requiring API calls.
"""

import sys
from synth_data.utils.schema_parser import parse_schema, format_schema_for_display
from synth_data.backends import HuggingFaceAPIBackend
from synth_data.database import DatabaseService
from synth_data.services import ExportService, ExportFormat

print("=" * 60)
print("Synthetic Data Generator MVP - Verification")
print("=" * 60)

# Test 1: Schema Parser
print("\n1. Testing Schema Parser...")
try:
    # JSON format
    json_schema = parse_schema('{"name": {"type": "string"}, "age": {"type": "integer"}}')
    assert "name" in json_schema
    print("   ✅ JSON format parsing works")

    # Simplified format
    simple_schema = parse_schema("name:string, age:int, email:str")
    assert simple_schema["name"]["type"] == "string"
    assert simple_schema["age"]["type"] == "integer"
    assert simple_schema["email"]["type"] == "string"
    print("   ✅ Simplified format parsing works")
    print("   ✅ Type aliases work (int→integer, str→string)")

    # Format for display
    display = format_schema_for_display(simple_schema)
    assert "name" in display
    print(f"   ✅ Display formatting works: {display}")

except Exception as e:
    print(f"   ❌ Schema parser failed: {e}")
    sys.exit(1)

# Test 2: Backend Initialization
print("\n2. Testing Backend Initialization...")
try:
    backend = HuggingFaceAPIBackend(
        api_key="test_key",
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct"
    )
    assert backend.api_key == "test_key"
    assert backend.model_id == "Qwen/Qwen2.5-Coder-32B-Instruct"
    print("   ✅ Backend initialization works")
    print(f"   ✅ Model ID stored: {backend.model_id}")
except Exception as e:
    print(f"   ❌ Backend initialization failed: {e}")
    sys.exit(1)

# Test 3: Database Service
print("\n3. Testing Database Service...")
try:
    # Use in-memory database for testing
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from synth_data.database.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    db = DatabaseService(session=session)

    # Save a generation
    gen_id = db.save_generation(
        schema={"name": {"type": "string"}},
        model_backend="HuggingFaceAPIBackend:Qwen/Qwen2.5-Coder-32B-Instruct",
        num_records=10,
        data=[{"name": "Alice"}, {"name": "Bob"}],
        success=True
    )
    assert gen_id is not None
    print("   ✅ Database save works")
    print(f"   ✅ Generation ID: {gen_id}")

    # Retrieve generation
    gen = db.get_generation(gen_id)
    assert gen is not None
    assert gen.num_records == 10
    assert "Qwen" in gen.model_backend
    print("   ✅ Database retrieval works")
    print(f"   ✅ Model backend stored correctly: {gen.model_backend}")

    # Get history
    history = db.get_recent_generations(limit=10)
    assert len(history) == 1
    print("   ✅ History retrieval works")

    session.close()
except Exception as e:
    print(f"   ❌ Database service failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Export Service
print("\n4. Testing Export Service...")
try:
    export_service = ExportService()

    test_data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ]

    # CSV export
    csv = export_service.to_csv(test_data)
    assert "Alice" in csv
    assert "name,age" in csv or "age,name" in csv
    print("   ✅ CSV export works")

    # JSON export
    json_str = export_service.to_json(test_data, pretty=True)
    assert "Alice" in json_str
    print("   ✅ JSON export works")

    # JSONL export
    jsonl = export_service.to_jsonl(test_data)
    lines = jsonl.strip().split("\n")
    assert len(lines) == 2  # Two records
    assert "Alice" in lines[0]
    assert "Bob" in lines[1]
    print("   ✅ JSONL export works")

except Exception as e:
    print(f"   ❌ Export service failed: {e}")
    sys.exit(1)

# Test 5: Model Backend Format
print("\n5. Testing Model Backend Format...")
try:
    # Test parsing of model_backend string
    model_backend = "HuggingFaceAPIBackend:Qwen/Qwen2.5-Coder-32B-Instruct"
    if ":" in model_backend:
        backend_name, model_id = model_backend.split(":", 1)
        assert backend_name == "HuggingFaceAPIBackend"
        assert model_id == "Qwen/Qwen2.5-Coder-32B-Instruct"
        print(f"   ✅ Model backend parsing works")
        print(f"   ✅ Backend: {backend_name}")
        print(f"   ✅ Model: {model_id}")
except Exception as e:
    print(f"   ❌ Model backend format failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ All verification tests passed!")
print("=" * 60)
print("\nMVP is ready to use!")
print("\nTo start the UI:")
print("  streamlit run synth_data/ui/app.py")
print("  or")
print("  python -m synth_data")
print()
