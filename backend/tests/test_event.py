
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.storage import database


def test_health_endpoint():
    with TestClient(main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_retrieve_event(tmp_path, monkeypatch):
    test_db = tmp_path / "test_nexus.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        payload = {
            "source": "wireless",
            "finding_type": "suspicious_access_point",
            "severity": "medium",
            "summary": "Automated test event",
            "evidence_reference": "test-evidence-001",
        }

        create_response = client.post(
            "/api/v1/events",
            json=payload,
        )

        assert create_response.status_code == 201
        created_event = create_response.json()
        event_id = created_event["event_id"]

        get_response = client.get(
            f"/api/v1/events/{event_id}"
        )

        assert get_response.status_code == 200
        assert get_response.json()["event_id"] == event_id
        assert get_response.json()["summary"] == "Automated test event"

        list_response = client.get("/api/v1/events")

        assert list_response.status_code == 200
        assert any(
            event["event_id"] == event_id
            for event in list_response.json()["items"]
        )


def test_invalid_severity_is_rejected():
    with TestClient(main.app) as client:
        response = client.post(
            "/api/v1/events",
            json={
                "source": "wireless",
                "finding_type": "invalid_test",
                "severity": "extreme",
                "summary": "This should fail validation",
            },
        )

    assert response.status_code == 422


def test_duplicate_event_id_is_rejected(tmp_path, monkeypatch):
    test_db = tmp_path / "duplicate_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        payload = {
            "event_id": "fixed-test-event-001",
            "source": "wireless",
            "finding_type": "duplicate_test",
            "severity": "low",
            "summary": "Duplicate ID test",
        }

        first_response = client.post(
            "/api/v1/events",
            json=payload,
        )
        second_response = client.post(
            "/api/v1/events",
            json=payload,
        )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

def test_filter_events_by_source_and_severity(tmp_path, monkeypatch):
    test_db = tmp_path / "filter_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        events = [
            {
                "source": "wireless",
                "finding_type": "ap_test",
                "severity": "high",
                "summary": "Wireless high severity event",
            },
            {
                "source": "android_api",
                "finding_type": "api_test",
                "severity": "medium",
                "summary": "Android medium severity event",
            },
        ]

        for event in events:
            response = client.post("/api/v1/events", json=event)
            assert response.status_code == 201

        response = client.get(
            "/api/v1/events",
            params={"source": "wireless", "severity": "high"},
        )

    assert response.status_code == 200
    data = response.json()
    results = data["items"]

    assert len(results) == 1
    assert results[0]["source"] == "wireless"
    assert results[0]["severity"] == "high"
    assert data["total"] == 1


def test_invalid_source_filter_is_rejected():
    with TestClient(main.app) as client:
        response = client.get(
            "/api/v1/events",
            params={"source": "unknown_module"},
        )

    assert response.status_code == 422


def test_event_limit_is_respected(tmp_path, monkeypatch):
    test_db = tmp_path / "limit_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        for index in range(3):
            response = client.post(
                "/api/v1/events",
                json={
                    "source": "wireless",
                    "finding_type": f"test_event_{index}",
                    "severity": "low",
                    "summary": f"Test event number {index}",
                },
            )
            assert response.status_code == 201

        response = client.get(
            "/api/v1/events",
            params={"limit": 1},
        )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_event_pagination_returns_different_pages(tmp_path, monkeypatch):
    test_db = tmp_path / "pagination_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        for index in range(5):
            response = client.post(
                "/api/v1/events",
                json={
                    "source": "wireless",
                    "finding_type": f"pagination_test_{index}",
                    "severity": "low",
                    "summary": f"Pagination event {index}",
                },
            )
            assert response.status_code == 201

        first_response = client.get(
            "/api/v1/events",
            params={"limit": 2, "offset": 0},
        )
        second_response = client.get(
            "/api/v1/events",
            params={"limit": 2, "offset": 2},
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_page = first_response.json()
    second_page = second_response.json()

    assert len(first_page["items"]) == 2
    assert len(second_page["items"]) == 2

    first_ids = {event["event_id"] for event in first_page["items"]}
    second_ids = {event["event_id"] for event in second_page["items"]}

    assert first_ids.isdisjoint(second_ids)


def test_negative_offset_is_rejected():
    with TestClient(main.app) as client:
        response = client.get(
            "/api/v1/events",
            params={"offset": -1},
        )

    assert response.status_code == 422


def test_event_can_be_created_and_retrieved(tmp_path, monkeypatch):
    test_db = tmp_path / "integration_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        create_response = client.post(
            "/api/v1/events",
            json={
                "source": "wireless",
                "finding_type": "suspicious_access_point",
                "severity": "medium",
                "asset_or_subject": "lab-ap-integration-test",
                "summary": "Synthetic event for an integration test.",
                "evidence_reference": "test-evidence-001",
                "rule_or_model_version": "test-rules-1.0",
            },
        )

        assert create_response.status_code == 201
        created_event = create_response.json()
        event_id = created_event["event_id"]

        retrieve_response = client.get(
            f"/api/v1/events/{event_id}"
        )

    assert retrieve_response.status_code == 200
    retrieved_event = retrieve_response.json()

    assert retrieved_event["event_id"] == event_id
    assert retrieved_event["source"] == "wireless"
    assert retrieved_event["finding_type"] == "suspicious_access_point"
    assert retrieved_event["severity"] == "medium"
    assert retrieved_event["evidence_reference"] == "test-evidence-001"


def test_list_events_returns_pagination_metadata(tmp_path, monkeypatch):
    test_db = tmp_path / "metadata_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        for index in range(3):
            response = client.post(
                "/api/v1/events",
                json={
                    "source": "wireless",
                    "finding_type": f"metadata_test_{index}",
                    "severity": "low",
                    "summary": f"Metadata test event {index}",
                },
            )
            assert response.status_code == 201

        response = client.get(
            "/api/v1/events",
            params={"limit": 2, "offset": 0},
        )

    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["has_more"] is True


def test_list_events_with_no_matches_returns_empty_page(tmp_path, monkeypatch):
    test_db = tmp_path / "empty_page_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        response = client.get("/api/v1/events")

    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert data["has_more"] is False


def test_list_events_offset_beyond_end_returns_empty_page(
    tmp_path, monkeypatch
):
    test_db = tmp_path / "offset_beyond_end_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        for index in range(3):
            response = client.post(
                "/api/v1/events",
                json={
                    "source": "wireless",
                    "finding_type": f"offset_test_{index}",
                    "severity": "low",
                    "summary": f"Offset test event {index}",
                },
            )
            assert response.status_code == 201

        response = client.get(
            "/api/v1/events",
            params={"limit": 2, "offset": 10},
        )

    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 10
    assert data["has_more"] is False


def test_filtered_event_total_counts_only_matching_events(
    tmp_path, monkeypatch
):
    test_db = tmp_path / "filtered_total_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    with TestClient(main.app) as client:
        events = [
            {
                "source": "wireless",
                "finding_type": "wireless_high",
                "severity": "high",
                "summary": "Wireless high event",
            },
            {
                "source": "wireless",
                "finding_type": "wireless_low",
                "severity": "low",
                "summary": "Wireless low event",
            },
            {
                "source": "android_api",
                "finding_type": "android_high",
                "severity": "high",
                "summary": "Android high event",
            },
        ]

        for event in events:
            response = client.post("/api/v1/events", json=event)
            assert response.status_code == 201

        response = client.get(
            "/api/v1/events",
            params={
                "source": "wireless",
                "severity": "high",
                "limit": 10,
                "offset": 0,
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["finding_type"] == "wireless_high"
    assert data["has_more"] is False
