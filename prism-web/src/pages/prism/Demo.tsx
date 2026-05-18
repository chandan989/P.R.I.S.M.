import { useEffect, useRef, useState } from "react";
import CommandCenter from "@/components/prism/CommandCenter";
import StreamingText, { type Token } from "@/components/prism/StreamingText";
import DeliberationTree from "@/components/prism/DeliberationTree";
import ConfidenceBadge from "@/components/prism/ConfidenceBadge";
import SkeletonLoader from "@/components/prism/SkeletonLoader";
import { streamAudit } from "@/lib/api";
import { demoQueries } from "@/lib/demo-queries";
import type { AuditStreamEvent, Confidence, Interpretation } from "@/lib/types";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.15 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export default function Demo() {
  const [query, setQuery] = useState(demoQueries.polypharmacy);
  const [busy, setBusy] = useState(false);
  const [tokens, setTokens] = useState<Token[]>([]);
  const [interps, setInterps] = useState<Interpretation[]>([]);
  const [discarded, setDiscarded] = useState<string[]>([]);
  const [selected, setSelected] = useState(0);
  const [confidence, setConfidence] = useState<Confidence | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => { document.title = "Demo · P.R.I.S.M."; }, []);

  const reset = () => { setTokens([]); setInterps([]); setDiscarded([]); setSelected(0); setConfidence(null); setError(null); };

  const run = async (q?: string) => {
    const text = q ?? query;
    if (!text.trim() || busy) return;
    if (q) setQuery(q);
    reset();
    setBusy(true);
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      await streamAudit(text, (e: AuditStreamEvent) => {
        if (e.type === "thought" && e.content) {
          try {
            const p = JSON.parse(e.content);
            setInterps(p.interpretations ?? []); setDiscarded(p.discarded ?? []); setSelected(p.selected ?? 0);
          } catch { /* */ }
        } else if (e.type === "answer" && e.content !== undefined) {
          setTokens((prev) => [...prev, { type: "text", text: e.content! }]);
        } else if (e.type === "source_dot") {
          setTokens((prev) => [...prev, { type: "dot", ref: { signal: e.signal!, source: e.source ?? "Source", snippet: e.snippet ?? "", claim_text: e.claim_text } }]);
        } else if (e.type === "confidence" && e.confidence) {
          setConfidence(e.confidence);
        }
      }, ctrl.signal);
    } catch (err) {
      setError((err as Error).message);
      document.dispatchEvent(new CustomEvent("open-backend-settings"));
    } finally {
      setBusy(false);
    }
  };


  const scenarios = [
    { label: "💊 Polypharmacy Audit", desc: "72yo female on 15-drug regimen — enumerate all pairwise and multi-way interactions, verify against FDA Drug Labels and DrugBank.", onClick: () => { setQuery(demoQueries.polypharmacy); run(demoQueries.polypharmacy); } },
    { label: "🧬 CYP450 Analysis", desc: "Analyze CYP2D6 and CYP3A4 metabolic load — identify enzyme saturation risks and dose adjustments via PharmGKB.", onClick: () => { setQuery(demoQueries.cyp450); run(demoQueries.cyp450); } },
    { label: "🔬 Emerging Evidence", desc: "GLP-1 agonists with Warfarin — weigh pharmacovigilance data, check nightly delta-updated index for FDA MedWatch alerts.", onClick: () => { setQuery(demoQueries.glp1); run(demoQueries.glp1); } },
  ];

  return (
    <motion.div className="container" style={{ paddingTop: "var(--space-8)", position: "relative" }} variants={containerVariants} initial="hidden" animate="show">
      <div className="mesh-aura" />
      <motion.header style={{ textAlign: "center", marginBottom: "var(--space-8)" }} variants={itemVariants}>
        <h1 style={{ fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)" }}>Clinical Demo Scenarios</h1>
        <p className="hero-sub" style={{ marginTop: "var(--space-3)" }}>
          The Glass Box MVP is optimized for polypharmacy contraindication auditing and clinical decision support.
          Pick a scenario or write your own — every claim is source-grounded with 🟢🟡🔴⚪ verification dots.
        </p>
      </motion.header>

      <motion.div style={{ maxWidth: 820, margin: "0 auto var(--space-8)" }} variants={itemVariants}>
        <CommandCenter
          value={query}
          onChange={setQuery}
          onSubmit={() => run()}
          busy={busy}
          scenarios={scenarios}
        />
      </motion.div>

      <motion.section className="output-panel" style={{ maxWidth: 820, margin: "0 auto" }} aria-label="Demo output" variants={itemVariants}>
        <div className="output-body">
          {error && <div className="error-card">⚠ {error}</div>}
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
                tokens={tokens}
              />
            </div>
          )}
          {!busy && tokens.length === 0 && (
            <div style={{ color: "var(--ink-tertiary)", fontSize: "var(--text-ui)" }}>
              Pick a scenario above and the Glass Box will stream a real-time audit.
            </div>
          )}
        </div>
      </motion.section>
    </motion.div>
  );
}
