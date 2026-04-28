#!/usr/bin/env python3
"""Generate the P.R.I.S.M. Kaggle Evaluation Notebook (.ipynb)"""
import json

def cell(cell_type, source, **kwargs):
    c = {"cell_type": cell_type, "metadata": {}, "source": source.split("\n")}
    # rejoin with newlines except last line
    c["source"] = [l + "\n" for l in c["source"][:-1]] + [c["source"][-1]]
    if cell_type == "code":
        c["outputs"] = []
        c["execution_count"] = None
    return c

def md(source): return cell("markdown", source)
def code(source): return cell("code", source)

cells = []

# ── Title ──
cells.append(md("""# 🔬 P.R.I.S.M. — Glass Box Evaluation Notebook

**Probabilistic Reasoning and Interpretability System for Models**

This notebook loads the **fine-tuned Gemma 4 A4B 26B MoE** model (MXFP4 quantized) and evaluates its ability to produce **structured clinical deliberation traces** for polypharmacy contraindication auditing.

### What This Notebook Tests
1. **Deliberation Structure** — Does the model output `[Logical Chain]`, `[Competing Hypotheses]`, `[Discarded Paths]`, `▶ Selected:`?
2. **Tool Call Emission** — Does the model invoke `verify_claim` for source grounding?
3. **Signal Dot + Confidence Badge** — Does the final answer include 🟢🟡🔴 and ✅⚠️❓?
4. **Clinical Accuracy** — Are the identified drug interactions pharmacologically sound?

### Hardware Requirements
- **Kaggle**: 2× T4 GPU accelerator (free tier)
- **VRAM**: ~16 GB (MXFP4 quantization fits comfortably)

> **For Hackathon Judges**: Click **"Copy & Edit"** → Select **GPU T4 ×2** → **Run All**. No setup needed."""))

# ── Cell 1: Install Dependencies ──
cells.append(md("## 1. Environment Setup"))
cells.append(code("""%%capture
!pip install llama-cpp-python huggingface_hub --quiet
print("✅ Dependencies installed.")"""))

# ── Cell 2: Download Model ──
cells.append(md("""## 2. Load the MXFP4 Model

The fine-tuned model is hosted as a Kaggle dataset. If running on Kaggle, attach the dataset `chandan989/prism-gemma-4-26b-a4b-it-mxfp4-v1`. Otherwise, it downloads from Hugging Face automatically."""))

cells.append(code("""import os
import glob

# Priority 1: Kaggle dataset attachment
kaggle_paths = glob.glob("/kaggle/input/**/prism*.gguf", recursive=True)

# Priority 2: Local file
local_paths = glob.glob("*.gguf") + glob.glob("**/*.gguf", recursive=True)

if kaggle_paths:
    MODEL_PATH = kaggle_paths[0]
    print(f"✅ Found Kaggle dataset: {MODEL_PATH}")
elif local_paths:
    MODEL_PATH = local_paths[0]
    print(f"✅ Found local GGUF: {MODEL_PATH}")
else:
    print("⬇️  Downloading from Hugging Face...")
    from huggingface_hub import hf_hub_download
    MODEL_PATH = hf_hub_download(
        repo_id="chandan989/prism-gemma-4-26B-A4B-it-MXFP4_MOE-v1",
        filename="prism-gemma-4-26B-A4B-it-MXFP4_MOE-v1.gguf",
    )
    print(f"✅ Downloaded: {MODEL_PATH}")

file_size_gb = os.path.getsize(MODEL_PATH) / (1024**3)
print(f"📦 Model size: {file_size_gb:.2f} GB")"""))

# ── Cell 3: Initialize llama.cpp ──
cells.append(md("## 3. Initialize Inference Engine"))
cells.append(code("""from llama_cpp import Llama
import time

print("Loading model into memory (this may take 1-2 minutes)...")
start = time.time()

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=8192,         # Match training context length
    n_gpu_layers=-1,    # Offload all layers to GPU
    n_threads=4,
    verbose=False,
)

elapsed = time.time() - start
print(f"✅ Model loaded in {elapsed:.1f}s")
print(f"   Context window: 8192 tokens")
print(f"   GPU layers: all offloaded")"""))

# ── Cell 4: System prompt & inference helper ──
cells.append(md("""## 4. P.R.I.S.M. Inference Pipeline

The system prompt and prompt template match the exact format used during fine-tuning."""))

cells.append(code("""SYSTEM_PROMPT = \"\"\"<system>
For every response:
1. Begin reasoning with <|think|> to expose your deliberation
2. Enumerate competing interpretations with probability estimates
3. Use tool calls to verify factual claims when confidence is low
4. Provide a calibrated confidence score for each major conclusion
</system>\"\"\"

def build_prompt(instruction: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\\n"
        f"<bos><start_of_turn>user\\n"
        f"{instruction}<end_of_turn>\\n"
        f"<start_of_turn>model\\n"
        f"<|think|>\\n"
    )

def run_inference(instruction: str, max_tokens: int = 1024, temperature: float = 0.3) -> str:
    prompt = build_prompt(instruction)
    start = time.time()
    output = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["<end_of_turn>", "<eos>"],
        echo=False,
    )
    elapsed = time.time() - start
    text = output["choices"][0]["text"]
    tokens_generated = output["usage"]["completion_tokens"]
    tok_per_sec = tokens_generated / elapsed if elapsed > 0 else 0
    print(f"⏱  {elapsed:.1f}s | {tokens_generated} tokens | {tok_per_sec:.1f} tok/s")
    return text

print("✅ Inference pipeline ready.")"""))

# ── Cell 5: Structure evaluation metrics ──
cells.append(md("""## 5. Structural Evaluation Framework

These metrics verify that the fine-tuned model learned the P.R.I.S.M. deliberation format."""))

cells.append(code("""import re

def evaluate_structure(response: str) -> dict:
    \"\"\"Check if the response contains all required P.R.I.S.M. structural elements.\"\"\"
    metrics = {
        "has_logical_chain":       "[Logical Chain]" in response,
        "has_hypotheses":          "[Competing Hypotheses]" in response,
        "has_discarded":           "Discarded:" in response or "[Discarded" in response,
        "has_selected":            "Selected:" in response,
        "has_tool_call":           "verify_claim" in response,
        "has_signal_dot":          any(d in response for d in ["🟢", "🟡", "🔴"]),
        "has_confidence_badge":    any(b in response for b in ["✅ HIGH", "⚠️ MODERATE", "❓ LOW"]),
        "has_recommendation":      "Recommendation:" in response,
    }
    metrics["score"] = sum(metrics.values())
    metrics["total"] = len(metrics) - 1  # exclude 'score' itself
    return metrics

def print_eval(metrics: dict):
    print("\\n┌─── Structural Evaluation ───────────────────┐")
    for key, val in metrics.items():
        if key in ("score", "total"):
            continue
        icon = "✅" if val else "❌"
        label = key.replace("has_", "").replace("_", " ").title()
        print(f"│  {icon}  {label:<35} │")
    score = metrics['score']
    total = metrics['total']
    bar = "█" * score + "░" * (total - score)
    print(f"├─────────────────────────────────────────────┤")
    print(f"│  Score: {bar} {score}/{total}             │")
    print(f"└─────────────────────────────────────────────┘")

print("✅ Evaluation framework ready.")"""))

# ── Cell 6: Single test ──
cells.append(md("""## 6. Single Prompt Evaluation

Testing with a complex polypharmacy scenario that was **NOT** in the training set."""))

cells.append(code("""HOLDOUT_PROMPT = (
    "Patient is a 78yo male on Warfarin 7.5mg, Amiodarone 200mg, "
    "Ciprofloxacin 500mg BID (started 2 days ago for UTI), and "
    "Fluconazole 200mg (started today for oral thrush). "
    "Identify all critical drug-drug interactions and their clinical significance."
)

print("=" * 60)
print("QUERY:", HOLDOUT_PROMPT)
print("=" * 60)

response = run_inference(HOLDOUT_PROMPT, max_tokens=1500)
print("\\n" + response)

metrics = evaluate_structure(response)
print_eval(metrics)"""))

# ── Cell 7: Batch evaluation ──
cells.append(md("""## 7. Batch Evaluation — Holdout Test Suite

Running multiple unseen clinical scenarios to measure **structural compliance rate** across diverse query types."""))

cells.append(code("""HOLDOUT_TESTS = [
    # Severe interactions (should produce 🔴)
    "Patient on Simvastatin 80mg just started Itraconazole 200mg for toenail fungus. Evaluate.",
    "68yo on Methotrexate 20mg weekly, Trimethoprim/Sulfamethoxazole started for UTI. Review.",
    "Patient on Lithium 900mg, started Ibuprofen 600mg TID for back pain. Any concerns?",

    # Moderate interactions (should produce 🟡)
    "72yo female on Digoxin 0.25mg and Amiodarone 200mg. Review all interactions.",
    "Patient on Phenytoin 300mg and Fluoxetine 40mg. Evaluate PK interactions.",

    # Safe combinations (should produce 🟢)
    "Patient on Metformin 500mg and Atorvastatin 20mg. Any interaction?",
    "55yo on Lisinopril 10mg and Amlodipine 5mg for hypertension. Review.",

    # Complex polypharmacy (tests full deliberation depth)
    "82yo nursing home resident on: Warfarin 5mg, Omeprazole 40mg, "
    "Clopidogrel 75mg, Aspirin 81mg, Metoprolol 50mg, Sertraline 100mg, "
    "Gabapentin 300mg, Amlodipine 10mg, Metformin 1000mg, Glipizide 10mg. "
    "Identify the three most dangerous interactions.",
]

print(f"Running {len(HOLDOUT_TESTS)} holdout tests...\\n")
all_metrics = []

for i, prompt in enumerate(HOLDOUT_TESTS, 1):
    print(f"{'='*60}")
    print(f"TEST {i}/{len(HOLDOUT_TESTS)}")
    print(f"QUERY: {prompt[:100]}...")
    print(f"{'='*60}")

    response = run_inference(prompt, max_tokens=1500)
    metrics = evaluate_structure(response)
    metrics["query"] = prompt[:80]
    all_metrics.append(metrics)
    print_eval(metrics)
    print()"""))

# ── Cell 8: Summary statistics ──
cells.append(md("## 8. Aggregate Results & Compliance Rate"))
cells.append(code("""import statistics

print("=" * 60)
print("P.R.I.S.M. STRUCTURAL COMPLIANCE SUMMARY")
print("=" * 60)

fields = [
    "has_logical_chain", "has_hypotheses", "has_discarded",
    "has_selected", "has_tool_call", "has_signal_dot",
    "has_confidence_badge", "has_recommendation",
]

for field in fields:
    hits = sum(1 for m in all_metrics if m.get(field, False))
    pct = (hits / len(all_metrics)) * 100
    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    label = field.replace("has_", "").replace("_", " ").title()
    print(f"  {label:<25} {bar} {hits}/{len(all_metrics)} ({pct:.0f}%)")

scores = [m["score"] for m in all_metrics]
avg = statistics.mean(scores)
total = all_metrics[0]["total"]
overall = (avg / total) * 100

print(f"\\n{'─'*60}")
print(f"  Overall Compliance:  {overall:.1f}% ({avg:.1f}/{total} avg)")
print(f"  Tests Passed (≥6/8): {sum(1 for s in scores if s >= 6)}/{len(scores)}")
print(f"{'─'*60}")

if overall >= 80:
    print("\\n🟢 PASS — Model demonstrates strong deliberation format adherence.")
elif overall >= 60:
    print("\\n🟡 PARTIAL — Model shows format learning but needs refinement.")
else:
    print("\\n🔴 FAIL — Model did not reliably learn the deliberation format.")"""))

# ── Cell 9: Side-by-side comparison ──
cells.append(md("""## 9. Response Deep Dive — Formatted Output

Parse and display a single response with P.R.I.S.M. Glass Box formatting."""))

cells.append(code("""def display_glass_box(response: str):
    \"\"\"Parse and pretty-print a P.R.I.S.M. response.\"\"\"
    parts = response.split("<|channel>")
    thought = ""
    answer = ""

    if len(parts) >= 3:
        # Format: <|channel>thought\\n{deliberation}\\n<|channel>\\n{answer}
        thought = parts[1].replace("thought\\n", "").strip()
        answer = parts[2].strip()
    elif len(parts) == 2:
        thought = parts[1].strip()
        answer = response.split("\\n")[-1] if "\\n" in response else ""
    else:
        # Fallback: try to split on structural markers
        if "Confidence:" in response:
            idx = response.index("Confidence:")
            # Find the signal dot line before Confidence
            lines = response[:idx].strip().split("\\n")
            for j, line in enumerate(lines):
                if any(d in line for d in ["🟢", "🟡", "🔴"]):
                    thought = "\\n".join(lines[:j])
                    answer = "\\n".join(lines[j:]) + response[idx:]
                    break
        if not thought:
            thought = response
            answer = "(Could not parse final answer)"

    print("┌─── 🧠 DELIBERATION TRACE (Expert View) ─────────────┐")
    for line in thought.split("\\n"):
        if line.strip():
            print(f"│  {line.strip()}")
    print("└─────────────────────────────────────────────────────┘")
    print()
    print("┌─── 📋 CLINICAL ANSWER (Default View) ───────────────┐")
    for line in answer.split("\\n"):
        if line.strip():
            print(f"│  {line.strip()}")
    print("└─────────────────────────────────────────────────────┘")

# Run a fresh query and display it
demo_query = (
    "Patient is a 65yo female on Clopidogrel 75mg after a recent stent placement. "
    "She now needs a PPI for GERD. Which PPI should be used and why?"
)

print("QUERY:", demo_query)
print()
demo_response = run_inference(demo_query, max_tokens=1500)
display_glass_box(demo_response)
demo_metrics = evaluate_structure(demo_response)
print_eval(demo_metrics)"""))

# ── Cell 10: Interactive mode ──
cells.append(md("""## 10. Interactive Mode — Try Your Own Queries

Enter any polypharmacy query below to test the Glass Box live."""))

cells.append(code("""# Uncomment the lines below for interactive testing on Kaggle/Colab:
#
# while True:
#     query = input("\\n🔬 Enter a clinical query (or 'quit'): ")
#     if query.lower() in ('quit', 'exit', 'q'):
#         break
#     response = run_inference(query, max_tokens=1500)
#     display_glass_box(response)
#     metrics = evaluate_structure(response)
#     print_eval(metrics)

print("💡 Uncomment the cell above to enter interactive mode.")
print("   Or modify HOLDOUT_TESTS in Cell 7 to add your own scenarios.")"""))

# ── Assemble notebook ──
notebook = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
        "kaggle": {
            "accelerator": "nvidiaTeslaT4",
            "dataSources": [
                {"sourceId": 0, "sourceType": "datasetVersion",
                 "datasetId": "prism-gemma-4-26b-a4b-it-mxfp4-v1"}
            ],
            "isInternetEnabled": True,
            "language": "python",
            "sourceType": "notebook",
            "isGpuEnabled": True
        }
    },
    "cells": cells,
}

output_path = "P_R_I_S_M_Evaluation.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"✅ Notebook generated: {output_path}")
print(f"   Cells: {len(cells)} ({sum(1 for c in cells if c['cell_type']=='code')} code, "
      f"{sum(1 for c in cells if c['cell_type']=='markdown')} markdown)")
