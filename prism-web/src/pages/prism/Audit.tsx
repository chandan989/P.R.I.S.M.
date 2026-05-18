import { useEffect, useRef, useState } from "react";
import PatientRegimenForm, { emptyPatient, patientToQuery, type PatientData } from "@/components/prism/PatientRegimenForm";
import DeliberationTree from "@/components/prism/DeliberationTree";
import StreamingText, { type Token } from "@/components/prism/StreamingText";
import ConfidenceBadge from "@/components/prism/ConfidenceBadge";
import SkeletonLoader from "@/components/prism/SkeletonLoader";
import { streamAudit } from "@/lib/api";
import type { AuditStreamEvent, Confidence, Interpretation } from "@/lib/types";
import { ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Tab = "default" | "expert";

export default function Audit() {
  const [patient, setPatient] = useState<PatientData>(() => emptyPatient());
  const [tab, setTab] = useState<Tab>("default");
  const [busy, setBusy] = useState(false);
  const [tokens, setTokens] = useState<Token[]>([]);
  const [interps, setInterps] = useState<Interpretation[]>([]);
  const [discarded, setDiscarded] = useState<string[]>([]);
  const [selected, setSelected] = useState(0);
  const [confidence, setConfidence] = useState<Confidence | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    document.title = "Glass Box · P.R.I.S.M.";
  }, []);

  const reset = () => {
    setTokens([]); setInterps([]); setDiscarded([]); setSelected(0); setConfidence(null); setError(null);
  };

  const run = async () => {
    const query = patientToQuery(patient);
    const hasDrug = patient.drugs.some((d) => d.name.trim().length > 0);
    if (!hasDrug || busy) return;
    reset();
    setBusy(true);
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      await streamAudit(query, (e: AuditStreamEvent) => {
        if (e.type === "thought" && e.content) {
          try {
            const parsed = JSON.parse(e.content);
            setInterps(parsed.interpretations ?? []);
            setDiscarded(parsed.discarded ?? []);
            setSelected(parsed.selected ?? 0);
          } catch { /* ignore */ }
        } else if (e.type === "answer" && e.content !== undefined) {
          setTokens((prev) => [...prev, { type: "text", text: e.content! }]);
        } else if (e.type === "source_dot") {
          setTokens((prev) => [...prev, {
            type: "dot",
            ref: { signal: e.signal!, source: e.source ?? "Source", snippet: e.snippet ?? "", claim_text: e.claim_text },
          }]);
        } else if (e.type === "confidence" && e.confidence) {
          setConfidence(e.confidence);
        } else if (e.type === "error") {
          setError(e.content ?? "Stream error");
        }
      }, ctrl.signal);
    } catch (err) {
      setError((err as Error).message);
      document.dispatchEvent(new CustomEvent("open-backend-settings"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div className="container audit-grid" initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } }}>
      <motion.section aria-label="Patient and regimen input" variants={{ hidden: { opacity: 0, x: -20 }, show: { opacity: 1, x: 0, transition: { type: "spring", stiffness: 300, damping: 24 } } }}>
        <PatientRegimenForm
          value={patient}
          onChange={setPatient}
          onSubmit={run}
          busy={busy}
        />
      </motion.section>

      <motion.section className="output-panel" aria-label="Glass Box output" variants={{ hidden: { opacity: 0, x: 20 }, show: { opacity: 1, x: 0, transition: { type: "spring", stiffness: 300, damping: 24 } } }}>
        <div className="tab-strip" role="tablist">
          <button
            role="tab"
            aria-selected={tab === "default"}
            className={`tab ${tab === "default" ? "tab--active" : ""}`}
            onClick={() => setTab("default")}
          >
            Default View
          </button>
          <button
            role="tab"
            aria-selected={tab === "expert"}
            className={`tab ${tab === "expert" ? "tab--active" : ""}`}
            onClick={() => setTab("expert")}
          >
            Expert View
          </button>
        </div>

        <div className="output-body">
          {error && <div className="error-card">⚠ {error}</div>}

          {!busy && tokens.length === 0 && interps.length === 0 && !error && (
            <div style={{ color: "var(--ink-tertiary)", fontSize: "var(--text-ui)" }}>
              Enter the patient's demographics and regimen on the left, then click <strong>Analyze Regimen</strong>.
              Source-grounded answers and the deliberation tree will appear here.
            </div>
          )}

          {busy && tokens.length === 0 && <SkeletonLoader rows={4} />}

          <AnimatePresence mode="wait">
          {tab === "default" ? (
            <motion.div key="default" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
              {tokens.length > 0 && <StreamingText tokens={tokens} isStreaming={busy} />}
              {confidence && <ConfidenceBadge level={confidence.level} score={confidence.score} />}
              {interps.length > 0 && (
                <button
                  className="pill"
                  style={{ marginTop: "var(--space-4)" }}
                  onClick={() => setTab("expert")}
                >
                  Why did the AI say this? <ChevronDown size={14} />
                </button>
              )}
            </motion.div>
          ) : (
            <motion.div key="expert" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
              {interps.length > 0 ? (
                <DeliberationTree
                  interpretations={interps}
                  discarded={discarded}
                  selected={selected}
                  calibration={confidence ?? undefined}
                  tokens={tokens}
                />
              ) : (
                <div style={{ color: "var(--ink-tertiary)", fontSize: "var(--text-ui)" }}>
                  Run an analysis to see the model's deliberation tree.
                </div>
              )}
            </motion.div>
          )}
          </AnimatePresence>
        </div>
      </motion.section>
    </motion.div>
  );
}
