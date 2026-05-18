import type { Confidence, Interpretation } from "@/lib/types";

interface Props {
  interpretations: Interpretation[];
  discarded: string[];
  selected: number;
  calibration?: any;
}

export default function DeliberationTree({ interpretations, discarded, selected, calibration }: Props) {
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
    </div>
  );
}
