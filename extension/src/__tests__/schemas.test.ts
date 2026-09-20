/**
 * Vitest tests for TypeScript schema interfaces and Phase 1 message types.
 */

import { describe, it, expect } from "vitest";
import type {
  BrowserEvent,
  DownloadEvent,
  ScanJob,
  Evidence,
  RiskSnapshot,
  Decision,
  RuleVersion,
  HelloMessage,
  HelloAckMessage,
  DownloadStartedMessage,
  DownloadProgressMessage,
  ErrorMessage,
} from "../types";

describe("Schema interfaces", () => {
  it("BrowserEvent has all required fields", () => {
    const event: BrowserEvent = {
      event_id: "550e8400-e29b-41d4-a716-446655440000",
      tab_id: 42,
      url: "https://example.com",
      referrer: "https://google.com",
      timestamp: new Date().toISOString(),
      action_type: "navigate",
    };
    expect(event.tab_id).toBe(42);
    expect(event.action_type).toBe("navigate");
  });

  it("DownloadEvent has all required fields", () => {
    const event: DownloadEvent = {
      download_id: 100,
      event_id: "550e8400-e29b-41d4-a716-446655440001",
      original_url: "https://example.com/file.zip",
      final_url: "https://cdn.example.com/file.zip",
      filename: "file.zip",
      mime: "application/zip",
      bytes_received: 1024,
      state: "in_progress",
      timestamp: new Date().toISOString(),
    };
    expect(event.mime).toBe("application/zip");
  });

  it("ScanJob defaults status correctly", () => {
    const job: ScanJob = {
      job_id: "550e8400-e29b-41d4-a716-446655440002",
      download_id: 1,
      status: "pending",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    expect(job.status).toBe("pending");
  });

  it("Evidence has valid confidence", () => {
    const evidence: Evidence = {
      evidence_id: "550e8400-e29b-41d4-a716-446655440003",
      job_id: "550e8400-e29b-41d4-a716-446655440002",
      module: "yara",
      feature: "suspicious_strings",
      value: "eval(atob(...))",
      details: "Obfuscated JavaScript detected",
      severity: "high",
      confidence: 0.92,
      rule_id: "YARA_JS_OBFUSC_001",
      timestamp: new Date().toISOString(),
      status: "active",
    };
    expect(evidence.confidence).toBeGreaterThanOrEqual(0);
    expect(evidence.confidence).toBeLessThanOrEqual(1);
  });

  it("RiskSnapshot has valid score range", () => {
    const snap: RiskSnapshot = {
      job_id: "550e8400-e29b-41d4-a716-446655440002",
      score: 75.5,
      classification: "suspicious",
      confidence: 0.88,
      coverage: 0.95,
      evidence_set_version: "abc123",
      timestamp: new Date().toISOString(),
    };
    expect(snap.score).toBeGreaterThanOrEqual(0);
    expect(snap.score).toBeLessThanOrEqual(100);
  });

  it("Decision has valid action", () => {
    const decision: Decision = {
      job_id: "550e8400-e29b-41d4-a716-446655440002",
      action: "block",
      actor: "auto",
      reason: "High risk score",
      timestamp: new Date().toISOString(),
    };
    expect(["allow", "block", "quarantine", "warn"]).toContain(decision.action);
  });

  it("RuleVersion has all fields", () => {
    const rv: RuleVersion = {
      pack: "yara-community",
      version: "1.2.0",
      hash_signature: "sha256:abcdef1234567890",
      installed_at: new Date().toISOString(),
    };
    expect(rv.pack).toBe("yara-community");
  });
});

describe("Phase 1 message types", () => {
  it("HELLO message can be constructed", () => {
    const hello: HelloMessage = {
      type: "HELLO",
      version: "1",
      timestamp: new Date().toISOString(),
      correlation_id: crypto.randomUUID(),
      payload: { extension_version: "0.1.0" },
    };
    expect(hello.type).toBe("HELLO");
    expect(hello.payload.extension_version).toBe("0.1.0");
  });

  it("HELLO_ACK message has expected structure", () => {
    const ack: HelloAckMessage = {
      type: "HELLO_ACK",
      version: "1",
      timestamp: new Date().toISOString(),
      correlation_id: crypto.randomUUID(),
      payload: {
        agent_version: "0.1.0",
        protocol_version: "1",
        capabilities: ["scan", "yara", "provenance"],
      },
    };
    expect(ack.payload.capabilities).toContain("scan");
  });

  it("DOWNLOAD_STARTED message can be constructed", () => {
    const msg: DownloadStartedMessage = {
      type: "DOWNLOAD_STARTED",
      version: "1",
      timestamp: new Date().toISOString(),
      correlation_id: crypto.randomUUID(),
      payload: {
        download_id: 42,
        url: "https://example.com/file.zip",
        final_url: "https://cdn.example.com/file.zip",
        filename: "file.zip",
        mime: "application/zip",
        file_size: 1024000,
        referrer: "https://example.com",
        tab_id: 5,
      },
    };
    expect(msg.type).toBe("DOWNLOAD_STARTED");
    expect(msg.payload.download_id).toBe(42);
    expect(msg.payload.mime).toBe("application/zip");
  });

  it("DOWNLOAD_PROGRESS message can be constructed", () => {
    const msg: DownloadProgressMessage = {
      type: "DOWNLOAD_PROGRESS",
      version: "1",
      timestamp: new Date().toISOString(),
      correlation_id: crypto.randomUUID(),
      payload: {
        download_id: 42,
        state: "complete",
        bytes_received: 1024000,
        total_bytes: 1024000,
        filename: "file.zip",
      },
    };
    expect(msg.type).toBe("DOWNLOAD_PROGRESS");
    expect(msg.payload.state).toBe("complete");
  });

  it("ERROR message can be constructed", () => {
    const msg: ErrorMessage = {
      type: "ERROR",
      version: "1",
      timestamp: new Date().toISOString(),
      correlation_id: crypto.randomUUID(),
      payload: {
        error: "Unknown message type",
        original_type: "FAKE_TYPE",
        details: "No handler for this type",
      },
    };
    expect(msg.type).toBe("ERROR");
    expect(msg.payload.error).toBe("Unknown message type");
  });

  it("HELLO message serializes to valid JSON for the agent", () => {
    const hello: HelloMessage = {
      type: "HELLO",
      version: "1",
      timestamp: new Date().toISOString(),
      correlation_id: crypto.randomUUID(),
      payload: { extension_version: "0.1.0" },
    };
    const json = JSON.stringify(hello);
    const parsed = JSON.parse(json);
    expect(parsed.type).toBe("HELLO");
    expect(parsed.payload.extension_version).toBe("0.1.0");
  });
});
