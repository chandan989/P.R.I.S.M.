import { useEffect, useRef, useState } from "react";
import CommandCenter from "@/components/prism/CommandCenter";
import StreamingText, { type Token } from "@/components/prism/StreamingText";
import DeliberationTree from "@/components/prism/DeliberationTree";
import ConfidenceBadge from "@/components/prism/ConfidenceBadge";
import SkeletonLoader from "@/components/prism/SkeletonLoader";
import { streamAudit } from "@/lib/api";
import { demoQueries } from "@/lib/mock-data";
import type { AuditStreamEvent, Confidence, Interpretation } from "@/lib/types";

export default function Demo() {
  const [query, setQuery] = useState(demoQueries.polypharmacy);
  const [busy, setBusy] = useState(false);
  const [tokens, setTokens] = useState<Token[]>([]);
  const [interps, setInterps] = useState<Interpretation[]>([]);
  const [discarded, setDiscarded] = useState<string[]>([]);
  const [selected, setSelected] = useState(0);
  const [confidence, setConfidence] = useState<Confidence | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => { document.title = "Demo · P.R.I.S.M."; }, []);

  const reset = () => { setTokens([]); setInterps([]); setDiscarded([]); setSelected(0); setConfidence(null); };

  const run = async (q?: string) => {
    const text = q ?? query;
    if (!text.trim() || busy) return;
    if (q) setQuery(q);
    reset();
    setBusy(true);
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    await streamAudit(text, (e: AuditStreamEvent) => {
      if (e.type === "thought" && e.content) {
        try {
          const p = JSON.parse(e.content);
          setInterps(p.interpretations ?? []); setDiscarded(p.discarded ?? []); setSelected(p.selected ?? 0);
        } catch { /* */ }
      } else if (e.type === "answer" && e.content !== undefined) {
        setTokens((prev) => [...prev, { type: "text", text: e.content! }]);
      } else if (e.type === "source_dot") {
        setTokens((prev) => [...prev, { type: "dot", ref: { signal: e.signal!, source: e.source ?? "Source", snippet: e.snippet ?? "" } }]);
      } else if (e.type === "confidence" && e.confidence) {
        setConfidence(e.confidence);
      }
    }, ctrl.signal);
    setBusy(false);
  };

  const scenarios = [
    { label: "💊 Polypharmacy Audit", onClick: () => { setQuery(demoQueries.polypharmacy); run(demoQueries.polypharmacy); } },
    { label: "🧬 CYP450 Analysis", onClick: () => { setQuery(demoQueries.cyp450); run(demoQueries.cyp450); } },
    { label: "🔬 Emerging Evidence", onClick: () => { setQuery(demoQueries.glp1); run(demoQueries.glp1); } },
  ];

  return (
    <div className="container" style={{ paddingTop: "var(--space-8)", position: "relative" }}>
      <div className="mesh-aura" />
      <header style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
        <h1 style={{ fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)" }}>Try the Glass Box</h1>
        <p className="hero-sub" style={{ marginTop: "var(--space-3)" }}>
          Pick a scenario or write your own. Every claim is tagged with a verified / inferred / contradicted / unknown source.
        </p>
      </header>

      <div style={{ maxWidth: 820, margin: "0 auto var(--space-8)" }}>
        <CommandCenter
          value={query}
          onChange={setQuery}
          onSubmit={() => run()}
          busy={busy}
          scenarios={scenarios}
        />
      </div>

      <section className="output-panel" style={{ maxWidth: 820, margin: "0 auto" }} aria-label="Demo output">
        <div className="output-body">
          {busy && tokens.length === 0 && <SkeletonLoader rows={4} />}
          {tokens.length > 0 && <StreamingText tokens={tokens} isStreaming={busy} />}
          {confidence && <ConfidenceBadge level={confidence.level} score={confidence.score} />}
          {interps.length > 0 && (
            <div style={{ marginTop: "var(--space-6)" }}>
              <DeliberationTree
                interpretations={interps}
                discarded={discarded}
                selected={selected}
                calibration={confidence ?? undefined}
              />
            </div>
          )}
          {!busy && tokens.length === 0 && (
            <div style={{ color: "var(--ink-tertiary)", fontSize: "var(--text-ui)" }}>
              Pick a scenario above and the Glass Box will stream a real-time audit.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
