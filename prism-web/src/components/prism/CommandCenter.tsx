import { Send } from "lucide-react";
import StalenessWarning from "./StalenessWarning";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  busy?: boolean;
  daysSinceUpdate?: number;
  quickInserts?: string[];
  onQuickInsert?: (s: string) => void;
  scenarios?: { label: string; desc?: string; onClick: () => void }[];
}

export default function CommandCenter({
  value,
  onChange,
  onSubmit,
  busy,
  daysSinceUpdate = 9,
  quickInserts = ["Warfarin 5mg", "Clarithromycin 500mg", "Metformin 1000mg", "+ Add Drug"],
  onQuickInsert,
  scenarios,
}: Props) {
  const insert = (drug: string) => {
    if (drug.startsWith("+")) return;
    onQuickInsert?.(drug);
  };
  return (
    <div className="command-border">
      <div className="command-center">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
          <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.1rem" }}>Drug Regimen Audit</div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)", color: "var(--ink-inverse-muted)" }}>
            session · {Math.random().toString(36).slice(2, 8)}
          </span>
        </div>

        {scenarios && scenarios.length > 0 && (
          <div aria-label="Demo scenarios">
            <div className="cmd-row">
              {scenarios.map((s, i) => (
                <button key={i} className="cmd-pill" onClick={s.onClick}>{s.label}</button>
              ))}
            </div>
            {scenarios.some(s => s.desc) && (
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: "var(--space-3)" }}>
                {scenarios.map((s, i) => s.desc ? (
                  <div key={i} style={{ flex: "1 1 200px", fontSize: "var(--text-caption)", color: "var(--ink-inverse-muted)", lineHeight: 1.5, fontFamily: "var(--font-primary)" }}>
                    <strong style={{ color: "var(--ink-inverse)" }}>{s.label}</strong>: {s.desc}
                  </div>
                ) : null)}
              </div>
            )}
          </div>
        )}

        <textarea
          className="cmd-textarea"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={"Patient: 78F, eGFR 52\nRegimen:\n- Warfarin 5mg daily\n- Clarithromycin 500mg BID\n- ..."}
          aria-label="Drug regimen"
        />

        <div className="cmd-row">
          {quickInserts.map((q) => (
            <button key={q} className="cmd-pill" onClick={() => insert(q)}>{q}</button>
          ))}
        </div>

        <div className="cmd-submit">
          <button className="btn-submit" onClick={onSubmit} disabled={busy} aria-label="Analyze regimen">
            <Send size={16} />
          </button>
          <span className="cmd-submit-label">{busy ? "Analyzing…" : "Analyze Regimen"}</span>
        </div>

        <StalenessWarning daysSinceUpdate={daysSinceUpdate} />
      </div>
    </div>
  );
}
