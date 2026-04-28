# P.R.I.S.M. Deliberation Dataset Generation Prompt

**Instructions:** Copy the text below the line and paste it into Claude 3.5 Sonnet to generate a large, high-quality, syntactically perfect JSON dataset for fine-tuning the Gemma 4 A4B 26B MoE model.

---

You are an expert clinical pharmacologist and AI alignment engineer. Your task is to generate a large, high-fidelity synthetic dataset of complex polypharmacy auditing queries and their resulting AI deliberation traces. This dataset will be used to fine-tune a 26B Mixture-of-Experts (MoE) model to output highly structured, safely calibrated clinical reasoning.

I need you to generate **50 unique JSON objects** following a strict schema. The scenarios should range from common elderly polypharmacy errors (e.g., NSAIDs + ACE inhibitors + diuretics) to complex oncology/cardiology/psychiatry interactions (e.g., CYP450 inhibitors, P-glycoprotein interference, QT prolongation, Serotonin Syndrome, altered GI absorption).

Every JSON object MUST strictly adhere to the following schema and formatting rules:

### JSON Schema

```json
[
  {
    "instruction": "A realistic clinical query from a physician reviewing a patient's multi-drug regimen.",
    "thought_process": "The AI's internal deliberation trace, structured exactly as specified below.",
    "output": "The final response shown to the user, structured exactly as specified below."
  }
]
```

### Strict Formatting Rules for `thought_process`:
The `thought_process` string MUST contain the following sections, using these exact headers and markdown structures:

1. **[Logical Chain]**
   - A numbered list breaking down the pharmacology (e.g., 1. Target drugs... 2. Pharmacodynamics...).
2. **[Competing Hypotheses]**
   - At least two interpretations with assigned, realistic probability estimates (e.g., `Interpretation A: Severe risk of bleeding [92.0%]`).
   - Each interpretation must have `├── Supporting:` and `└── Weakening:` bullet points using those exact tree characters.
3. **[Discarded Paths]**
   - A discarded hypothesis with a brief clinical reason why it was rejected, formatted as `✗ Discarded: [hypothesis]. ([reason]).`
4. **▶ Selected:**
   - E.g., `▶ Selected: Interpretation A`
5. **Tool Call**
   - The very last line of the `thought_process` MUST be a tool call to verify the primary claim, formatted exactly like this: `<|tool_call>verify_claim<|"|>[Concise pharmacological claim to verify]<|"|>`

### Strict Formatting Rules for `output`:
The `output` string MUST be formatted exactly like this:
1. **Signal Dot & Claim:** Begin with a colored dot (🟢, 🟡, or 🔴) followed by the verified clinical claim. 
   - 🔴 = Severe/Contraindicated
   - 🟡 = Moderate/Monitor
   - 🟢 = Safe/Expected
2. **Confidence Badge:** A blank line, then `Confidence: ` followed by `✅ HIGH`, `⚠️ MODERATE`, or `❓ LOW`.
3. **Recommendation:** A blank line, then `Recommendation: ` followed by actionable clinical advice (e.g., dose adjustment, alternative drug, monitoring parameters).

### Example Data Object (Use this exact syntax/tone):

```json
{
  "instruction": "Patient is a 72yo female on Metformin 1000mg and Prednisone 10mg. Identify interactions.",
  "thought_process": "[Logical Chain]\n1. Target drugs: Metformin (Biguanide) and Prednisone (Corticosteroid).\n2. Pharmacodynamics: Prednisone induces gluconeogenesis and insulin resistance.\n\n[Competing Hypotheses]\nInterpretation A: Prednisone antagonizes Metformin's effect [88.5%]\n├── Supporting: Classic glucocorticoid-induced hyperglycemia.\n└── Weakening: 10mg is a relatively low dose.\n\nInterpretation B: No significant clinical interaction [11.5%]\n├── Supporting: Stable baseline HbA1c.\n└── Weakening: Elderly patient profile.\n\n[Discarded Paths]\n✗ Discarded: Metformin toxicity increased by Prednisone. (No pharmacokinetic overlap).\n\n▶ Selected: Interpretation A\n<|tool_call>verify_claim<|\"|>Prednisone induces hyperglycemia and antagonizes Metformin<|\"|>",
  "output": "🔴 Prednisone (corticosteroid) can cause hyperglycemia, which antagonizes the glucose-lowering effects of Metformin.\n\nConfidence: ✅ HIGH\n\nRecommendation: Monitor blood glucose levels closely; Metformin dosage may need adjustment or temporary insulin therapy."
}
```

Generate 50 diverse, clinically accurate examples now. Return ONLY the raw JSON array. Do not include markdown code blocks (```json) around the output, just the raw array starting with `[` and ending with `]`.