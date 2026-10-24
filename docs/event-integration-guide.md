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

The `event_id`, `timestamp`, `schema_version`, and `enforcement_result` fields have defaults when omitted. The backend generates the event ID and UTC timestamp; `schema_version` defaults to `1.0`, and `enforcement_result` defaults to `not_applicable`. Clients may supply these fields explicitly when appropriate.

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

### List events

Use `GET /api/v1/events` to retrieve security events.

Example request:

```http
GET /api/v1/events?limit=10&offset=0
```

The endpoint supports pagination and optional filtering:

- `limit`: maximum number of events to return (default: `100`, maximum: `500`).
- `offset`: number of matching events to skip (default: `0`).
- `source`: optional source filter, such as `wireless`.
- `severity`: optional severity filter, such as `high`.

Example request with filters:

```http
GET /api/v1/events?source=wireless&severity=high&limit=10&offset=0
```

The response is a JSON object containing the event list and pagination metadata.

Example response:

```json
{
  "items": [
    {
      "event_id": "example-event-id",
      "schema_version": "1.0",
      "timestamp": "2026-10-24T12:00:00Z",
      "source": "wireless",
      "finding_type": "suspicious_access_point",
      "severity": "high",
      "asset_or_subject": null,
      "summary": "A suspicious access point was observed in an authorized lab.",
      "evidence_reference": null,
      "rule_or_model_version": null,
      "policy_decision": null,
      "enforcement_result": "not_applicable"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0,
  "has_more": false
}
```

The example values are illustrative.

Response fields:

- `items`: events returned for the requested page.
- `total`: total number of events matching the supplied filters, before pagination.
- `limit`: maximum number of events requested.
- `offset`: number of matching events skipped.
- `has_more`: `true` when more matching events remain after the current page; otherwise `false`.

When integrating with the API, read event records from `items`, not directly from the top-level response.

### Retrieve a specific event

Use `GET /api/v1/events/{event_id}` to retrieve one event by its ID. This endpoint returns the event object directly, rather than the paginated response format.

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

## 10. Module integration responsibilities

All modules must use the shared `SecurityEvent` contract documented in `docs/event-contract.md`. The backend API is the common ingestion and retrieval interface.

### Wireless module — Seif

- Submit normalized wireless findings using `source: "wireless"`.
- Use a meaningful `finding_type` and an allowed severity.
- Use synthetic or authorized lab data for development and demonstrations.
- Keep evidence in the appropriate evidence store and provide an `evidence_reference` when available; do not put unnecessary raw capture data in the event summary.

### Android/API policy module — Mohamed

- Submit relevant findings using `source: "android_api"`.
- Set `policy_decision` when a policy outcome has been determined.
- Set `enforcement_result` to the observed result, not merely the intended action.
- Keep policy decisions and enforcement outcomes distinct.

### Privacy module — Nada

- Submit privacy findings using `source: "privacy_guard"`.
- Use concise summaries and evidence references rather than raw sensitive input.
- Do not include credentials, tokens, or unnecessary personal or confidential data in event summaries.
- Confirm the privacy module's redaction and evidence-handling behavior with the team before integration.

### Dashboard — Rana

- Retrieve events through `GET /api/v1/events`.
- Read records from the response's `items` array and use `total`, `limit`, `offset`, and `has_more` for pagination.
- Handle loading, empty results, and API errors explicitly.
- Treat event fields as potentially absent or `null` where the contract permits this.
- Do not assume that a policy decision means enforcement succeeded.

### Backend and integration — Sandy

- Maintain the shared event model, API validation, persistence, and integration documentation.
- Validate incoming events against the agreed contract.
- Coordinate contract changes with the other module owners before changing field names, allowed values, or endpoint behavior.

## 11. Dashboard response expectations

For `GET /api/v1/events`, the dashboard should expect this response structure:

- `items`: array of event objects.
- `total`: number of matching events before pagination.
- `limit`: requested page size.
- `offset`: number of matching records skipped.
- `has_more`: whether additional matching events remain.

The dashboard should provide clear states for:

1. **Loading:** the request is in progress.
2. **Populated:** one or more events are available.
3. **Empty:** the request succeeded but no events match.
4. **Error:** the request failed; display a useful message without exposing sensitive backend details.

These are client-side integration expectations, not additional backend endpoints.

## 12. Integration acceptance checklist

Before a shared demonstration, verify that:

- [ ] Each module owner can produce an event using an agreed source and finding type.
- [ ] A valid event can be submitted to `POST /api/v1/events`.
- [ ] The created event can be retrieved by its `event_id`.
- [ ] The dashboard can parse the list response and its pagination metadata.
- [ ] The dashboard handles loading, empty, and error states.
- [ ] Invalid event values are rejected by the API.
- [ ] Synthetic examples are used for the demonstration.
- [ ] No unnecessary raw sensitive data or credentials are included in event summaries.
- [ ] Any unresolved contract decisions are documented and assigned to the relevant owner.

Passing these checks demonstrates basic integration readiness; it does not establish production readiness or prove that all privacy and security controls are implemented.
