import type { Interpretation } from "@/lib/types";

interface Props {
  interpretations: Interpretation[];
  discarded: string[];
  selected: number;
  calibration?: any;
  clinicalAudit?: ClinicalAuditItem[];
}

interface ClinicalAuditItem {
  category: string;
  title: string;
  items: ClinicalAuditEntry[];
}

interface ClinicalAuditEntry {
  title: string;
  content: string;
  severity: "high" | "moderate" | "low" | "minor";
  recommendation: string;
}

export default function EnhancedDeliberationTree({
  interpretations,
  discarded,
  selected,
  calibration,
  clinicalAudit
}: Props) {
  return (
    <div className="delib" aria-label="Deliberation tree">
      <div style={{ color: "var(--aura-cyan)", marginBottom: 12 }}>{"<|think|>"}</div>

      {/* Competing Interpretations Section */}
      <div className="delib-section-header">
        <h3>Competing Interpretations</h3>
      </div>
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

      {/* Clinical Audit Section */}
      {clinicalAudit && (
        <div className="clinical-audit-section">
          <div className="delib-section-header">
            <h3>Clinical Audit Findings</h3>
          </div>
          {clinicalAudit.map((auditItem, index) => (
            <div key={index} className="clinical-audit-item">
              <div className="clinical-audit-title">{auditItem.title}</div>
              <div className="clinical-audit-content">
                {auditItem.items.map((item, itemIndex) => (
                  <div
                    key={itemIndex}
                    className={`clinical-audit-entry clinical-audit-entry--${item.severity}`}
                  >
                    <div className="clinical-audit-entry-header">{item.title}</div>
                    <div className="clinical-audit-entry-content">{item.content}</div>
                    <div className="clinical-audit-recommendation">{item.recommendation}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

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
            <span>ECE <strong>{calibration.ece?.toFixed(2) ?? "—"}</span>
            <span>OOD <strong style={{ color: calibration.ood ? "var(--aura-orange)" : "#4ADE80" }}>{calibration.ood ? "FLAG" : "no"}</strong></span>
          </div>
        </div>
      )}
    </div>
  );
}