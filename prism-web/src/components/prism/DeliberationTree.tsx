import type { Confidence, Interpretation, SourceRef } from "@/lib/types";

interface Token {
  type: "text" | "dot";
  text?: string;
  ref?: SourceRef;
}

interface Props {
  interpretations: Interpretation[];
  discarded: string[];
  selected: number;
  calibration?: any;
  tokens?: Token[];
}

export default function DeliberationTree({ interpretations, discarded, selected, calibration, tokens }: Props) {
  return (
    <div className="delib" aria-label="Deliberation tree" style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--ink-inverse-muted)" }}>
      <div style={{ color: "var(--ink-inverse)", marginBottom: 8 }}>{"<|channel>thought\n"}</div>
      
      <div style={{ paddingLeft: 16, borderLeft: "2px solid var(--border-dark)", marginBottom: 12 }}>
        {interpretations.map((it, i) => (
          <div key={i} style={{ marginBottom: i === interpretations.length - 1 ? 0 : 12, animationDelay: `${i * 80}ms` }} className="animate-in fade-in slide-in-from-bottom-2">
            <div style={{ color: "var(--ink-inverse)" }}>
              Interpretation {String.fromCharCode(65 + i)}: {it.label} [{it.probability}%]
            </div>
            {it.supporting.map((s, k) => (
              <div key={`s-${k}`}>├── Supporting: {s}</div>
            ))}
            {it.weakening.map((w, k) => (
              <div key={`w-${k}`}>└── Weakening: {w}</div>
            ))}
          </div>
        ))}

        {discarded.length > 0 && (
          <div style={{ marginTop: 8 }}>
            {discarded.map((d, i) => (
              <div key={`d-${i}`} className="animate-in fade-in" style={{ animationDelay: `${(interpretations.length + i) * 80}ms` }}>
                ✗ Discarded: {d}
              </div>
            ))}
          </div>
        )}
      </div>

      {interpretations[selected] && (
        <div style={{ color: "var(--aura-cyan)" }}>
          ▶ Selected: Interpretation {String.fromCharCode(65 + selected)}
        </div>
      )}

      {calibration && (
        <div style={{ marginTop: 12, borderTop: "1px dashed var(--border-dark)", paddingTop: 12, fontSize: 11 }}>
          CALIBRATION METRICS:<br />
          Brier Score: {calibration.brier?.toFixed(3) ?? "—"} · ECE: {calibration.ece?.toFixed(3) ?? "—"} · OOD Distance: {calibration.ood ? <span style={{ color: "var(--aura-orange)" }}>FLAG</span> : <span style={{ color: "#4ADE80" }}>Safe</span>}
        </div>
      )}

      {tokens && tokens.filter(t => t.type === "dot" && t.ref && t.ref.signal !== "grey").length > 0 && (
        <div style={{ marginTop: 24, borderTop: "2px solid var(--border-dark)", paddingTop: 16 }}>
          <div style={{ color: "var(--ink-inverse)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
            Source Grounding Verification Logs
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {tokens.filter(t => t.type === "dot" && t.ref && t.ref.signal !== "grey").map((t, i) => {
              const r = t.ref!;
              let color = "#999";
              if (r.signal === "green") color = "#16A34A";
              if (r.signal === "yellow") color = "var(--aura-yellow)";
              if (r.signal === "red") color = "#DC2626";
              
              return (
                <div key={i} className="animate-in fade-in" style={{ paddingLeft: 12, borderLeft: `2px solid ${color}`, animationDelay: `${i * 100}ms` }}>
                  <div style={{ color: "var(--ink-inverse)", fontWeight: 500, marginBottom: 4 }}>
                    Claim {i + 1} Status: <span style={{ color }}>[{r.signal.toUpperCase()}]</span>
                  </div>
                  <div style={{ color: "var(--ink-inverse-muted)" }}>Source: {r.source}</div>
                  {r.snippet && <div style={{ color: "var(--ink-tertiary)", marginTop: 4, fontStyle: "italic" }}>"{r.snippet}"</div>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
