"""Native messaging host — reads/writes length-prefixed JSON over stdio.

Phase 1: Communication-only. Validates every inbound message with Pydantic,
rejects unknown types and malformed payloads with structured ERROR responses,
and never crashes.
"""

from __future__ import annotations

import json
import struct
import sys
import traceback

from agent import __version__
from agent.logging_config import get_logger
from agent.models.messages import (
    DownloadProgressPayload,
    DownloadStartedPayload,
    ErrorPayload,
    HelloAckPayload,
    MessageEnvelope,
    MessageType,
)

logger = get_logger("native_messaging.host")


def read_message() -> dict | None:
    """Read a single length-prefixed JSON message from stdin.

    Returns None when stdin is closed. Never raises — returns an error
    dict for malformed input.
    """
    try:
        raw_length = sys.stdin.buffer.read(4)

        if not raw_length:
            return None

        if len(raw_length) < 4:
            return {"__parse_error": "Incomplete message length header"}

        message_length = struct.unpack("<I", raw_length)[0]

        # Guard against absurdly large messages (> 10 MB)
        if message_length > 10 * 1024 * 1024:
            return {"__parse_error": f"Message too large: {message_length} bytes"}

        message = sys.stdin.buffer.read(message_length)

        if len(message) < message_length:
            return {"__parse_error": "Message truncated"}

        return json.loads(message.decode("utf-8"))

    except json.JSONDecodeError as exc:
        return {"__parse_error": f"Invalid JSON: {exc}"}
    except Exception as exc:
        return {"__parse_error": f"Read error: {exc}"}


def send_message(message: dict) -> None:
    """Write a length-prefixed JSON message to stdout."""
    encoded = json.dumps(message).encode("utf-8")

    sys.stdout.buffer.write(struct.pack("<I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _make_error(
    error: str,
    *,
    correlation_id: str | None = None,
    original_type: str = "",
    details: str = "",
) -> dict:
    """Build a structured ERROR envelope."""
    envelope = MessageEnvelope(
        type=MessageType.ERROR,
        payload=ErrorPayload(
            error=error,
            original_type=original_type,
            details=details,
        ).model_dump(),
    )
    if correlation_id:
        from uuid import UUID

        try:
            envelope.correlation_id = UUID(correlation_id)
        except (ValueError, AttributeError):
            pass
    return envelope.model_dump(mode="json")


def handle_message(raw: dict) -> dict:
    """Route an incoming message and return a response dict.

    Never raises — always returns a valid response envelope.
    """
    # ── Handle parse errors from read_message ────────────────────────
    if "__parse_error" in raw:
        error_msg = raw["__parse_error"]
        logger.error("Parse error: %s", error_msg)
        return _make_error(error_msg)

    # ── Validate envelope with Pydantic ──────────────────────────────
    try:
        envelope = MessageEnvelope.model_validate(raw)
    except Exception as exc:
        logger.error("Invalid message schema: %s", exc)
        return _make_error(
            "Invalid message schema",
            correlation_id=raw.get("correlation_id"),
            original_type=raw.get("type", ""),
            details=str(exc),
        )

    cid = str(envelope.correlation_id)

    # ── HELLO ────────────────────────────────────────────────────────
    if envelope.type == MessageType.HELLO:
        logger.info("HELLO received", extra={"event_id": cid})

        ack_payload = HelloAckPayload(
            agent_version=__version__,
            protocol_version="1",
            capabilities=["scan", "yara", "provenance"],
        )
        response = MessageEnvelope(
            type=MessageType.HELLO_ACK,
            correlation_id=envelope.correlation_id,
            payload=ack_payload.model_dump(),
        )
        return response.model_dump(mode="json")

    # ── DOWNLOAD_STARTED ─────────────────────────────────────────────
    if envelope.type == MessageType.DOWNLOAD_STARTED:
        try:
            payload = DownloadStartedPayload.model_validate(envelope.payload)
        except Exception as exc:
            return _make_error(
                "Invalid DOWNLOAD_STARTED payload",
                correlation_id=cid,
                original_type="DOWNLOAD_STARTED",
                details=str(exc),
            )

        logger.info(
            "Download started: %s (%s)",
            payload.filename or payload.url,
            payload.mime,
            extra={"event_id": cid},
        )
        # Phase 1: acknowledge receipt, no scanning yet
        return MessageEnvelope(
            type=MessageType.DOWNLOAD_PROGRESS,
            correlation_id=envelope.correlation_id,
            payload={"download_id": payload.download_id, "status": "received"},
        ).model_dump(mode="json")

    # ── DOWNLOAD_PROGRESS ────────────────────────────────────────────
    if envelope.type == MessageType.DOWNLOAD_PROGRESS:
        try:
            payload = DownloadProgressPayload.model_validate(envelope.payload)
        except Exception as exc:
            return _make_error(
                "Invalid DOWNLOAD_PROGRESS payload",
                correlation_id=cid,
                original_type="DOWNLOAD_PROGRESS",
                details=str(exc),
            )

        logger.info(
            "Download progress: id=%d state=%s (%d/%d bytes)",
            payload.download_id,
            payload.state,
            payload.bytes_received,
            payload.total_bytes,
            extra={"event_id": cid},
        )
        # Phase 1: acknowledge, no action yet
        return MessageEnvelope(
            type=MessageType.DOWNLOAD_PROGRESS,
            correlation_id=envelope.correlation_id,
            payload={
                "download_id": payload.download_id,
                "status": "acknowledged",
                "state": payload.state,
            },
        ).model_dump(mode="json")

    # ── SCAN_REQUEST ─────────────────────────────────────────────────
    if envelope.type == MessageType.SCAN_REQUEST:
        logger.info("Scan requested (Phase 1: no analysis)", extra={"event_id": cid})
        # Phase 1: communication-only, return ANALYSIS_INCOMPLETE
        return MessageEnvelope(
            type=MessageType.ANALYSIS_INCOMPLETE,
            correlation_id=envelope.correlation_id,
            payload={
                "reason": "No analyzers available in Phase 1",
                "status": "not_implemented",
            },
        ).model_dump(mode="json")

    # ── Unknown message type ─────────────────────────────────────────
    logger.warning("Unknown message type: %s", envelope.type, extra={"event_id": cid})
    return _make_error(
        f"Unknown message type: {envelope.type}",
        correlation_id=cid,
        original_type=str(envelope.type),
    )


def run() -> None:
    """Main loop: read messages, handle them, write responses.

    Never crashes — all exceptions are caught and returned as ERROR messages.
    """
    logger.info("Native messaging host started (Phase 1)")

    while True:
        try:
            message = read_message()

            if message is None:
                logger.info("Stdin closed, shutting down")
                break

            response = handle_message(message)
            send_message(response)

        except Exception:
            # Absolute last-resort safety net — should never reach here,
            # but we must never crash.
            logger.critical("Unhandled exception in main loop", exc_info=True)
            try:
                error_response = _make_error(
                    "Internal agent error",
                    details=traceback.format_exc(),
                )
                send_message(error_response)
            except Exception:
                pass  # If we can't even send an error, just continue