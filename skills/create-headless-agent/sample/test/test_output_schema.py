"""
Tests for output schema validation.
Python equivalent of test/output-schema.test.ts
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def validate(schema: dict, text: str) -> dict:
    """Validate text against a JSON schema. Returns {valid, errors?}."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"valid": False, "errors": "not valid JSON"}

    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(parsed))
    if not errors:
        return {"valid": True}
    error_msgs = "; ".join(e.message for e in errors)
    return {"valid": False, "errors": error_msgs}


REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "count": {"type": "integer", "minimum": 0},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "count"],
    "additionalProperties": False,
}


class TestOutputSchemaValidation:
    def test_accepts_valid_json_matching_schema(self):
        result = validate(REPORT_SCHEMA, '{"summary":"ok","count":3}')
        assert result["valid"] is True

    def test_accepts_valid_json_with_optional_fields(self):
        result = validate(REPORT_SCHEMA, '{"summary":"ok","count":3,"tags":["a","b"]}')
        assert result["valid"] is True

    def test_rejects_missing_required_field(self):
        result = validate(REPORT_SCHEMA, '{"summary":"ok"}')
        assert result["valid"] is False
        assert "count" in result.get("errors", "")

    def test_rejects_wrong_type_for_field(self):
        result = validate(REPORT_SCHEMA, '{"summary":"ok","count":"three"}')
        assert result["valid"] is False
        assert "integer" in result.get("errors", "") or "count" in result.get("errors", "")

    def test_rejects_additional_properties(self):
        result = validate(REPORT_SCHEMA, '{"summary":"ok","count":3,"extra":true}')
        assert result["valid"] is False

    def test_rejects_non_json_text(self):
        result = validate(REPORT_SCHEMA, "not json at all")
        assert result["valid"] is False
        assert result.get("errors") == "not valid JSON"

    def test_rejects_empty_object_against_required_fields(self):
        result = validate(REPORT_SCHEMA, "{}")
        assert result["valid"] is False
        errors = result.get("errors", "")
        assert "summary" in errors or "count" in errors
