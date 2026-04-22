import type { AuditResult } from "./types";

export const polypharmacyMock: AuditResult = {
  answer:
    "Clarithromycin is a potent CYP3A4 inhibitor.[SOURCED:green] Co-administration with Atorvastatin dramatically increases rhabdomyolysis risk and is generally contraindicated.[SOURCED:red] Warfarin INR may be altered by Omeprazole through shared CYP2C19 metabolism, requiring closer monitoring.[SOURCED:yellow] Long-term outcome data for this specific 15-drug combination is limited and should be interpreted with caution.[SOURCED:grey]",
  sources: [
    {
      signal: "green",
      source: "FDA Drug Label — Clarithromycin (Biaxin)",
      snippet:
        "Clarithromycin is a strong inhibitor of CYP3A4. Concomitant use with substrates metabolized by CYP3A4 may result in increased plasma concentrations.",
    },
    {
      signal: "red",
      source: "DrugBank DB00641 — Atorvastatin interaction profile",
      snippet:
        "Concurrent use of strong CYP3A4 inhibitors (e.g., clarithromycin) with atorvastatin substantially elevates plasma statin levels and the risk of rhabdomyolysis. Combination is contraindicated.",
    },
    {
      signal: "yellow",
      source: "Inferred from CYP2C19 pathway map — Lexicomp",
      snippet:
        "Omeprazole inhibits CYP2C19, which contributes to S-warfarin metabolism. INR elevations have been reported, though magnitude varies. Closer monitoring recommended.",
    },
    {
      signal: "grey",
      source: "No high-quality evidence indexed",
      snippet:
        "No long-term RCTs or registry data were found indexed for this exact 15-drug combination at the time of audit.",
    },
  ],
  interpretations: [
    {
      label: "Interpretation A: Clinically significant CYP3A4-mediated interaction stack",
      probability: 72.3,
      supporting: [
        "Clarithromycin labeled as strong CYP3A4 inhibitor (FDA)",
        "Atorvastatin is CYP3A4 substrate with known rhabdomyolysis risk",
        "Multiple case reports in DrugBank corroborate severity",
      ],
      weakening: ["Patient renal/hepatic function not provided"],
    },
    {
      label: "Interpretation B: Interaction present but clinically manageable with monitoring",
      probability: 21.8,
      supporting: ["Some guidelines permit short-course clarithromycin with statin hold"],
      weakening: [
        "Regimen length not specified",
        "Other CYP3A4 substrates also present in regimen",
      ],
    },
  ],
  discarded: ["Interpretation C: No meaningful interaction (insufficient evidence to retain)"],
  selected: 0,
  confidence: {
    level: "HIGH",
    score: 82,
    brier: 0.11,
    ece: 0.04,
    ood: false,
  },
  daysSinceUpdate: 9,
};

export const cyp450Mock: AuditResult = {
  answer:
    "The patient's regimen exhibits competing CYP3A4 substrate load.[SOURCED:green] Fluconazole moderately inhibits CYP2C9 affecting Warfarin clearance.[SOURCED:yellow] Inducer/inhibitor balance suggests dose adjustment may be required.[SOURCED:grey]",
  sources: [
    { signal: "green", source: "Lexicomp CYP3A4 substrate registry", snippet: "Multiple substrates competing for CYP3A4 hepatic metabolism." },
    { signal: "yellow", source: "DrugBank — Fluconazole", snippet: "Moderate CYP2C9 inhibitor, increases warfarin AUC ~40%." },
    { signal: "grey", source: "No combined PK study indexed", snippet: "No PK study covering this exact triple combination found." },
  ],
  interpretations: [
    { label: "Interpretation A: Net inhibition dominates", probability: 64, supporting: ["Two strong inhibitors present"], weakening: ["No inducer present"] },
    { label: "Interpretation B: Clinically negligible at low doses", probability: 28, supporting: ["Doses below typical interaction threshold"], weakening: ["Patient age not specified"] },
  ],
  discarded: [],
  selected: 0,
  confidence: { level: "MODERATE", score: 64, brier: 0.18, ece: 0.07, ood: false },
  daysSinceUpdate: 9,
};

export const glp1Mock: AuditResult = {
  answer:
    "Limited published evidence directly addresses GLP-1 agonist + Warfarin interaction.[SOURCED:grey] Delayed gastric emptying may alter Warfarin absorption kinetics.[SOURCED:yellow] No clinically significant INR shift documented in current pharmacovigilance data.[SOURCED:green]",
  sources: [
    { signal: "grey", source: "PubMed — search returned no RCTs", snippet: "Only case reports and small observational series indexed." },
    { signal: "yellow", source: "Inferred from semaglutide PK profile", snippet: "Semaglutide delays gastric emptying ~12-15%, may shift Tmax of co-administered drugs." },
    { signal: "green", source: "FDA FAERS pharmacovigilance summary", snippet: "No signal of clinically significant INR change reported in FAERS." },
  ],
  interpretations: [
    { label: "Interpretation A: Pharmacokinetic shift without clinical effect", probability: 58, supporting: ["FAERS lacks signal", "Effect size small in PK studies"], weakening: ["Limited long-term data"] },
    { label: "Interpretation B: Possible underreporting; monitor INR", probability: 34, supporting: ["Mechanistic plausibility"], weakening: ["No outcome data"] },
  ],
  discarded: ["Interpretation C: Major interaction (insufficient support)"],
  selected: 0,
  confidence: { level: "LOW", score: 41, brier: 0.27, ece: 0.12, ood: true },
  daysSinceUpdate: 9,
};

export const demoQueries = {
  polypharmacy: `Patient: 78F, eGFR 52
Regimen:
- Warfarin 5mg daily
- Clarithromycin 500mg BID (new, 7-day course)
- Atorvastatin 40mg daily
- Metformin 1000mg BID
- Omeprazole 20mg daily
- Lisinopril 10mg daily
- Amlodipine 5mg daily
- Metoprolol 50mg BID
- Furosemide 40mg daily
- Levothyroxine 75mcg daily
- Sertraline 50mg daily
- Tramadol 50mg PRN
- Aspirin 81mg daily
- Vitamin D3 2000 IU daily
- Calcium carbonate 500mg BID

Audit for clinically significant interactions.`,
  cyp450: `Patient on:
- Warfarin 5mg
- Fluconazole 200mg
- Amiodarone 200mg

Analyze CYP450 metabolic competition and predicted INR impact.`,
  glp1: `Patient on Warfarin 5mg daily, considering initiation of Semaglutide 0.5mg weekly for T2DM.
What does emerging evidence suggest about pharmacokinetic interaction?`,
};

export function pickMockForQuery(q: string): AuditResult {
  const s = q.toLowerCase();
  if (s.includes("semaglutide") || s.includes("glp-1") || s.includes("glp1")) return glp1Mock;
  if (s.includes("fluconazole") || s.includes("cyp")) return cyp450Mock;
  return polypharmacyMock;
}
