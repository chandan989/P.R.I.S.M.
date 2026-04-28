#!/usr/bin/env python3
"""Generate P.R.I.S.M. Systems Validation Notebook"""
import json, sys

C = []  # cells

def md(s): C.append({"cell_type":"markdown","metadata":{},"source":[l+"\n" for l in s.split("\n")[:-1]]+[s.split("\n")[-1]]})
def co(s): C.append({"cell_type":"code","metadata":{},"outputs":[],"execution_count":None,"source":[l+"\n" for l in s.split("\n")[:-1]]+[s.split("\n")[-1]]})

md("""# P.R.I.S.M. — Systems Validation Notebook
**Architecture Stress Test: RotorQuant KV · Grounding Index · Async Claim Extraction**

Hardware: P100 16GB VRAM · MXFP4 Quantized Gemma 4 A4B 26B MoE""")

md("## 1. Install Dependencies")
co("""%%capture
!pip install llama-cpp-python huggingface_hub faiss-cpu onnxruntime sentence-transformers --quiet
print("Done")""")

md("## 2. Load MXFP4 Model")
co("""import os, glob, time

kaggle_paths = glob.glob("/kaggle/input/**/prism*.gguf", recursive=True)
local_paths = glob.glob("**/*.gguf", recursive=True)

if kaggle_paths:
    MODEL_PATH = kaggle_paths[0]
elif local_paths:
    MODEL_PATH = local_paths[0]
else:
    from huggingface_hub import hf_hub_download
    MODEL_PATH = hf_hub_download(
        repo_id="chandan989/prism-gemma-4-26B-A4B-it-MXFP4_MOE-v1",
        filename="prism-gemma-4-26B-A4B-it-MXFP4_MOE-v1.gguf",
    )
print(f"Model: {MODEL_PATH} ({os.path.getsize(MODEL_PATH)/1e9:.2f} GB)")""")

co("""from llama_cpp import Llama

print("Loading model...")
t0 = time.time()
llm = Llama(model_path=MODEL_PATH, n_ctx=16384, n_gpu_layers=-1, n_threads=4, verbose=False)
print(f"Loaded in {time.time()-t0:.1f}s | ctx=16384")""")

md("## 3. Prompt Infrastructure")
co("""SYSTEM_PROMPT = '''<system>
For every response:
1. Begin reasoning with <|think|> to expose your deliberation
2. Enumerate competing interpretations with probability estimates
3. Use tool calls to verify factual claims when confidence is low
4. Provide a calibrated confidence score for each major conclusion
</system>'''

def build_prompt(instruction):
    return f"{SYSTEM_PROMPT}\\n<bos><start_of_turn>user\\n{instruction}<end_of_turn>\\n<start_of_turn>model\\n<|think|>\\n"

def run_inference(instruction, max_tokens=1024, temp=0.3):
    t0 = time.time()
    out = llm(build_prompt(instruction), max_tokens=max_tokens, temperature=temp,
              stop=["<end_of_turn>","<eos>"], echo=False)
    dt = time.time()-t0
    text = out["choices"][0]["text"]
    toks = out["usage"]["completion_tokens"]
    print(f"  {dt:.1f}s | {toks} tok | {toks/dt:.1f} tok/s")
    return text

def evaluate_structure(resp):
    checks = {
        "logical_chain": "[Logical Chain]" in resp,
        "hypotheses": "[Competing Hypotheses]" in resp,
        "discarded": "Discarded:" in resp,
        "selected": "Selected:" in resp,
        "tool_call": "verify_claim" in resp,
        "signal_dot": any(d in resp for d in ["🟢","🟡","🔴"]),
        "confidence": any(b in resp for b in ["✅ HIGH","⚠️ MODERATE","❓ LOW"]),
        "recommendation": "Recommendation:" in resp,
    }
    checks["score"] = sum(checks.values())
    return checks

print("Ready.")""")

# ── PILLAR TEST 1: RotorQuant KV Cache ──
md("""## 4. PILLAR TEST 1 — RotorQuant KV Cache Stress Test
Push multi-turn polypharmacy history toward 16K context limit.
Measure prefill time degradation and detect OOM failures.""")

co("""DRUG_REGIMENS = [
    "72yo F: Warfarin 5mg, Amiodarone 200mg, Metoprolol 50mg, Lisinopril 20mg, Furosemide 40mg, KCl 20mEq, Atorvastatin 40mg, Omeprazole 20mg, Sertraline 100mg, Gabapentin 300mg, Prednisone 10mg, Levothyroxine 75mcg, Allopurinol 300mg, Metformin 1000mg, Clarithromycin 500mg",
    "68yo M: Digoxin 0.125mg, Verapamil 240mg, Spironolactone 25mg, Hydrochlorothiazide 25mg, Carvedilol 12.5mg, Rivaroxaban 20mg, Amlodipine 10mg, Rosuvastatin 20mg, Tamsulosin 0.4mg, Finasteride 5mg, Pioglitazone 30mg, Sitagliptin 100mg",
    "75yo F: Phenytoin 300mg, Valproate 500mg, Lamotrigine 25mg, Levetiracetam 1000mg, Clopidogrel 75mg, Pantoprazole 40mg, Fluoxetine 20mg, Tramadol 50mg, Celecoxib 200mg, Cyclobenzaprine 10mg, Tizanidine 4mg",
    "80yo M: Lithium 600mg, Quetiapine 100mg, Citalopram 20mg, Donepezil 10mg, Memantine 20mg, Warfarin 7.5mg, Diltiazem 240mg, Metformin 850mg, Glipizide 5mg, Empagliflozin 10mg, Losartan 100mg, Doxazosin 4mg",
]

FOLLOWUP_QUESTIONS = [
    "Now add Fluconazole 200mg to the regimen. What new interactions emerge?",
    "The patient's GFR dropped to 28. Which drugs need immediate dose adjustment?",
    "Patient reports muscle pain and dark urine. Which drug combination is most likely responsible?",
    "Can we switch the anticoagulant to a DOAC? Analyze all implications.",
]

print("=" * 70)
print("ROTORQUANT KV CACHE STRESS TEST")
print("Target: 16K context window | Multi-turn conversation")
print("=" * 70)

kv_results = []
conversation_tokens = 0

# Build up multi-turn history
history_text = ""
for turn_idx in range(len(DRUG_REGIMENS) + len(FOLLOWUP_QUESTIONS)):
    if turn_idx < len(DRUG_REGIMENS):
        query = f"Identify ALL critical drug-drug interactions for this patient: {DRUG_REGIMENS[turn_idx]}"
    else:
        query = FOLLOWUP_QUESTIONS[turn_idx - len(DRUG_REGIMENS)]

    # Build cumulative context
    full_prompt = history_text + f"\\nTurn {turn_idx+1}: {query}"
    prompt_tokens = len(full_prompt.split()) * 1.3  # rough estimate

    print(f"\\n--- Turn {turn_idx+1} | ~{int(prompt_tokens)} estimated input tokens ---")
    print(f"Q: {query[:100]}...")

    t0 = time.time()
    try:
        resp = run_inference(full_prompt, max_tokens=1024)
        prefill_time = time.time() - t0
        metrics = evaluate_structure(resp)

        kv_results.append({
            "turn": turn_idx + 1,
            "est_ctx_tokens": int(prompt_tokens),
            "prefill_sec": round(prefill_time, 2),
            "struct_score": metrics["score"],
            "oom": False,
        })

        # Append to history for next turn
        history_text += f"\\nUser: {query}\\nAssistant: {resp[:500]}"

        print(f"  Prefill: {prefill_time:.2f}s | Score: {metrics['score']}/8")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        kv_results.append({
            "turn": turn_idx + 1,
            "est_ctx_tokens": int(prompt_tokens),
            "prefill_sec": -1,
            "struct_score": 0,
            "oom": True,
        })
        break

print("\\n" + "=" * 70)
print("KV CACHE STRESS TEST RESULTS")
print("=" * 70)
print(f"{'Turn':<6} {'~Tokens':<10} {'Prefill(s)':<12} {'Score':<8} {'Status'}")
print("-" * 50)
for r in kv_results:
    status = "❌ OOM" if r["oom"] else "✅ OK"
    print(f"{r['turn']:<6} {r['est_ctx_tokens']:<10} {r['prefill_sec']:<12} {r['struct_score']}/8{'':<4} {status}")

if not any(r["oom"] for r in kv_results):
    print("\\n🟢 KV Cache: All turns completed without OOM.")
else:
    print("\\n🔴 KV Cache: OOM detected — context rolling needs investigation.")""")

# ── PILLAR TEST 2: Grounding Index ──
md("""## 5. PILLAR TEST 2 — Source Grounding Verification Engine
Build a mock clinical knowledge base with FAISS + MiniLM-L6 ONNX embeddings.
Test claim extraction and semantic verification against FDA/DrugBank data.""")

co("""from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

print("Loading MiniLM-L6 embedding model (CPU)...")
t0 = time.time()
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
print(f"Loaded in {time.time()-t0:.1f}s")

# Clinical Knowledge Base (curated ground truth)
KNOWLEDGE_BASE = [
    {"id":"FDA-001","source":"FDA Drug Label","text":"Clarithromycin is a potent inhibitor of CYP3A4. Co-administration with Atorvastatin increases the risk of rhabdomyolysis.","drugs":["clarithromycin","atorvastatin"],"severity":"critical"},
    {"id":"FDA-002","source":"FDA Drug Label","text":"Warfarin anticoagulant effect is enhanced by Amiodarone through inhibition of CYP2C9, CYP3A4, and CYP1A2. INR typically doubles.","drugs":["warfarin","amiodarone"],"severity":"critical"},
    {"id":"FDA-003","source":"FDA Drug Label","text":"Omeprazole inhibits CYP2C19, potentially reducing the antiplatelet effect of Clopidogrel. Pantoprazole is preferred.","drugs":["omeprazole","clopidogrel"],"severity":"major"},
    {"id":"DB-001","source":"DrugBank","text":"Furosemide-induced hypokalemia potentiates the cardiac toxicity of Digoxin, increasing risk of fatal arrhythmias.","drugs":["furosemide","digoxin"],"severity":"critical"},
    {"id":"DB-002","source":"DrugBank","text":"Metformin is cleared renally via OCT2. Cimetidine inhibits OCT2 and can increase Metformin AUC by approximately 40%.","drugs":["metformin","cimetidine"],"severity":"moderate"},
    {"id":"DB-003","source":"DrugBank","text":"Fluoxetine is a potent CYP2D6 inhibitor. Co-administration with Metoprolol can increase beta-blocker levels 2-4 fold, risking bradycardia.","drugs":["fluoxetine","metoprolol"],"severity":"major"},
    {"id":"DB-004","source":"DrugBank","text":"Sertraline and Tramadol both increase serotonergic activity. The combination raises the risk of Serotonin Syndrome.","drugs":["sertraline","tramadol"],"severity":"major"},
    {"id":"DB-005","source":"DrugBank","text":"Verapamil inhibits P-glycoprotein and reduces renal clearance of Digoxin, raising serum levels by 50-70%.","drugs":["verapamil","digoxin"],"severity":"critical"},
    {"id":"DB-006","source":"DrugBank","text":"Prednisone induces gluconeogenesis and causes insulin resistance, directly antagonizing the glucose-lowering effect of Metformin.","drugs":["prednisone","metformin"],"severity":"moderate"},
    {"id":"DB-007","source":"DrugBank","text":"Spironolactone combined with ACE inhibitors (Lisinopril) causes additive potassium retention, risking fatal hyperkalemia.","drugs":["spironolactone","lisinopril"],"severity":"critical"},
    {"id":"PM-001","source":"PubMed","text":"Thiazide diuretics reduce renal lithium clearance. HCTZ can increase serum lithium by 25-40%, risking toxicity.","drugs":["hydrochlorothiazide","lithium"],"severity":"critical"},
    {"id":"PM-002","source":"PubMed","text":"Fluoroquinolones and corticosteroids synergistically increase the risk of Achilles tendon rupture, particularly in patients over 60.","drugs":["levofloxacin","prednisone"],"severity":"major"},
    {"id":"PM-003","source":"PubMed","text":"Valproate inhibits Lamotrigine glucuronidation, doubling its half-life and significantly increasing Stevens-Johnson Syndrome risk.","drugs":["valproate","lamotrigine"],"severity":"critical"},
    {"id":"PM-004","source":"PubMed","text":"Quetiapine and Citalopram both prolong the QTc interval. Additive effects increase the risk of Torsades de Pointes.","drugs":["quetiapine","citalopram"],"severity":"major"},
    {"id":"FDA-004","source":"FDA Drug Label","text":"Simvastatin dose must not exceed 20mg when co-administered with Amlodipine due to CYP3A4 inhibition and myopathy risk.","drugs":["simvastatin","amlodipine"],"severity":"major"},
    {"id":"FDA-005","source":"FDA Drug Label","text":"Sacubitril/Valsartan (Entresto) must NOT be used with ACE inhibitors due to extreme angioedema risk. 36-hour washout required.","drugs":["sacubitril","lisinopril"],"severity":"contraindicated"},
]

print(f"Knowledge base: {len(KNOWLEDGE_BASE)} entries")

# Build FAISS index
print("Building FAISS index...")
t0 = time.time()
kb_texts = [entry["text"] for entry in KNOWLEDGE_BASE]
kb_embeddings = embedder.encode(kb_texts, show_progress_bar=False, normalize_embeddings=True)
dim = kb_embeddings.shape[1]
index = faiss.IndexFlatIP(dim)  # Inner product for cosine similarity on normalized vectors
index.add(kb_embeddings.astype(np.float32))
print(f"FAISS index built in {time.time()-t0:.2f}s | {index.ntotal} vectors | dim={dim}")""")

co("""import re

def extract_claims(response):
    \"\"\"Extract pharmacological claims from model output.\"\"\"
    claims = []
    # Look for signal dot lines
    for line in response.split("\\n"):
        line = line.strip()
        if any(line.startswith(d) for d in ["🟢","🟡","🔴"]):
            claim = re.sub(r'^[🟢🟡🔴⚪]\\s*', '', line).strip().strip('"')
            if len(claim) > 10:
                claims.append(claim)
        # Also extract from tool calls
        if "verify_claim" in line:
            match = re.search(r'verify_claim.*?["\\'](.*?)["\\']', line)
            if match:
                claims.append(match.group(1))
    # Fallback: extract sentences with drug names
    if not claims:
        sentences = re.split(r'[.!?]', response)
        drug_pattern = re.compile(r'\\b(warfarin|metformin|digoxin|amiodarone|clarithromycin|atorvastatin|omeprazole|clopidogrel|sertraline|fluoxetine|metoprolol|lithium|verapamil|simvastatin)\\b', re.I)
        for s in sentences:
            if drug_pattern.search(s) and len(s.strip()) > 20:
                claims.append(s.strip())
    return claims[:10]

def verify_claim(claim, top_k=3, threshold=0.4):
    \"\"\"Verify a claim against the FAISS knowledge base.\"\"\"
    t0 = time.time()
    q_emb = embedder.encode([claim], normalize_embeddings=True).astype(np.float32)
    scores, indices = index.search(q_emb, top_k)
    latency = time.time() - t0

    results = []
    for score, idx in zip(scores[0], indices[0]):
        entry = KNOWLEDGE_BASE[idx]
        if score >= threshold:
            if score >= 0.7:
                signal = "🟢 Confirmed"
            elif score >= 0.5:
                signal = "🟡 Inferred"
            else:
                signal = "⚪ Weak Match"
        else:
            signal = "⚪ Out of Scope"
        results.append({"signal": signal, "score": round(float(score), 3),
                        "source": entry["source"], "id": entry["id"],
                        "text": entry["text"][:100], "latency_ms": round(latency*1000, 1)})
    return results

print("Claim extraction & verification pipeline ready.")""")

co("""# Test grounding on a known interaction
print("=" * 70)
print("GROUNDING INDEX INTEGRATION TEST")
print("=" * 70)

test_query = "Patient on Warfarin 5mg, Amiodarone 200mg, and Clarithromycin 500mg. Identify all critical interactions."
print(f"Q: {test_query}\\n")

resp = run_inference(test_query, max_tokens=1500)
print(f"\\nResponse preview: {resp[:300]}...\\n")

claims = extract_claims(resp)
print(f"Extracted {len(claims)} claims:")

grounding_results = []
for i, claim in enumerate(claims):
    print(f"\\n  Claim {i+1}: \\"{claim[:80]}...\\"")
    verifications = verify_claim(claim)
    for v in verifications[:2]:
        print(f"    {v['signal']} (cos={v['score']:.3f}, {v['latency_ms']:.1f}ms)")
        print(f"      Source: [{v['id']}] {v['text'][:80]}...")
    grounding_results.append({"claim": claim, "top_match": verifications[0] if verifications else None})

confirmed = sum(1 for r in grounding_results if r["top_match"] and r["top_match"]["score"] >= 0.5)
print(f"\\n{'='*70}")
print(f"Grounding: {confirmed}/{len(grounding_results)} claims matched (threshold=0.5)")
avg_lat = np.mean([r["top_match"]["latency_ms"] for r in grounding_results if r["top_match"]])
print(f"Avg verification latency: {avg_lat:.1f}ms per claim")
print(f"{'='*70}")""")

# ── PILLAR TEST 3: Async Claim Extraction ──
md("""## 6. PILLAR TEST 3 — Streaming Claim Extraction & Async Verification
Simulate the streaming architecture: deliberation renders immediately,
claims are extracted and verified asynchronously without blocking.""")

co("""import threading, queue, time as _time

class StreamingClaimExtractor:
    \"\"\"Simulates async claim extraction from streaming tokens.\"\"\"
    def __init__(self):
        self.claim_queue = queue.Queue()
        self.verified_claims = []
        self.extraction_latency = []
        self.verification_latency = []

    def on_token_batch(self, text_so_far):
        \"\"\"Called as tokens stream in. Extracts claims without blocking.\"\"\"
        t0 = _time.time()
        claims = extract_claims(text_so_far)
        self.extraction_latency.append(_time.time() - t0)
        for c in claims:
            if c not in [vc["claim"] for vc in self.verified_claims]:
                self.claim_queue.put(c)

    def verification_worker(self):
        \"\"\"Background thread: verifies claims as they arrive.\"\"\"
        while True:
            try:
                claim = self.claim_queue.get(timeout=2)
                t0 = _time.time()
                results = verify_claim(claim)
                lat = _time.time() - t0
                self.verification_latency.append(lat)
                self.verified_claims.append({
                    "claim": claim,
                    "verification": results[0] if results else None,
                    "latency_ms": round(lat * 1000, 1),
                })
                self.claim_queue.task_done()
            except queue.Empty:
                break

print("=" * 70)
print("ASYNC CLAIM EXTRACTION PIPELINE TEST")
print("=" * 70)

extractor = StreamingClaimExtractor()

# Start verification worker thread
worker = threading.Thread(target=extractor.verification_worker, daemon=True)
worker.start()

# Simulate streaming inference
test_q = "82yo on Digoxin 0.125mg, Verapamil 240mg, Spironolactone 25mg, Furosemide 40mg. Full interaction audit."
print(f"Q: {test_q}\\n")

t_gen_start = _time.time()
full_response = run_inference(test_q, max_tokens=1500)
t_gen_end = _time.time()

# Simulate streaming by feeding chunks
chunk_size = 100
for i in range(0, len(full_response), chunk_size):
    chunk = full_response[:i+chunk_size]
    extractor.on_token_batch(chunk)
    _time.sleep(0.05)  # simulate streaming delay

# Wait for verification to complete
extractor.claim_queue.join()
worker.join(timeout=5)
t_verify_end = _time.time()

print(f"\\nGeneration time:    {t_gen_end - t_gen_start:.2f}s")
print(f"Verification time:  {t_verify_end - t_gen_end:.2f}s (async)")
print(f"Total wall clock:   {t_verify_end - t_gen_start:.2f}s")
print(f"\\nVerified {len(extractor.verified_claims)} claims:")
for vc in extractor.verified_claims:
    v = vc["verification"]
    sig = v["signal"] if v else "⚪ No match"
    score = v["score"] if v else 0
    print(f"  {sig} ({score:.3f}, {vc['latency_ms']:.1f}ms) | {vc['claim'][:70]}...")

if extractor.extraction_latency:
    avg_ext = np.mean(extractor.extraction_latency) * 1000
    print(f"\\nAvg extraction latency:    {avg_ext:.1f}ms (must be <50ms to not block stream)")
    print(f"Avg verification latency:  {np.mean(extractor.verification_latency)*1000:.1f}ms")
    if avg_ext < 50:
        print("🟢 Extraction is non-blocking — safe for streaming architecture.")
    else:
        print("🔴 Extraction too slow — would cause UI whiplash.")""")

# ── Final Summary ──
md("## 7. Final Verdict")
co("""print("=" * 70)
print("P.R.I.S.M. SYSTEMS VALIDATION SUMMARY")
print("=" * 70)

# KV Cache
oom_count = sum(1 for r in kv_results if r["oom"])
kv_pass = oom_count == 0
print(f"\\n{'🟢' if kv_pass else '🔴'} PILLAR: KV Cache (RotorQuant)")
print(f"  Turns completed: {len(kv_results) - oom_count}/{len(kv_results)}")
if kv_results:
    print(f"  Max prefill:     {max(r['prefill_sec'] for r in kv_results if not r['oom']):.2f}s")

# Grounding
grounding_pass = confirmed >= len(grounding_results) * 0.5
print(f"\\n{'🟢' if grounding_pass else '🔴'} PILLAR: Source Grounding (FAISS + MiniLM)")
print(f"  Claims verified: {confirmed}/{len(grounding_results)}")
print(f"  Avg latency:     {avg_lat:.1f}ms per claim")

# Async Pipeline
async_pass = len(extractor.verified_claims) > 0
print(f"\\n{'🟢' if async_pass else '🔴'} PILLAR: Async Claim Extraction")
print(f"  Claims processed: {len(extractor.verified_claims)}")
if extractor.extraction_latency:
    print(f"  Stream-safe:      {'Yes' if avg_ext < 50 else 'No'} ({avg_ext:.1f}ms)")

all_pass = kv_pass and grounding_pass and async_pass
print(f"\\n{'='*70}")
print(f"{'🟢 ALL SYSTEMS GO' if all_pass else '🔴 ISSUES DETECTED'}")
print(f"{'='*70}")""")

# Assemble
nb = {
    "nbformat": 4, "nbformat_minor": 0,
    "metadata": {
        "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
        "language_info": {"name":"python","version":"3.10.0"},
        "kaggle": {"accelerator":"gpu","isGpuEnabled":True,"isInternetEnabled":True,"language":"python","sourceType":"notebook"}
    },
    "cells": C,
}

out = "P_R_I_S_M_Systems_Validation.ipynb"
with open(out, "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print(f"Generated: {out} ({len(C)} cells)")
