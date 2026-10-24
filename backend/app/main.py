
from contextlib import asynccontextmanager
import sqlite3

from fastapi import FastAPI, HTTPException, Query, status

from backend.app.schemas.event import SecurityEvent
from backend.app.storage import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize_database()
    yield


app = FastAPI(
    title="NEXUS Security Platform API",
    description="Shared event ingestion API for the NEXUS cybersecurity platform.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "nexus-backend",
    }


@app.post(
    "/api/v1/events",
    response_model=SecurityEvent,
    status_code=status.HTTP_201_CREATED,
)
def create_event(event: SecurityEvent):
    try:
        database.save_event(event)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An event with this event_id already exists.",
        )

    return event



@app.get("/api/v1/events", response_model=list[SecurityEvent])
def get_events(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    source: str | None = None,
    severity: str | None = None,
):
    valid_sources = {
        "wireless",
        "android_api",
        "privacy_guard",
        "system_log",
    }
    valid_severities = {
        "info",
        "low",
        "medium",
        "high",
        "critical",
    }

    if source is not None and source not in valid_sources:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid source. Choose from: {sorted(valid_sources)}",
        )

    if severity is not None and severity not in valid_severities:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid severity. Choose from: {sorted(valid_severities)}",
        )


    return database.list_events(
        limit=limit,
        offset=offset,
        source=source,
        severity=severity,
    )


@app.get("/api/v1/events/{event_id}", response_model=SecurityEvent)
def get_event(event_id: str):
    event = database.get_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    return event
