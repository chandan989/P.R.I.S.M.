import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

const pillars = [
  {
    title: "Deliberation Engine",
    body: "We instrument Gemma 4's chain-of-thought tokens, parse competing hypotheses, score them probabilistically, and surface them — discarded paths included. The clinician sees not just the answer, but the road not taken.",
  },
  {
    title: "Source Grounding",
    body: "Each generated claim is split into atomic propositions and matched against an indexed corpus (FDA labels, DrugBank, Lexicomp, peer-reviewed journals). Matches are tagged green (verified), yellow (inferred), red (contradicted), or grey (insufficient evidence).",
  },
  {
    title: "Certainty Indicators",
    body: "Raw model logits are unreliable. We calibrate using temperature scaling against a held-out clinical eval set, report Brier and ECE alongside each answer, and raise an out-of-distribution flag when a query falls far from training-time distribution.",
  },
];

const steps = [
  { h: "Nightly delta crawl", b: "Diff FDA, DrugBank, and Lexicomp endpoints. Pull only changed records." },
  { h: "Embedding refresh", b: "Re-embed deltas with the medical-domain encoder; upsert into the vector store." },
  { h: "Eval gate", b: "Run the 200-question regression suite. Block deploy on >2% accuracy regression." },
  { h: "Atomic swap", b: "Promote new index version; old version retained for 7 days for rollback." },
  { h: "Staleness clock", b: "Per-page banner when the active index is >7 days old." },
];

export default function HowItWorks() {
  const [open, setOpen] = useState<number | null>(0);
  useEffect(() => { document.title = "How It Works · P.R.I.S.M."; }, []);

  return (
    <div className="container" style={{ paddingTop: "var(--space-12)" }}>
      <header style={{ textAlign: "center", marginBottom: "var(--space-12)" }}>
        <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)" }}>The Glass Box, Explained.</h1>
        <p className="hero-sub" style={{ marginTop: "var(--space-4)" }}>
          A transparency stack built around three pillars, a hardened ingestion pipeline, and zero data egress.
        </p>
      </header>

      <section aria-label="Three pillars" style={{ marginBottom: "var(--space-12)" }}>
        {pillars.map((p, i) => (
          <div key={i} className="accordion">
            <button
              className="accordion-head"
              aria-expanded={open === i}
              onClick={() => setOpen(open === i ? null : i)}
            >
              <span>{i + 1}. {p.title}</span>
              {open === i ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
            {open === i && <div className="accordion-body">{p.body}</div>}
          </div>
        ))}
      </section>

      <section aria-label="Architecture" style={{ marginBottom: "var(--space-12)" }}>
        <h2 style={{ marginBottom: "var(--space-6)" }}>Architecture</h2>
        <div className="arch-diagram">
          <div className="arch-box">React + Vite — Glass Box UI</div>
          <div className="arch-arrow">↓</div>
          <div className="arch-box">FastAPI — orchestrator + SSE</div>
          <div className="arch-arrow">↓</div>
          <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", justifyContent: "center" }}>
            <div className="arch-box">Ollama / llama.cpp — Gemma 4</div>
            <div className="arch-box">Vector store — corpus index</div>
          </div>
        </div>
      </section>

      <section aria-label="Update protocol" style={{ marginBottom: "var(--space-12)" }}>
        <h2 style={{ marginBottom: "var(--space-6)" }}>Knowledge Base Update Protocol</h2>
        <div className="timeline">
          {steps.map((s, i) => (
            <div key={i} className="timeline-step">
              <h4>{i + 1}. {s.h}</h4>
              <p>{s.b}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-label="Tech stack">
        <h2 style={{ marginBottom: "var(--space-6)" }}>Tech Stack</h2>
        <div className="tech-table">
          <table>
            <thead><tr><th>Layer</th><th>Tooling</th></tr></thead>
            <tbody>
              <tr><td>Model</td><td>Gemma 4 via Ollama / llama.cpp</td></tr>
              <tr><td>Backend</td><td>FastAPI · Python 3.12 · SSE streaming</td></tr>
              <tr><td>Frontend</td><td>React 18 · Vite · TypeScript</td></tr>
              <tr><td>Index</td><td>FDA labels · DrugBank · Lexicomp · PubMed</td></tr>
              <tr><td>Calibration</td><td>Temperature scaling · Brier · ECE · OOD detector</td></tr>
              <tr><td>Deployment</td><td>On-prem · zero data egress · HIPAA-aligned</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
