import type { AuditResult, AuditStreamEvent } from "./types";
import { pickMockForQuery } from "./mock-data";

const API_BASE = "http://localhost:8000";

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
    const t = setTimeout(() => ctrl.abort(), 1500);

    const res = await fetch(`${API_BASE}/api/audit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: cryptoRandom() }),
      signal: ctrl.signal,
    });
    clearTimeout(t);
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
        try {
          const json = JSON.parse(line.slice(5).trim());
          onEvent(json as AuditStreamEvent);
        } catch {
          /* ignore malformed */
        }
      }
    }
    onEvent({ type: "done" });
  } catch {
    // Fallback: simulate stream from mock data
    await simulateStream(query, onEvent, signal);
  }
}

function cryptoRandom() {
  return Math.random().toString(36).slice(2);
}

async function simulateStream(
  query: string,
  onEvent: StreamHandler,
  signal?: AbortSignal,
): Promise<void> {
  const result: AuditResult = pickMockForQuery(query);

  // 1. Emit thought (deliberation) immediately
  onEvent({ type: "thought", content: JSON.stringify({
    interpretations: result.interpretations,
    discarded: result.discarded,
    selected: result.selected,
  }) });

  // 2. Stream the answer roughly 50ms per token, replacing markers with source dots
  const tokens = result.answer.split(/(\s+)/);
  let sourceIdx = 0;
  for (const tok of tokens) {
    if (signal?.aborted) return;
    // Detect SOURCED markers within token
    const markerRegex = /\[SOURCED:(green|yellow|red|grey)\]/;
    const match = tok.match(markerRegex);
    if (match) {
      const before = tok.slice(0, match.index!);
      if (before) onEvent({ type: "answer", content: before });
      const ref = result.sources[sourceIdx++];
      onEvent({
        type: "source_dot",
        signal: match[1] as AuditStreamEvent["signal"],
        source: ref?.source,
        snippet: ref?.snippet,
      });
      const after = tok.slice(match.index! + match[0].length);
      if (after) onEvent({ type: "answer", content: after });
    } else {
      onEvent({ type: "answer", content: tok });
    }
    await sleep(45);
  }

  // 3. Confidence
  await sleep(200);
  onEvent({ type: "confidence", confidence: result.confidence });
  onEvent({ type: "done" });
}

function sleep(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}

export function getMockResultSync(query: string): AuditResult {
  return pickMockForQuery(query);
}
