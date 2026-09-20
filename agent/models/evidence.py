"""Evidence — individual risk signals discovered during a scan."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for evidence items."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceStatus(str, Enum):
    """Lifecycle states for an evidence item."""

    ACTIVE = "active"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"


class Evidence(BaseModel):
    """A single piece of risk evidence found by an analysis module."""

    evidence_id: UUID = Field(description="Unique identifier for this evidence")
    job_id: UUID = Field(description="Scan job that produced this evidence")
    module: str = Field(description="Analysis module that generated this (e.g. yara, provenance)")
    feature: str = Field(description="Specific feature or indicator name")
    value: Any = Field(default=None, description="The detected value")
    details: str = Field(default="", description="Human-readable explanation")
    severity: Severity = Field(description="How severe this finding is")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0–1.0")
    rule_id: str = Field(default="", description="Identifier of the rule that matched")
    timestamp: datetime = Field(description="When this evidence was produced")
    status: EvidenceStatus = Field(
        default=EvidenceStatus.ACTIVE, description="Current status of this evidence"
    )
