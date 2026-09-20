"""DownloadEvent — tracks download lifecycle state changes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DownloadEvent(BaseModel):
    """A download state-change event from the browser downloads API."""

    download_id: int = Field(description="Chrome download item ID")
    event_id: UUID = Field(description="Unique identifier for this event")
    original_url: str = Field(description="URL that initiated the download")
    final_url: str = Field(description="Final URL after redirects")
    filename: str = Field(description="Name of the downloaded file")
    mime: str = Field(description="MIME type of the download")
    bytes_received: int = Field(default=0, description="Bytes received so far")
    state: str = Field(description="Download state (in_progress, complete, interrupted)")
    timestamp: datetime = Field(description="When this state change occurred")
