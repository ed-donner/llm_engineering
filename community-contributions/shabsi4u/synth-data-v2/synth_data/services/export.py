"""Export service for synthetic data to CSV, JSON, and JSONL formats."""

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
    """Metadata about an export operation."""

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
    """Service for exporting synthetic data to CSV, JSON, and JSONL formats."""

    def _validate_data(self, data: List[Dict[str, Any]]) -> None:
        """Validate data is a non-empty list of dicts."""
        if not isinstance(data, list):
            raise TypeError(f"Data must be a list, got {type(data).__name__}")
        if not data:
            raise ValueError("Cannot export empty data")
        if not isinstance(data[0], dict):
            raise TypeError(
                f"Data must be a list of dictionaries, got list of {type(data[0]).__name__}"
            )

    def to_csv(
        self,
        data: List[Dict[str, Any]],
        delimiter: str = ",",
        include_header: bool = True
    ) -> str:
        """Export data to CSV format."""
        self._validate_data(data)

        all_fields = set()
        for record in data:
            all_fields.update(record.keys())
        fieldnames = sorted(all_fields)

        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=delimiter,
            lineterminator="\n",
            extrasaction='ignore'
        )

        if include_header:
            writer.writeheader()
        writer.writerows(data)

        csv_content = output.getvalue()
        output.close()
        return csv_content

    def to_json(
        self,
        data: List[Dict[str, Any]],
        pretty: bool = False,
        include_metadata: bool = False
    ) -> str:
        """Export data to JSON format."""
        self._validate_data(data)

        if include_metadata:
            output = {
                "data": data,
                "metadata": {
                    "record_count": len(data),
                    "export_timestamp": datetime.now(UTC).isoformat(),
                    "format": "json"
                }
            }
        else:
            output = data

        indent = 2 if pretty else None
        return json.dumps(output, indent=indent, ensure_ascii=False)

    def to_jsonl(self, data: List[Dict[str, Any]]) -> str:
        """Export data to JSON Lines format (one JSON object per line)."""
        self._validate_data(data)
        lines = [json.dumps(record, ensure_ascii=False) for record in data]
        return "\n".join(lines)

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
