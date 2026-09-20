"""Decision — the final action taken on a scanned download."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Action(str, Enum):
    """Possible actions the agent can take on a download."""

    ALLOW = "allow"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    WARN = "warn"


class Decision(BaseModel):
    """The final verdict and action taken for a scan job."""

    job_id: UUID = Field(description="Scan job this decision applies to")
    action: Action = Field(description="Action taken (allow, block, quarantine, warn)")
    actor: str = Field(description="Who or what made the decision (auto, user, policy)")
    reason: str = Field(description="Human-readable explanation for the decision")
    timestamp: datetime = Field(description="When the decision was made")
