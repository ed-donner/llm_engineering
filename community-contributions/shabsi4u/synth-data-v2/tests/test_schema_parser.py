"""
Tests for schema parser utility.
"""

import pytest
from synth_data.utils.schema_parser import (
    parse_schema,
    validate_schema,
    format_schema_for_display,
    _parse_simplified_format
)
from synth_data.exceptions import SchemaValidationError


class TestParseSchema:
    """Test schema parsing from different formats."""

    def test_parse_json_format(self):
        """Test parsing valid JSON schema."""
        json_str = '{"name": {"type": "string"}, "age": {"type": "integer"}}'
        schema = parse_schema(json_str)

        assert schema == {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }

    def test_parse_simplified_format(self):
        """Test parsing simplified format."""
        simplified = "name:string, age:integer, email:string"
        schema = parse_schema(simplified)

        assert schema == {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"}
        }

    def test_parse_with_type_aliases(self):
        """Test type aliases (str, int, float, bool)."""
        simplified = "name:str, age:int, price:float, active:bool"
        schema = parse_schema(simplified)

        assert schema == {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "price": {"type": "number"},
            "active": {"type": "boolean"}
        }

    def test_parse_empty_string_raises(self):
        """Test that empty string raises error."""
        with pytest.raises(SchemaValidationError, match="cannot be empty"):
            parse_schema("")

    def test_parse_invalid_json_raises(self):
        """Test that invalid JSON raises error."""
        with pytest.raises(SchemaValidationError, match="Invalid JSON"):
            parse_schema('{"name": invalid}')

    def test_parse_invalid_simplified_format_raises(self):
        """Test that invalid simplified format raises error."""
        with pytest.raises(SchemaValidationError, match="Expected 'field:type' format"):
            parse_schema("name age email")  # Missing colons

    def test_parse_simplified_with_missing_type_raises(self):
        """Test simplified format with missing type."""
        with pytest.raises(SchemaValidationError, match="Field type cannot be empty"):
            parse_schema("name:, age:integer")

    def test_parse_simplified_with_missing_name_raises(self):
        """Test simplified format with missing field name."""
        with pytest.raises(SchemaValidationError, match="Field name cannot be empty"):
            parse_schema(":string, age:integer")


class TestValidateSchema:
    """Test schema validation."""

    def test_validate_valid_schema(self):
        """Test that valid schema passes validation."""
        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        validate_schema(schema)  # Should not raise

    def test_validate_empty_schema_raises(self):
        """Test that empty schema raises error."""
        with pytest.raises(SchemaValidationError, match="cannot be empty"):
            validate_schema({})

    def test_validate_non_dict_raises(self):
        """Test that non-dict raises error."""
        with pytest.raises(SchemaValidationError, match="must be a dictionary"):
            validate_schema("not a dict")

    def test_validate_none_field_value_raises(self):
        """Test that None field value raises error."""
        with pytest.raises(SchemaValidationError, match="has None value"):
            validate_schema({"name": None})

    def test_validate_non_string_field_name_raises(self):
        """Test that non-string field name raises error."""
        with pytest.raises(SchemaValidationError, match="must be strings"):
            validate_schema({123: {"type": "string"}})


class TestFormatSchemaForDisplay:
    """Test schema formatting for display."""

    def test_format_simple_schema(self):
        """Test formatting simple schema."""
        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        formatted = format_schema_for_display(schema)

        assert "name (string)" in formatted
        assert "age (integer)" in formatted

    def test_format_schema_with_constraints(self):
        """Test formatting schema with constraints."""
        schema = {
            "age": {
                "type": "integer",
                "minimum": 0,
                "maximum": 120
            }
        }
        formatted = format_schema_for_display(schema)

        assert "age (integer" in formatted
        assert "minimum: 0" in formatted
        assert "maximum: 120" in formatted

    def test_format_empty_schema(self):
        """Test formatting empty schema."""
        schema = {}
        formatted = format_schema_for_display(schema)
        assert formatted == ""


class TestParseSimplifiedFormat:
    """Test internal simplified format parser."""

    def test_parse_basic_fields(self):
        """Test parsing basic fields."""
        schema = _parse_simplified_format("name:string, age:integer")
        assert schema == {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }

    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace."""
        schema = _parse_simplified_format("  name : string ,  age : integer  ")
        assert schema == {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }

    def test_parse_single_field(self):
        """Test parsing single field."""
        schema = _parse_simplified_format("name:string")
        assert schema == {"name": {"type": "string"}}

    def test_parse_empty_raises(self):
        """Test that empty input raises error."""
        with pytest.raises(SchemaValidationError, match="cannot be empty"):
            _parse_simplified_format("")

    def test_parse_no_colon_raises(self):
        """Test that missing colon raises error."""
        with pytest.raises(SchemaValidationError, match="Expected 'field:type' format"):
            _parse_simplified_format("name string")
