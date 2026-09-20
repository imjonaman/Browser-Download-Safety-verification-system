"""Message protocol models for native messaging communication."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Discriminator for native messaging message types.

    Aligned with Phase 1 spec — communication-only, no file analysis yet.
    """

    HELLO = "HELLO"
    HELLO_ACK = "HELLO_ACK"
    DOWNLOAD_STARTED = "DOWNLOAD_STARTED"
    DOWNLOAD_PROGRESS = "DOWNLOAD_PROGRESS"
    SCAN_REQUEST = "SCAN_REQUEST"
    SCAN_PROGRESS = "SCAN_PROGRESS"
    EVIDENCE_UPDATE = "EVIDENCE_UPDATE"
    RISK_UPDATE = "RISK_UPDATE"
    SCAN_COMPLETE = "SCAN_COMPLETE"
    ANALYSIS_INCOMPLETE = "ANALYSIS_INCOMPLETE"
    ERROR = "ERROR"


class MessageEnvelope(BaseModel):
    """Standard envelope wrapping every native messaging payload."""

    type: MessageType = Field(description="Message type discriminator")
    version: str = Field(default="1", description="Protocol version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Sender wall-clock time"
    )
    correlation_id: UUID = Field(
        default_factory=uuid4, description="Ties request to response"
    )
    payload: dict[str, Any] = Field(default_factory=dict, description="Type-specific data")


# ── HELLO ────────────────────────────────────────────────────────────


class HelloPayload(BaseModel):
    """Payload for a HELLO message from the extension."""

    extension_version: str = Field(description="Version of the Chrome extension")


class HelloAckPayload(BaseModel):
    """Payload for a HELLO_ACK response from the agent."""

    agent_version: str = Field(description="Version of the Python agent")
    protocol_version: str = Field(default="1", description="Supported protocol version")
    capabilities: list[str] = Field(
        default_factory=lambda: ["scan", "yara", "provenance"],
        description="List of agent capabilities",
    )


# ── Download Events ──────────────────────────────────────────────────


class DownloadStartedPayload(BaseModel):
    """Payload for DOWNLOAD_STARTED — sent when a new download begins."""

    download_id: int = Field(description="Chrome download item ID")
    url: str = Field(description="URL being downloaded")
    final_url: str = Field(default="", description="Final URL after redirects")
    filename: str = Field(default="", description="Suggested filename")
    mime: str = Field(default="", description="MIME type")
    file_size: int = Field(default=-1, description="Total size in bytes, -1 if unknown")
    referrer: str = Field(default="", description="Referrer URL")
    tab_id: int = Field(default=-1, description="Tab that initiated the download")


class DownloadProgressPayload(BaseModel):
    """Payload for DOWNLOAD_PROGRESS — sent on download state changes."""

    download_id: int = Field(description="Chrome download item ID")
    state: str = Field(description="Download state (in_progress, complete, interrupted)")
    bytes_received: int = Field(default=0, description="Bytes received so far")
    total_bytes: int = Field(default=-1, description="Total size in bytes, -1 if unknown")
    filename: str = Field(default="", description="Final resolved filename")


# ── Error ────────────────────────────────────────────────────────────


class ErrorPayload(BaseModel):
    """Payload for ERROR messages."""

    error: str = Field(description="Human-readable error description")
    original_type: str = Field(default="", description="The message type that caused the error")
    details: str = Field(default="", description="Additional context or traceback summary")
