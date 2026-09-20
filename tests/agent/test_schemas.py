"""Tests for all core Pydantic schemas, Phase 1 message handling,
and acceptance criteria (malformed JSON, invalid schemas, unknown types)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agent.models import (
    BrowserEvent,
    Decision,
    DownloadEvent,
    DownloadProgressPayload,
    DownloadStartedPayload,
    ErrorPayload,
    Evidence,
    HelloAckPayload,
    HelloPayload,
    MessageEnvelope,
    MessageType,
    RiskSnapshot,
    RuleVersion,
    ScanJob,
)
from agent.native_messaging.host import handle_message


# ── BrowserEvent ─────────────────────────────────────────────────────


class TestBrowserEvent:
    def test_valid(self):
        ev = BrowserEvent(
            event_id=uuid4(),
            tab_id=42,
            url="https://example.com",
            referrer="https://google.com",
            timestamp=datetime.now(tz=timezone.utc),
            action_type="navigate",
        )
        assert ev.tab_id == 42
        assert ev.action_type == "navigate"

    def test_serialization_roundtrip(self):
        ev = BrowserEvent(
            event_id=uuid4(),
            tab_id=1,
            url="https://example.com",
            referrer="",
            timestamp=datetime.now(tz=timezone.utc),
            action_type="reload",
        )
        data = ev.model_dump(mode="json")
        restored = BrowserEvent.model_validate(data)
        assert restored.url == ev.url


# ── DownloadEvent ────────────────────────────────────────────────────


class TestDownloadEvent:
    def test_valid(self):
        ev = DownloadEvent(
            download_id=100,
            event_id=uuid4(),
            original_url="https://example.com/file.zip",
            final_url="https://cdn.example.com/file.zip",
            filename="file.zip",
            mime="application/zip",
            bytes_received=1024,
            state="in_progress",
            timestamp=datetime.now(tz=timezone.utc),
        )
        assert ev.mime == "application/zip"


# ── ScanJob ──────────────────────────────────────────────────────────


class TestScanJob:
    def test_defaults_to_pending(self):
        job = ScanJob(
            job_id=uuid4(),
            download_id=1,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        assert job.status.value == "pending"


# ── Evidence ─────────────────────────────────────────────────────────


class TestEvidence:
    def test_confidence_range(self):
        with pytest.raises(ValidationError):
            Evidence(
                evidence_id=uuid4(),
                job_id=uuid4(),
                module="yara",
                feature="suspicious_strings",
                severity="high",
                confidence=1.5,  # out of range
                timestamp=datetime.now(tz=timezone.utc),
            )

    def test_valid_evidence(self):
        ev = Evidence(
            evidence_id=uuid4(),
            job_id=uuid4(),
            module="yara",
            feature="suspicious_strings",
            value="eval(atob(...))",
            details="Obfuscated JavaScript detected",
            severity="high",
            confidence=0.92,
            rule_id="YARA_JS_OBFUSC_001",
            timestamp=datetime.now(tz=timezone.utc),
        )
        assert ev.confidence == 0.92


# ── RiskSnapshot ─────────────────────────────────────────────────────


class TestRiskSnapshot:
    def test_valid(self):
        snap = RiskSnapshot(
            job_id=uuid4(),
            score=75.5,
            classification="suspicious",
            confidence=0.88,
            coverage=0.95,
            evidence_set_version="abc123",
            timestamp=datetime.now(tz=timezone.utc),
        )
        assert snap.classification == "suspicious"

    def test_score_range(self):
        with pytest.raises(ValidationError):
            RiskSnapshot(
                job_id=uuid4(),
                score=150,  # out of range
                classification="malicious",
                confidence=0.99,
                coverage=1.0,
                evidence_set_version="xyz",
                timestamp=datetime.now(tz=timezone.utc),
            )


# ── Decision ─────────────────────────────────────────────────────────


class TestDecision:
    def test_valid(self):
        d = Decision(
            job_id=uuid4(),
            action="block",
            actor="auto",
            reason="High risk score",
            timestamp=datetime.now(tz=timezone.utc),
        )
        assert d.action.value == "block"


# ── RuleVersion ──────────────────────────────────────────────────────


class TestRuleVersion:
    def test_valid(self):
        rv = RuleVersion(
            pack="yara-community",
            version="1.2.0",
            hash_signature="sha256:abcdef1234567890",
            installed_at=datetime.now(tz=timezone.utc),
        )
        assert rv.pack == "yara-community"


# ── Phase 1 Message Types ───────────────────────────────────────────


class TestPhase1MessageTypes:
    """Verify Phase 1 message types are defined correctly."""

    def test_all_phase1_types_exist(self):
        expected = {
            "HELLO", "HELLO_ACK",
            "DOWNLOAD_STARTED", "DOWNLOAD_PROGRESS",
            "SCAN_REQUEST", "SCAN_PROGRESS",
            "EVIDENCE_UPDATE", "RISK_UPDATE",
            "SCAN_COMPLETE", "ANALYSIS_INCOMPLETE",
            "ERROR",
        }
        actual = {t.value for t in MessageType}
        assert actual == expected

    def test_download_started_payload(self):
        p = DownloadStartedPayload(
            download_id=42,
            url="https://example.com/file.zip",
            final_url="https://cdn.example.com/file.zip",
            filename="file.zip",
            mime="application/zip",
            file_size=1024000,
            referrer="https://example.com",
            tab_id=5,
        )
        assert p.download_id == 42
        assert p.mime == "application/zip"

    def test_download_progress_payload(self):
        p = DownloadProgressPayload(
            download_id=42,
            state="in_progress",
            bytes_received=512000,
            total_bytes=1024000,
            filename="file.zip",
        )
        assert p.bytes_received == 512000

    def test_error_payload(self):
        p = ErrorPayload(
            error="Something went wrong",
            original_type="DOWNLOAD_STARTED",
            details="Missing required field: url",
        )
        assert p.error == "Something went wrong"


# ── HELLO Message Round-Trip ─────────────────────────────────────────


class TestHelloRoundTrip:
    """Verify that a HELLO message can be serialized by TypeScript-compatible
    JSON and parsed back by Pydantic (simulates the TS→Python path)."""

    def test_hello_serialize_and_parse(self):
        hello_json = {
            "type": "HELLO",
            "version": "1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "correlation_id": str(uuid4()),
            "payload": {"extension_version": "0.1.0"},
        }

        envelope = MessageEnvelope.model_validate(hello_json)
        assert envelope.type == MessageType.HELLO
        assert envelope.version == "1"

        payload = HelloPayload.model_validate(envelope.payload)
        assert payload.extension_version == "0.1.0"

    def test_hello_ack_serialize(self):
        ack = HelloAckPayload(
            agent_version="0.1.0",
            protocol_version="1",
            capabilities=["scan", "yara", "provenance"],
        )
        envelope = MessageEnvelope(
            type=MessageType.HELLO_ACK,
            payload=ack.model_dump(),
        )
        data = envelope.model_dump(mode="json")

        assert data["type"] == "HELLO_ACK"
        assert data["payload"]["agent_version"] == "0.1.0"
        assert "scan" in data["payload"]["capabilities"]


# ── Phase 1 Acceptance Tests ─────────────────────────────────────────


class TestAcceptanceCriteria:
    """Acceptance tests from the Phase 1 spec."""

    def test_malformed_json_rejected_safely(self):
        """Malformed JSON → ERROR response, host doesn't crash."""
        result = handle_message({"__parse_error": "Invalid JSON: Expecting value"})

        assert result["type"] == "ERROR"
        assert "Invalid JSON" in result["payload"]["error"]

    def test_invalid_schema_rejected_safely(self):
        """Invalid message schema → ERROR response with details."""
        result = handle_message({
            "type": "NOT_A_REAL_TYPE",
            "version": "1",
            "timestamp": "2026-01-01T00:00:00Z",
            "correlation_id": str(uuid4()),
            "payload": {},
        })

        assert result["type"] == "ERROR"
        assert "Invalid message schema" in result["payload"]["error"]

    def test_missing_required_fields_rejected(self):
        """Missing required envelope fields → ERROR response."""
        result = handle_message({"some": "garbage", "data": 123})

        assert result["type"] == "ERROR"

    def test_download_started_handled(self):
        """DOWNLOAD_STARTED is acknowledged (Phase 1: communication-only)."""
        cid = str(uuid4())
        result = handle_message({
            "type": "DOWNLOAD_STARTED",
            "version": "1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "correlation_id": cid,
            "payload": {
                "download_id": 42,
                "url": "https://example.com/file.zip",
                "final_url": "https://example.com/file.zip",
                "filename": "file.zip",
                "mime": "application/zip",
                "file_size": 1024,
                "referrer": "",
                "tab_id": 1,
            },
        })

        assert result["type"] == "DOWNLOAD_PROGRESS"
        assert result["payload"]["download_id"] == 42
        assert result["payload"]["status"] == "received"

    def test_download_progress_handled(self):
        """DOWNLOAD_PROGRESS is acknowledged."""
        result = handle_message({
            "type": "DOWNLOAD_PROGRESS",
            "version": "1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "correlation_id": str(uuid4()),
            "payload": {
                "download_id": 42,
                "state": "complete",
                "bytes_received": 1024,
                "total_bytes": 1024,
                "filename": "file.zip",
            },
        })

        assert result["type"] == "DOWNLOAD_PROGRESS"
        assert result["payload"]["status"] == "acknowledged"

    def test_scan_request_returns_analysis_incomplete(self):
        """SCAN_REQUEST → ANALYSIS_INCOMPLETE (Phase 1: no analyzers yet)."""
        result = handle_message({
            "type": "SCAN_REQUEST",
            "version": "1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "correlation_id": str(uuid4()),
            "payload": {},
        })

        assert result["type"] == "ANALYSIS_INCOMPLETE"
        assert "Phase 1" in result["payload"]["reason"]

    def test_invalid_download_started_payload_rejected(self):
        """DOWNLOAD_STARTED with bad payload → ERROR, not crash."""
        result = handle_message({
            "type": "DOWNLOAD_STARTED",
            "version": "1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "correlation_id": str(uuid4()),
            "payload": {"wrong_field": "bad_data"},  # Missing download_id and url
        })

        assert result["type"] == "ERROR"
        assert "DOWNLOAD_STARTED" in result["payload"]["original_type"]
