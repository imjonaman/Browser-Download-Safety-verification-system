/**
 * Message protocol types for native messaging communication.
 *
 * Phase 1: Communication-only message types, aligned with the build spec.
 */

/** All supported message types — Phase 1. */
export type MessageType =
  | "HELLO"
  | "HELLO_ACK"
  | "DOWNLOAD_STARTED"
  | "DOWNLOAD_PROGRESS"
  | "SCAN_REQUEST"
  | "SCAN_PROGRESS"
  | "EVIDENCE_UPDATE"
  | "RISK_UPDATE"
  | "SCAN_COMPLETE"
  | "ANALYSIS_INCOMPLETE"
  | "ERROR";

/** Standard envelope wrapping every native messaging payload. */
export interface MessageEnvelope<T = Record<string, unknown>> {
  type: MessageType;
  version: string;
  timestamp: string; // ISO-8601
  correlation_id: string; // UUID
  payload: T;
}

// ── HELLO ───────────────────────────────────────────────────────────

/** Payload for a HELLO message from the extension. */
export interface HelloPayload {
  extension_version: string;
}

/** Payload for a HELLO_ACK response from the agent. */
export interface HelloAckPayload {
  agent_version: string;
  protocol_version: string;
  capabilities: string[];
}

// ── Download Events ─────────────────────────────────────────────────

/** Payload for DOWNLOAD_STARTED — sent when a new download begins. */
export interface DownloadStartedPayload {
  download_id: number;
  url: string;
  final_url: string;
  filename: string;
  mime: string;
  file_size: number;
  referrer: string;
  tab_id: number;
}

/** Payload for DOWNLOAD_PROGRESS — sent on download state changes. */
export interface DownloadProgressPayload {
  download_id: number;
  state: "in_progress" | "complete" | "interrupted";
  bytes_received: number;
  total_bytes: number;
  filename: string;
}

// ── Error ───────────────────────────────────────────────────────────

/** Payload for ERROR messages. */
export interface ErrorPayload {
  error: string;
  original_type: string;
  details: string;
}

// ── Typed Envelopes ─────────────────────────────────────────────────

export type HelloMessage = MessageEnvelope<HelloPayload>;
export type HelloAckMessage = MessageEnvelope<HelloAckPayload>;
export type DownloadStartedMessage = MessageEnvelope<DownloadStartedPayload>;
export type DownloadProgressMessage = MessageEnvelope<DownloadProgressPayload>;
export type ErrorMessage = MessageEnvelope<ErrorPayload>;
