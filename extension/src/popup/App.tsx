import { useState, useEffect } from "react";

interface AgentState {
  connected: boolean;
  agentVersion: string | null;
  capabilities: string[];
  lastJobState: "idle" | "download_detected" | "scanning" | "complete" | "error";
  lastError: string | null;
}

const JOB_STATE_LABELS: Record<AgentState["lastJobState"], string> = {
  idle: "Idle",
  download_detected: "Download Detected",
  scanning: "Scanning…",
  complete: "Scan Complete",
  error: "Error",
};

export default function App() {
  const [state, setState] = useState<AgentState>({
    connected: false,
    agentVersion: null,
    capabilities: [],
    lastJobState: "idle",
    lastError: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    chrome.runtime.sendMessage({ action: "get_status" }, (response) => {
      setLoading(false);
      if (chrome.runtime.lastError || !response) {
        setState((prev) => ({
          ...prev,
          connected: false,
          lastError: chrome.runtime.lastError?.message ?? "Could not reach background",
        }));
      } else {
        setState(response);
      }
    });
  }, []);

  const statusColor = state.connected ? "#22c55e" : "#ef4444";
  const statusText = loading
    ? "Checking…"
    : state.connected
      ? `Connected — v${state.agentVersion}`
      : "Disconnected";

  return (
    <div style={{ width: 320, padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 16, margin: "0 0 12px", fontWeight: 600 }}>
        Download Security
      </h1>

      {/* Connection Status */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 12px",
          borderRadius: 8,
          backgroundColor: state.connected ? "#f0fdf4" : "#fef2f2",
          marginBottom: 10,
        }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: loading ? "#eab308" : statusColor,
            display: "inline-block",
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: 13 }}>Agent: {statusText}</span>
      </div>

      {/* Job State */}
      <div
        style={{
          padding: "8px 12px",
          borderRadius: 8,
          backgroundColor: "#f8fafc",
          marginBottom: 10,
          fontSize: 13,
        }}
      >
        <span style={{ color: "#64748b" }}>Status: </span>
        <span style={{ fontWeight: 500 }}>{JOB_STATE_LABELS[state.lastJobState]}</span>
      </div>

      {/* Error Display */}
      {state.lastError && (
        <div
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            backgroundColor: "#fef2f2",
            color: "#dc2626",
            fontSize: 12,
            wordBreak: "break-word",
          }}
        >
          {state.lastError}
        </div>
      )}

      {/* Capabilities */}
      {state.connected && state.capabilities.length > 0 && (
        <div style={{ marginTop: 10, fontSize: 12, color: "#94a3b8" }}>
          Capabilities: {state.capabilities.join(", ")}
        </div>
      )}
    </div>
  );
}
