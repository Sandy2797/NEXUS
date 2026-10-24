# NEXUS API Error Reference

**API version:** `/api/v1`  
**Status:** Proposed contract; pending team review

## 1. Purpose

This document describes the HTTP responses clients may receive when interacting with the NEXUS event API.

## 2. Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| POST | `/api/v1/events` | Submit a security event |
| GET | `/api/v1/events` | List events with optional filters and pagination |
| GET | `/api/v1/events/{event_id}` | Retrieve one event by ID |

Interactive API documentation is available at `/docs` while the FastAPI application is running.

## 3. Success responses

| HTTP status | Meaning |
|---|---|
| `200 OK` | Health check, event listing, or event retrieval succeeded |
| `201 Created` | Event was accepted and saved |

The event-list endpoint returns an object containing `items`, `total`, `limit`, `offset`, and `has_more`.

## 4. Client error responses

| HTTP status | Meaning | Typical cause |
|---|---|---|
| `404 Not Found` | Requested event does not exist | Unknown `event_id` |
| `409 Conflict` | Event conflicts with an existing record | Duplicate `event_id` |
| `422 Unprocessable Entity` | Request parameters or event data are invalid | Missing required field, invalid severity, unsupported source, invalid timestamp, or invalid pagination value |

FastAPI may return a `422` response when request-body validation fails. The exact response structure can vary by error type.

### Example: duplicate event

A request using an `event_id` that already exists returns `409 Conflict`.

```json
{
  "detail": "An event with this event_id already exists."
}
```

### Example: event not found

Requesting a nonexistent event returns `404 Not Found`.

```json
{
  "detail": "Event not found."
}
```

### Example: invalid filter

An unsupported `source` or `severity` filter returns `422 Unprocessable Entity`.

## 5. Pagination and filter constraints

The event-list endpoint supports:

- `limit`: integer from 1 to 500; default 100.
- `offset`: integer greater than or equal to 0; default 0.
- `source`: optional supported event source.
- `severity`: optional supported severity.

Supported sources are `wireless`, `android_api`, `privacy_guard`, and `system_log`.

Supported severities are `info`, `low`, `medium`, `high`, and `critical`.

## 6. Server errors and security

Unexpected database or server errors may result in a `500 Internal Server Error`. Their behavior and response format have not yet been standardized by the NEXUS API contract.

Clients should not retry invalid requests without correcting them. For transient server failures, clients should use bounded retries with backoff where appropriate.

The backend must not expose passwords, access tokens, raw prompts, or other sensitive payloads in error messages or logs. This requirement still needs explicit implementation and verification.

## 7. Known limitations

- A standardized error response model has not yet been implemented.
- Database failure handling and degraded health reporting need verification.
- Error responses have not yet been checked against every endpoint using dedicated contract tests.
- This API is a graduation-project prototype and is not yet certified as production-ready.

## 8. Change management

Changes to endpoint behavior, status codes, validation rules, or response structures should be reflected in this document and reviewed with the NEXUS integration team.
