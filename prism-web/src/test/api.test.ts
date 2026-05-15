import { afterEach, describe, expect, it, vi } from "vitest";
import { getApiBase, setApiBase, streamAudit } from "@/lib/api";
import type { AuditStreamEvent } from "@/lib/types";

function sseResponse(payload: unknown) {
  const encoder = new TextEncoder();
  const chunks = [encoder.encode(`data: ${JSON.stringify(payload)}\n\n`)];

  return {
    ok: true,
    body: {
      getReader() {
        return {
          async read() {
            return chunks.length
              ? { value: chunks.shift(), done: false }
              : { value: undefined, done: true };
          },
        };
      },
    },
  };
}

describe("api base configuration", () => {
  afterEach(() => {
    setApiBase(null);
    vi.restoreAllMocks();
  });

  it("persists backend URLs without trailing slashes", () => {
    setApiBase(" https://peers-activists-ratios-sic.trycloudflare.com/ ");

    expect(localStorage.getItem("prism_api_url")).toBe(
      "https://peers-activists-ratios-sic.trycloudflare.com",
    );
    expect(getApiBase()).toBe("https://peers-activists-ratios-sic.trycloudflare.com");
  });
});

describe("streamAudit", () => {
  afterEach(() => {
    setApiBase(null);
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("falls back to mock stream when the backend emits an SSE error event", async () => {
    vi.useFakeTimers();
    setApiBase("https://peers-activists-ratios-sic.trycloudflare.com/");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(sseResponse({ type: "error", content: "No documents found" }) as Response);
    const events: AuditStreamEvent[] = [];

    const streamPromise = streamAudit("warfarin aspirin interaction", (event) => {
      events.push(event);
    });

    await vi.runAllTimersAsync();
    await streamPromise;

    expect(fetchMock).toHaveBeenCalledWith(
      "https://peers-activists-ratios-sic.trycloudflare.com/api/audit",
      expect.any(Object),
    );
    expect(events.some((event) => event.type === "answer")).toBe(true);
    expect(events.some((event) => event.type === "confidence")).toBe(true);
    expect(events).not.toContainEqual({ type: "error", content: "No documents found" });
    expect(events.at(-1)).toEqual({ type: "done" });
  });
});
