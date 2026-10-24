# NEXUS Backend

## Overview
The NEXUS backend provides a shared API for submitting, storing, filtering, and retrieving security events from supported monitoring modules.

## Requirements
- Python 3.13 or a compatible Python version
- Dependencies listed in `requirements.txt`

## Setup

Activate the virtual environment in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run the API

From the project root:

```powershell
python -m uvicorn backend.app.main:app --reload
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

Health check:

`GET /health`

## Event API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/events` | Submit a security event |
| GET | `/api/v1/events` | List events with filtering and pagination |
| GET | `/api/v1/events/{event_id}` | Retrieve an event by ID |

### List query parameters

- `limit`: Number of events to return; default 100, minimum 1, maximum 500.
- `offset`: Number of matching events to skip; default 0, minimum 0.
- `source`: Optional source filter.
- `severity`: Optional severity filter.

Supported sources:
- `wireless`
- `android_api`
- `privacy_guard`
- `system_log`

Supported severity levels:
- `info`
- `low`
- `medium`
- `high`
- `critical`

### Example event

```json
{
  "source": "wireless",
  "finding_type": "suspicious_access_point",
  "severity": "medium",
  "asset_or_subject": "lab-ap-01",
  "summary": "A test finding from the authorized wireless lab.",
  "evidence_reference": "lab-evidence-001",
  "rule_or_model_version": "wireless-rules-0.1"
}
```

The API generates an event ID and timestamp when they are omitted.

### Example requests

Submit an event:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/events" `
  -ContentType "application/json" `
  -Body '{"source":"wireless","finding_type":"suspicious_access_point","severity":"medium","summary":"Authorized lab test event"}'
```

List the first 10 events:

`GET /api/v1/events?limit=10&offset=0`

Filter by source and severity:

`GET /api/v1/events?source=wireless&severity=high&limit=10&offset=0`

Retrieve one event:

`GET /api/v1/events/{event_id}`

## Development and tests

Run the automated tests:

```powershell
python -m pytest -v
```

## Integration notes

- Use the documented source and severity values.
- Treat event IDs as unique identifiers.
- Send references to evidence rather than unnecessary sensitive raw payloads.
- `policy_decision` records a policy outcome such as `allow`, `redact`, `block`, or `approval_required`.
- `enforcement_result` records the observed enforcement status; it should not be assumed from the policy decision alone.
- The API currently uses SQLite for local development.
- Authentication, deployment hardening, and production database configuration must be addressed before production use.
