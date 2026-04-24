import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { motion } from "framer-motion";

const sectionVariants = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
};

const pillars = [
  {
    title: "Deliberation Engine",
    body: `We instrument Gemma 4's chain-of-thought tokens by injecting the <|think|> token into the system prompt. The Glass Box intercepts native <|channel>thought blocks and captures competing hypotheses with probability estimates, discarded reasoning paths (what the model rejected and why), and the step-by-step logical chain from question to conclusion. The clinician sees not just the answer, but the road not taken — all through progressive disclosure.`,
  },
  {
    title: "Source Grounding Visualizer",
    body: `Each generated claim is split into atomic propositions and verified against a curated clinical knowledge base (FDA Drug Labels, DrugBank, PubMed/MIMIC). There is no live web search — guaranteeing a strictly air-gapped, zero-data-egress environment. To bypass semantic brittleness of pure lexical BM25 retrieval, P.R.I.S.M. uses a highly quantized, ultra-lightweight dense embedding model (ONNX-optimized MiniLM-L6) running strictly on the CPU. The latency difference compared to BM25 is negligible, but recall for recognizing semantically similar pharmacological terminology (e.g., "CYP3A4 inhibitor" vs. "enzyme blocker") is exponentially higher. Verification runs asynchronously — the deliberation trace renders immediately, while claims are only presented alongside their completed verification dots (🟢🟡🔴⚪).`,
  },
  {
    title: "Certainty Indicators",
    body: `Raw model logits are unreliable for clinical safety. P.R.I.S.M. leverages Conformal Prediction and Speculative Decoding to establish statistically guaranteed confidence boundaries from a single pass.

Dynamic Conformal Prediction: Standard conformal prediction is vulnerable to calibration shift. P.R.I.S.M. implements dynamic conformal prediction paired with a lightweight out-of-distribution (OOD) detector. If the incoming query's semantic distance from the calibration set is high, the system automatically widens the conformal threshold (α) or explicitly flags the certainty indicator as unreliable.

Speculative Decoding (Draft & Verify): A heavily quantized tiny model rapidly "drafts" the reasoning trace. The massive 26B model strictly verifies and accepts/rejects drafted tokens in parallel — guaranteeing the final output matches the 26B model's distribution at 2-3× the speed.

Temperature scaling is validated against Brier Score and Expected Calibration Error (ECE) metrics. We explicitly chose NOT to blur or fade text for uncertainty — explicit badges, color-coded borders, and progress bars are clearer and more accessible.`,
  },
];

const steps = [
  { h: "Generate", b: "Upstream server diffs current canonical index against last-published manifest. Deterministic, reproducible delta." },
  { h: "Sign", b: "Ed25519 signature over manifest + all delta payloads. Tamper detection — reject unsigned/modified bundles." },
  { h: "Encrypt", b: "AES-256-GCM with per-institution rotating keys. Confidentiality in transit and at rest." },
  { h: "Pull", b: "Local agent initiates one-way TLS 1.3 pull (no inbound connections). Zero-data-egress maintained." },
  { h: "Verify", b: "Signature verification → hash chain validation → schema check. Integrity guaranteed before any index mutation." },
  { h: "Apply", b: "Atomic delta application — rollback on any failure. Index never left in partial/corrupt state." },
  { h: "Re-embed", b: "New/modified documents re-embedded via CPU MiniLM-L6. Updated vectors without GPU dependency." },
  { h: "Audit", b: "Update receipt written to TPM-encrypted local audit log. Full institutional compliance trail." },
];

export default function HowItWorks() {
  const [open, setOpen] = useState<number | null>(0);
  useEffect(() => { document.title = "How It Works · P.R.I.S.M."; }, []);

  return (
    <motion.div className="container" style={{ paddingTop: "var(--space-12)" }} initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.15 } } }}>
      <motion.header style={{ textAlign: "center", marginBottom: "var(--space-12)" }} variants={sectionVariants}>
        <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)" }}>The Glass Box, Explained.</h1>
        <p className="hero-sub" style={{ marginTop: "var(--space-4)" }}>
          A transparency stack built around three pillars, a hardened knowledge base update protocol, and zero data egress. Powered by Gemma 4 A4B 26B.
        </p>
      </motion.header>

      <motion.section aria-label="Three pillars" style={{ marginBottom: "var(--space-12)" }} variants={sectionVariants}>
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
            {open === i && <div className="accordion-body" style={{ whiteSpace: "pre-line" }}>{p.body}</div>}
          </div>
        ))}
      </motion.section>

      <motion.section aria-label="Architecture" style={{ marginBottom: "var(--space-12)" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <h2 style={{ marginBottom: "var(--space-6)" }}>Architecture</h2>
        <div className="arch-diagram">
          <div className="arch-box">Next.js — Glass Box UI<br /><span style={{ fontSize: 11, color: "var(--ink-inverse-muted)" }}>Default View + Expert View · Progressive Disclosure</span></div>
          <div className="arch-arrow">↓ API</div>
          <div className="arch-box">Python (FastAPI) — Orchestrator + SSE<br /><span style={{ fontSize: 11, color: "var(--ink-inverse-muted)" }}>Thought parser · Claim extractor · Logprobs · KB search</span></div>
          <div className="arch-arrow">↓ Local API call</div>
          <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", justifyContent: "center" }}>
            <div className="arch-box">Ollama / llama.cpp<br /><span style={{ fontSize: 11, color: "var(--ink-inverse-muted)" }}>Gemma 4 A4B 26B MoE (MXFP4 + RotorQuant)</span></div>
            <div className="arch-box">Knowledge Base<br /><span style={{ fontSize: 11, color: "var(--ink-inverse-muted)" }}>FAISS/ChromaDB · CPU MiniLM-L6 ONNX</span></div>
          </div>
        </div>
      </motion.section>

      <motion.section aria-label="Update protocol" style={{ marginBottom: "var(--space-12)" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <h2 style={{ marginBottom: "var(--space-3)" }}>Knowledge Base Update Protocol</h2>
        <p style={{ color: "var(--ink-secondary)", marginBottom: "var(--space-6)", lineHeight: 1.6 }}>
          Secure, batched delta-update protocol — nightly encrypted pulls that keep the clinical grounding index current while maintaining full HIPAA compliance. If the local index hasn't received a successful delta update in &gt;7 days, a staleness warning is surfaced.
        </p>
        <div className="timeline">
          {steps.map((s, i) => (
            <div key={i} className="timeline-step">
              <h4>{i + 1}. {s.h}</h4>
              <p>{s.b}</p>
            </div>
          ))}
        </div>
      </motion.section>

      <motion.section aria-label="Privacy" style={{ marginBottom: "var(--space-12)" }} variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <h2 style={{ marginBottom: "var(--space-6)" }}>Mathematically Stateless Privacy</h2>
        <div className="arch-diagram" style={{ textAlign: "left", justifyItems: "start" }}>
          <p style={{ color: "var(--ink-inverse-muted)", lineHeight: 1.6, maxWidth: 700 }}>
            While Ollama wraps the llama.cpp engine, securing Wi-Fi transit with mTLS/JWT is insufficient if PHI remains accessible on disk. P.R.I.S.M. makes the core inference loop <strong style={{ color: "var(--ink-inverse)" }}>mathematically stateless</strong> — strict in-memory-only processing with zero local disk caching.
          </p>
          <p style={{ color: "var(--ink-inverse-muted)", lineHeight: 1.6, maxWidth: 700, marginTop: 12 }}>
            For mandatory audit trails: local encrypted logging via the workstation's <strong style={{ color: "var(--aura-cyan)" }}>TPM / HSM</strong>. If centralized logging is required, strict <strong style={{ color: "var(--aura-cyan)" }}>on-device NER scrubbing</strong> strips all PHI before any transmission.
          </p>
        </div>
      </motion.section>

      <motion.section aria-label="Tech stack" variants={sectionVariants} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-50px" }}>
        <h2 style={{ marginBottom: "var(--space-6)" }}>Tech Stack</h2>
        <div className="tech-table">
          <table>
            <thead><tr><th>Layer</th><th>Technology</th><th>Why</th></tr></thead>
            <tbody>
              <tr><td>Model</td><td>Gemma 4 A4B (26B MoE, ~4B active)</td><td>Optimized local context, MoE efficiency, best-in-class reasoning</td></tr>
              <tr><td>Fine-Tuning</td><td>Unsloth</td><td>Deliberation format adapter via QLoRA (~16 GB VRAM, 2× faster)</td></tr>
              <tr><td>Local Hosting</td><td>Ollama / llama.cpp</td><td>MXFP4 quantization, RotorQuant KV cache, containerization</td></tr>
              <tr><td>Backend</td><td>Python (FastAPI)</td><td>Thought block parsing, selective verification, logprob extraction</td></tr>
              <tr><td>Frontend</td><td>Next.js / React Native</td><td>Progressive disclosure UI, streaming response rendering</td></tr>
              <tr><td>Embeddings</td><td>ONNX MiniLM-L6 (CPU)</td><td>Air-gapped dense retrieval, no GPU dependency</td></tr>
              <tr><td>Calibration</td><td>Conformal Prediction + OOD</td><td>Statistically guaranteed confidence, not raw logprobs</td></tr>
              <tr><td>Deployment</td><td>On-prem · zero data egress</td><td>HIPAA-aligned, mathematically stateless</td></tr>
            </tbody>
          </table>
        </div>
      </motion.section>
    </motion.div>
  );
}
