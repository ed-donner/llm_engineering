"""
Schema parser for flexible schema input formats.

Supports two input formats:
1. JSON Schema: Full JSON schema with type definitions
2. Simplified: name:type, name:type format

Type Mapping:
    - string, str -> string
    - integer, int -> integer
    - number, float -> number
    - boolean, bool -> boolean
    - array, list -> array
"""

import json
import logging
from typing import Dict, Any

from ..exceptions import SchemaValidationError

logger = logging.getLogger(__name__)

# Type aliases for simplified format
TYPE_ALIASES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
}


def parse_schema(input_str: str) -> Dict[str, Any]:
    """
    Parse schema from either JSON or simplified format.

    Formats:
        JSON: {"name": {"type": "string"}, "age": {"type": "integer"}}
        Simplified: name:string, age:integer, email:string

    Args:
        input_str: Schema string in either format

    Returns:
        Dictionary schema definition

    Raises:
        SchemaValidationError: If schema cannot be parsed or is invalid

    Examples:
        >>> # JSON format
        >>> schema = parse_schema('{"name": {"type": "string"}}')
        >>> print(schema)
        {'name': {'type': 'string'}}

        >>> # Simplified format
        >>> schema = parse_schema('name:string, age:integer')
        >>> print(schema)
        {'name': {'type': 'string'}, 'age': {'type': 'integer'}}

        >>> # With aliases
        >>> schema = parse_schema('count:int, price:float, active:bool')
        >>> print(schema)
        {'count': {'type': 'integer'}, 'price': {'type': 'number'}, 'active': {'type': 'boolean'}}
    """
    if not input_str or not input_str.strip():
        raise SchemaValidationError("Schema input cannot be empty")

    input_str = input_str.strip()

    # Try JSON format first
    if input_str.startswith("{"):
        try:
            schema = json.loads(input_str)
            logger.debug("Parsed schema as JSON format")
            return schema
        except json.JSONDecodeError as e:
            raise SchemaValidationError(
                f"Invalid JSON schema: {str(e)}"
            ) from e

    # Parse simplified format
    try:
        schema = _parse_simplified_format(input_str)
        logger.debug("Parsed schema as simplified format")
        return schema
    except Exception as e:
        raise SchemaValidationError(
            f"Invalid schema format. Expected JSON or 'field:type, field:type' format. Error: {str(e)}"
        ) from e


def _parse_simplified_format(input_str: str) -> Dict[str, Any]:
    """
    Parse simplified schema format: field:type, field:type

    Args:
        input_str: Simplified format string

    Returns:
        Schema dictionary

    Raises:
        SchemaValidationError: If format is invalid

    Examples:
        >>> schema = _parse_simplified_format("name:string, age:integer")
        >>> print(schema)
        {'name': {'type': 'string'}, 'age': {'type': 'integer'}}
    """
    schema = {}

    # Split by comma
    fields = [f.strip() for f in input_str.split(",")]

    for field_def in fields:
        if not field_def:
            continue

        # Split by colon
        if ":" not in field_def:
            raise SchemaValidationError(
                f"Invalid field definition: '{field_def}'. Expected 'field:type' format"
            )

        parts = field_def.split(":", 1)
        if len(parts) != 2:
            raise SchemaValidationError(
                f"Invalid field definition: '{field_def}'. Expected 'field:type' format"
            )

        field_name = parts[0].strip()
        field_type = parts[1].strip()

        if not field_name:
            raise SchemaValidationError(
                f"Field name cannot be empty in '{field_def}'"
            )

        if not field_type:
            raise SchemaValidationError(
                f"Field type cannot be empty in '{field_def}'"
            )

        # Resolve type aliases
        resolved_type = TYPE_ALIASES.get(field_type.lower(), field_type.lower())

        schema[field_name] = {"type": resolved_type}

    if not schema:
        raise SchemaValidationError("Schema cannot be empty")

    return schema


def validate_schema(schema: Dict[str, Any]) -> None:
    """
    Validate a parsed schema dictionary.

    Args:
        schema: Schema dictionary to validate

    Raises:
        SchemaValidationError: If schema is invalid

    Examples:
        >>> validate_schema({"name": {"type": "string"}})  # OK
        >>> validate_schema({})  # Raises SchemaValidationError
    """
    if not isinstance(schema, dict):
        raise SchemaValidationError(
            f"Schema must be a dictionary, got {type(schema).__name__}"
        )

    if not schema:
        raise SchemaValidationError("Schema cannot be empty")

    for field_name, field_spec in schema.items():
        if not isinstance(field_name, str):
            raise SchemaValidationError(
                f"Field names must be strings, got {type(field_name).__name__}"
            )

        if field_spec is None:
            raise SchemaValidationError(
                f"Field '{field_name}' has None value"
            )

        if isinstance(field_spec, dict) and "type" not in field_spec:
            logger.warning(
                f"Field '{field_name}' missing 'type' key. LLM may not interpret correctly"
            )


def format_schema_for_display(schema: Dict[str, Any]) -> str:
    """
    Format schema for display in UI.

    Args:
        schema: Schema dictionary

    Returns:
        Human-readable schema string

    Example:
        >>> schema = {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 0}}
        >>> print(format_schema_for_display(schema))
        name (string), age (integer, minimum: 0)
    """
    parts = []
    for field_name, field_spec in schema.items():
        if isinstance(field_spec, dict):
            field_type = field_spec.get("type", "unknown")
            extras = []
            for key, value in field_spec.items():
                if key != "type":
                    extras.append(f"{key}: {value}")

            if extras:
                parts.append(f"{field_name} ({field_type}, {', '.join(extras)})")
            else:
                parts.append(f"{field_name} ({field_type})")
        else:
            parts.append(f"{field_name} ({field_spec})")

    return ", ".join(parts)
