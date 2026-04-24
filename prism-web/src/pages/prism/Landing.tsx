import { Link } from "react-router-dom";
import { Sparkles, Brain, Link2, Gauge, ArrowRight, Github, Database, Lock, Cpu, Server, AlertCircle, CheckCircle2, Layers, Zap, ArchiveRestore, Workflow, ShieldCheck, ArrowDownToLine, RefreshCcw, DatabaseZap } from "lucide-react";
import PillarCard from "@/components/prism/PillarCard";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

const comparisonData = [
  { subject: 'Time Horizon (Minutes)', Triage: 1, Audit: 9, fullMark: 10 },
  { subject: 'Data Density', Triage: 2, Audit: 10, fullMark: 10 },
  { subject: 'Interpretability ROI', Triage: 4, Audit: 10, fullMark: 10 },
  { subject: 'Audit-friendly', Triage: 3, Audit: 9, fullMark: 10 },
];

const archFlowVariants = {
  hidden: { pathLength: 0, opacity: 0 },
  show: { pathLength: 1, opacity: 1, transition: { duration: 1.5, ease: "easeInOut", repeat: Infinity, repeatType: "loop" as const } }
};

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
          <Link to="/demo" className="pill pill--solid">
            <Sparkles size={14} /> Launch Glass Box
          </Link>
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
                  <div className="cmd-preview-line"><span className="source-dot source-dot--red" /> The orbit changes by 2% every century. <span style={{ color: "#F87171", fontSize: 11, marginLeft: 4 }}>⚠️ Contradicted</span></div>
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
        <div className="compare-card" style={{ background: "transparent", border: "none", padding: 0, height: 350, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={comparisonData}>
              <PolarGrid stroke="var(--border-dark)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--ink-inverse-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
              <Radar name="Emergency Triage" dataKey="Triage" stroke="#F87171" fill="#F87171" fillOpacity={0.3} />
              <Radar name="Polypharmacy Audit" dataKey="Audit" stroke="var(--aura-cyan)" fill="var(--aura-cyan)" fillOpacity={0.6} />
              <Legend wrapperStyle={{ fontFamily: 'var(--font-primary)', fontSize: 13 }} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--canvas-dark)', border: '1px solid var(--border-dark)', borderRadius: 8, fontFamily: 'var(--font-mono)' }} itemStyle={{ color: '#fff' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </motion.section>

      <motion.section className="container" aria-label="Tech Stack" style={{ padding: "var(--space-12) 0" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <div style={{ textAlign: "center" }}>
          <h2>Gemma 4 A4B 26B + Unsloth</h2>
          <p style={{ color: "var(--ink-secondary)", maxWidth: 600, margin: "var(--space-3) auto 0" }}>Knowledge of a large model. Cost of a small one.</p>
        </div>
        <motion.div className="tech-bento-grid" variants={staggerContainer} initial="hidden" whileInView="show" viewport={{ once: true }}>
          <motion.div className="tech-bento-item" variants={itemVariants} style={{ position: "relative", overflow: "hidden" }}>
            <h4><Layers size={16} style={{ display: "inline", verticalAlign: "text-bottom", marginRight: 4 }} /> MIXTURE OF EXPERTS</h4>
            <div style={{ display: "flex", alignItems: "center", gap: 16, margin: "16px 0" }}>
              <div style={{ width: 80, height: 80 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[{ name: "Active", value: 4, fill: "var(--aura-magenta)" }, { name: "Idle", value: 22, fill: "var(--border-dark)" }]} layout="vertical" margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                    <XAxis type="number" hide domain={[0, 26]} />
                    <YAxis dataKey="name" type="category" hide />
                    <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ backgroundColor: 'var(--canvas-dark)', border: '1px solid var(--border-dark)' }} />
                    <Bar dataKey="value" stackId="a" radius={[4, 4, 4, 4]} barSize={12} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="tech-bento-val" style={{ margin: 0, fontSize: "1.75rem" }}>26B <span style={{ fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500, display: "block" }}>total params</span></div>
            </div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>MoE routing activates ~4B relevant expert subnetworks per token, delivering flagship reasoning on consumer hardware.</p>
          </motion.div>

          <motion.div className="tech-bento-item" variants={itemVariants}>
            <h4><ArchiveRestore size={16} style={{ display: "inline", verticalAlign: "text-bottom", marginRight: 4 }} /> MXFP4 QUANTIZATION</h4>
            <div style={{ margin: "16px 0", height: 80, display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-inverse-muted)" }}>
                <span>VRAM Usage</span>
                <span style={{ color: "var(--aura-cyan)" }}>16GB / 24GB</span>
              </div>
              <div style={{ height: 12, background: "var(--border-dark)", borderRadius: 6, overflow: "hidden" }}>
                <motion.div initial={{ width: 0 }} whileInView={{ width: "66%" }} transition={{ duration: 1.5, delay: 0.5, ease: "easeOut" }} style={{ height: "100%", background: "var(--aura-cyan)", borderRadius: 6 }} />
              </div>
            </div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>Microscaling Formats 4-bit precision squeezes the entire 26B model securely into consumer GPUs with near-uncompressed quality.</p>
          </motion.div>

          <motion.div className="tech-bento-item" variants={itemVariants}>
            <h4><Zap size={16} style={{ display: "inline", verticalAlign: "text-bottom", marginRight: 4 }} /> ROTORQUANT KV CACHE</h4>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 16, margin: "16px 0", height: 80 }}>
              <div style={{ flex: 1, display: "flex", alignItems: "flex-end", gap: 4, height: "100%" }}>
                <motion.div initial={{ height: "20%" }} whileInView={{ height: "100%" }} transition={{ duration: 1, ease: "easeOut" }} style={{ flex: 1, background: "var(--aura-orange)", borderRadius: "4px 4px 0 0", opacity: 0.8 }} />
                <motion.div initial={{ height: "20%" }} whileInView={{ height: "20%" }} style={{ flex: 1, background: "var(--border-dark)", borderRadius: "4px 4px 0 0" }} />
              </div>
              <div className="tech-bento-val" style={{ margin: 0, fontSize: "1.75rem" }}>5.3x <span style={{ fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500, display: "block" }}>faster prefill</span></div>
            </div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>Sparse 3D Clifford rotors replace heavy dense transforms, handling massive patient records instantly without OOM errors.</p>
          </motion.div>

          <motion.div className="tech-bento-item" variants={itemVariants}>
            <h4><Workflow size={16} style={{ display: "inline", verticalAlign: "text-bottom", marginRight: 4 }} /> UNSLOTH QLoRA</h4>
            <div style={{ margin: "16px 0", height: 80, display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: "linear" }} style={{ position: "absolute", width: 60, height: 60, borderRadius: "50%", border: "2px dashed var(--ink-tertiary)", borderTopColor: "var(--aura-cyan)", borderRightColor: "var(--aura-cyan)" }} />
              <div className="tech-bento-val" style={{ margin: 0, fontSize: "1.75rem" }}>2x <span style={{ fontSize: "1rem", color: "var(--ink-tertiary)", fontWeight: 500, display: "inline" }}>speed</span></div>
            </div>
            <p style={{ color: "var(--ink-secondary)", fontSize: "var(--text-ui)" }}>Fine-tuned deliberation format adapter and temperature scaling layer for rigorous probability calibration.</p>
          </motion.div>
        </motion.div>
      </motion.section>

      <motion.section className="container" aria-label="Context Rolling" style={{ paddingBottom: "var(--space-12)" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <style>{`
          .flowchart-split {
            display: flex;
            width: 320px;
            height: 40px;
            position: relative;
          }
          .flowchart-branches {
            display: flex;
            width: 100%;
            max-width: 800px;
            justify-content: space-between;
            gap: 32px;
          }
          @media (max-width: 768px) {
            .flowchart-split {
              display: none;
            }
            .flowchart-branches {
              flex-direction: column;
              gap: 32px;
              align-items: center;
            }
          }
        `}</style>
        <div className="context-rolling">
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, justifyContent: "center" }}>
            <ShieldCheck size={28} color="var(--aura-cyan)" />
            <h3 style={{ fontSize: "var(--text-h2)", color: "var(--ink-inverse)", fontFamily: "var(--font-display)", margin: 0 }}>Strict Extractive Context Rolling</h3>
          </div>
          <p style={{ color: "var(--ink-inverse-muted)", fontSize: "var(--text-ui)", fontFamily: "var(--font-primary)", marginBottom: 48, maxWidth: 800, textAlign: "center", marginInline: "auto", lineHeight: 1.6 }}>
            Attempting a 256K context window locally causes OOM failures. Lossy abstractive summarization drops critical PHI, creating fatal clinical risks. P.R.I.S.M. uses extractive rolling and hybrid memory pooling.
          </p>

          <div className="flowchart-container" style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>

            <div style={{ background: "var(--canvas-dark-elevated)", border: "1px solid var(--border-dark)", padding: "16px 24px", borderRadius: 12, display: "flex", flexDirection: "column", alignItems: "center", zIndex: 2, width: "100%", maxWidth: 300, boxShadow: "0 8px 32px rgba(0,0,0,0.2)" }}>
              <Database size={24} style={{ color: "var(--ink-secondary)", marginBottom: 8 }} />
              <strong style={{ color: "var(--ink-inverse)", fontSize: 15 }}>Raw Clinical Context</strong>
              <span style={{ fontSize: 13, color: "var(--ink-inverse-muted)", marginTop: 4 }}>256K Tokens (OOM Risk)</span>
            </div>

            <div className="flowchart-split">
              <div style={{ position: "absolute", left: "50%", top: 0, bottom: "50%", width: 2, background: "var(--border-dark)", marginLeft: -1 }} />
              <div style={{ position: "absolute", left: 0, right: 0, top: "50%", height: 2, background: "var(--border-dark)" }} />
              <div style={{ position: "absolute", left: 0, top: "50%", bottom: 0, width: 2, background: "var(--border-dark)" }} />
              <div style={{ position: "absolute", right: 0, top: "50%", bottom: 0, width: 2, background: "var(--border-dark)" }} />
            </div>

            <div className="flowchart-branches">

              <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 16, width: "100%" }}>
                <div style={{ background: "rgba(248, 113, 113, 0.03)", border: "1px solid rgba(248, 113, 113, 0.2)", padding: "24px", borderRadius: 16, width: "100%", position: "relative", display: "flex", flexDirection: "column", height: "100%" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                    <AlertCircle size={20} color="#F87171" />
                    <span style={{ color: "#F87171", fontWeight: 600, fontSize: 15 }}>Abstractive Summarization</span>
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--ink-inverse-muted)", marginBottom: 20, background: "rgba(0,0,0,0.2)", padding: "12px 16px", borderRadius: 8, border: "1px dashed rgba(248, 113, 113, 0.2)" }}>
                    "Patient has heart issues and takes meds."
                  </div>
                  <div style={{ marginTop: "auto", fontSize: 13, color: "#F87171", background: "rgba(248, 113, 113, 0.1)", padding: "10px 12px", borderRadius: 8, display: "flex", gap: 8, alignItems: "flex-start", border: "1px solid rgba(248, 113, 113, 0.2)" }}>
                    <span style={{ fontSize: 16, lineHeight: 1 }}>⚠️</span>
                    <span style={{ lineHeight: 1.4 }}>Information Loss Detected (Dosages, CYP pathways stripped)</span>
                  </div>
                </div>
              </div>

              <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 16, width: "100%" }}>
                <div style={{ background: "rgba(34, 211, 238, 0.03)", border: "1px solid rgba(34, 211, 238, 0.3)", padding: "24px", borderRadius: 16, width: "100%", position: "relative", boxShadow: "0 0 40px rgba(34, 211, 238, 0.05)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                    <CheckCircle2 size={20} color="var(--aura-cyan)" />
                    <span style={{ color: "var(--aura-cyan)", fontWeight: 600, fontSize: 15 }}>Extractive Rolling</span>
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--ink-inverse)", marginBottom: 20, lineHeight: 1.6, background: "rgba(0,0,0,0.2)", padding: "12px 16px", borderRadius: 8, border: "1px dashed rgba(34, 211, 238, 0.3)" }}>
                    "<span style={{ color: "var(--aura-cyan)", background: "rgba(34, 211, 238, 0.1)", padding: "2px 6px", borderRadius: 4 }}>Metoprolol 50mg</span>. Ejection fraction <span style={{ color: "var(--aura-cyan)", background: "rgba(34, 211, 238, 0.1)", padding: "2px 6px", borderRadius: 4 }}>35%</span>."
                  </div>
                  <div style={{ fontSize: 13, color: "var(--aura-cyan)", background: "rgba(34, 211, 238, 0.1)", padding: "10px 12px", borderRadius: 8, display: "flex", alignItems: "center", gap: 8, border: "1px solid rgba(34, 211, 238, 0.2)" }}>
                    <ShieldCheck size={16} /> <span style={{ fontWeight: 500 }}>Critical PHI Preserved</span>
                  </div>
                  <motion.div
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: "100%", opacity: [0, 1, 0] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                    style={{ position: "absolute", bottom: -1, left: 0, height: 2, background: "var(--aura-cyan)" }}
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>
                  <div style={{ width: 2, height: 24, background: "linear-gradient(to bottom, rgba(34,211,238,0.5), transparent)" }} />
                  <motion.div style={{ background: "var(--canvas-dark-elevated)", border: "1px dashed var(--aura-cyan)", padding: "16px 24px", borderRadius: 12, display: "flex", alignItems: "center", gap: 12, position: "relative", overflow: "hidden", width: "100%", justifyContent: "center", boxShadow: "0 4px 20px rgba(0,0,0,0.3)" }} animate={{ borderColor: ["rgba(34, 211, 238, 0.3)", "rgba(34, 211, 238, 0.8)", "rgba(34, 211, 238, 0.3)"] }} transition={{ duration: 3, repeat: Infinity }}>
                    <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at center, rgba(34, 211, 238, 0.1) 0%, transparent 70%)" }} />
                    <Server size={20} color="var(--aura-cyan)" style={{ position: "relative", zIndex: 1 }} />
                    <span style={{ color: "var(--aura-cyan)", fontWeight: 600, fontSize: 14, position: "relative", zIndex: 1 }}>Hybrid Pool (RAM Offload)</span>
                  </motion.div>
                </div>
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
              <strong style={{ color: "var(--ink-inverse)", fontFamily: "var(--font-primary)" }}>Institutional Server</strong><br />
              <span style={{ color: "var(--ink-inverse-muted)", fontSize: 11 }}>Canonical DB (FDA, DrugBank)</span>
            </div>

            <div className="arch-edge" style={{ position: "relative", overflow: "hidden" }}>
              <ArrowDownToLine size={16} />
              <span style={{ background: "var(--canvas-dark-pill)", padding: "2px 8px", borderRadius: 12, border: "1px solid var(--border-dark)", position: "relative", zIndex: 1 }}>Nightly Ed25519 Signed Delta</span>
              <ArrowDownToLine size={16} />
              <motion.div style={{ position: "absolute", top: 0, bottom: 0, width: 2, background: "linear-gradient(to bottom, transparent, var(--aura-magenta), transparent)", left: "50%", marginLeft: -1 }} animate={{ y: ["-100%", "100%"] }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} />
            </div>

            <div className="arch-node" style={{ borderTopColor: "var(--aura-cyan)", position: "relative" }}>
              <motion.div animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }} transition={{ duration: 3, repeat: Infinity }} style={{ position: "absolute", inset: -20, background: "radial-gradient(circle at center, rgba(34, 211, 238, 0.15) 0%, transparent 70%)", zIndex: 0 }} />
              <Lock size={20} style={{ margin: "0 auto 8px", color: "var(--aura-cyan)", position: "relative", zIndex: 1 }} />
              <strong style={{ color: "var(--ink-inverse)", fontFamily: "var(--font-primary)", position: "relative", zIndex: 1 }}>Local Clinical Index</strong><br />
              <span style={{ color: "var(--ink-inverse-muted)", fontSize: 11, position: "relative", zIndex: 1 }}>CPU MiniLM-L6 Embeddings</span>
            </div>

            <div className="arch-edge" style={{ position: "relative", overflow: "hidden" }}>
              <RefreshCcw size={16} />
              <span style={{ background: "var(--canvas-dark-pill)", padding: "2px 8px", borderRadius: 12, border: "1px solid var(--border-dark)", position: "relative", zIndex: 1 }}>Air-Gapped Claim Verification</span>
              <RefreshCcw size={16} />
              <motion.div style={{ position: "absolute", top: 0, bottom: 0, width: 2, background: "linear-gradient(to bottom, transparent, var(--aura-cyan), transparent)", left: "50%", marginLeft: -1 }} animate={{ y: ["-100%", "100%"] }} transition={{ duration: 2, repeat: Infinity, ease: "linear", delay: 1 }} />
            </div>

            <div className="arch-node" style={{ borderTopColor: "var(--aura-orange)" }}>
              <Cpu size={20} style={{ margin: "0 auto 8px", color: "var(--aura-orange)" }} />
              <strong style={{ color: "var(--ink-inverse)", fontFamily: "var(--font-primary)" }}>llama.cpp Engine</strong><br />
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
