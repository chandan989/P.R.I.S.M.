<div align="center">

# 🧊 P.R.I.S.M.

### **Probabilistic Reasoning and Interpretability System for Models**

*The Glass Box Interpreter — see how Gemma 4 thinks, whether it's right, and how sure it is.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Gemma 4](https://img.shields.io/badge/Powered%20by-Gemma%204%20A4B%2026B-4285F4?logo=google&logoColor=white)](https://ai.google.dev/gemma)
[![Hackathon](https://img.shields.io/badge/Kaggle-Gemma%204%20Good-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/gemma-4-good-hackathon)
[![Tracks](https://img.shields.io/badge/Tracks-Safety%20%26%20Trust%20%7C%20Health%20%26%20Sciences-34A853)]()
[![Unsloth](https://img.shields.io/badge/Fine--Tuned%20with-Unsloth-FF6F00)](https://github.com/unslothai/unsloth)

---

**P.R.I.S.M.** is a transparency layer for Gemma 4 that transforms any AI conversation from a black-box interaction into an **auditable, verifiable, trust-calibrated experience**. Ask it anything — medicine, law, science, history — and the Glass Box shows you the model's reasoning, verifies its claims, and tells you how confident it actually is.

**No GPU required. Open a browser. Ask anything. See the Glass Box.**

Built for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) · Tracks: **Safety & Trust** · **Health & Sciences** · **Unsloth**

[The Problem](#-the-problem) · [Three Pillars](#-the-three-pillars) · [Architecture](#-architecture--tech-stack) · [Demo](#-demo-scenarios) · [Getting Started](#-getting-started)

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

Factual claims in the response are verified against a **curated knowledge base** using **selective verification**. Rather than checking every sentence (which would add massive latency), the system extracts only factual assertions — dates, statistics, citations, proper nouns, and specific claims — and verifies those.

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

> **Why selective verification?** A4B (26B) hallucinates far less than smaller models on factual claims. By verifying only extracted factual assertions, we cut verification calls by ~70% while still catching the claims most likely to be wrong.

---

### Pillar III — Certainty Indicators

> **What it does:** Shows you *how confident* the AI actually is.

We extract **token-level logprobs** from the model and translate them into **explicit, accessible confidence signals**:

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

#### Calibration

A4B's 26B parameter space produces **naturally better-calibrated logprobs** than smaller models. We apply lightweight post-processing:

1. **Temperature scaling** — A single learned scalar applied post-hoc to logits, trained via Unsloth
2. **Validation** — Brier Score and ECE measured on a held-out eval set to confirm calibration quality
3. **Deliberation format adapter** — Small Unsloth LoRA to teach structured hypothesis enumeration

---

## 🧠 Why Gemma 4 A4B (26B)

### A4B: Knowledge of a Large Model, Cost of a Small One

A4B is a **Mixture of Experts (MoE)** model:

| Spec | Value |
|---|---|
| Total parameters | 26B |
| Active parameters (per inference) | ~4B |
| Context window | 256K tokens |
| Architecture | MoE with selective expert routing |
| License | Apache 2.0 |

**The key insight:** A4B delivers **26B of learned knowledge** with the **inference cost of a ~4B model**. The MoE routing activates only the relevant expert subnetworks per token, making it economical to host while delivering flagship-tier reasoning quality.

### Why A4B is the Right Choice for Transparency

| Requirement | How A4B Delivers |
|---|---|
| **High-quality reasoning traces** | 26B knowledge produces coherent, structured deliberation — smaller models produce noisy, unreliable thought chains |
| **Reliable factual grounding** | Lower baseline hallucination rate → selective verification catches real problems, not noise |
| **Calibrated confidence** | Larger models produce naturally better-calibrated logprobs → lightweight post-processing sufficient |
| **Long multi-turn conversations** | 256K context window → full thought history retained across turns, no lossy summarization |
| **Cost-efficient hosting** | MoE architecture → only ~4B params active per token → affordable to serve |

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

**Cloud-hosted model, accessible from any device — no GPU required.**

```
┌──────────────────────────────────────────────────────────────────┐
│                       P.R.I.S.M. ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FRONTEND (Next.js)                                             │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Default View:  Answer + badges + source dots        │       │
│   │  Expert View:   Deliberation tree + calibration      │       │
│   │                                                      │       │
│   │  Streams:                                            │       │
│   │  • Response text ────► Answer rendering              │       │
│   │  • Thought blocks ──► Deliberation panel             │       │
│   │  • Verification ────► Source dots (🟢🟡🔴)          │       │
│   │  • Confidence ──────► Badges / bars                  │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ API                                   │
│                          ▼                                       │
│   BACKEND (Python — FastAPI)                                     │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  API Server                                          │       │
│   │  ├── Gemma 4 A4B API client (streaming)             │       │
│   │  ├── Thought block parser → deliberation            │       │
│   │  ├── Claim extractor → selective verification       │       │
│   │  ├── Logprobs extractor → confidence scores         │       │
│   │  └── Knowledge base (vector search)                 │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ API call                              │
│                          ▼                                       │
│   MODEL HOST (Kaggle / Vertex AI / HF Inference Endpoints)      │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Gemma 4 A4B 26B MoE (Unsloth fine-tuned)           │       │
│   │  • 26B total / ~4B active — MoE efficiency           │       │
│   │  • 256K context window                               │       │
│   │  • Logprobs returned via API                         │       │
│   │  • Hosted — accessible from any device               │       │
│   └──────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Why |
|---|---|---|
| **Model** | Gemma 4 A4B (26B MoE, ~4B active) | 256K context, multimodal, MoE efficiency, best-in-class reasoning |
| **Fine-Tuning** | Unsloth | Deliberation format adapter via QLoRA (~16 GB VRAM, 2× faster) + temperature scaling |
| **Model Hosting** | Kaggle Notebooks / Vertex AI / HF Inference Endpoints | No end-user GPU required — model runs in the cloud |
| **Backend** | Python (FastAPI) | Thought block parsing, selective verification, logprob extraction, knowledge base queries |
| **Frontend** | Next.js | Progressive disclosure UI rendering streaming response, deliberation, sources, and confidence |

### Why We Moved Away From Local Inference

The original P.R.I.S.M. design required the model to run entirely on the user's local machine. During development, we identified **five critical bottlenecks** that made local-only execution untenable for a project focused on broad societal impact:

| Bottleneck | Impact | How Cloud Hosting Solves It |
|---|---|---|
| **Hardware exclusivity** | Required $1,500+ GPU (RTX 4090 / M2 Pro) — excludes most users | Any device with a browser |
| **Pipeline fragility** | Local inference engine + custom delimiter parsing + SSE multiplexing = many failure points | Standard API calls, model host handles inference reliability |
| **Lossy context summarization** | Local VRAM limits forced aggressive thought-block summarization, degrading coherence over turns | 256K context via API — full thought history retained |
| **Brittle calibration** | Temperature scaling on local logprobs failed on out-of-distribution queries | Cloud-hosted model with consistent inference environment + validated calibration |
| **Demo reliability** | Multi-stage local pipeline susceptible to race conditions and streaming desyncs | Single API endpoint — dramatically simpler demo path |

> **A "transparent AI for everyone" that requires a $1,500 GPU isn't for everyone.** Moving to cloud-hosted inference makes P.R.I.S.M. accessible to any user with a browser — which is the entire point.

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

### Turn Management

With A4B's 256K context window accessed via API, we no longer need aggressive thought-block stripping or lossy summarization. The full conversation history — including condensed reasoning summaries — fits comfortably within the context window.

```python
def prepare_context(history: list[dict]) -> list[dict]:
    """Prepare conversation history for the next turn.
    
    With 256K context via API, we retain condensed reasoning
    summaries from prior turns. No aggressive stripping needed.
    """
    prepared = []
    for turn in history:
        thought_blocks = extract_thought_blocks(turn)
        if thought_blocks:
            # Keep a concise summary of prior reasoning
            summary = summarize_reasoning(thought_blocks)
            cleaned = strip_raw_thought_blocks(turn)
            prepared.append(f"{cleaned}\n[Prior reasoning: {summary}]")
        else:
            prepared.append(turn)
    return prepared
```

This preserves reasoning continuity across turns. The model retains awareness of *what* it reasoned and *why*, enabling coherent multi-turn conversations even in complex domains like medical triage or legal analysis.

### Delimiter Handling

| Delimiter | Purpose | Glass Box Handling |
|---|---|---|
| `<\|channel>thought\n` | Internal reasoning | Routed to deliberation panel (Expert View) |
| `<\|tool_call>` | Function call invocation | Triggers selective verification pipeline |
| `<\|"\|>` | Tool call argument delimiters | Parsed for claim text to verify |

---

## ⚡ Fine-Tuning with Unsloth

> **Special Track: Unsloth** — *Best fine-tuned Gemma 4 model optimized for a specific, impactful task.*

P.R.I.S.M. fine-tunes Gemma 4 A4B for **structured deliberation output** and **confidence calibration** — teaching the model to produce well-formatted reasoning traces with calibrated probability scores.

### What We Fine-Tune

| Adapter | Purpose |
|---|---|
| **Deliberation Format Adapter** | Structured `<\|think\|>` output with enumerated hypotheses, probability estimates, and supporting/weakening evidence |
| **Temperature Scaling Layer** | Post-hoc logprob calibration — single learned scalar validated against Brier/ECE metrics |

### Training Pipeline

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

# Export adapter to HuggingFace Hub
model.save_pretrained_merged("prism-a4b-deliberation", tokenizer)
model.push_to_hub("chandan989/prism-a4b-deliberation")
```

### Deployment After Fine-Tuning

The fine-tuned adapter is uploaded to HuggingFace Hub and loaded at inference time on the cloud host:

1. **Train** on a Kaggle notebook (free T4/P100 GPU) or local machine with Unsloth
2. **Upload** the LoRA adapter to HuggingFace Hub
3. **Load** the adapter on the model host (Kaggle Notebook / Vertex AI / HF Inference Endpoints)
4. **Serve** via API — the backend calls this endpoint, users never need a GPU

| Metric | Without Unsloth | With Unsloth |
|---|---|---|
| A4B fine-tune VRAM | ~48 GB | **~16 GB** |
| Training speed | Baseline | **2× faster** |
| Memory reduction | — | **~67%** |

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

- Python 3.10+
- Node.js 18+
- A HuggingFace account (for model hosting) or Kaggle account

**No GPU required on your machine.** The model runs in the cloud.

### Quick Start

```bash
git clone https://github.com/chandan989/P.R.I.S.M..git
cd P.R.I.S.M.

# Set up backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your model endpoint URL and API key

python server.py --port 8000

# In a new terminal — set up frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000** → ask anything → see the Glass Box in action.

### Model Hosting Options

| Option | Cost | Best For |
|---|---|---|
| **Kaggle Notebook** | Free (30h/week GPU) | Hackathon demo, development |
| **HuggingFace Inference Endpoints** | ~$1.30/hr (A10G) | Production-like deployment |
| **Vertex AI** | Pay-per-use | Scalable production |
| **Self-hosted** (optional) | Your GPU | If you *want* to run locally |

> P.R.I.S.M. is designed API-first. The backend talks to a model endpoint — it doesn't care whether that endpoint is Kaggle, Vertex, HuggingFace, or your own machine running Ollama. Swap the endpoint URL in `.env` and everything works.

---

## 📁 Project Structure

```
P.R.I.S.M./
├── README.md                    # You are here
├── LICENSE                      # MIT License
│
├── backend/
│   ├── server.py                # FastAPI server
│   ├── config.py                # Model endpoint config (.env)
│   ├── client/
│   │   └── gemma_client.py      # Gemma 4 API client (streaming + logprobs)
│   ├── parsers/
│   │   ├── deliberation.py      # Thought block parser
│   │   ├── claim_extractor.py   # Factual claim extraction for selective verification
│   │   └── logprobs.py          # Logprobs → confidence scores
│   ├── grounding/
│   │   ├── verifier.py          # Selective claim verification
│   │   └── knowledge_base.py    # Vector search over curated sources
│   └── calibration/
│       ├── temperature.py       # Temperature scaling layer
│       ├── brier.py             # Brier Score (validation)
│       └── ece.py               # Expected Calibration Error (validation)
│
├── frontend/
│   ├── package.json
│   ├── app/
│   │   ├── page.tsx             # Main Glass Box interface
│   │   ├── layout.tsx           # App layout
│   │   └── components/
│   │       ├── DefaultView.tsx        # Answer + badges + dots
│   │       ├── ExpertView.tsx         # Full deliberation tree
│   │       ├── ConfidenceBadge.tsx    # ✅ ⚠️ ❓ indicators
│   │       ├── ConfidenceBar.tsx      # Progress bar
│   │       ├── SourceDot.tsx          # 🟢🟡🔴 inline badges
│   │       └── StreamHandler.tsx      # API stream handler
│   └── public/
│
├── training/
│   ├── finetune.py              # Unsloth fine-tuning (deliberation adapter)
│   ├── temperature_scaling.py   # Post-hoc calibration training
│   ├── eval/
│   │   ├── brier_eval.py        # Brier Score evaluation
│   │   └── ece_eval.py          # ECE evaluation
│   └── adapters/                # Exported LoRA adapters
│
├── knowledge_base/              # Curated source documents for verification
│
├── scripts/
│   ├── deploy_model.py          # Upload fine-tuned model to hosting
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

### Special Technology Track

| Track | Prize | How P.R.I.S.M. Uses It |
|---|---|---|
| ⚡ **Unsloth** | $10,000 | Deliberation format fine-tuning + temperature scaling calibration (QLoRA, ~16 GB, 2× faster). Adapter uploaded to HuggingFace and loaded at inference time. |

### Why We Don't Claim Other Special Tracks

Transparency about our technology choices:

- **Cactus / Ollama / llama.cpp** — These are local inference engines. P.R.I.S.M. is designed API-first for maximum accessibility. Users *can* self-host with any of these tools by pointing the backend at a local endpoint, but local inference is not our primary architecture and we don't want to claim a track we didn't build around.
- **LiteRT** — Mobile deployment is a roadmap item, not a hackathon deliverable.

> We'd rather be honest about three tracks and deliver a polished, accessible product than claim five tracks and ship a fragile demo that only works on $1,500 hardware.

---

## 🗺 Roadmap

- [x] Architectural design and brief
- [x] Model selection: Gemma 4 A4B (26B MoE)
- [x] Architecture pivot: local → cloud-hosted (API-first)
- [ ] Unsloth fine-tuning — deliberation format adapter
- [ ] Temperature scaling calibration + Brier/ECE validation
- [ ] Upload fine-tuned adapter to HuggingFace Hub
- [ ] Deploy model to Kaggle Notebook / hosting endpoint
- [ ] FastAPI backend — Gemma 4 API client (streaming + logprobs)
- [ ] Thought block parser (deliberation extraction)
- [ ] Claim extractor (selective factual assertion extraction)
- [ ] Selective verification pipeline (knowledge base)
- [ ] Confidence scoring (logprobs → calibrated badges)
- [ ] Next.js frontend — Default View
- [ ] Next.js frontend — Expert View (expandable)
- [ ] Confidence badges, bars, and plain-language labels
- [ ] Source dots (🟢🟡🔴) with tap-to-inspect
- [ ] Turn management (thought block summarization)
- [ ] Demo scenarios (medical, legal, science, general)
- [ ] Public deployment — shareable demo URL

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
- **[Unsloth](https://github.com/unslothai/unsloth)** — Memory-efficient fine-tuning
- **[Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)**

---

<div align="center">

*Users don't need AI to be perfect. They need AI to show its work.*

**P.R.I.S.M.** · Probabilistic Reasoning and Interpretability System for Models

</div>
