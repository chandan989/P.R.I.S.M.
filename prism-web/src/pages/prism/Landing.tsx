import { Link } from "react-router-dom";
import { Sparkles, Brain, Link2, Gauge, ArrowRight, Github, Database, Lock, Cpu, Server, AlertCircle, CheckCircle2, Layers, Zap, ArchiveRestore, Workflow, ShieldCheck, ArrowDownToLine, RefreshCcw, DatabaseZap } from "lucide-react";
import PillarCard from "@/components/prism/PillarCard";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const heroVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.15 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

const sectionVariants = {
  hidden: { opacity: 0, y: 40 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

export default function Landing() {
  const [expertMode, setExpertMode] = useState(false);

  useEffect(() => {
    document.title = "P.R.I.S.M. — The Glass Box Interpreter";
    setMeta("description", "Transparency layer for clinical AI. Auditable, verifiable, trust-calibrated polypharmacy decision support powered by Gemma 4.");
  }, []);

  return (
    <>
      <motion.section className="hero container" variants={heroVariants} initial="hidden" animate="show">
        <div className="mesh-aura" />
        <motion.span className="eyebrow" variants={itemVariants}><Sparkles size={12} /> Built for the Gemma 4 Good Hackathon</motion.span>
        <motion.h1 variants={itemVariants}>
          See Inside the AI.<br />
          <span className="hero-grad">Trust Every Answer.</span>
        </motion.h1>
        <motion.p className="hero-sub" variants={itemVariants}>
          P.R.I.S.M. is a transparency layer for Gemma 4 that turns black-box clinical AI into auditable,
          verifiable, trust-calibrated decision support.
        </motion.p>
        <motion.div className="hero-ctas" variants={itemVariants}>
          <Link to="/audit" className="pill pill--solid">→ Launch Glass Box</Link>
          <a href="https://github.com" className="pill" target="_blank" rel="noreferrer">
            <Github size={14} /> View on GitHub ↗
          </a>
        </motion.div>

        <motion.div className="command-border" style={{ maxWidth: 760, margin: "0 auto" }} variants={itemVariants}>
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
        </motion.div>
      </motion.section>

      <motion.section className="container why" aria-label="The Problem vs Solution" style={{ paddingTop: 0 }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <div className="problem-card">
          <h3><AlertCircle size={20} color="#F87171" /> What Users Get Today</h3>
          <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>A confident-sounding answer without reasoning, sources, or certainty metrics.</p>
          <div className="mock-llm-response bad">
            <div style={{ fontWeight: 600, marginBottom: 8 }}>LLM Output</div>
            "Do not co-administer Warfarin and Omeprazole. It will cause bleeding."
            <div className="missing-label">No reasoning shown</div>
          </div>
        </div>
        <div className="problem-card" style={{ borderColor: "var(--aura-cyan)" }}>
          <h3><CheckCircle2 size={20} color="var(--aura-cyan)" /> The P.R.I.S.M. Glass Box</h3>
          <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>Authentic deliberation, verified claims, and calibrated confidence.</p>
          <div className="mock-llm-response good">
            <div style={{ color: "var(--ink-tertiary)", fontFamily: "var(--font-mono)", fontSize: 11, marginBottom: 8 }}>{"<|think|> Omeprazole is a CYP2C19 inhibitor. Warfarin is metabolized by CYP2C9. However, minor pathway overlap exists. Moderate risk."}</div>
            <span className="source-dot source-dot--yellow" /> "Omeprazole may alter Warfarin metabolism."
            <div style={{ marginTop: 8, fontSize: 11, fontWeight: 600, color: "#9A3412", background: "#FFEDD5", display: "inline-block", padding: "2px 6px", borderRadius: 4 }}>⚠️ MODERATE CONFIDENCE</div>
          </div>
        </div>
      </motion.section>

      <motion.section className="container bento" aria-label="Three pillars" variants={staggerContainer} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <motion.div variants={itemVariants}>
          <PillarCard
            accent="magenta"
            icon={<Brain size={22} />}
            title="Deliberation Engine"
            body="Surfaces the model's competing hypotheses, supporting evidence, and discarded paths — not just the final answer."
            preview={<code style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-tertiary)" }}>{"<|think|> A 72% · B 22% · ✗ discarded"}</code>}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
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
        </motion.div>
        <motion.div variants={itemVariants}>
          <PillarCard
            accent="cyan"
            icon={<Gauge size={22} />}
            title="Certainty Indicators"
            body="Calibrated confidence — Brier-scored, ECE-corrected, with OOD flags so clinicians know when to slow down."
            preview={<code style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-tertiary)" }}>████████░░ 80%</code>}
          />
        </motion.div>
      </motion.section>

      <motion.section className="container" aria-label="Progressive Disclosure" style={{ paddingBottom: "var(--space-12)" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
          <h2 style={{ fontSize: "var(--text-h1)", marginBottom: "var(--space-3)" }}>Progressive Disclosure</h2>
          <p style={{ color: "var(--ink-secondary)", maxWidth: 600, margin: "0 auto" }}>Users who just want the answer aren't overwhelmed. Users who want the detail can get it.</p>
        </div>
        <div className="prog-container" style={{ maxWidth: 800, margin: "0 auto" }}>
          <div className="prog-view-toggle">
            <button className={`prog-tab ${!expertMode ? 'active' : ''}`} onClick={() => setExpertMode(false)}>Default View</button>
            <button className={`prog-tab ${expertMode ? 'active' : ''}`} onClick={() => setExpertMode(true)}>Expert View</button>
          </div>
          <div className="prog-content">
            <AnimatePresence mode="wait">
              {!expertMode ? (
                <motion.div key="default" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
                <div className="cmd-preview-line"><span className="source-dot source-dot--green" /> The Earth orbits the Sun every 365.25 days.</div>
                <div className="cmd-preview-line"><span className="source-dot source-dot--green" /> This is why we have leap years.</div>
                <div className="cmd-preview-line"><span className="source-dot source-dot--yellow" /> The orbit is nearly circular.</div>
                <div className="cmd-preview-line"><span className="source-dot source-dot--red" /> The orbit changes by 2% every century. <span style={{color: "#F87171", fontSize: 11, marginLeft: 4}}>⚠️ Contradicted</span></div>
                <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ flex: 1, height: 6, background: "var(--canvas-dark-pill)", borderRadius: 99 }}><div style={{ height: "100%", width: "80%", background: "#4ADE80", borderRadius: 99 }} /></div>
                  <span style={{ fontSize: 12, color: "#4ADE80", fontWeight: 600 }}>✅ HIGH CONFIDENCE</span>
                </div>
              </motion.div>
            ) : (
              <motion.div key="expert" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--ink-inverse-muted)" }}>
                <div style={{ color: "var(--ink-inverse)", marginBottom: 8 }}>{"<|channel>thought\n"}</div>
                <div style={{ paddingLeft: 16, borderLeft: "2px solid var(--border-dark)", marginBottom: 12 }}>
                  <div style={{ color: "var(--ink-inverse)" }}>Interpretation A: Heliocentric model [99.8%]</div>
                  <div>├── Supporting: Kepler's laws, stellar parallax</div>
                  <div>└── Weakening: None significant</div>
                  <div style={{ marginTop: 8 }}>✗ Discarded: Geocentric model [0.1%]</div>
                </div>
                <div style={{ color: "var(--aura-cyan)" }}>▶ Selected: Interpretation A</div>
                <div style={{ marginTop: 12, borderTop: "1px dashed var(--border-dark)", paddingTop: 12, fontSize: 11 }}>
                  CALIBRATION METRICS:<br />
                  Brier Score: 0.042 · ECE: 0.015 · OOD Distance: 0.82 (Safe)
                </div>
              </motion.div>
            )}
            </AnimatePresence>
          </div>
        </div>
      </motion.section>

      <motion.section className="container why" aria-label="Why polypharmacy" variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
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
      </motion.section>

      <motion.section className="container" aria-label="Tech Stack" style={{ padding: "var(--space-12) 0" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <div style={{ textAlign: "center" }}>
          <h2>Gemma 4 A4B 26B + Unsloth</h2>
          <p style={{ color: "var(--ink-secondary)", maxWidth: 600, margin: "var(--space-3) auto 0" }}>Knowledge of a large model. Cost of a small one.</p>
        </div>
        <motion.div className="tech-bento-grid" variants={staggerContainer} initial="hidden" whileInView="show" viewport={{ once: true }}>
          <motion.div className="tech-bento-item" variants={itemVariants}>
            <h4><Layers size={16} style={{display: "inline", verticalAlign: "text-bottom", marginRight: 4}}/> MIXTURE OF EXPERTS</h4>
            <div className="tech-bento-val">26B <span style={{fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500}}>total</span> / ~4B <span style={{fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500}}>active</span></div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>MoE routing activates only relevant expert subnetworks per token, delivering flagship reasoning on consumer hardware.</p>
          </motion.div>
          <motion.div className="tech-bento-item" variants={itemVariants}>
            <h4><ArchiveRestore size={16} style={{display: "inline", verticalAlign: "text-bottom", marginRight: 4}}/> MXFP4 QUANTIZATION</h4>
            <div className="tech-bento-val">16GB <span style={{fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500}}>VRAM target</span></div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>Microscaling Formats 4-bit precision squeezes the entire 26B model securely into consumer GPUs with near-uncompressed quality.</p>
          </motion.div>
          <motion.div className="tech-bento-item" variants={itemVariants}>
            <h4><Zap size={16} style={{display: "inline", verticalAlign: "text-bottom", marginRight: 4}}/> ROTORQUANT KV CACHE</h4>
            <div className="tech-bento-val">5.3x <span style={{fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500}}>faster prefill</span></div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>Sparse 3D Clifford rotors replace heavy dense transforms, handling massive patient records instantly without OOM errors.</p>
          </motion.div>
          <motion.div className="tech-bento-item" variants={itemVariants}>
            <h4><Workflow size={16} style={{display: "inline", verticalAlign: "text-bottom", marginRight: 4}}/> UNSLOTH QLoRA</h4>
            <div className="tech-bento-val">2x <span style={{fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500}}>training speed</span></div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>Fine-tuned deliberation format adapter and temperature scaling layer for rigorous probability calibration.</p>
          </motion.div>
        </motion.div>
      </motion.section>

      <motion.section className="container" aria-label="Context Rolling" style={{ paddingBottom: "var(--space-12)" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <div className="context-rolling">
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
            <ShieldCheck size={24} color="var(--aura-cyan)" />
            <h3 style={{ fontSize: "var(--text-body-lg)", color: "var(--ink-inverse)", fontFamily: "var(--font-display)" }}>Strict Extractive Context Rolling</h3>
          </div>
          <p style={{ color: "var(--ink-inverse-muted)", fontSize: "var(--text-ui)", fontFamily: "var(--font-primary)", marginBottom: 16, maxWidth: 800 }}>
            Attempting a 256K context window locally causes OOM failures. Lossy abstractive summarization drops critical PHI, creating fatal clinical risks. P.R.I.S.M. uses extractive rolling and hybrid memory pooling.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="cr-turn">
              <div className="cr-box" style={{ borderColor: "#F87171" }}>
                <span style={{color: "#F87171", fontWeight: 600}}>❌ BAD: Abstractive Summarization</span><br/>
                "Patient has heart issues and takes meds." (Loses exact dosages & CYP pathways)
              </div>
            </div>
            <div className="cr-turn">
              <div className="cr-box" style={{ borderColor: "var(--aura-cyan)" }}>
                <span style={{color: "var(--aura-cyan)", fontWeight: 600}}>✅ GOOD: Extractive Rolling</span><br/>
                "Metoprolol 50mg. Ejection fraction 35%." (Verbatim extraction)
              </div>
              <div className="cr-arrow">→</div>
              <div className="cr-box" style={{ borderStyle: "dashed", textAlign: "center", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: "var(--aura-cyan)", fontWeight: 600 }}>Hybrid Pool<br/>(RAM Offload)</span>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section className="container why" aria-label="Architecture & Privacy" variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <div>
          <h2>True Local Privacy</h2>
          <p>
            Processing polypharmacy auditing queries via cloud APIs introduces unacceptable compliance risks.
            P.R.I.S.M. solves this by implementing a strictly local execution strategy: <strong>The model comes to the data, not the data to the model.</strong>
          </p>
          <div className="timeline" style={{ marginTop: 32 }}>
            <div className="timeline-step">
              <h4>1. Local Inference</h4>
              <p>Executes Gemma 4 26B locally using MXFP4 quantization and llama.cpp's RotorQuant on consumer hardware.</p>
            </div>
            <div className="timeline-step">
              <h4>2. Zero-Data-Egress</h4>
              <p>All deliberation and factual grounding happens entirely offline. Patient data never leaves the hospital firewall.</p>
            </div>
            <div className="timeline-step">
              <h4>3. Nightly Delta Updates</h4>
              <p>The clinical knowledge base is kept fresh via secure, encrypted one-way pulls from trusted institutional servers.</p>
            </div>
          </div>
        </div>
        <div className="arch-diagram" style={{ alignSelf: "center", justifySelf: "center", width: "100%", maxWidth: 440, background: "none", padding: 0 }}>
          <div className="arch-pipeline">
            <div className="arch-node" style={{ borderTopColor: "var(--aura-magenta)" }}>
              <DatabaseZap size={20} style={{ margin: "0 auto 8px", color: "var(--aura-magenta)" }} />
              <strong style={{ color: "var(--ink-inverse)", fontFamily: "var(--font-primary)" }}>Institutional Server</strong><br/>
              <span style={{ color: "var(--ink-inverse-muted)", fontSize: 11 }}>Canonical DB (FDA, DrugBank)</span>
            </div>
            
            <div className="arch-edge">
              <ArrowDownToLine size={16} />
              <span style={{ background: "var(--canvas-dark-pill)", padding: "2px 8px", borderRadius: 12, border: "1px solid var(--border-dark)" }}>Nightly Ed25519 Signed Delta</span>
              <ArrowDownToLine size={16} />
            </div>

            <div className="arch-node" style={{ borderTopColor: "var(--aura-cyan)" }}>
              <Lock size={20} style={{ margin: "0 auto 8px", color: "var(--aura-cyan)" }} />
              <strong style={{ color: "var(--ink-inverse)", fontFamily: "var(--font-primary)" }}>Local Clinical Index</strong><br/>
              <span style={{ color: "var(--ink-inverse-muted)", fontSize: 11 }}>CPU MiniLM-L6 Embeddings</span>
            </div>

            <div className="arch-edge">
              <RefreshCcw size={16} />
              <span style={{ background: "var(--canvas-dark-pill)", padding: "2px 8px", borderRadius: 12, border: "1px solid var(--border-dark)" }}>Air-Gapped Claim Verification</span>
              <RefreshCcw size={16} />
            </div>

            <div className="arch-node" style={{ borderTopColor: "var(--aura-orange)" }}>
              <Cpu size={20} style={{ margin: "0 auto 8px", color: "var(--aura-orange)" }} />
              <strong style={{ color: "var(--ink-inverse)", fontFamily: "var(--font-primary)" }}>llama.cpp Engine</strong><br/>
              <span style={{ color: "var(--ink-inverse-muted)", fontSize: 11 }}>Gemma 26B (MXFP4 / RotorQuant)</span>
            </div>
          </div>
        </div>
      </motion.section>
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
