# The Glass Box Interpreter

### Architectural Blueprint for the Gemma 4 Good Hackathon

---

## What Is This?

The **Glass Box Interpreter** is a transparency layer for Gemma 4. It transforms the model from a black-box chatbot into a **transparent reasoning engine** where users can see:

1. **How** the AI reached its conclusion (deliberation)
2. **Whether** its claims are grounded in real sources (verification)
3. **How confident** it actually is (calibrated certainty)

It works for **any domain, any query**. Ask it about medicine, law, science, history — the Glass Box shows its work regardless.

---

## The Core Problem

Every LLM today has the same fundamental UX failure:

> The model sounds equally confident whether it's right or wrong. The user has no way to tell the difference.

| What Users Get Today | What's Missing |
| -------------------- | -------------- |
| A confident-sounding answer | The reasoning that produced it |
| Stated facts | Whether those facts are real |
| Uniform tone | How certain the model actually is |

The Glass Box fixes all three.

---

## Why Gemma 4 A4B (26B) — Not E4B

The original blueprint specified Gemma 4 E4B (4.5B effective). After evaluating the technical hurdles — latency bottlenecks from the multi-stage verification pipeline, context management fragility, and the difficulty of logprob calibration on small models — we upgraded to **Gemma 4 A4B (26B MoE)**.

### The Key Insight

A4B is a **Mixture of Experts** model: 26B total parameters but only **~4B active** during inference. This means:

- **Inference cost comparable to E4B** — the active parameter count is nearly identical
- **Knowledge capacity of a 26B model** — the full 26B parameter space stores far deeper domain knowledge
- **256K context window** (vs 128K on E4B) — critical for multi-turn deliberation with thought block history
- **Better native calibration** — larger models produce inherently more calibrated logprobs, reducing the burden on fine-tuning

### What This Fixes

| Problem with E4B | How A4B Solves It |
| --- | --- |
| **Latency:** Small model + heavy pipeline = slow | A4B reasons better → simpler pipeline → lower end-to-end latency |
| **Context stripping:** Had to delete thought blocks to prevent hallucination loops | A4B is robust enough to retain summarized thought history |
| **Calibration:** Logprobs badly uncalibrated → needed heavy Unsloth fine-tuning | A4B logprobs are naturally better calibrated → light-touch fine-tuning suffices |
| **RAG overload:** Had to verify every sentence | A4B hallucinates less → selective verification only on flagged claims |

### Hardware Requirements

| Config | VRAM | Notes |
| --- | --- | --- |
| A4B Q4 (4-bit quantized) | ~16 GB | Runs on RTX 4090, M2 Pro/Max with unified memory |
| A4B Q8 (8-bit quantized) | ~28 GB | M3 Max, dual GPU setups |
| A4B FP16 | ~52 GB | Cloud / multi-GPU only |

The MoE architecture means that despite having 26B total params, active memory during inference is dominated by the ~4B active experts — making quantized A4B surprisingly lightweight.

---

## The Three Pillars

### Pillar I: Latent Deliberation Engine

Standard interfaces hide the model's reasoning. By injecting `<|think|>` into the system prompt, the Glass Box intercepts Gemma 4's native `<|channel>thought\n` blocks and exposes:

* Competing hypotheses with probability estimates
* Discarded reasoning paths
* The step-by-step chain from question to answer

**Default behavior:** Reasoning is captured but shown only when the user clicks "Why?" — progressive disclosure, not information overload.

### Pillar II: Source Grounding Visualizer

Claims in the response are verified against a local RAG knowledge base using **selective verification** — only claims flagged as factual assertions are checked, not every sentence. We parse Gemma 4's native `<|tool_call>` and `<|"|>` delimiters to trigger background verification.

Each verified claim gets a colored dot:

| Color     | Meaning                   |
| --------- | ------------------------- |
| 🟢 Green  | Verified against source   |
| 🟡 Yellow | Reasonable inference      |
| 🔴 Red    | Unverified — possible hallucination |

**Why selective verification?** A4B hallucinates far less than E4B on factual claims. Running RAG on every sentence was the primary latency bottleneck in the original design. By verifying only extracted factual claims (dates, statistics, citations, proper nouns), we cut verification calls by ~70% while catching the claims most likely to be wrong.

### Pillar III: Certainty Indicators

Token-level logprobs are streamed from the inference engine and translated into **explicit, accessible confidence signals**:

* **Confidence badges:** ✅ HIGH · ⚠️ MODERATE · ❓ LOW
* **Progress bars:** `████████░░` (80%)
* **Plain-language labels:** "The AI is confident" / "The AI is guessing"

We removed the earlier blur/fade approach because it's an accessibility anti-pattern — unreadable in poor lighting and unusable for visually impaired users.

#### Calibration Strategy (Simplified)

With A4B, raw logprobs are **naturally better calibrated** than E4B. Our fine-tuning strategy shifts from heavy calibration training to light-touch adjustment:

1. **Temperature scaling** — A single learned scalar applied post-hoc to logits. Simple, effective, and proven
2. **Deliberation format adapter** — Small Unsloth LoRA to teach structured `<|think|>` output with enumerated hypotheses
3. **Validation** — Brier Score and ECE measured on held-out eval set to confirm calibration quality

This replaces the original plan of training a full calibration adapter + deliberation adapter with complex Brier Score minimization loss.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       P.R.I.S.M. ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FRONTEND (Next.js + Tailwind CSS)                              │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Default View:  Answer + badges + source dots        │       │
│   │  Expert View:   Deliberation tree + calibration      │       │
│   │                                                      │       │
│   │  Multiplexed Streams:                                │       │
│   │  • Text ─────────────► Response rendering            │       │
│   │  • Thought blocks ───► Deliberation panel            │       │
│   │  • Verification ─────► Source dots (🟢🟡🔴)          │       │
│   │  • Logprobs ─────────► Confidence badges/bars        │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ SSE / WebSocket                       │
│                          ▼                                       │
│   BACKEND (Python)                                               │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Streaming Server                                    │       │
│   │  ├── <|channel>thought\n parser → deliberation       │       │
│   │  ├── Claim extractor → selective RAG verification    │       │
│   │  ├── Logprobs extractor → temperature-scaled scores  │       │
│   │  └── RAG pipeline (local vector store)               │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ Local inference                       │
│                          ▼                                       │
│   INFERENCE (Cactus Compute / Ollama)                            │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Gemma 4 A4B 26B MoE (Unsloth format-tuned)         │       │
│   │  • 26B total / ~4B active — MoE efficiency           │       │
│   │  • 256K context window                               │       │
│   │  • Logprobs streaming for certainty extraction       │       │
│   │  • Runs locally — no cloud                           │       │
│   └──────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Why |
| ----- | ---------- | --- |
| Model | Gemma 4 A4B (26B MoE, ~4B active) | 256K context, multimodal, MoE efficiency — 26B knowledge with 4B inference cost |
| Fine-Tuning | Unsloth | Deliberation format adapter (QLoRA, ~16 GB VRAM, 2× faster) + temperature scaling |
| Inference | Cactus Compute / Ollama | Local execution, logprobs access, offline-capable |
| Backend | Python | Gemma 4 delimiter parsing, selective RAG verification, stream multiplexing |
| Frontend | Next.js + Tailwind | Progressive disclosure UI with real-time multi-stream rendering |

---

## Gemma 4 Integration Details

### Prompting

```
<system>
For every response:
1. Begin reasoning with <|think|> to expose your deliberation
2. Enumerate competing interpretations with probability estimates
3. Use tool calls to verify factual claims when confidence is low
4. Provide a calibrated confidence score for each major conclusion
</system>
```

### Turn Management (Revised)

The original design stripped all `<|channel>thought\n` blocks from context history between turns. This prevented cyclical hallucination loops but caused the model to "forget" its own reasoning — crippling multi-turn coherence.

**New approach with A4B:**

```python
def prepare_context(history):
    """Summarize (not strip) thought blocks from prior turns.
    
    A4B's 256K context and stronger reasoning make it robust
    enough to handle condensed versions of its prior thoughts
    without entering hallucination loops.
    """
    prepared = []
    for turn in history:
        thought_blocks = extract_thought_blocks(turn)
        if thought_blocks:
            # Keep a one-line summary of prior reasoning, not the full block
            summary = summarize_reasoning(thought_blocks)
            cleaned = strip_raw_thought_blocks(turn)
            prepared.append(f"{cleaned}\n[Prior reasoning: {summary}]")
        else:
            prepared.append(turn)
    return prepared
```

This preserves reasoning continuity across turns while keeping context lean.

### Delimiter Handling

| Delimiter | Purpose | Glass Box Handling |
| --------- | ------- | ------------------ |
| `<\|channel>thought\n` | Internal reasoning | Routed to deliberation panel |
| `<\|tool_call>` | Function call | Triggers selective RAG verification |
| `<\|"\|>` | Tool call arguments | Parsed for claim text |

---

## Fine-Tuning with Unsloth

| What | Why |
| ---- | --- |
| Deliberation format adapter | Structured `<\|think\|>` output with enumerated hypotheses and probability estimates |
| Temperature scaling layer | Post-hoc calibration of logprobs — single scalar, validated against Brier/ECE |

**Simplified from original design:** The original plan called for a full calibration adapter trained with Brier Score minimization loss. A4B's naturally better-calibrated logprobs mean a simple temperature scaling layer (trained on a small validation set) achieves comparable calibration with far less complexity.

Training efficiency with Unsloth: ~16 GB VRAM for A4B QLoRA 4-bit (vs ~48 GB without Unsloth). Rank-16 LoRA, fused kernels for 2× speedup.

---

## Getting Started

### Prerequisites

* macOS (Apple Silicon M2 Pro+ recommended) or Linux with 16GB+ VRAM GPU
* Python 3.10+
* Node.js 18+

### Setup

```bash
# Clone
git clone https://github.com/chandan989/P.R.I.S.M..git
cd P.R.I.S.M.

# Inference backend (Option A: Cactus Compute)
brew install cactus-compute/cactus/cactus
cactus download chandan989/gemma-4-a4b-calibrated
python backend/server.py --model gemma-4-a4b-calibrated --port 8000

# Inference backend (Option B: Ollama)
ollama pull gemma4:a4b
python backend/server.py --runtime ollama --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000** → ask anything → see the Glass Box in action.

---

## Demo Scenarios

The Glass Box works with any query. Here are examples that showcase the three pillars:

**Medical:** "Patient has chest pain and shortness of breath. History of DVT. What are the possible diagnoses?"
→ Shows competing hypotheses, verifies clinical claims, shows calibrated confidence per diagnosis.

**Legal:** "What are a tenant's rights if a landlord refuses to return a security deposit in California?"
→ Shows reasoning chain, verifies statutes, flags unverified claims.

**Science:** "Is there evidence that intermittent fasting improves longevity in humans?"
→ Shows evidence weighing, verifies study references, shows low confidence where data is limited.

**General:** "Why did the Roman Empire fall?"
→ Shows multiple historiographic perspectives, verifies specific claims, shows uncertainty across competing theories.

---

## Hackathon Alignment

### Main Tracks

| Track | Fit |
| ----- | --- |
| 🛡 **Safety & Trust** | Core mission — making AI transparent, verifiable, and calibrated |
| 🏥 **Health & Sciences** | Medical triage is a compelling demo scenario for the transparency layer |

### Special Technology Tracks

| Track | How We Use It |
| ----- | ------------- |
| 🌵 **Cactus** | Primary inference engine — local, offline, logprobs streaming for A4B |
| ⚡ **Unsloth** | Deliberation format fine-tuning + temperature scaling calibration |
| 🦙 **Ollama** | Alternative local runtime for development and model switching |
| 🦙 **llama.cpp** | Lightweight alternative backend (powers both Cactus and Ollama under the hood) |
| 📱 **LiteRT** | Future mobile deployment path — A4B's MoE efficiency makes this viable |

---

## Closing

The Glass Box Interpreter is not a medical app. It's not a legal app. It's a **transparency layer** that works for any domain.

The core insight: users don't need AI to be perfect — they need AI to **show its work** so they can decide for themselves.

The choice of Gemma 4 A4B over E4B is pragmatic: 26B parameters of knowledge with ~4B inference cost, better native calibration, and a 256K context window — enabling a simpler, faster, more reliable architecture that doesn't need to compensate for a small model's weaknesses with an over-engineered pipeline.
