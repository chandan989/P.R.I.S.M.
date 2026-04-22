import { useMemo, useState } from "react";
import { Send, Trash2, Plus, AlertCircle } from "lucide-react";
import StalenessWarning from "./StalenessWarning";

export interface DrugEntry {
  id: string;
  name: string;
  dose: string;
  frequency: string;
}

export interface PatientData {
  age: string;
  sex: "" | "F" | "M" | "Other";
  weightKg: string;
  egfr: string;
  conditions: string;
  allergies: string;
  drugs: DrugEntry[];
}

interface Props {
  value: PatientData;
  onChange: (next: PatientData) => void;
  onSubmit: () => void;
  busy?: boolean;
  daysSinceUpdate?: number;
  scenarios?: { label: string; onClick: () => void }[];
}

const FREQS = ["", "Once daily", "BID", "TID", "QID", "QHS", "PRN", "Weekly"];

const newDrug = (): DrugEntry => ({
  id: Math.random().toString(36).slice(2, 9),
  name: "",
  dose: "",
  frequency: "",
});

// ---------- Validation ----------
type FieldKey = "age" | "weightKg" | "egfr";
type DrugFieldKey = "name" | "dose";

interface FormErrors {
  age?: string;
  weightKg?: string;
  egfr?: string;
  drugs: Record<string, { name?: string; dose?: string }>;
  form?: string;
}

const DOSE_RE = /^\d+(\.\d+)?\s?(mcg|mg|g|ml|units?|iu|%)?$/i;

function validateNumeric(raw: string, label: string, min: number, max: number, required = false): string | undefined {
  const v = raw.trim();
  if (!v) return required ? `${label} is required` : undefined;
  const n = Number(v);
  if (!Number.isFinite(n)) return `${label} must be a number`;
  if (n < min || n > max) return `${label} must be between ${min} and ${max}`;
  return undefined;
}

export function validatePatient(p: PatientData): FormErrors {
  const errors: FormErrors = { drugs: {} };

  errors.age = validateNumeric(p.age, "Age", 0, 120);
  errors.weightKg = validateNumeric(p.weightKg, "Weight", 1, 400);
  errors.egfr = validateNumeric(p.egfr, "eGFR", 1, 200);

  let hasNamedDrug = false;
  for (const d of p.drugs) {
    const de: { name?: string; dose?: string } = {};
    const name = d.name.trim();
    if (!name && (d.dose.trim() || d.frequency)) {
      de.name = "Drug name is required";
    } else if (name) {
      hasNamedDrug = true;
      if (name.length < 2) de.name = "Use at least 2 characters";
    }
    const dose = d.dose.trim();
    if (dose && !DOSE_RE.test(dose)) {
      de.dose = "Use a number with optional unit (e.g. 5 mg)";
    }
    if (de.name || de.dose) errors.drugs[d.id] = de;
  }

  if (!hasNamedDrug) errors.form = "Add at least one drug to analyze";

  return errors;
}

export function isValid(errors: FormErrors): boolean {
  if (errors.age || errors.weightKg || errors.egfr || errors.form) return false;
  return Object.keys(errors.drugs).length === 0;
}

// ---------- Component ----------
export default function PatientRegimenForm({
  value,
  onChange,
  onSubmit,
  busy,
  daysSinceUpdate = 9,
  scenarios,
}: Props) {
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [submitted, setSubmitted] = useState(false);

  const errors = useMemo(() => validatePatient(value), [value]);
  const valid = isValid(errors);

  const show = (key: string) => submitted || touched[key];
  const markTouched = (key: string) => setTouched((t) => ({ ...t, [key]: true }));

  const set = <K extends keyof PatientData>(k: K, v: PatientData[K]) =>
    onChange({ ...value, [k]: v });

  const updateDrug = (id: string, patch: Partial<DrugEntry>) =>
    onChange({
      ...value,
      drugs: value.drugs.map((d) => (d.id === id ? { ...d, ...patch } : d)),
    });

  const removeDrug = (id: string) =>
    onChange({ ...value, drugs: value.drugs.filter((d) => d.id !== id) });

  const addDrug = () => onChange({ ...value, drugs: [...value.drugs, newDrug()] });

  const handleSubmit = () => {
    setSubmitted(true);
    if (!valid || busy) return;
    onSubmit();
  };

  const fieldErrId = (k: string) => `pf-err-${k}`;
  const errorOf = (k: FieldKey) => (show(k) ? errors[k] : undefined);
  const drugErrorOf = (id: string, k: DrugFieldKey) =>
    show(`drug-${id}-${k}`) ? errors.drugs[id]?.[k] : undefined;

  return (
    <div className="command-border">
      <div className="command-center">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
          <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.1rem" }}>
            Drug Regimen Audit
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)", color: "var(--ink-inverse-muted)" }}>
            session · {Math.random().toString(36).slice(2, 8)}
          </span>
        </div>

        {scenarios && scenarios.length > 0 && (
          <div className="cmd-row" aria-label="Demo scenarios">
            {scenarios.map((s, i) => (
              <button key={i} className="cmd-pill" onClick={s.onClick}>{s.label}</button>
            ))}
          </div>
        )}

        {/* Demographics */}
        <div className="pf-section">
          <div className="pf-section-title">Patient</div>
          <div className="pf-grid pf-grid--3">
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-age">Age</label>
              <input id="pf-age"
                className={`pf-input ${errorOf("age") ? "pf-input--error" : ""}`}
                type="number" min={0} max={120} placeholder="78"
                aria-invalid={!!errorOf("age")}
                aria-describedby={errorOf("age") ? fieldErrId("age") : undefined}
                value={value.age}
                onBlur={() => markTouched("age")}
                onChange={(e) => set("age", e.target.value)} />
              {errorOf("age") && <div id={fieldErrId("age")} className="pf-error"><AlertCircle size={12} />{errorOf("age")}</div>}
            </div>
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-sex">Sex</label>
              <select id="pf-sex" className="pf-select"
                value={value.sex}
                onChange={(e) => set("sex", e.target.value as PatientData["sex"])}>
                <option value="">—</option>
                <option value="F">Female</option>
                <option value="M">Male</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-weight">Weight (kg)</label>
              <input id="pf-weight"
                className={`pf-input ${errorOf("weightKg") ? "pf-input--error" : ""}`}
                type="number" min={0} max={400} placeholder="68"
                aria-invalid={!!errorOf("weightKg")}
                aria-describedby={errorOf("weightKg") ? fieldErrId("weightKg") : undefined}
                value={value.weightKg}
                onBlur={() => markTouched("weightKg")}
                onChange={(e) => set("weightKg", e.target.value)} />
              {errorOf("weightKg") && <div id={fieldErrId("weightKg")} className="pf-error"><AlertCircle size={12} />{errorOf("weightKg")}</div>}
            </div>
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-egfr">eGFR (mL/min)</label>
              <input id="pf-egfr"
                className={`pf-input ${errorOf("egfr") ? "pf-input--error" : ""}`}
                type="number" min={0} max={200} placeholder="52"
                aria-invalid={!!errorOf("egfr")}
                aria-describedby={errorOf("egfr") ? fieldErrId("egfr") : undefined}
                value={value.egfr}
                onBlur={() => markTouched("egfr")}
                onChange={(e) => set("egfr", e.target.value)} />
              {errorOf("egfr") && <div id={fieldErrId("egfr")} className="pf-error"><AlertCircle size={12} />{errorOf("egfr")}</div>}
            </div>
            <div className="pf-field" style={{ gridColumn: "span 2" }}>
              <label className="pf-label" htmlFor="pf-allergies">Allergies</label>
              <input id="pf-allergies" className="pf-input" type="text" maxLength={200}
                placeholder="Penicillin, sulfa…"
                value={value.allergies}
                onChange={(e) => set("allergies", e.target.value)} />
            </div>
            <div className="pf-field pf-field--full">
              <label className="pf-label" htmlFor="pf-conditions">Conditions</label>
              <input id="pf-conditions" className="pf-input" type="text" maxLength={300}
                placeholder="Atrial fibrillation, T2DM, CKD stage 3"
                value={value.conditions}
                onChange={(e) => set("conditions", e.target.value)} />
            </div>
          </div>
        </div>

        <div className="pf-divider" />

        {/* Regimen */}
        <div className="pf-section">
          <div className="pf-section-title">
            Regimen ({value.drugs.length}) <span className="pf-required">· at least one required</span>
          </div>
          <div className="pf-drug-list">
            {value.drugs.map((d, i) => {
              const nameErr = drugErrorOf(d.id, "name");
              const doseErr = drugErrorOf(d.id, "dose");
              return (
                <div key={d.id} className="pf-drug-row-wrap">
                  <div className="pf-drug-row">
                    <div className="pf-field pf-field--drug-name">
                      <input
                        className={`pf-input ${nameErr ? "pf-input--error" : ""}`}
                        type="text"
                        maxLength={120}
                        placeholder={i === 0 ? "Warfarin" : "Drug name"}
                        aria-label={`Drug ${i + 1} name`}
                        aria-invalid={!!nameErr}
                        aria-describedby={nameErr ? `pf-err-drug-${d.id}-name` : undefined}
                        value={d.name}
                        onBlur={() => markTouched(`drug-${d.id}-name`)}
                        onChange={(e) => updateDrug(d.id, { name: e.target.value })}
                      />
                    </div>
                    <input
                      className={`pf-input ${doseErr ? "pf-input--error" : ""}`}
                      type="text"
                      maxLength={40}
                      placeholder="5 mg"
                      aria-label={`Drug ${i + 1} dose`}
                      aria-invalid={!!doseErr}
                      aria-describedby={doseErr ? `pf-err-drug-${d.id}-dose` : undefined}
                      value={d.dose}
                      onBlur={() => markTouched(`drug-${d.id}-dose`)}
                      onChange={(e) => updateDrug(d.id, { dose: e.target.value })}
                    />
                    <select
                      className="pf-select"
                      aria-label={`Drug ${i + 1} frequency`}
                      value={d.frequency}
                      onChange={(e) => updateDrug(d.id, { frequency: e.target.value })}
                    >
                      {FREQS.map((f) => (
                        <option key={f} value={f}>{f || "Frequency"}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="pf-icon-btn"
                      aria-label={`Remove drug ${i + 1}`}
                      onClick={() => removeDrug(d.id)}
                      disabled={value.drugs.length <= 1}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  {(nameErr || doseErr) && (
                    <div className="pf-drug-errors">
                      {nameErr && <div id={`pf-err-drug-${d.id}-name`} className="pf-error"><AlertCircle size={12} />{nameErr}</div>}
                      {doseErr && <div id={`pf-err-drug-${d.id}-dose`} className="pf-error"><AlertCircle size={12} />{doseErr}</div>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <button type="button" className="pf-add-btn" onClick={addDrug}>
            <Plus size={14} /> Add drug
          </button>
        </div>

        {submitted && errors.form && (
          <div className="pf-form-error" role="alert">
            <AlertCircle size={14} /> {errors.form}
          </div>
        )}

        <div className="cmd-submit">
          <button
            className="btn-submit"
            onClick={handleSubmit}
            disabled={busy || !valid}
            aria-label="Analyze regimen"
            aria-disabled={busy || !valid}
            title={!valid ? "Fix the highlighted fields to continue" : "Analyze regimen"}
          >
            <Send size={16} />
          </button>
          <span className="cmd-submit-label">{busy ? "Analyzing…" : "Analyze Regimen"}</span>
        </div>

        <StalenessWarning daysSinceUpdate={daysSinceUpdate} />
      </div>
    </div>
  );
}

export function emptyPatient(): PatientData {
  return {
    age: "",
    sex: "",
    weightKg: "",
    egfr: "",
    conditions: "",
    allergies: "",
    drugs: [newDrug()],
  };
}

export function patientToQuery(p: PatientData): string {
  const demo: string[] = [];
  if (p.age) demo.push(`${p.age}${p.sex || ""}`);
  else if (p.sex) demo.push(p.sex);
  if (p.weightKg) demo.push(`${p.weightKg} kg`);
  if (p.egfr) demo.push(`eGFR ${p.egfr}`);

  const lines: string[] = [];
  lines.push(`Patient: ${demo.join(", ") || "—"}`);
  if (p.conditions.trim()) lines.push(`Conditions: ${p.conditions.trim()}`);
  if (p.allergies.trim()) lines.push(`Allergies: ${p.allergies.trim()}`);
  lines.push("Regimen:");
  for (const d of p.drugs) {
    if (!d.name.trim()) continue;
    const parts = [d.name.trim()];
    if (d.dose.trim()) parts.push(d.dose.trim());
    if (d.frequency) parts.push(d.frequency);
    lines.push(`- ${parts.join(" ")}`);
  }
  return lines.join("\n");
}
