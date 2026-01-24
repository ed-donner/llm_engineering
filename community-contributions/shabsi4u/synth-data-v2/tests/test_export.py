"""
Tests for ExportService.

Test coverage:
- CSV export functionality
- JSON export functionality
- JSONL export functionality
- File export operations
- Streaming exports
- Export metadata
- Error handling
"""

import pytest
import json
import csv
from io import StringIO
from pathlib import Path
import tempfile

from synth_data.services.export import (
    ExportService,
    ExportFormat,
    ExportMetadata
)


@pytest.fixture
def export_service():
    """Provide an ExportService instance."""
    return ExportService()


@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
    return [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "San Francisco"},
        {"name": "Charlie", "age": 35, "city": "Boston"}
    ]


@pytest.fixture
def large_data():
    """Provide large dataset for streaming tests."""
    return [
        {"id": i, "name": f"User{i}", "value": i * 10}
        for i in range(5000)
    ]


class TestCSVExport:
    """Test CSV export functionality."""

    def test_to_csv_basic(self, export_service, sample_data):
        """Test basic CSV export."""
        csv_content = export_service.to_csv(sample_data)

        # Parse CSV back to verify
        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == "30"
        assert rows[0]["city"] == "New York"

    def test_to_csv_with_header(self, export_service, sample_data):
        """Test CSV export includes header."""
        csv_content = export_service.to_csv(sample_data, include_header=True)

        lines = csv_content.strip().split("\n")
        # FIX: Fields are now sorted alphabetically for consistency
        assert lines[0] == "age,city,name"
        assert len(lines) == 4  # header + 3 data rows

    def test_to_csv_without_header(self, export_service, sample_data):
        """Test CSV export without header."""
        csv_content = export_service.to_csv(sample_data, include_header=False)

        lines = csv_content.strip().split("\n")
        assert len(lines) == 3  # No header, just data

    def test_to_csv_custom_delimiter(self, export_service, sample_data):
        """Test CSV export with custom delimiter."""
        csv_content = export_service.to_csv(sample_data, delimiter=";")

        lines = csv_content.strip().split("\n")
        assert ";" in lines[0]
        # FIX: Fields are now sorted alphabetically for consistency
        assert lines[0] == "age;city;name"

    def test_to_csv_empty_data_raises(self, export_service):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="Cannot export empty data"):
            export_service.to_csv([])


class TestJSONExport:
    """Test JSON export functionality."""

    def test_to_json_basic(self, export_service, sample_data):
        """Test basic JSON export."""
        json_content = export_service.to_json(sample_data)

        # Parse JSON back to verify
        data = json.loads(json_content)

        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == 30

    def test_to_json_pretty(self, export_service, sample_data):
        """Test pretty-printed JSON export."""
        json_content = export_service.to_json(sample_data, pretty=True)

        # Pretty printing adds newlines and indentation
        assert "\n" in json_content
        assert "  " in json_content  # Indentation

        # Should still be valid JSON
        data = json.loads(json_content)
        assert len(data) == 3

    def test_to_json_with_metadata(self, export_service, sample_data):
        """Test JSON export with metadata."""
        json_content = export_service.to_json(
            sample_data,
            include_metadata=True
        )

        result = json.loads(json_content)

        assert "data" in result
        assert "metadata" in result
        assert result["metadata"]["record_count"] == 3
        assert result["metadata"]["format"] == "json"
        assert "export_timestamp" in result["metadata"]

    def test_to_json_empty_data_raises(self, export_service):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="Cannot export empty data"):
            export_service.to_json([])


class TestJSONLExport:
    """Test JSONL (JSON Lines) export functionality."""

    def test_to_jsonl_basic(self, export_service, sample_data):
        """Test basic JSONL export."""
        jsonl_content = export_service.to_jsonl(sample_data)

        # Each line should be valid JSON
        lines = jsonl_content.strip().split("\n")
        assert len(lines) == 3

        # Parse each line
        records = [json.loads(line) for line in lines]
        assert records[0]["name"] == "Alice"
        assert records[1]["name"] == "Bob"
        assert records[2]["name"] == "Charlie"

    def test_to_jsonl_format(self, export_service, sample_data):
        """Test JSONL format structure."""
        jsonl_content = export_service.to_jsonl(sample_data)

        lines = jsonl_content.strip().split("\n")

        # Each line should be compact JSON (no newlines within)
        for line in lines:
            assert "\n" not in line
            data = json.loads(line)
            assert isinstance(data, dict)

    def test_to_jsonl_empty_data_raises(self, export_service):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="Cannot export empty data"):
            export_service.to_jsonl([])


class TestFileExport:
    """Test file export functionality."""

    def test_export_to_file_csv(self, export_service, sample_data):
        """Test exporting to CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.csv"

            metadata = export_service.export_to_file(
                sample_data,
                str(file_path),
                ExportFormat.CSV
            )

            # Check metadata
            assert metadata.format == ExportFormat.CSV
            assert metadata.record_count == 3
            assert metadata.file_path == str(file_path.absolute())
            assert metadata.file_size_bytes > 0

            # Verify file contents
            assert file_path.exists()
            content = file_path.read_text()
            assert "Alice" in content

    def test_export_to_file_json(self, export_service, sample_data):
        """Test exporting to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"

            metadata = export_service.export_to_file(
                sample_data,
                str(file_path),
                ExportFormat.JSON,
                pretty=True
            )

            assert metadata.format == ExportFormat.JSON
            assert file_path.exists()

            # Verify valid JSON
            with open(file_path) as f:
                data = json.load(f)
            assert len(data) == 3

    def test_export_to_file_jsonl(self, export_service, sample_data):
        """Test exporting to JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"

            metadata = export_service.export_to_file(
                sample_data,
                str(file_path),
                ExportFormat.JSONL
            )

            assert metadata.format == ExportFormat.JSONL
            assert file_path.exists()

            # Verify JSONL format
            lines = file_path.read_text().strip().split("\n")
            assert len(lines) == 3

    def test_export_creates_directory(self, export_service, sample_data):
        """Test that export creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "nested" / "test.csv"

            metadata = export_service.export_to_file(
                sample_data,
                str(file_path),
                ExportFormat.CSV
            )

            assert file_path.exists()
            assert file_path.parent.exists()

    def test_export_to_file_empty_data_raises(self, export_service):
        """Test that exporting empty data raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.csv"

            with pytest.raises(ValueError, match="Cannot export empty data"):
                export_service.export_to_file(
                    [],
                    str(file_path),
                    ExportFormat.CSV
                )


class TestStreamingExport:
    """Test streaming export functionality."""

    def test_stream_to_csv(self, export_service, large_data):
        """Test CSV streaming."""
        chunks = list(export_service.stream_to_csv(
            large_data,
            chunk_size=1000
        ))

        # Should have header + 5 data chunks
        assert len(chunks) == 6  # 1 header + 5 chunks of 1000

        # Combine all chunks
        full_content = "".join(chunks)

        # Verify completeness
        lines = full_content.strip().split("\n")
        assert len(lines) == 5001  # header + 5000 data rows

    def test_stream_to_csv_without_header(self, export_service, large_data):
        """Test CSV streaming without header."""
        chunks = list(export_service.stream_to_csv(
            large_data,
            chunk_size=1000,
            include_header=False
        ))

        # Should have only data chunks
        assert len(chunks) == 5

    def test_stream_to_jsonl(self, export_service, large_data):
        """Test JSONL streaming."""
        chunks = list(export_service.stream_to_jsonl(
            large_data,
            chunk_size=1000
        ))

        # Should have 5 chunks
        assert len(chunks) == 5

        # Combine all chunks
        full_content = "".join(chunks)

        # Verify completeness
        lines = full_content.strip().split("\n")
        assert len(lines) == 5000

    def test_stream_to_file(self, export_service, large_data):
        """Test streaming large data to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "large.csv"

            with open(file_path, "w") as f:
                for chunk in export_service.stream_to_csv(large_data, chunk_size=1000):
                    f.write(chunk)

            assert file_path.exists()

            # Verify file contents
            lines = file_path.read_text().strip().split("\n")
            assert len(lines) == 5001  # header + 5000 rows

    def test_stream_empty_data_raises(self, export_service):
        """Test that streaming empty data raises ValueError."""
        with pytest.raises(ValueError, match="Cannot stream empty data"):
            list(export_service.stream_to_csv([]))


class TestExportMetadata:
    """Test ExportMetadata class."""

    def test_metadata_creation(self):
        """Test creating ExportMetadata."""
        metadata = ExportMetadata(
            format=ExportFormat.CSV,
            record_count=100,
            file_path="/path/to/file.csv",
            file_size_bytes=1024
        )

        assert metadata.format == ExportFormat.CSV
        assert metadata.record_count == 100
        assert metadata.file_path == "/path/to/file.csv"
        assert metadata.file_size_bytes == 1024
        assert metadata.timestamp is not None

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = ExportMetadata(
            format=ExportFormat.JSON,
            record_count=50
        )

        metadata_dict = metadata.to_dict()

        assert metadata_dict["format"] == "json"
        assert metadata_dict["record_count"] == 50
        assert "timestamp" in metadata_dict
        assert metadata_dict["file_path"] is None


class TestGenerationExport:
    """Test exporting Generation objects."""

    def test_export_generation_to_file(self, export_service):
        """Test exporting generation data to file."""
        generation_data = {
            "generation_id": 123,
            "backend": "huggingface",
            "num_records": 3,
            "success": True,
            "data": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
                {"name": "Charlie", "age": 35}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "generation.json"

            metadata = export_service.export_generation_to_file(
                generation_data,
                str(file_path),
                ExportFormat.JSON
            )

            assert metadata.record_count == 3
            assert file_path.exists()

    def test_export_generation_with_metadata(self, export_service):
        """Test exporting generation with metadata included."""
        generation_data = {
            "generation_id": 456,
            "backend": "ollama",
            "num_records": 2,
            "success": True,
            "data": [
                {"name": "Alice"},
                {"name": "Bob"}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "generation_with_metadata.json"

            metadata = export_service.export_generation_to_file(
                generation_data,
                str(file_path),
                ExportFormat.JSON,
                include_generation_metadata=True
            )

            # Verify metadata is included in file
            with open(file_path) as f:
                content = json.load(f)

            assert "generation_metadata" in content
            assert "data" in content
            assert content["generation_metadata"]["generation_id"] == 456
            assert content["generation_metadata"]["backend"] == "ollama"

    def test_export_generation_empty_data_raises(self, export_service):
        """Test that exporting generation with empty data raises error."""
        generation_data = {
            "generation_id": 789,
            "data": []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "empty.json"

            with pytest.raises(ValueError, match="Generation data is empty"):
                export_service.export_generation_to_file(
                    generation_data,
                    str(file_path),
                    ExportFormat.JSON
                )


class TestUtilityMethods:
    """Test utility methods."""

    def test_get_export_extension(self, export_service):
        """Test getting file extension for formats."""
        assert export_service.get_export_extension(ExportFormat.CSV) == ".csv"
        assert export_service.get_export_extension(ExportFormat.JSON) == ".json"
        assert export_service.get_export_extension(ExportFormat.JSONL) == ".jsonl"

    def test_suggest_filename_basic(self, export_service):
        """Test filename suggestion."""
        filename = export_service.suggest_filename(
            ExportFormat.CSV,
            prefix="test",
            include_timestamp=False
        )
        assert filename == "test.csv"

    def test_suggest_filename_with_timestamp(self, export_service):
        """Test filename suggestion with timestamp."""
        filename = export_service.suggest_filename(
            ExportFormat.JSON,
            include_timestamp=True
        )

        assert filename.startswith("synthetic_data_")
        assert filename.endswith(".json")
        assert "_" in filename  # Timestamp separator

    def test_suggest_filename_different_formats(self, export_service):
        """Test filename suggestions for different formats."""
        csv_filename = export_service.suggest_filename(
            ExportFormat.CSV,
            include_timestamp=False
        )
        json_filename = export_service.suggest_filename(
            ExportFormat.JSON,
            include_timestamp=False
        )
        jsonl_filename = export_service.suggest_filename(
            ExportFormat.JSONL,
            include_timestamp=False
        )

        assert csv_filename.endswith(".csv")
        assert json_filename.endswith(".json")
        assert jsonl_filename.endswith(".jsonl")


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_record_export(self, export_service):
        """Test exporting single record."""
        single_record = [{"name": "Alice", "age": 30}]

        csv_content = export_service.to_csv(single_record)
        json_content = export_service.to_json(single_record)
        jsonl_content = export_service.to_jsonl(single_record)

        assert "Alice" in csv_content
        assert "Alice" in json_content
        assert "Alice" in jsonl_content

    def test_unicode_characters(self, export_service):
        """Test exporting data with unicode characters."""
        unicode_data = [
            {"name": "José", "city": "São Paulo"},
            {"name": "李明", "city": "北京"},
            {"name": "Müller", "city": "München"}
        ]

        csv_content = export_service.to_csv(unicode_data)
        json_content = export_service.to_json(unicode_data)

        assert "José" in csv_content
        assert "李明" in json_content

    def test_special_characters_in_csv(self, export_service):
        """Test CSV export with special characters."""
        special_data = [
            {"text": "Hello, world!"},
            {"text": 'Quote: "test"'},
            {"text": "Newline:\ntest"}
        ]

        csv_content = export_service.to_csv(special_data)

        # Should be properly escaped
        assert csv_content  # Just verify it doesn't crash

    def test_nested_data_warning(self, export_service):
        """Test that nested structures are handled (as strings in CSV)."""
        nested_data = [
            {"name": "Alice", "tags": ["python", "data"]},
            {"name": "Bob", "tags": ["java", "backend"]}
        ]

        # Should not crash, but nested arrays become strings in CSV
        csv_content = export_service.to_csv(nested_data)
        assert csv_content

        # JSON should preserve structure
        json_content = export_service.to_json(nested_data)
        parsed = json.loads(json_content)
        assert isinstance(parsed[0]["tags"], list)
