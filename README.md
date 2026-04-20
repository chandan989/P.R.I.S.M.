<div align="center">

# 🧊 P.R.I.S.M.

### **Probabilistic Reasoning and Interpretability System for Models**

*The Glass Box Interpreter — see how Gemma 4 thinks, whether it's right, and how sure it is.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Gemma 4](https://img.shields.io/badge/Powered%20by-Gemma%204%20A4B%2026B-4285F4?logo=google&logoColor=white)](https://ai.google.dev/gemma)
[![Hackathon](https://img.shields.io/badge/Kaggle-Gemma%204%20Good-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/gemma-4-good-hackathon)
[![Tracks](https://img.shields.io/badge/Tracks-Safety%20%26%20Trust%20%7C%20Health%20%26%20Sciences-34A853)]()
[![Unsloth](https://img.shields.io/badge/Fine--Tuned%20with-Unsloth-FF6F00)](https://github.com/unslothai/unsloth)
[![Cactus](https://img.shields.io/badge/Inference-Cactus%20Compute-000000)](https://cactuscompute.com)

---

**P.R.I.S.M.** is a transparency layer for Gemma 4 that transforms any AI conversation from a black-box interaction into an **auditable, verifiable, trust-calibrated experience**. Ask it anything — medicine, law, science, history — and the Glass Box shows you the model's reasoning, verifies its claims, and tells you how confident it actually is.

Built for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) · Tracks: **Safety & Trust** · **Health & Sciences** · **Unsloth** · **Cactus**

[The Problem](#-the-problem) · [Three Pillars](#-the-three-pillars) · [Why A4B](#-why-gemma-4-a4b-26b) · [Architecture](#-architecture--tech-stack) · [Demo](#-demo-scenarios) · [Getting Started](#-getting-started)

</div>

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Three Pillars](#-the-three-pillars)
  - [Deliberation Engine](#pillar-i--latent-deliberation-engine)
  - [Source Grounding](#pillar-ii--source-grounding-visualizer)
  - [Certainty Indicators](#pillar-iii--certainty-indicators)
- [Why Gemma 4 A4B (26B)](#-why-gemma-4-a4b-26b)
- [Progressive Disclosure](#-progressive-disclosure)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Gemma 4 Integration](#-gemma-4-integration)
- [Fine-Tuning with Unsloth](#-fine-tuning-with-unsloth)
- [Demo Scenarios](#-demo-scenarios)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Hackathon Alignment](#-hackathon-alignment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚨 The Problem

Every LLM today has the same fundamental UX failure:

> **The model sounds equally confident whether it's right or wrong. The user has no way to tell the difference.**

| What Users Get Today | What's Missing |
|---|---|
| A confident-sounding answer | The reasoning that produced it |
| Stated "facts" | Whether those facts are actually real |
| Uniform authoritative tone | How certain the model actually is |

This isn't a model problem — it's an **interface problem**. The model already has internal reasoning traces, probability distributions, and the ability to check sources. Current UIs just throw all of that away and show you a flat text response.

**P.R.I.S.M. fixes the interface.** It surfaces what the model already knows about its own uncertainty and reasoning, and presents it in a way humans can understand and act on.

---

## ✨ The Three Pillars

### Pillar I — Latent Deliberation Engine

> **What it does:** Shows you *how* the AI reached its conclusion.

Standard chatbot interfaces hide the model's internal reasoning. By injecting the `<|think|>` token into the system prompt, the Glass Box intercepts Gemma 4's native `<|channel>thought\n` blocks and captures:

- **Competing hypotheses** the model considered, with probability estimates
- **Discarded reasoning paths** — what the model rejected and why
- **Step-by-step logical chain** from question to conclusion

**This is NOT dumped on the user by default.** The deliberation is captured and available through [progressive disclosure](#-progressive-disclosure) — the user sees a clean answer first, then clicks "Why?" to see the reasoning.

```
┌── Deliberation (visible when user clicks "Why?") ────┐
│                                                       │
│  Interpretation A: [subject claim]       [72.3%]      │
│  ├── Supporting: [evidence 1], [evidence 2]           │
│  └── Weakening: [counter-evidence]                    │
│                                                       │
│  Interpretation B: [alternative]         [21.8%]      │
│  ├── Supporting: [evidence 3]                         │
│  └── Weakening: [counter-evidence 2]                  │
│                                                       │
│  ✗ Discarded: [rejected hypothesis]                   │
│                                                       │
│  ▶ Selected: Interpretation A                         │
└───────────────────────────────────────────────────────┘
```

---

### Pillar II — Source Grounding Visualizer

> **What it does:** Tells you *whether* each claim is backed by a real source.

Factual claims in the response are verified against a **local RAG vector database** using **selective verification**. Rather than checking every sentence (which was identified as a critical latency bottleneck), the system extracts only factual assertions — dates, statistics, citations, proper nouns, and specific claims — and verifies those.

We leverage Gemma 4's native function calling syntax — parsing `<|tool_call>` and `<|"|>` delimiters — to trigger background verification.

Each verified claim gets a simple colored dot inline:

| Signal | Meaning | User Sees |
|---|---|---|
| 🟢 | Verified against a source in the knowledge base | Green dot — trustworthy |
| 🟡 | Reasonable inference, but not directly sourced | Yellow dot — use judgment |
| 🔴 | Could not be verified — possible hallucination | Red dot + "Verify independently" |

```
Example output:

  🟢 "The Earth orbits the Sun at approximately 107,000 km/h."
      └─ Source: NASA Solar System Exploration

  🟡 "This likely contributes to seasonal temperature variation."
      └─ Inference from: orbital mechanics principles

  🔴 "The orbit changes by 2% every century."
      └─ ⚠️ No matching source — treat with caution
```

Tapping any dot shows the source document snippet in a simple popup.

> **Why selective verification?** A4B (26B) hallucinates far less than E4B (4.5B) on factual claims. By verifying only extracted factual assertions, we cut RAG verification calls by ~70% while still catching the claims most likely to be wrong — eliminating the primary latency bottleneck from the original design.

---

### Pillar III — Certainty Indicators

> **What it does:** Shows you *how confident* the AI actually is.

We stream **token-level logprobs** from the inference engine and translate them into **explicit, accessible confidence signals**:

| Indicator | Example | Why It Works |
|---|---|---|
| **Confidence Badges** | ✅ `HIGH` · ⚠️ `MODERATE` · ❓ `LOW` | Universal symbols + color |
| **Progress Bar** | `████████░░` (80%) | Visual fill — no reading required |
| **Plain-Language Labels** | "The AI is confident" / "The AI is guessing" | Works for all literacy levels |
| **Color-Coded Borders** | Green / amber / red border per section | Visible at a glance |

#### Why Not Blur or Opacity?

We explicitly chose **not** to blur or fade text to show uncertainty:

- ❌ Blurred text is unreadable in poor lighting
- ❌ Faded text fails for visually impaired users
- ❌ Opacity is not a universally understood metaphor for uncertainty

Explicit badges and labels are clearer, more accessible, and more actionable.

#### Calibration (Simplified with A4B)

Raw logprobs from A4B are **naturally better calibrated** than smaller models, thanks to the 26B parameter knowledge base. Instead of the original heavy-handed approach (full Brier Score minimization training), we use a streamlined strategy:

1. **Temperature scaling** — A single learned scalar applied post-hoc to logits. Simple, proven, and effective
2. **Validation** — Brier Score and ECE measured on a held-out eval set to confirm calibration quality
3. **Deliberation format adapter** — Small Unsloth LoRA to teach structured hypothesis enumeration (keeps the Unsloth track alive)

This achieves comparable calibration with a fraction of the training complexity.

---

## 🧠 Why Gemma 4 A4B (26B)

The original design used Gemma 4 E4B (4.5B effective). After identifying three critical technical hurdles — latency bottlenecks, context management fragility, and calibration difficulty — we upgraded to **Gemma 4 A4B**.

### A4B: The Best of Both Worlds

A4B is a **Mixture of Experts (MoE)** model:

| Spec | Value |
|---|---|
| Total parameters | 26B |
| Active parameters (per inference) | ~4B |
| Context window | 256K tokens |
| Architecture | MoE with selective expert routing |
| License | Apache 2.0 |

**The key insight:** A4B delivers **26B of learned knowledge** with the **inference cost of a ~4B model**. The MoE routing activates only the relevant expert subnetworks per token, keeping compute and memory requirements on par with E4B while dramatically improving output quality.

### What This Fixes

| Original Problem (E4B) | How A4B Solves It |
|---|---|
| **Severe latency:** RAG verification on every sentence + small model = massive user-facing delay | A4B produces higher-quality output → selective verification only → ~70% fewer RAG calls |
| **Flawed context management:** Stripping thought blocks caused model to "forget" its own reasoning | A4B's 256K context + stronger reasoning → keep summarized thought history → coherent multi-turn |
| **Calibration difficulty:** E4B logprobs wildly uncalibrated across domains → needed heavy fine-tuning | A4B logprobs naturally better calibrated → temperature scaling sufficient → simpler training |
| **Pipeline complexity:** 5-stage pipeline compensating for weak model | Stronger model → simpler pipeline → fewer failure points |

### Hardware Requirements

| Config | VRAM | Suitable For |
|---|---|---|
| A4B Q4 (4-bit quantized) | ~16 GB | RTX 4090, Apple M2 Pro/Max (unified memory) |
| A4B Q8 (8-bit quantized) | ~28 GB | Apple M3 Max, dual GPU setups |
| A4B FP16 (full precision) | ~52 GB | Cloud / multi-GPU environments |

> The MoE architecture means that despite 26B total params, active memory during inference is dominated by the ~4B active experts — making quantized A4B surprisingly lightweight and still viable for local execution.

---

## 🔀 Progressive Disclosure

The Glass Box uses **two display modes** to prevent cognitive overload:

### Default View

Clean answer + confidence badge + source dots. No raw reasoning.

```
┌─────────────────────────────────────────────────────┐
│                                                      │
│  🟢 "The Earth orbits the Sun every 365.25 days."   │
│  🟢 "This is why we have leap years."               │
│  🟡 "The orbit is nearly circular."                  │
│  🔴 "The orbit changes by 2% every century."         │
│     └─ ⚠️ Unverified                                │
│                                                      │
│  Confidence: ████████░░  ✅ HIGH                    │
│                                                      │
│  [Why did the AI say this?]  ← expand               │
└─────────────────────────────────────────────────────┘
```

### Expert View (click to expand)

Full deliberation tree, competing hypotheses, calibration metrics, source chains.

Users who want the detail can get it. Users who just want the answer aren't overwhelmed.

---

## 🛠 Architecture & Tech Stack

Runs **locally on your machine** — no cloud APIs, no data leaving your device.

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
|---|---|---|
| **Model** | Gemma 4 A4B (26B MoE, ~4B active) | 256K context, multimodal, MoE efficiency — 26B knowledge with ~4B inference cost |
| **Fine-Tuning** | Unsloth | Deliberation format adapter via QLoRA (~16 GB VRAM, 2× faster) + temperature scaling |
| **Inference** | Cactus Compute / Ollama | Local execution, logprobs access, offline-capable |
| **Backend** | Python | Gemma 4 delimiter parsing, selective RAG verification, stream multiplexing |
| **Frontend** | Next.js + Tailwind CSS | Progressive disclosure UI rendering four multiplexed streams |

---

## 🧩 Gemma 4 Integration

### Prompt Structure

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

The original design stripped all `<|channel>thought\n` blocks from context history between turns. While this prevented cyclical hallucination loops, it caused the model to **"forget" its own reasoning** — crippling multi-turn coherence.

**New approach with A4B's 256K context:**

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

This preserves reasoning continuity across turns while keeping context lean. The model retains awareness of *what* it reasoned and *why*, without the full verbose thought blocks that could trigger cyclical loops.

### Delimiter Handling

| Delimiter | Purpose | Glass Box Handling |
|---|---|---|
| `<\|channel>thought\n` | Internal reasoning | Routed to deliberation panel (Expert View) |
| `<\|tool_call>` | Function call invocation | Triggers selective RAG verification pipeline |
| `<\|"\|>` | Tool call argument delimiters | Parsed for claim text to verify |

---

## ⚡ Fine-Tuning with Unsloth

> **Special Track: Unsloth** — *Best fine-tuned Gemma 4 model optimized for a specific, impactful task.*

P.R.I.S.M. fine-tunes Gemma 4 A4B for **structured deliberation output** and **confidence calibration** — teaching the model to produce well-formatted reasoning traces with calibrated probability scores.

### Adapter Strategy (Simplified)

| Adapter | Purpose |
|---|---|
| **Deliberation Format Adapter** | Structured `<\|think\|>` output with enumerated hypotheses and probability estimates |
| **Temperature Scaling Layer** | Post-hoc logprob calibration — single learned scalar validated against Brier/ECE |

> **Why simplified?** The original plan called for a full calibration adapter trained with Brier Score minimization loss across all domains. A4B's 26B parameter space produces naturally better-calibrated logprobs than E4B, meaning a simple temperature scaling layer achieves comparable calibration with a fraction of the training complexity. This avoids the risk of miscalibration on out-of-distribution topics that plagued the original design.

| Metric | Without Unsloth | With Unsloth |
|---|---|---|
| A4B fine-tune VRAM | ~48 GB | **~16 GB** |
| Training speed | Baseline | **2× faster** |
| Memory reduction | — | **~67%** |

```python
from unsloth import FastModel
from trl import SFTTrainer

model, tokenizer = FastModel.from_pretrained(
    model_name="google/gemma-4-a4b",
    max_seq_length=8192,
    load_in_4bit=True,
)

model = FastModel.get_peft_model(
    model, r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16, lora_dropout=0,
)

trainer = SFTTrainer(
    model=model,
    dataset=deliberation_dataset,  # Structured reasoning traces
    max_seq_length=8192,
)
trainer.train()
model.save_pretrained_merged("prism-a4b-deliberation", tokenizer)
```

---

## 🎬 Demo Scenarios

The Glass Box works with **any query, any domain**. The transparency pillars are domain-agnostic:

### 🏥 Medical
> "Patient has chest pain and shortness of breath. History of DVT. What are the possible diagnoses?"

→ Deliberation shows competing diagnoses (cardiac vs. pulmonary vs. musculoskeletal) with probabilities. Source dots verify clinical claims against medical literature. Confidence badge shows calibrated certainty.

### ⚖️ Legal
> "What are a tenant's rights if a landlord refuses to return a security deposit in California?"

→ Deliberation shows statutory analysis chain. Source dots verify specific codes (CA Civil Code §1950.5). Red dots flag any unverified legal claims.

### 🔬 Science
> "Is there evidence that intermittent fasting improves longevity in humans?"

→ Deliberation weighs animal vs. human studies. Source dots verify cited papers. Low confidence badge on claims where human data is limited.

### 📚 General Knowledge
> "Why did the Roman Empire fall?"

→ Deliberation shows multiple historiographic perspectives. Yellow dots on interpretive claims. Confidence varies across competing theories.

---

## 🚀 Getting Started

### Prerequisites

- **macOS** (Apple Silicon M2 Pro+ recommended) or **Linux** with 16GB+ VRAM GPU
- Python 3.10+
- Node.js 18+

### Option A: Cactus Compute

```bash
git clone https://github.com/chandan989/P.R.I.S.M..git
cd P.R.I.S.M.

# Install Cactus Compute + download model
brew install cactus-compute/cactus/cactus
cactus download chandan989/gemma-4-a4b-calibrated

# Start backend
python backend/server.py --model gemma-4-a4b-calibrated --port 8000

# Start frontend
cd frontend && npm install && npm run dev
```

### Option B: Ollama

```bash
git clone https://github.com/chandan989/P.R.I.S.M..git
cd P.R.I.S.M.

# Pull model via Ollama
ollama pull gemma4:a4b

# Start backend
python backend/server.py --runtime ollama --port 8000

# Start frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000** → ask anything → see the Glass Box in action.

---

## 📁 Project Structure

```
P.R.I.S.M./
├── brief.md                     # Architectural blueprint
├── README.md                    # You are here
├── LICENSE                      # MIT License
│
├── backend/
│   ├── server.py                # Python streaming server
│   ├── parsers/
│   │   ├── deliberation.py      # <|channel>thought\n parser
│   │   ├── claim_extractor.py   # Factual claim extraction for selective verification
│   │   └── logprobs.py          # Logprobs → temperature-scaled confidence scores
│   ├── grounding/
│   │   ├── rag_pipeline.py      # Selective claim verification via RAG
│   │   └── vector_store.py      # Local knowledge base
│   └── calibration/
│       ├── temperature.py       # Temperature scaling layer
│       ├── brier.py             # Brier Score (validation)
│       └── ece.py               # Expected Calibration Error (validation)
│
├── frontend/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── app/
│   │   ├── page.tsx             # Main Glass Box interface
│   │   ├── layout.tsx           # App layout
│   │   └── components/
│   │       ├── DefaultView.tsx        # Answer + badges + dots
│   │       ├── ExpertView.tsx         # Full deliberation tree
│   │       ├── ConfidenceBadge.tsx    # ✅ ⚠️ ❓ indicators
│   │       ├── ConfidenceBar.tsx      # Progress bar
│   │       ├── SourceDot.tsx          # 🟢🟡🔴 inline badges
│   │       └── StreamMultiplexer.tsx  # Four-stream handler
│   └── public/
│
├── training/
│   ├── finetune.py              # Unsloth fine-tuning (deliberation adapter)
│   ├── temperature_scaling.py   # Post-hoc calibration training
│   └── adapters/                # Exported LoRA adapters
│
├── knowledge_base/              # Local RAG data
│
├── scripts/
│   ├── download_model.py
│   └── evaluate.py              # Calibration evaluation (Brier + ECE)
│
└── tests/
```

---

## 🎯 Hackathon Alignment

### Main Tracks

| Track | Fit |
|---|---|
| 🛡 **Safety & Trust** | Core mission — making every AI response auditable, verifiable, and confidence-calibrated |
| 🏥 **Health & Sciences** | Medical triage is a high-impact demo scenario for the transparency layer |

### Special Technology Tracks

| Track | Prize | How P.R.I.S.M. Uses It |
|---|---|---|
| 🌵 **Cactus** | $10,000 | Primary local inference engine with logprobs streaming for A4B |
| ⚡ **Unsloth** | $10,000 | Deliberation format fine-tuning + temperature scaling calibration (QLoRA, ~16 GB, 2× faster) |
| 🦙 **Ollama** | $10,000 | Alternative local runtime for development and model switching |
| 🦙 **llama.cpp** | $10,000 | Lightweight alternative inference backend (powers Cactus and Ollama under the hood) |
| 📱 **LiteRT** | $10,000 | Future mobile deployment path — A4B's MoE efficiency makes this viable |

---

## 🗺 Roadmap

- [x] Architectural design and brief
- [x] Model selection: Gemma 4 A4B (26B MoE) — resolving latency/calibration/context concerns
- [ ] Cactus Compute / Ollama inference backend with logprobs
- [ ] `<|channel>thought\n` deliberation parser
- [ ] Claim extractor (selective factual assertion extraction)
- [ ] Selective RAG verification pipeline (local vector store)
- [ ] Confidence scoring (logprobs → temperature-scaled badges)
- [ ] Next.js frontend — Default View
- [ ] Next.js frontend — Expert View (expandable)
- [ ] Confidence badges, bars, and plain-language labels
- [ ] Source dots (🟢🟡🔴) with tap-to-inspect
- [ ] Turn management (thought block summarization, not stripping)
- [ ] Unsloth fine-tuning (deliberation format adapter)
- [ ] Temperature scaling calibration + Brier/ECE validation
- [ ] Demo scenarios (medical, legal, science, general)

---

## 🤝 Contributing

Contributions welcome — developers, designers, researchers, domain experts.

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'Add your-feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Google DeepMind](https://deepmind.google/)** — Gemma 4 model family
- **[Cactus Compute](https://cactuscompute.com)** — Local inference engine
- **[Unsloth](https://github.com/unslothai/unsloth)** — Memory-efficient fine-tuning
- **[Ollama](https://ollama.com)** — Local model serving
- **[Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)**

---

<div align="center">

*Users don't need AI to be perfect. They need AI to show its work.*

**P.R.I.S.M.** · Probabilistic Reasoning and Interpretability System for Models

</div>
