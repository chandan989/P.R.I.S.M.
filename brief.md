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

## The Three Pillars

### Pillar I: Latent Deliberation Engine

Standard interfaces hide the model's reasoning. By injecting `<|think|>` into the system prompt, the Glass Box intercepts Gemma 4's native `<|channel>thought\n` blocks and exposes:

* Competing hypotheses with probability estimates
* Discarded reasoning paths
* The step-by-step chain from question to answer

**Default behavior:** Reasoning is captured but shown only when the user clicks "Why?" — progressive disclosure, not information overload.

### Pillar II: Source Grounding Visualizer

Every claim in the response is automatically verified against a local RAG knowledge base. We parse Gemma 4's native `<|tool_call>` and `<|"|>` delimiters to trigger background verification.

Each claim gets a colored dot:

| Color     | Meaning                   |
| --------- | ------------------------- |
| 🟢 Green  | Verified against source   |
| 🟡 Yellow | Reasonable inference      |
| 🔴 Red    | Unverified — possible hallucination |

### Pillar III: Certainty Indicators

Token-level logprobs are streamed from the inference engine and translated into **explicit, accessible confidence signals**:

* **Confidence badges:** ✅ HIGH · ⚠️ MODERATE · ❓ LOW
* **Progress bars:** `████████░░` (80%)
* **Plain-language labels:** "The AI is confident" / "The AI is guessing"

We removed the earlier blur/fade approach because it's an accessibility anti-pattern — unreadable in poor lighting and unusable for visually impaired users.

Confidence is calibrated via Unsloth fine-tuning using Brier Score minimization and Expected Calibration Error (ECE).

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  FRONTEND (Next.js + Tailwind CSS)                   │
│  • Text response                                     │
│  • Deliberation panel (expandable)                   │
│  • Source dots (🟢🟡🔴)                               │
│  • Confidence badges + bars                          │
├──────────────────────────────────────────────────────┤
│  BACKEND (Python streaming server)                   │
│  • Parses <|channel>thought\n blocks                 │
│  • Parses <|tool_call> / <|"|> for verification      │
│  • Extracts logprobs → confidence scores             │
│  • Runs RAG verification pipeline                    │
├──────────────────────────────────────────────────────┤
│  INFERENCE (Cactus Compute / Ollama)                 │
│  • Gemma 4 E4B (Unsloth fine-tuned)                  │
│  • Runs locally on your machine                      │
│  • Logprobs streaming                                │
│  • Fully offline-capable                             │
└──────────────────────────────────────────────────────┘
```

| Layer | Technology | Why |
| ----- | ---------- | --- |
| Model | Gemma 4 E4B | 4.5B effective params, 128K context, multimodal, edge-optimized |
| Fine-Tuning | Unsloth | Confidence calibration with QLoRA in ~10 GB VRAM, 60% memory reduction |
| Inference | Cactus Compute / Ollama | Local execution, logprobs access, offline-capable |
| Backend | Python | Gemma 4 delimiter parsing, RAG verification, stream multiplexing |
| Frontend | Next.js + Tailwind | Progressive disclosure UI with real-time multi-stream rendering |

---

## Gemma 4 Integration Details

### Prompting

```
<system>
For every response:
1. Begin reasoning with <|think|> to expose your deliberation
2. Enumerate competing interpretations with probability estimates
3. Use tool calls to verify factual claims
4. Provide a calibrated confidence score for each major conclusion
</system>
```

### Turn Management

Previous `<|channel>thought\n` blocks are stripped from context history between turns to prevent cyclical hallucination loops.

### Delimiter Handling

| Delimiter | Purpose | Glass Box Handling |
| --------- | ------- | ------------------ |
| `<\|channel>thought\n` | Internal reasoning | Routed to deliberation panel |
| `<\|tool_call>` | Function call | Triggers RAG verification |
| `<\|"\|>` | Tool call arguments | Parsed for claim text |

---

## Fine-Tuning with Unsloth

| What | Why |
| ---- | --- |
| Calibration adapter | Model outputs well-calibrated confidence scores, not just raw logits |
| Deliberation adapter | Structured `<\|think\|>` output with enumerated hypotheses |

Training efficiency: ~10 GB VRAM for E4B (vs ~24 GB without Unsloth). QLoRA 4-bit NF4, rank-16 LoRA, fused kernels for 2× speedup.

---

## Getting Started

### Prerequisites

* macOS (Apple Silicon recommended) or Linux
* Python 3.10+
* Node.js 18+

### Setup

```bash
# Clone
git clone https://github.com/chandan989/P.R.I.S.M..git
cd P.R.I.S.M.

# Inference backend (Option A: Cactus Compute)
brew install cactus-compute/cactus/cactus
cactus download chandan989/gemma-4-e4b-calibrated
python backend/server.py --model gemma-4-e4b-calibrated --port 8000

# Inference backend (Option B: Ollama)
ollama pull gemma4:e4b
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
| 🌵 **Cactus** | Primary inference engine — local, offline, logprobs streaming |
| ⚡ **Unsloth** | Confidence calibration + deliberation fine-tuning |
| 🦙 **Ollama** | Alternative local runtime for development |
| 🦙 **llama.cpp** | Lightweight alternative backend |
| 📱 **LiteRT** | Future mobile deployment path |

---

## Closing

The Glass Box Interpreter is not a medical app. It's not a legal app. It's a **transparency layer** that works for any domain.

The core insight: users don't need AI to be perfect — they need AI to **show its work** so they can decide for themselves.
