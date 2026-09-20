"""RiskSnapshot — aggregated risk assessment for a completed scan."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RiskSnapshot(BaseModel):
    """An aggregated risk score produced after all evidence is collected."""

    job_id: UUID = Field(description="Scan job this snapshot belongs to")
    score: float = Field(ge=0.0, le=100.0, description="Overall risk score 0–100")
    classification: str = Field(description="Risk classification (safe, suspicious, malicious)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the classification 0.0–1.0")
    coverage: float = Field(
        ge=0.0, le=1.0, description="Fraction of analysis modules that completed 0.0–1.0"
    )
    evidence_set_version: str = Field(
        description="Version hash of the evidence set used for scoring"
    )
    timestamp: datetime = Field(description="When this snapshot was generated")
