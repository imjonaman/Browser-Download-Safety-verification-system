"""BrowserEvent — captures navigation and tab activity from the extension."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BrowserEvent(BaseModel):
    """A browser navigation or tab event forwarded by the extension."""

    event_id: UUID = Field(description="Unique identifier for this event")
    tab_id: int = Field(description="Chrome tab ID where the event occurred")
    url: str = Field(description="URL of the page")
    referrer: str = Field(default="", description="Referrer URL, if any")
    timestamp: datetime = Field(description="When the event occurred")
    action_type: str = Field(description="Type of browser action (navigate, reload, link_click, etc.)")
