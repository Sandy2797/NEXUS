# NEXUS Security Event Contract

**Contract version:** 1.0.0 (proposed)  
**Status:** Pending team review  
**Owner:** Sandy Hesham Lotfy  
**API prefix:** `/api/v1`

## 1. Purpose

This document defines the shared event format used by NEXUS modules to submit normalized security findings to the backend.

This contract describes the current `SecurityEvent` implementation. It is a proposed canonical contract until the team approves it.

## 2. API Endpoints

| Method | Endpoint | Purpose | Success |
|---|---|---|---|
| GET | `/health` | Check backend health | 200 |
| POST | `/api/v1/events` | Submit a security event | 201 |
| GET | `/api/v1/events` | List events with pagination and filters | 200 |
| GET | `/api/v1/events/{event_id}` | Retrieve an event by ID | 200 |

The interactive API documentation is available at `/docs` while the local backend is running.

## 3. SecurityEvent fields

| Field | Meaning |
|---|---|
| `event_id` | Unique event identifier; generated when omitted |
| `schema_version` | Event contract version; defaults to `1.0` |
| `timestamp` | Event timestamp; generated in UTC when omitted |
| `source` | Originating module |
| `finding_type` | Normalized finding or detection category |
| `severity` | Severity classification |
| `asset_or_subject` | Optional affected asset or subject reference |
| `summary` | Short description of the finding |
| `evidence_reference` | Optional reference to supporting evidence |
| `rule_or_model_version` | Optional detector or rule version |
| `policy_decision` | Optional policy outcome |
| `enforcement_result` | Enforcement outcome; defaults to `not_applicable` |

### Allowed values

**`source`**
- `wireless`
- `android_api`
- `privacy_guard`
- `system_log`

**`severity`**
- `info`
- `low`
- `medium`
- `high`
- `critical`

**`policy_decision`**
- `allow`
- `redact`
- `block`
- `approval_required`

**`enforcement_result`**
- `not_applicable`
- `forwarded`
- `redacted`
- `blocked`
- `pending_approval`
- `failed`

The backend schema is authoritative for required fields, defaults, field types, and rejection of unknown fields. Refer to `backend/app/schemas/event.py`.

## 4. Integration rules

1. Every module must submit normalized events using the agreed schema.
2. Use synthetic fixtures for development and testing.
3. Do not include raw prompts, credentials, tokens, or unnecessary personal data in summaries or evidence.
4. Keep `policy_decision` separate from `enforcement_result`. A recommendation to block does not prove that enforcement succeeded.
5. Preserve the originating `source` value so wireless events are not confused with privacy or API findings.
6. Coordinate schema changes with the backend owner before adopting them.
7. Treat this contract as proposed until the team confirms it.

## 5. Pagination and filtering

`GET /api/v1/events` supports:
- `limit`: page size
- `offset`: number of records to skip
- `source`: optional source filter
- `severity`: optional severity filter

The response uses an `EventPage` structure containing `items`, `total`, `limit`, `offset`, and `has_more`.

## 6. Error handling

Clients should inspect HTTP status codes and response details rather than assuming a request succeeded.

- `201`: event created
- `200`: request succeeded
- `404`: requested event was not found
- `409`: duplicate event identifier
- `422`: invalid request or filter values

Database failure and degraded-health behavior still require explicit verification.

## 7. Current limitations and pending work

- Team approval of this contract is pending.
- Module-to-backend integration has not yet been completed.
- A standalone JSON Schema file and dedicated contract tests are pending.
- Correlation IDs and explicit inspection-status semantics are not yet confirmed.
- Redaction guarantees and secret-free logging require dedicated verification.
- The service is a local development prototype, not a production-ready security system.

## 8. Approval record

| Role | Status |
|---|---|
| Sandy — backend | Proposed |
| Seif — wireless | Pending |
| Nada — AI/privacy | Pending |
| Mohamed — Android/API policy | Pending |
| Rana — dashboard | Pending |
| Abdelrahman — gateway | Pending where applicable |