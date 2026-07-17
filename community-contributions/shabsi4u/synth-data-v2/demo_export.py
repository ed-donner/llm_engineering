"""
Demo script for ExportService.

Demonstrates:
1. Basic CSV, JSON, and JSONL exports
2. File export operations
3. Streaming large datasets
4. Exporting generation data
5. Export metadata tracking
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from synth_data.services.export import ExportService, ExportFormat


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def demo_basic_exports():
    """Demonstrate basic export functionality."""
    print_section("Demo 1: Basic Exports (CSV, JSON, JSONL)")

    service = ExportService()

    # Sample data
    data = [
        {"name": "Alice", "age": 30, "city": "New York", "role": "Engineer"},
        {"name": "Bob", "age": 25, "city": "San Francisco", "role": "Designer"},
        {"name": "Charlie", "age": 35, "city": "Boston", "role": "Manager"},
        {"name": "Diana", "age": 28, "city": "Seattle", "role": "Analyst"}
    ]

    print("Sample data:")
    for record in data:
        print(f"  {record}")

    # CSV Export
    print("\n1. CSV Export:")
    print("-" * 40)
    csv_content = service.to_csv(data)
    print(csv_content)

    # JSON Export (pretty-printed)
    print("\n2. JSON Export (pretty):")
    print("-" * 40)
    json_content = service.to_json(data, pretty=True)
    print(json_content[:200] + "..." if len(json_content) > 200 else json_content)

    # JSONL Export
    print("\n3. JSONL Export:")
    print("-" * 40)
    jsonl_content = service.to_jsonl(data)
    print(jsonl_content)


def demo_file_exports():
    """Demonstrate file export operations."""
    print_section("Demo 2: File Export Operations")

    service = ExportService()

    data = [
        {"product": "Laptop", "price": 1200, "stock": 15},
        {"product": "Mouse", "price": 25, "stock": 150},
        {"product": "Keyboard", "price": 75, "stock": 80}
    ]

    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    # Export to CSV file
    print("1. Exporting to CSV file...")
    csv_metadata = service.export_to_file(
        data,
        str(exports_dir / "products.csv"),
        ExportFormat.CSV
    )
    print(f"   File: {csv_metadata.file_path}")
    print(f"   Records: {csv_metadata.record_count}")
    print(f"   Size: {csv_metadata.file_size_bytes} bytes")
    print(f"   Timestamp: {csv_metadata.timestamp}")

    # Export to JSON file
    print("\n2. Exporting to JSON file...")
    json_metadata = service.export_to_file(
        data,
        str(exports_dir / "products.json"),
        ExportFormat.JSON,
        pretty=True
    )
    print(f"   File: {json_metadata.file_path}")
    print(f"   Records: {json_metadata.record_count}")
    print(f"   Size: {json_metadata.file_size_bytes} bytes")

    # Export to JSONL file
    print("\n3. Exporting to JSONL file...")
    jsonl_metadata = service.export_to_file(
        data,
        str(exports_dir / "products.jsonl"),
        ExportFormat.JSONL
    )
    print(f"   File: {jsonl_metadata.file_path}")
    print(f"   Records: {jsonl_metadata.record_count}")

    print(f"\nAll files saved to: {exports_dir.absolute()}")


def demo_streaming():
    """Demonstrate streaming exports for large datasets."""
    print_section("Demo 3: Streaming Large Datasets")

    service = ExportService()

    # Generate large dataset
    print("Generating 10,000 synthetic records...")
    large_data = [
        {
            "id": i,
            "name": f"User{i}",
            "email": f"user{i}@example.com",
            "score": i * 10 % 100,
            "active": i % 2 == 0
        }
        for i in range(10000)
    ]
    print(f"Generated {len(large_data)} records")

    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    # Stream to CSV file
    print("\n1. Streaming to CSV (chunk_size=1000)...")
    csv_path = exports_dir / "large_dataset.csv"

    with open(csv_path, "w") as f:
        chunk_count = 0
        for chunk in service.stream_to_csv(large_data, chunk_size=1000):
            f.write(chunk)
            chunk_count += 1
            if chunk_count <= 3:  # Show first few chunks
                print(f"   Chunk {chunk_count}: {len(chunk)} bytes written")

    file_size = csv_path.stat().st_size
    print(f"   Complete: {file_size:,} bytes written to {csv_path.name}")

    # Stream to JSONL file
    print("\n2. Streaming to JSONL (chunk_size=2000)...")
    jsonl_path = exports_dir / "large_dataset.jsonl"

    with open(jsonl_path, "w") as f:
        chunk_count = 0
        for chunk in service.stream_to_jsonl(large_data, chunk_size=2000):
            f.write(chunk)
            chunk_count += 1

    file_size = jsonl_path.stat().st_size
    print(f"   Complete: {file_size:,} bytes written to {jsonl_path.name}")

    print(f"\nStreaming allows processing large datasets without loading all data in memory!")


def demo_generation_export():
    """Demonstrate exporting generation data."""
    print_section("Demo 4: Exporting Generation Data")

    service = ExportService()

    # Simulate generation result from GeneratorService
    generation_result = {
        "generation_id": 42,
        "backend": "huggingface",
        "num_records": 5,
        "success": True,
        "data": [
            {"user": "alice123", "score": 95, "category": "premium"},
            {"user": "bob456", "score": 78, "category": "standard"},
            {"user": "charlie789", "score": 88, "category": "premium"},
            {"user": "diana012", "score": 65, "category": "basic"},
            {"user": "eve345", "score": 92, "category": "premium"}
        ]
    }

    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    # Export without generation metadata
    print("1. Export generation data (data only)...")
    metadata1 = service.export_generation_to_file(
        generation_result,
        str(exports_dir / "generation_42_data_only.json"),
        ExportFormat.JSON,
        include_generation_metadata=False,
        pretty=True
    )
    print(f"   Exported {metadata1.record_count} records")
    print(f"   File: {Path(metadata1.file_path).name}")

    # Export with generation metadata
    print("\n2. Export generation data (with metadata)...")
    metadata2 = service.export_generation_to_file(
        generation_result,
        str(exports_dir / "generation_42_with_metadata.json"),
        ExportFormat.JSON,
        include_generation_metadata=True
    )
    print(f"   Exported {metadata2.record_count} records")
    print(f"   File: {Path(metadata2.file_path).name}")
    print("   Metadata included: generation_id, backend, timestamp")

    # Show contents of file with metadata
    print("\n3. Contents of file with metadata:")
    print("-" * 40)
    with open(metadata2.file_path) as f:
        import json
        content = json.load(f)
        print(json.dumps(content, indent=2)[:400] + "...")


def demo_utility_functions():
    """Demonstrate utility functions."""
    print_section("Demo 5: Utility Functions")

    service = ExportService()

    print("1. Getting file extensions:")
    print(f"   CSV:   {service.get_export_extension(ExportFormat.CSV)}")
    print(f"   JSON:  {service.get_export_extension(ExportFormat.JSON)}")
    print(f"   JSONL: {service.get_export_extension(ExportFormat.JSONL)}")

    print("\n2. Suggesting filenames:")
    print(f"   With timestamp:    {service.suggest_filename(ExportFormat.CSV)}")
    print(f"   Without timestamp: {service.suggest_filename(ExportFormat.JSON, include_timestamp=False)}")
    print(f"   Custom prefix:     {service.suggest_filename(ExportFormat.JSONL, prefix='users')}")

    print("\n3. Export metadata tracking:")
    data = [{"name": "Test"}]
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    metadata = service.export_to_file(
        data,
        str(exports_dir / "test.csv"),
        ExportFormat.CSV
    )

    print(f"   Format:        {metadata.format.value}")
    print(f"   Record count:  {metadata.record_count}")
    print(f"   Timestamp:     {metadata.timestamp.isoformat()}")
    print(f"   File path:     {Path(metadata.file_path).name}")
    print(f"   File size:     {metadata.file_size_bytes} bytes")

    print("\n   Metadata as dict:")
    for key, value in metadata.to_dict().items():
        print(f"     {key}: {value}")


def demo_advanced_features():
    """Demonstrate advanced features."""
    print_section("Demo 6: Advanced Features")

    service = ExportService()

    # Unicode data
    print("1. Unicode character support:")
    unicode_data = [
        {"name": "José García", "city": "São Paulo", "country": "Brasil"},
        {"name": "李明", "city": "北京", "country": "中国"},
        {"name": "Müller", "city": "München", "country": "Deutschland"}
    ]

    csv_content = service.to_csv(unicode_data)
    print("   CSV export with unicode characters:")
    print(csv_content)

    # Custom CSV delimiter
    print("\n2. Custom CSV delimiter (semicolon):")
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    csv_semicolon = service.to_csv(data, delimiter=";")
    print(csv_semicolon)

    # JSON with metadata
    print("\n3. JSON with export metadata:")
    json_with_meta = service.to_json(
        data,
        include_metadata=True,
        pretty=True
    )
    print(json_with_meta)


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  EXPORT SERVICE DEMO")
    print("  Synthetic Data Generator v2 - Step 5")
    print("=" * 60)

    try:
        # Run all demos
        demo_basic_exports()
        demo_file_exports()
        demo_streaming()
        demo_generation_export()
        demo_utility_functions()
        demo_advanced_features()

        print("\n" + "=" * 60)
        print("  All demos completed successfully!")
        print("=" * 60 + "\n")

        # Show summary
        exports_dir = Path("exports")
        if exports_dir.exists():
            files = list(exports_dir.glob("*"))
            print(f"Generated files ({len(files)}):")
            for file in sorted(files):
                size = file.stat().st_size
                print(f"  - {file.name} ({size:,} bytes)")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
