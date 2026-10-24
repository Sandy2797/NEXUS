
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
            for event in list_response.json()
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
    results = response.json()
    assert len(results) == 1
    assert results[0]["source"] == "wireless"
    assert results[0]["severity"] == "high"


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
    assert len(response.json()) == 1


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

    assert len(first_page) == 2
    assert len(second_page) == 2

    first_ids = {event["event_id"] for event in first_page}
    second_ids = {event["event_id"] for event in second_page}

    assert first_ids.isdisjoint(second_ids)


def test_negative_offset_is_rejected():
    with TestClient(main.app) as client:
        response = client.get(
            "/api/v1/events",
            params={"offset": -1},
        )

    assert response.status_code == 422
