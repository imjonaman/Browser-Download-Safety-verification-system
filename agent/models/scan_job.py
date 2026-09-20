"""ScanJob — represents a scanning task for a downloaded file."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ScanStatus(str, Enum):
    """Lifecycle states for a scan job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanJob(BaseModel):
    """A scan job that tracks the analysis of a single download."""

    job_id: UUID = Field(description="Unique identifier for this scan job")
    download_id: int = Field(description="Chrome download item ID being scanned")
    status: ScanStatus = Field(default=ScanStatus.PENDING, description="Current job status")
    created_at: datetime = Field(description="When the job was created")
    updated_at: datetime = Field(description="When the job was last updated")
