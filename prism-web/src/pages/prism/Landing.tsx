import { Link } from "react-router-dom";
import { Sparkles, Brain, Link2, Gauge, ArrowRight, Github } from "lucide-react";
import PillarCard from "@/components/prism/PillarCard";
import { useEffect } from "react";

export default function Landing() {
  useEffect(() => {
    document.title = "P.R.I.S.M. — The Glass Box Interpreter";
    setMeta("description", "Transparency layer for clinical AI. Auditable, verifiable, trust-calibrated polypharmacy decision support powered by Gemma 4.");
  }, []);

  return (
    <>
      <section className="hero container">
        <div className="mesh-aura" />
        <span className="eyebrow"><Sparkles size={12} /> Built for the Gemma 4 Good Hackathon</span>
        <h1>
          See Inside the AI.<br />
          <span className="hero-grad">Trust Every Answer.</span>
        </h1>
        <p className="hero-sub">
          P.R.I.S.M. is a transparency layer for Gemma 4 that turns black-box clinical AI into auditable,
          verifiable, trust-calibrated decision support.
        </p>
        <div className="hero-ctas">
          <Link to="/audit" className="pill pill--solid">→ Launch Glass Box</Link>
          <a href="https://github.com" className="pill" target="_blank" rel="noreferrer">
            <Github size={14} /> View on GitHub ↗
          </a>
        </div>

        <div className="command-border" style={{ maxWidth: 760, margin: "0 auto" }}>
          <div className="command-center" style={{ textAlign: "left" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>Polypharmacy Audit · preview</span>
              <span style={{ color: "var(--ink-inverse-muted)", fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)" }}>session · 4f9k2x</span>
            </div>
            <div className="cmd-preview-card">
              <div className="cmd-preview-line">› Warfarin + Clarithromycin + Atorvastatin</div>
              <div className="cmd-preview-line"><span className="source-dot source-dot--green" /> Clarithromycin is a strong CYP3A4 inhibitor.</div>
              <div className="cmd-preview-line"><span className="source-dot source-dot--red" /> Atorvastatin co-administration contraindicated.</div>
              <div className="cmd-preview-line"><span className="source-dot source-dot--yellow" /> Omeprazole may shift Warfarin INR.</div>
              <div className="cmd-preview-bar"><div className="cmd-preview-bar-fill" /></div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, color: "var(--ink-inverse-muted)", fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)" }}>
                <span>██████████ 82%</span><span style={{ color: "#4ADE80" }}>✓ HIGH</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="container bento" aria-label="Three pillars">
        <PillarCard
          accent="magenta"
          icon={<Brain size={22} />}
          title="Deliberation Engine"
          body="Surfaces the model's competing hypotheses, supporting evidence, and discarded paths — not just the final answer."
          preview={<code style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-tertiary)" }}>{"<|think|> A 72% · B 22% · ✗ discarded"}</code>}
        />
        <PillarCard
          accent="orange"
          icon={<Link2 size={22} />}
          title="Source Grounding"
          body="Every clinical claim is verified against an indexed corpus and tagged with a green / yellow / red / grey signal."
          preview={<div style={{ display: "flex", gap: 6 }}>
            <span className="source-dot source-dot--green" />
            <span className="source-dot source-dot--red" />
            <span className="source-dot source-dot--yellow" />
            <span className="source-dot source-dot--grey" />
          </div>}
        />
        <PillarCard
          accent="cyan"
          icon={<Gauge size={22} />}
          title="Certainty Indicators"
          body="Calibrated confidence — Brier-scored, ECE-corrected, with OOD flags so clinicians know when to slow down."
          preview={<code style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-tertiary)" }}>████████░░ 80%</code>}
        />
      </section>

      <section className="container why" aria-label="Why polypharmacy">
        <div>
          <h2>Why Polypharmacy?</h2>
          <p>
            Emergency triage is fast, dramatic — and unforgiving of opacity. Polypharmacy auditing is slow, structured,
            and exactly the place where an interpretable AI earns its keep.
          </p>
          <p>
            Clinicians don't need a chatbot. They need a colleague that shows its working: which sources it trusts,
            which alternatives it ruled out, and how confident it really is.
          </p>
          <Link to="/how-it-works" className="pill" style={{ marginTop: 16 }}>
            Read the architecture <ArrowRight size={14} />
          </Link>
        </div>
        <div className="compare-card">
          <table>
            <thead>
              <tr><th>Dimension</th><th>Emergency Triage</th><th>Polypharmacy Audit</th></tr>
            </thead>
            <tbody>
              <tr><td>Time horizon</td><td>Seconds</td><td>Minutes</td></tr>
              <tr><td>Data per patient</td><td>Sparse</td><td>Dense</td></tr>
              <tr><td>Interpretability ROI</td><td>Modest</td><td>High</td></tr>
              <tr><td>Audit-friendly</td><td>Hard</td><td>Natural fit</td></tr>
              <tr><td>Failure mode</td><td>Missed dx</td><td>Silent interaction</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function setMeta(name: string, content: string) {
  let el = document.querySelector(`meta[name="${name}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute("name", name);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}
