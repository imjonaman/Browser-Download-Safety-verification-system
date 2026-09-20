/**
 * Content script — injected into web pages.
 *
 * Captures browser events (navigations, link clicks) and forwards
 * them to the background service worker.
 */

import type { BrowserEvent } from "@/types";

function generateUUID(): string {
  return crypto.randomUUID();
}

function captureBrowserEvent(actionType: string): void {
  const event: BrowserEvent = {
    event_id: generateUUID(),
    tab_id: -1, // filled in by background
    url: window.location.href,
    referrer: document.referrer,
    timestamp: new Date().toISOString(),
    action_type: actionType,
  };

  chrome.runtime.sendMessage({ type: "BROWSER_EVENT", payload: event });
}

// Capture page load
captureBrowserEvent("navigate");

// Capture link clicks
document.addEventListener("click", (e) => {
  const anchor = (e.target as HTMLElement).closest("a");
  if (anchor?.href) {
    captureBrowserEvent("link_click");
  }
});

console.log("[content] Download Security content script loaded");
