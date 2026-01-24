"""
Export service for synthetic data.

Handles exporting generated data to various formats (CSV, JSON, JSONL)
with support for streaming large datasets and metadata tracking.

Supported Formats:
    - CSV: Standard comma-separated values
    - JSON: Array of objects
    - JSONL: JSON Lines (one object per line)

Features:
    - Streaming exports for memory efficiency
    - Metadata tracking (format, timestamp, record count)
    - Configurable CSV delimiters and formatting
    - Pretty-printed JSON option
"""

import csv
import json
import logging
from io import StringIO
from typing import Dict, Any, List, Optional, Iterator
from datetime import datetime, UTC
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"


class ExportMetadata:
    """
    Metadata about an export operation.

    Attributes:
        format: Export format used
        record_count: Number of records exported
        timestamp: When export was created
        file_path: Path to exported file (if saved)
        file_size_bytes: Size of exported file
    """

    def __init__(
        self,
        format: ExportFormat,
        record_count: int,
        timestamp: Optional[datetime] = None,
        file_path: Optional[str] = None,
        file_size_bytes: Optional[int] = None
    ):
        self.format = format
        self.record_count = record_count
        self.timestamp = timestamp or datetime.now(UTC)
        self.file_path = file_path
        self.file_size_bytes = file_size_bytes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "format": self.format.value,
            "record_count": self.record_count,
            "timestamp": self.timestamp.isoformat(),
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes
        }


class ExportService:
    """
    Service for exporting synthetic data to various formats.

    Design Pattern: Strategy Pattern
    - Different export strategies for different formats
    - Consistent interface regardless of format

    Example:
        >>> service = ExportService()
        >>> data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        >>>
        >>> # Export to CSV string
        >>> csv_content = service.to_csv(data)
        >>>
        >>> # Export to file
        >>> metadata = service.export_to_file(data, "output.json", ExportFormat.JSON)
        >>> print(f"Exported {metadata.record_count} records")
        >>>
        >>> # Stream large dataset
        >>> for chunk in service.stream_to_csv(large_data, chunk_size=1000):
        >>>     file.write(chunk)
    """

    def __init__(self):
        """Initialize export service."""
        logger.info("ExportService initialized")

    def to_csv(
        self,
        data: List[Dict[str, Any]],
        delimiter: str = ",",
        include_header: bool = True
    ) -> str:
        """
        Export data to CSV format.

        Args:
            data: List of dictionaries to export
            delimiter: Field delimiter (default: comma)
            include_header: Include header row with field names

        Returns:
            CSV-formatted string

        Raises:
            ValueError: If data is empty or invalid
            TypeError: If data is not a list of dictionaries

        Example:
            >>> data = [{"name": "Alice", "age": 30}]
            >>> csv_str = service.to_csv(data)
            >>> print(csv_str)
            name,age
            Alice,30
        """
        # FIX: Validate data type
        if not isinstance(data, list):
            raise TypeError(f"Data must be a list, got {type(data).__name__}")

        if not data:
            raise ValueError("Cannot export empty data")

        # FIX: Validate first item is a dict
        if not isinstance(data[0], dict):
            raise TypeError(
                f"Data must be a list of dictionaries, got list of {type(data[0]).__name__}"
            )

        logger.info(f"Exporting {len(data)} records to CSV")

        output = StringIO()

        # FIX: Collect all unique fields from all records and sort for consistency
        # This ensures consistent column order and handles records with different fields
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())

        fieldnames = sorted(list(all_fields))

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=delimiter,
            lineterminator="\n",
            extrasaction='ignore'  # Ignore extra fields not in fieldnames
        )

        if include_header:
            writer.writeheader()

        writer.writerows(data)

        csv_content = output.getvalue()
        output.close()

        logger.info(f"CSV export complete: {len(csv_content)} bytes")
        return csv_content

    def to_json(
        self,
        data: List[Dict[str, Any]],
        pretty: bool = False,
        include_metadata: bool = False
    ) -> str:
        """
        Export data to JSON format.

        Args:
            data: List of dictionaries to export
            pretty: Pretty-print with indentation
            include_metadata: Include export metadata in output

        Returns:
            JSON-formatted string

        Raises:
            ValueError: If data is empty
            TypeError: If data is not a list of dictionaries

        Example:
            >>> data = [{"name": "Alice", "age": 30}]
            >>> json_str = service.to_json(data, pretty=True)
        """
        # FIX: Validate data type
        if not isinstance(data, list):
            raise TypeError(f"Data must be a list, got {type(data).__name__}")

        if not data:
            raise ValueError("Cannot export empty data")

        if data and not isinstance(data[0], dict):
            raise TypeError(
                f"Data must be a list of dictionaries, got list of {type(data[0]).__name__}"
            )

        logger.info(f"Exporting {len(data)} records to JSON")

        output = {
            "data": data
        }

        if include_metadata:
            output["metadata"] = {
                "record_count": len(data),
                "export_timestamp": datetime.now(UTC).isoformat(),
                "format": "json"
            }
        else:
            # Just export the data array without wrapper
            output = data

        indent = 2 if pretty else None
        json_content = json.dumps(output, indent=indent, ensure_ascii=False)

        logger.info(f"JSON export complete: {len(json_content)} bytes")
        return json_content

    def to_jsonl(self, data: List[Dict[str, Any]]) -> str:
        """
        Export data to JSON Lines format.

        JSON Lines (JSONL) format: one JSON object per line.
        More efficient for streaming and processing large datasets.

        Args:
            data: List of dictionaries to export

        Returns:
            JSONL-formatted string (one JSON object per line)

        Raises:
            ValueError: If data is empty
            TypeError: If data is not a list of dictionaries

        Example:
            >>> data = [{"name": "Alice"}, {"name": "Bob"}]
            >>> jsonl_str = service.to_jsonl(data)
            >>> print(jsonl_str)
            {"name":"Alice"}
            {"name":"Bob"}
        """
        # FIX: Validate data type
        if not isinstance(data, list):
            raise TypeError(f"Data must be a list, got {type(data).__name__}")

        if not data:
            raise ValueError("Cannot export empty data")

        if not isinstance(data[0], dict):
            raise TypeError(
                f"Data must be a list of dictionaries, got list of {type(data[0]).__name__}"
            )

        logger.info(f"Exporting {len(data)} records to JSONL")

        lines = []
        for record in data:
            line = json.dumps(record, ensure_ascii=False)
            lines.append(line)

        jsonl_content = "\n".join(lines)

        logger.info(f"JSONL export complete: {len(jsonl_content)} bytes")
        return jsonl_content

    def export_to_file(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        format: ExportFormat,
        **kwargs
    ) -> ExportMetadata:
        """
        Export data to a file.

        Args:
            data: List of dictionaries to export
            file_path: Destination file path
            format: Export format (CSV, JSON, or JSONL)
            **kwargs: Format-specific options (delimiter, pretty, etc.)

        Returns:
            ExportMetadata with information about the export

        Raises:
            ValueError: If format is invalid or data is empty
            IOError: If file cannot be written

        Example:
            >>> data = [{"name": "Alice", "age": 30}]
            >>> metadata = service.export_to_file(
            ...     data,
            ...     "users.csv",
            ...     ExportFormat.CSV
            ... )
            >>> print(f"Exported to {metadata.file_path}")
        """
        if not data:
            raise ValueError("Cannot export empty data")

        logger.info(f"Exporting to file: {file_path} (format: {format.value})")

        # Generate content based on format
        if format == ExportFormat.CSV:
            content = self.to_csv(data, **kwargs)
        elif format == ExportFormat.JSON:
            content = self.to_json(data, **kwargs)
        elif format == ExportFormat.JSONL:
            content = self.to_jsonl(data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        # Write to file
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        # Get file size
        file_size = path.stat().st_size

        metadata = ExportMetadata(
            format=format,
            record_count=len(data),
            file_path=str(path.absolute()),
            file_size_bytes=file_size
        )

        logger.info(
            f"Export complete: {metadata.record_count} records, "
            f"{file_size} bytes written to {file_path}"
        )

        return metadata

    def stream_to_csv(
        self,
        data: List[Dict[str, Any]],
        chunk_size: int = 1000,
        delimiter: str = ",",
        include_header: bool = True
    ) -> Iterator[str]:
        """
        Stream data to CSV format in chunks.

        Memory-efficient for large datasets. Yields CSV chunks that can be
        written incrementally to a file or sent over a network.

        Args:
            data: List of dictionaries to export
            chunk_size: Number of records per chunk
            delimiter: Field delimiter
            include_header: Include header in first chunk

        Yields:
            CSV-formatted string chunks

        Example:
            >>> data = [{"name": f"User{i}", "age": i} for i in range(10000)]
            >>> with open("large.csv", "w") as f:
            ...     for chunk in service.stream_to_csv(data, chunk_size=1000):
            ...         f.write(chunk)
        """
        if not data:
            raise ValueError("Cannot stream empty data")

        logger.info(f"Streaming {len(data)} records to CSV (chunk_size={chunk_size})")

        fieldnames = list(data[0].keys())

        # Yield header as first chunk if requested
        if include_header:
            header_output = StringIO()
            writer = csv.DictWriter(
                header_output,
                fieldnames=fieldnames,
                delimiter=delimiter,
                lineterminator="\n"
            )
            writer.writeheader()
            header_chunk = header_output.getvalue()
            header_output.close()
            yield header_chunk

        # Yield data in chunks
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]

            chunk_output = StringIO()
            writer = csv.DictWriter(
                chunk_output,
                fieldnames=fieldnames,
                delimiter=delimiter,
                lineterminator="\n"
            )
            writer.writerows(chunk)

            chunk_str = chunk_output.getvalue()
            chunk_output.close()

            logger.debug(f"Yielding CSV chunk {i // chunk_size + 1}: {len(chunk)} records")
            yield chunk_str

        logger.info("CSV streaming complete")

    def stream_to_jsonl(
        self,
        data: List[Dict[str, Any]],
        chunk_size: int = 1000
    ) -> Iterator[str]:
        """
        Stream data to JSONL format in chunks.

        Args:
            data: List of dictionaries to export
            chunk_size: Number of records per chunk

        Yields:
            JSONL-formatted string chunks

        Example:
            >>> with open("data.jsonl", "w") as f:
            ...     for chunk in service.stream_to_jsonl(large_data):
            ...         f.write(chunk)
        """
        if not data:
            raise ValueError("Cannot stream empty data")

        logger.info(f"Streaming {len(data)} records to JSONL (chunk_size={chunk_size})")

        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            lines = []

            for record in chunk:
                line = json.dumps(record, ensure_ascii=False)
                lines.append(line)

            chunk_str = "\n".join(lines) + "\n"

            logger.debug(f"Yielding JSONL chunk {i // chunk_size + 1}: {len(chunk)} records")
            yield chunk_str

        logger.info("JSONL streaming complete")

    def export_generation_to_file(
        self,
        generation_data: Dict[str, Any],
        file_path: str,
        format: ExportFormat,
        include_generation_metadata: bool = False,
        **kwargs
    ) -> ExportMetadata:
        """
        Export a Generation object's data to file.

        Convenience method for exporting from database Generation records.

        Args:
            generation_data: Generation data dict (from service.generate())
            file_path: Destination file path
            format: Export format
            include_generation_metadata: Include generation info in export
            **kwargs: Format-specific options

        Returns:
            ExportMetadata

        Example:
            >>> result = generator_service.generate(schema, 100)
            >>> metadata = export_service.export_generation_to_file(
            ...     result,
            ...     "output.json",
            ...     ExportFormat.JSON,
            ...     include_generation_metadata=True
            ... )
        """
        data = generation_data.get("data", [])

        if not data:
            raise ValueError("Generation data is empty or invalid")

        logger.info(
            f"Exporting generation (id: {generation_data.get('generation_id')}) "
            f"to {file_path}"
        )

        # If including metadata, wrap data with generation info
        if include_generation_metadata and format == ExportFormat.JSON:
            enriched_data = {
                "generation_metadata": {
                    "generation_id": generation_data.get("generation_id"),
                    "backend": generation_data.get("backend"),
                    "num_records": generation_data.get("num_records"),
                    "success": generation_data.get("success"),
                    "export_timestamp": datetime.now(UTC).isoformat()
                },
                "data": data
            }

            # Write enriched data directly
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(enriched_data, f, indent=2, ensure_ascii=False)

            file_size = path.stat().st_size

            return ExportMetadata(
                format=format,
                record_count=len(data),
                file_path=str(path.absolute()),
                file_size_bytes=file_size
            )

        # Standard export
        return self.export_to_file(data, file_path, format, **kwargs)

    def get_export_extension(self, format: ExportFormat) -> str:
        """
        Get file extension for a format.

        Args:
            format: Export format

        Returns:
            File extension including dot (e.g., ".csv")

        Example:
            >>> ext = service.get_export_extension(ExportFormat.CSV)
            >>> print(ext)  # ".csv"
        """
        extensions = {
            ExportFormat.CSV: ".csv",
            ExportFormat.JSON: ".json",
            ExportFormat.JSONL: ".jsonl"
        }
        return extensions.get(format, ".txt")

    def suggest_filename(
        self,
        format: ExportFormat,
        prefix: str = "synthetic_data",
        include_timestamp: bool = True
    ) -> str:
        """
        Suggest a filename for an export.

        Args:
            format: Export format
            prefix: Filename prefix
            include_timestamp: Include timestamp in filename

        Returns:
            Suggested filename

        Example:
            >>> filename = service.suggest_filename(ExportFormat.CSV)
            >>> print(filename)  # "synthetic_data_20260124_143022.csv"
        """
        extension = self.get_export_extension(format)

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{prefix}_{timestamp}{extension}"

        return f"{prefix}{extension}"
