import type { Confidence, Interpretation } from "@/lib/types";

interface Props {
  interpretations: Interpretation[];
  discarded: string[];
  selected: number;
  calibration?: Confidence;
}

export default function DeliberationTree({ interpretations, discarded, selected, calibration }: Props) {
  return (
    <div className="delib" aria-label="Deliberation tree">
      <div style={{ color: "var(--aura-cyan)", marginBottom: 12 }}>{"<|think|>"}</div>
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
            <div key={`s-${k}`} className="delib-bullet delib-bullet--pos">{s}</div>
          ))}
          {it.weakening.map((s, k) => (
            <div key={`w-${k}`} className="delib-bullet delib-bullet--neg">{s}</div>
          ))}
        </div>
      ))}
      {discarded.map((d, i) => (
        <div
          key={`d-${i}`}
          className="delib-item delib-item--discarded"
          style={{ animationDelay: `${(interpretations.length + i) * 80}ms` }}
        >
          ✗ Discarded: {d}
        </div>
      ))}
      {calibration && (
        <div className="delib-calib">
          <span>Brier <strong>{calibration.brier?.toFixed(2) ?? "—"}</strong></span>
          <span>ECE <strong>{calibration.ece?.toFixed(2) ?? "—"}</strong></span>
          <span>OOD <strong style={{ color: calibration.ood ? "var(--aura-orange)" : "#4ADE80" }}>{calibration.ood ? "FLAG" : "no"}</strong></span>
        </div>
      )}
    </div>
  );
}
