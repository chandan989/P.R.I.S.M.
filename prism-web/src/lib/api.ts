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
  try {
    const ctrl = new AbortController();
    if (signal) signal.addEventListener("abort", () => ctrl.abort());
    // No hardcoded timeout — let the slow dual-T4 Kaggle backend take as long as it needs

    const res = await fetch(`${getApiBase()}/api/audit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: cryptoRandom() }),
      signal: ctrl.signal,
    });
    if (!res.ok || !res.body) throw new Error("Backend not OK");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        let json: unknown;
        try {
          json = JSON.parse(line.slice(5).trim());
        } catch {
          /* ignore malformed */
          continue;
        }
        if ((json as AuditStreamEvent)?.type === "error") {
          throw new Error((json as AuditStreamEvent).content ?? "Backend error");
        }
        onEvent(json as AuditStreamEvent);
      }
    }
    onEvent({ type: "done" });
  } catch (err) {
    console.error("PRISM Backend Error:", err);
    // Rethrow instead of falling back to mock data
    throw err;
  }
}

function cryptoRandom() {
  return Math.random().toString(36).slice(2);
}

export function getMockResultSync(query: string): AuditResult {
  return pickMockForQuery(query);
}
