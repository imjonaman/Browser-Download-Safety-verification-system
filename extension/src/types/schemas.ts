/**
 * Core schema interfaces — TypeScript mirrors of the Python Pydantic models.
 */

/** A browser navigation or tab event. */
export interface BrowserEvent {
  event_id: string;
  tab_id: number;
  url: string;
  referrer: string;
  timestamp: string; // ISO-8601
  action_type: string;
}

/** A download state-change event from the browser downloads API. */
export interface DownloadEvent {
  download_id: number;
  event_id: string;
  original_url: string;
  final_url: string;
  filename: string;
  mime: string;
  bytes_received: number;
  state: "in_progress" | "complete" | "interrupted";
  timestamp: string;
}

/** A scan job that tracks the analysis of a single download. */
export interface ScanJob {
  job_id: string;
  download_id: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  updated_at: string;
}

/** A single piece of risk evidence found by an analysis module. */
export interface Evidence {
  evidence_id: string;
  job_id: string;
  module: string;
  feature: string;
  value: unknown;
  details: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  rule_id: string;
  timestamp: string;
  status: "active" | "suppressed" | "expired";
}

/** An aggregated risk score produced after all evidence is collected. */
export interface RiskSnapshot {
  job_id: string;
  score: number;
  classification: string;
  confidence: number;
  coverage: number;
  evidence_set_version: string;
  timestamp: string;
}

/** The final verdict and action taken for a scan job. */
export interface Decision {
  job_id: string;
  action: "allow" | "block" | "quarantine" | "warn";
  actor: string;
  reason: string;
  timestamp: string;
}

/** Metadata for an installed rule pack version. */
export interface RuleVersion {
  pack: string;
  version: string;
  hash_signature: string;
  installed_at: string;
}
