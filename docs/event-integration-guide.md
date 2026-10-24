# NEXUS Event Integration Guide

## 1. Purpose

This guide explains how NEXUS modules submit security events to the shared backend API.

## 2. Start the backend

From the NEXUS project root, activate the virtual environment and run:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload
```

The local API base URL is `http://127.0.0.1:8000`.

Interactive documentation is available at `http://127.0.0.1:8000/docs`.

## 3. Submit an event

Send a `POST` request to `/api/v1/events` with a JSON body.

Example:

```json
{
  "source": "wireless",
  "finding_type": "suspicious_access_point",
  "severity": "medium",
  "summary": "A suspicious access point was observed in an authorized lab."
}
```

A successful request returns HTTP `201 Created` and the stored event, including its generated event ID and timestamp.

## 4. Supported sources

- `wireless`
- `android_api`
- `privacy_guard`
- `system_log`

## 5. Severity levels

- `info`
- `low`
- `medium`
- `high`
- `critical`

## 6. Policy and enforcement fields

`policy_decision` describes the intended policy outcome: `allow`, `redact`, `block`, or `approval_required`.

`enforcement_result` records the observed outcome: `not_applicable`, `forwarded`, `redacted`, `blocked`, `pending_approval`, or `failed`.

Do not assume that a policy decision proves enforcement succeeded.

## 7. Query events

List events:

`GET /api/v1/events?limit=10&offset=0`

Filter events:

`GET /api/v1/events?source=wireless&severity=high&limit=10&offset=0`

Retrieve a specific event:

`GET /api/v1/events/{event_id}`

## 8. Error handling

- `201`: event created successfully.
- `404`: requested event was not found.
- `409`: event ID already exists.
- `422`: request or query parameters failed validation.

If submission fails, record the status code and safe diagnostic details. Avoid logging raw sensitive payloads or credentials.

## 9. Integration notes

- Use only the documented enum values.
- Include concise summaries and evidence references where available.
- Do not include unnecessary sensitive data in event summaries.
- Test integrations against the local development API before shared demonstrations.
- The current setup is for development; production authentication and deployment hardening remain separate tasks.
