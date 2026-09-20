/**
 * Background service worker — Phase 1
 *
 * - Connects to the native messaging host and performs HELLO handshake
 * - Monitors chrome.downloads lifecycle → sends DOWNLOAD_STARTED / DOWNLOAD_PROGRESS
 * - Tracks connection state for the popup
 * - Handles disconnect/reconnect gracefully
 */

import type {
  HelloMessage,
  HelloAckMessage,
  DownloadStartedMessage,
  DownloadProgressMessage,
  MessageEnvelope,
} from "@/types";

const NATIVE_HOST_NAME = "com.downloadsecurity.agent";
const EXTENSION_VERSION = "0.1.0";
const RECONNECT_DELAY_MS = 5000;

// ── State ───────────────────────────────────────────────────────────

interface AgentState {
  connected: boolean;
  agentVersion: string | null;
  capabilities: string[];
  lastJobState: "idle" | "download_detected" | "scanning" | "complete" | "error";
  lastError: string | null;
}

const state: AgentState = {
  connected: false,
  agentVersion: null,
  capabilities: [],
  lastJobState: "idle",
  lastError: null,
};

let port: chrome.runtime.Port | null = null;

// ── Utilities ───────────────────────────────────────────────────────

function generateUUID(): string {
  return crypto.randomUUID();
}

function createEnvelope<T>(type: string, payload: T): MessageEnvelope<T> {
  return {
    type: type as MessageEnvelope["type"],
    version: "1",
    timestamp: new Date().toISOString(),
    correlation_id: generateUUID(),
    payload,
  };
}

// ── Native Messaging Connection ─────────────────────────────────────

function connectToAgent(): void {
  try {
    port = chrome.runtime.connectNative(NATIVE_HOST_NAME);

    port.onMessage.addListener((message: unknown) => {
      handleAgentMessage(message as MessageEnvelope);
    });

    port.onDisconnect.addListener(() => {
      const error = chrome.runtime.lastError?.message ?? "Unknown disconnect reason";
      console.warn("[background] Disconnected from agent:", error);

      state.connected = false;
      state.lastError = error;
      port = null;

      // Auto-reconnect after delay
      setTimeout(connectToAgent, RECONNECT_DELAY_MS);
    });

    // Send HELLO handshake
    const hello: HelloMessage = createEnvelope("HELLO", {
      extension_version: EXTENSION_VERSION,
    });
    console.log("[background] Sending HELLO");
    port.postMessage(hello);

  } catch (err) {
    console.error("[background] Failed to connect to agent:", err);
    state.connected = false;
    state.lastError = String(err);

    // Retry after delay
    setTimeout(connectToAgent, RECONNECT_DELAY_MS);
  }
}

// ── Message Handling ────────────────────────────────────────────────

function handleAgentMessage(message: MessageEnvelope): void {
  console.log("[background] Received:", message.type);

  switch (message.type) {
    case "HELLO_ACK": {
      const ack = message as unknown as HelloAckMessage;
      state.connected = true;
      state.agentVersion = ack.payload.agent_version;
      state.capabilities = ack.payload.capabilities;
      state.lastError = null;
      console.log(
        `[background] Agent connected — v${ack.payload.agent_version}, ` +
        `capabilities: ${ack.payload.capabilities.join(", ")}`,
      );
      break;
    }

    case "DOWNLOAD_PROGRESS": {
      console.log("[background] Download progress ack:", message.payload);
      break;
    }

    case "ANALYSIS_INCOMPLETE": {
      console.log("[background] Analysis incomplete:", message.payload);
      state.lastJobState = "idle";
      break;
    }

    case "ERROR": {
      console.error("[background] Agent error:", message.payload);
      state.lastError = (message.payload as { error?: string }).error ?? "Unknown error";
      break;
    }

    default:
      console.warn("[background] Unhandled message type:", message.type);
  }
}

// ── Chrome Downloads Monitoring ─────────────────────────────────────

chrome.downloads.onCreated.addListener((downloadItem) => {
  console.log("[background] Download started:", downloadItem.id, downloadItem.url);

  state.lastJobState = "download_detected";

  if (!port || !state.connected) {
    console.warn("[background] Agent not connected, cannot send DOWNLOAD_STARTED");
    return;
  }

  const message: DownloadStartedMessage = createEnvelope("DOWNLOAD_STARTED", {
    download_id: downloadItem.id,
    url: downloadItem.url,
    final_url: downloadItem.finalUrl ?? downloadItem.url,
    filename: downloadItem.filename ?? "",
    mime: downloadItem.mime ?? "",
    file_size: downloadItem.fileSize ?? -1,
    referrer: downloadItem.referrer ?? "",
    tab_id: -1, // Not available on onCreated
  });

  port.postMessage(message);
});

chrome.downloads.onChanged.addListener((delta) => {
  if (!port || !state.connected) return;

  // Only send progress when state changes
  if (!delta.state) return;

  // Look up the full download item to get current state
  chrome.downloads.search({ id: delta.id }, (results) => {
    if (!results || results.length === 0 || !port) return;

    const item = results[0];

    const message: DownloadProgressMessage = createEnvelope("DOWNLOAD_PROGRESS", {
      download_id: delta.id,
      state: (item.state as "in_progress" | "complete" | "interrupted") ?? "in_progress",
      bytes_received: item.bytesReceived ?? 0,
      total_bytes: item.totalBytes ?? -1,
      filename: item.filename ?? "",
    });

    port.postMessage(message);

    if (item.state === "complete") {
      state.lastJobState = "complete";
    }
  });
});

// ── Popup Communication ─────────────────────────────────────────────

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request.action === "get_status") {
    sendResponse({ ...state });
    return true;
  }
  return false;
});

// ── Initialise ──────────────────────────────────────────────────────

connectToAgent();
