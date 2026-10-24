
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


Source = Literal[
    "wireless",
    "android_api",
    "privacy_guard",
    "system_log",
]

Severity = Literal["info", "low", "medium", "high", "critical"]

PolicyDecision = Literal[
    "allow",
    "redact",
    "block",
    "approval_required",
]

EnforcementResult = Literal[
    "not_applicable",
    "forwarded",
    "redacted",
    "blocked",
    "pending_approval",
    "failed",
]


class SecurityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        min_length=1,
        max_length=100,
    )
    schema_version: Literal["1.0"] = "1.0"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    source: Source
    finding_type: str = Field(min_length=1, max_length=100)
    severity: Severity

    asset_or_subject: str | None = Field(default=None, max_length=250)
    summary: str = Field(min_length=1, max_length=2000)
    evidence_reference: str | None = Field(default=None, max_length=500)
    rule_or_model_version: str | None = Field(default=None, max_length=100)

    policy_decision: PolicyDecision | None = None
    enforcement_result: EnforcementResult = "not_applicable"


class EventPage(BaseModel):
    items: list[SecurityEvent]
    total: int
    limit: int
    offset: int
    has_more: bool
