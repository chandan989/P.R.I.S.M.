import type { AuditResult, AuditStreamEvent } from "./types";
import { pickMockForQuery } from "./mock-data";

const STORAGE_KEY = "prism_api_url";
const DEFAULT_BASE = "http://localhost:8000";

export function normalizeApiBase(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

/** Get the current backend URL. Priority: localStorage → env → fallback. */
export function getApiBase(): string {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && stored.trim()) return normalizeApiBase(stored);
  } catch { /* SSR-safe */ }
  if (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE) {
    return normalizeApiBase(import.meta.env.VITE_API_BASE);
  }
  return DEFAULT_BASE;
}

/** Persist a new backend URL (or clear it to revert to default). */
export function setApiBase(url: string | null): void {
  try {
    if (url && url.trim()) {
      localStorage.setItem(STORAGE_KEY, normalizeApiBase(url));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch { /* SSR-safe */ }
}

export type StreamHandler = (event: AuditStreamEvent) => void;

/**
 * Try to stream from FastAPI backend. If unreachable or non-OK, transparently
 * fall back to a simulated stream from realistic mock data.
 */
export async function streamAudit(
  query: string,
  onEvent: StreamHandler,
  signal?: AbortSignal,
): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      let wsBase = getApiBase().replace(/^http/, "ws");
      const ws = new WebSocket(`${wsBase}/api/audit/ws`);

      if (signal) {
        signal.addEventListener("abort", () => {
          ws.close();
          reject(new Error("The operation was aborted"));
        });
      }

      ws.onopen = () => {
        ws.send(JSON.stringify({ query, session_id: cryptoRandom() }));
      };

      ws.onmessage = (event) => {
        try {
          const json = JSON.parse(event.data);

          if (json.type === "ping") {
            return; // Ignore keep-alive pings
          }

          if (json.type === "error") {
            ws.close();
            reject(new Error(json.content ?? "Backend error"));
            return;
          }

          onEvent(json as AuditStreamEvent);

          if (json.type === "done") {
            ws.close();
            resolve();
          }
        } catch (e) {
          // ignore malformed JSON
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket Error:", error);
        reject(new Error("WebSocket connection failed"));
      };

      ws.onclose = () => {
        // Just resolve if not already resolved, though 'done' event should handle it
        resolve();
      };

    } catch (err) {
      console.error("PRISM Backend Error:", err);
      reject(err);
    }
  });
}

function cryptoRandom() {
  return Math.random().toString(36).slice(2);
}

export function getMockResultSync(query: string): AuditResult {
  return pickMockForQuery(query);
}
