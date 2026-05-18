import type { Confidence, Interpretation } from "@/lib/types";

interface Props {
  interpretations: Interpretation[];
  discarded: string[];
  selected: number;
  calibration?: any;
}

export default function DeliberationTree({ interpretations, discarded, selected, calibration }: Props) {
  return (
    <div className="delib" aria-label="Deliberation tree">
      <div style={{ color: "var(--aura-cyan)", marginBottom: 12 }}>{"<|think|>"}</div>

      {/* Competing Interpretations Section */}
      <div className="delib-section">
        <h3 style={{ color: "var(--ink-inverse)", margin: "12px 0 8px", fontFamily: "var(--font-display)", fontSize: "var(--text-ui)" }}>
          Competing Interpretations
        </h3>
        {interpretations.map((it, i) => (
          <div
            key={i}
            className={`delib-item ${i === selected ? "delib-item--selected" : ""}`}
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div className="delib-header">
              {i === selected ? "▶ " : ""}Interpretation {String.fromCharCode(65 + i)}: {it.label} — {it.probability}%
            </div>
            {it.supporting.map((s, k) => (
              <div key={`s-${k}`} className="delib-bullet delib-bullet--pos">+ {s}</div>
            ))}
            {it.weakening.map((s, k) => (
              <div key={`w-${k}`} className="delib-bullet delib-bullet--neg">- {s}</div>
            ))}
          </div>
        ))}
      </div>

      {/* Clinical Audit Findings Section */}
      <div className="clinical-audit-section">
        <h3 style={{ color: "var(--ink-inverse)", margin: "12px 0 8px", fontFamily: "var(--font-display)", fontSize: "var(--text-ui)" }}>
          Clinical Audit Findings
        </h3>
        {interpretations.map((it, i) => (
          <div key={i} className="clinical-audit-item">
            <div className="clinical-audit-header">
              Interpretation {String.fromCharCode(65 + i)}: {it.label} ({it.probability}%)
            </div>
            <div className="clinical-recommendations">
              {it.supporting.map((s, k) => (
                <div key={`rec-${k}`} className="clinical-recommendation-item">
                  <span className="recommendation-text">Recommendation: {s}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Discarded Interpretations */}
      {discarded.map((d, i) => (
        <div
          key={`d-${i}`}
          className="delib-item delib-item--discarded"
          style={{ animationDelay: `${(interpretations.length + i) * 80}ms` }}
        >
          ✗ Discarded: {d}
        </div>
      ))}

      {/* Calibration Information */}
      {calibration && (
        <div className="delib-calib">
          <div className="calibration-header">
            <span>Brier <strong>{calibration.brier?.toFixed(2) ?? "—"}</strong></span>
            <span>ECE <strong>{calibration.ece?.toFixed(2) ?? "—"}</strong></span>
            <span>OOD <strong style={{ color: calibration.ood ? "var(--aura-orange)" : "#4ADE80" }}>{calibration.ood ? "FLAG" : "no"}</strong></span>
          </div>
        </div>
      )}
    </div>
  );
}
