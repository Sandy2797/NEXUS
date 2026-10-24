import json
import pytest
from pathlib import Path
from pydantic import ValidationError
from backend.app.schemas.event import SecurityEvent
from fastapi.testclient import TestClient
from backend.app import main
from backend.app.storage import database

PROJECT_ROOT = Path(__file__).resolve().parents[2]
JSON_SCHEMA_PATH = (
    PROJECT_ROOT / "backend" / "app" / "schemas" / "event.schema.json"
)


def valid_event_data():
    return {
        "source": "wireless",
        "finding_type": "suspicious_network",
        "severity": "high",
        "summary": "A suspicious wireless network was detected.",
    }


def test_valid_event_is_accepted():
    event = SecurityEvent(**valid_event_data())

    assert event.source == "wireless"
    assert event.severity == "high"
    assert event.schema_version == "1.0"


def test_event_defaults_are_generated():
    event = SecurityEvent(**valid_event_data())

    assert event.event_id
    assert event.timestamp is not None
    assert event.enforcement_result == "not_applicable"


def test_missing_required_field_is_rejected():
    data = valid_event_data()
    del data["source"]

    with pytest.raises(ValidationError):
        SecurityEvent(**data)


def test_invalid_severity_is_rejected():
    data = valid_event_data()
    data["severity"] = "urgent"

    with pytest.raises(ValidationError):
        SecurityEvent(**data)


def test_invalid_timestamp_is_rejected():
    data = valid_event_data()
    data["timestamp"] = "not-a-timestamp"

    with pytest.raises(ValidationError):
        SecurityEvent(**data)


def test_oversized_evidence_reference_is_rejected():
    data = valid_event_data()
    data["evidence_reference"] = "x" * 501

    with pytest.raises(ValidationError):
        SecurityEvent(**data)


def test_unknown_fields_are_rejected():
    data = valid_event_data()
    data["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        SecurityEvent(**data)


def test_json_schema_file_is_valid_json():
    with JSON_SCHEMA_PATH.open(encoding="utf-8") as file:
        schema = json.load(file)

    assert schema["title"] == "NEXUS Security Event"
    assert schema["type"] == "object"


def test_json_schema_documents_required_fields():
    with JSON_SCHEMA_PATH.open(encoding="utf-8") as file:
        schema = json.load(file)

    assert set(schema["required"]) == {
        "event_id",
        "schema_version",
        "timestamp",
        "source",
        "finding_type",
        "severity",
        "summary",
        "enforcement_result",
    }

def test_unknown_schema_version_is_rejected():
    data = valid_event_data()
    data["schema_version"] = "2.0"

    with pytest.raises(ValidationError):
        SecurityEvent(**data)

def test_oversized_summary_is_rejected():
    data = valid_event_data()
    data["summary"] = "x" * 2001

    with pytest.raises(ValidationError):
        SecurityEvent(**data)


def test_oversized_rule_or_model_version_is_rejected():
    data = valid_event_data()
    data["rule_or_model_version"] = "x" * 101

    with pytest.raises(ValidationError):
        SecurityEvent(**data)

def test_example_fixture_through_api(tmp_path, monkeypatch):
    test_db = tmp_path / "fixture_integration.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    fixture_path = (
        PROJECT_ROOT / "docs" / "example-security-event.json"
    )
    with fixture_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    with TestClient(main.app) as client:
        create_response = client.post(
            "/api/v1/events",
            json=payload,
        )

        assert create_response.status_code == 201

        created_event = create_response.json()
        assert created_event["event_id"] == payload["event_id"]
        assert created_event["source"] == payload["source"]
        assert created_event["severity"] == payload["severity"]

        retrieve_response = client.get(
            f"/api/v1/events/{payload['event_id']}"
        )

    assert retrieve_response.status_code == 200

    retrieved_event = retrieve_response.json()
    assert retrieved_event["event_id"] == payload["event_id"]
    assert retrieved_event["policy_decision"] == "redact"
    assert retrieved_event["enforcement_result"] == "redacted"