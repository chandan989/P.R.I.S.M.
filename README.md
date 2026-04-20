<div align="center">

# 🧊 P.R.I.S.M.

### **Probabilistic Reasoning and Interpretability System for Models**

*The Glass Box Interpreter — An X-ray for AI reasoning, built for the community health worker.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Gemma 4](https://img.shields.io/badge/Powered%20by-Gemma%204%20E4B-4285F4?logo=google&logoColor=white)](https://ai.google.dev/gemma)
[![Hackathon](https://img.shields.io/badge/Kaggle-Gemma%204%20Good-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/gemma-4-good-hackathon)
[![Tracks](https://img.shields.io/badge/Tracks-Safety%20%26%20Trust%20%7C%20Health%20%26%20Sciences-34A853)]()
[![Unsloth](https://img.shields.io/badge/Fine--Tuned%20with-Unsloth-FF6F00)](https://github.com/unslothai/unsloth)
[![Cactus](https://img.shields.io/badge/Inference-Cactus%20Compute-000000)](https://cactuscompute.com)

---

**P.R.I.S.M.** is an offline-first, transparent AI triage assistant designed for **one user** — the community health worker in a rural clinic — and **one workflow** — turning a patient's symptoms into a trustworthy, explainable triage recommendation. Instead of functioning as a black-box chatbot, it acts as an **X-ray for the Gemma 4 reasoning engine**, showing clinicians *why* the AI reached its conclusion and *how confident* it is.

Built for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) · Tracks: **Safety & Trust** · **Health & Sciences** · **Unsloth**

[Core Features](#-core-features) · [Architecture](#-architecture--tech-stack) · [The Workflow](#-the-workflow) · [Deployment](#-edge-deployment) · [Getting Started](#-getting-started-local-deployment)

</div>

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The User & The Workflow](#-the-user--the-workflow)
- [Core Features](#-core-features)
  - [Latent Deliberation Engine](#-latent-deliberation-engine)
  - [Source Grounding Visualizer](#-source-grounding-visualizer-traffic-light-system)
  - [Certainty Indicators](#-certainty-indicators)
- [Progressive Disclosure — Simple View vs Expert View](#-progressive-disclosure)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Gemma 4 Prompting & State Management](#-gemma-4-prompting--state-management)
- [Model Specifications](#-model-specifications)
- [Fine-Tuning with Unsloth](#-fine-tuning-with-unsloth)
- [Edge Deployment](#-edge-deployment)
- [Getting Started](#-getting-started-local-deployment)
- [Project Structure](#-project-structure)
- [Hackathon Alignment](#-hackathon-alignment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚨 The Problem

Community health workers (CHWs) in rural and resource-limited clinics face a critical gap: they need diagnostic decision support, but existing AI tools are either **cloud-dependent** (unusable offline) or **opaque** (give confident-sounding answers with no way to judge reliability).

| Failure Mode | Consequence for the CHW |
|---|---|
| **AI gives an assertive diagnosis** with no reasoning | CHW cannot tell if the recommendation is sound |
| **AI hallucinates a treatment protocol** | Patient receives dangerous misguidance |
| **AI shows uniform confidence** on everything | CHW cannot prioritize what to trust vs. verify |
| **AI requires internet** | Useless in the rural settings that need it most |

> A triage assistant that the CHW cannot trust is worse than no assistant at all — it creates a false sense of safety.

---

## 👤 The User & The Workflow

> **One user. One workflow. One domain.**

### The User

The **Community Health Worker (CHW)** — a frontline healthcare provider in a rural or resource-limited setting, often with limited formal medical training, working offline, in challenging conditions (poor lighting, noisy environment, time pressure).

### The Workflow

```
Patient arrives at rural clinic
    ↓
CHW enters symptoms (voice or text, in local language)
    ↓
Glass Box processes via Gemma 4 E4B (on-device, fully offline)
    ↓
SIMPLE VIEW shows:
  • Triage level: 🔴 Urgent / 🟡 Semi-urgent / 🟢 Routine
  • Suspected condition with confidence badge (✅ HIGH / ⚠️ MODERATE / ❓ LOW)
  • Source verification dots (🟢 verified / 🟡 inferred / 🔴 unverified)
    ↓
CHW makes informed referral decision
    ↓
[Optional] Supervising clinician remotely reviews EXPERT VIEW
```

This is the **entire product**. Every architectural decision flows from making this workflow fast, trustworthy, and accessible.

---

## ✨ Core Features

### 🧠 Latent Deliberation Engine

> Standard interfaces hide how an AI reaches its conclusion.

By injecting the `<|think|>` token into the system prompt, the Glass Box intercepts the native `<|channel>thought\n` text blocks streamed by Gemma 4 and captures the model's step-by-step reasoning and discarded hypotheses.

**Critically, this reasoning is NOT shown by default.** It is available through [Progressive Disclosure](#-progressive-disclosure) when a supervising clinician needs it.

- **Competing hypotheses** — captured with probability estimates
- **Discarded reasoning paths** — what the model rejected and why
- **Step-by-step logical flow** — the full chain from symptoms to triage level

---

### 🚦 Source Grounding Visualizer (Traffic-Light System)

> AI hallucinates facts and presents them as truth.

Every generated claim is automatically verified against a **local RAG vector database** (preloaded with WHO guidelines, clinical protocols, and drug references). We leverage Gemma 4's native function calling — parsing `<|tool_call>` and `<|"|>` delimiters — to trigger background validations:

1. **Claim Extraction** — Each response is decomposed into individual factual statements.
2. **Verification** — Every claim is cross-referenced against the on-device knowledge base.
3. **Inline Badges** — Each claim gets a simple colored dot.

#### Traffic-Light Interface

| Signal | Meaning | CHW sees |
|---|---|---|
| 🟢 | Fully verified against clinical source | Green dot next to the claim |
| 🟡 | Reasonable inference, not directly sourced | Yellow dot — use clinical judgment |
| 🔴 | Could not be verified — possible hallucination | Red dot + warning: "Verify independently" |

The CHW sees colored dots inline. Tapping a dot shows the source in a simple popup — no complex panels.

---

### 📊 Certainty Indicators

> AI sounds confident even when it doesn't know.

We stream **token-level logprobs** from Cactus Compute and translate them into **explicit, accessible confidence signals**.

#### Why We Don't Use Blur or Opacity

The previous design proposed blurring or fading text to represent low confidence. **We removed this** because:

- ❌ Blurred text is unreadable in harsh lighting (field clinics have poor lighting)
- ❌ Faded text fails for users with visual impairments
- ❌ Low-literacy users cannot interpret opacity as a metaphor for uncertainty
- ❌ It's a well-documented accessibility anti-pattern

#### What We Use Instead

| Indicator | Example | Why It Works |
|---|---|---|
| **Confidence Badges** | ✅ `HIGH` · ⚠️ `MODERATE` · ❓ `LOW` | Universally understood symbols + color |
| **Progress Bar** | `████████░░` (80%) | Visual fill — no reading required |
| **Plain-Language Labels** | "The AI is confident" / "The AI is guessing — verify" | Works for low-literacy users |
| **Color-Coded Borders** | Green / amber / red border around each section | Visible in poor lighting conditions |
| **Audio Confidence (Voice Mode)** | Spoken: "I am fairly confident this is..." | Accessible to visually impaired users |

#### Calibration

To ensure these confidence scores are *meaningful* (not just raw logits):

- **Brier Score minimization** — Reduces the gap between predicted and actual accuracy
- **Expected Calibration Error (ECE)** — Ensures confidence bins align with true correctness
- **Fine-tuning via Unsloth** — Model trained to produce well-calibrated probability outputs

---

## 🔀 Progressive Disclosure

The Glass Box has **two display modes**, controlled by a single toggle. This prevents cognitive overload while preserving full transparency for those who need it.

### Simple View (Default)

This is what the CHW sees. Clean, actionable, fast.

```
┌─────────────────────────────────────────────────────┐
│  🔴 HIGH PRIORITY — Refer to physician urgently     │
│                                                      │
│  Suspected: Cardiac event                           │
│  Confidence: ████████░░  ✅ HIGH                    │
│                                                      │
│  🟢 "Aspirin is recommended for suspected ACS"      │
│  🟡 "Patient's age increases cardiovascular risk"    │
│  🔴 "95% survival rate with early intervention"      │
│     └─ ⚠️ Unverified — do not rely on this figure   │
│                                                      │
│  [Why did the AI decide this?]  ← expand button     │
└─────────────────────────────────────────────────────┘
```

**What's shown:** Triage level, suspected condition, confidence badge, source-verified claims with colored dots.

**What's hidden:** Raw deliberation trace, competing hypotheses, probability distributions, discarded reasoning.

### Expert View (On Demand)

Activated by tapping "Why did the AI decide this?" — designed for supervising clinicians or experienced CHWs.

```
┌─────────────────────────────────────────────────────┐
│  EXPERT VIEW — Full Deliberation                    │
│                                                      │
│  Hypothesis A: Cardiac Ischemia          [72.3%]    │
│  ├── Supporting: ST-segment elevation, age > 55     │
│  └── Weakening: No troponin elevation reported      │
│                                                      │
│  Hypothesis B: Pulmonary Embolism        [21.8%]    │
│  ├── Supporting: Sudden onset dyspnea, tachycardia  │
│  └── Weakening: No DVT history                      │
│                                                      │
│  Hypothesis C: Musculoskeletal           [ 5.9%]    │
│  └── Discarded — insufficient clinical evidence     │
│                                                      │
│  Source chain: WHO ACS Guidelines 2023 → Section 4  │
│  Calibration: Brier = 0.12, ECE = 0.04              │
└─────────────────────────────────────────────────────┘
```

---

## 🛠 Architecture & Tech Stack

Built to run **entirely on-device**, preserving absolute data sovereignty for sensitive medical data.

```
┌──────────────────────────────────────────────────────────────────┐
│                       P.R.I.S.M. ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FRONTEND (Next.js + Tailwind CSS)                              │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Progressive Disclosure UI:                          │       │
│   │  • Simple View: Triage + badges + dots (default)     │       │
│   │  • Expert View: Deliberation + probabilities         │       │
│   │                                                      │       │
│   │  Multiplexed Streams:                                │       │
│   │  • Text stream ──────────► Triage recommendation     │       │
│   │  • Thought blocks ───────► Expert deliberation panel │       │
│   │  • Tool-call statuses ───► Source grounding dots      │       │
│   │  • Probability metrics ──► Confidence badges/bars     │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ SSE / WebSocket                       │
│                          ▼                                       │
│   BACKEND (Python)                                               │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Streaming Server (server.py)                        │       │
│   │  ├── Deliberation parser (<|channel>thought\n)       │       │
│   │  ├── Tool-call parser (<|tool_call>, <|"|>)          │       │
│   │  ├── Logprobs extractor → confidence scoring         │       │
│   │  └── RAG verification (local medical knowledge base) │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ Zero-copy inference                   │
│                          ▼                                       │
│   INFERENCE ENGINE (Cactus Compute)                              │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Gemma 4 E4B (Unsloth fine-tuned, calibrated)        │       │
│   │  • Ultra-low latency on ARM CPUs                     │       │
│   │  • Zero-copy memory mapping                          │       │
│   │  • Adaptive context: 8K (edge) → 128K (workstation)  │       │
│   │  • Fully offline                                     │       │
│   └──────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Role |
|---|---|---|
| **Foundation Model** | Gemma 4 E4B (4.5B effective / 8.0B total) | 128K max context, multimodal, PLE architecture |
| **Fine-Tuning** | Unsloth | Calibration + medical triage adaptation in ~10 GB VRAM |
| **Inference** | Cactus Compute | Zero-copy, ARM-optimized, offline, logprobs streaming |
| **Backend** | Python streaming server | Parses Gemma 4 delimiters, runs RAG verification, computes confidence scores |
| **Frontend** | Next.js + Tailwind CSS | Progressive disclosure UI — Simple View default, Expert View on demand |
| **Knowledge Base** | Local RAG vector store | WHO guidelines, clinical protocols, drug references — all on-device |

---

## 🧩 Gemma 4 Prompting & State Management

### Prompt Structure

We use Gemma 4's native `system`, `user`, and `assistant` roles with `<|think|>` to activate deliberation:

```
<system>
You are a medical triage assistant. For every patient case:
1. Begin reasoning with <|think|> — enumerate differential diagnoses with probabilities
2. Use tool calls to verify each clinical claim against the knowledge base
3. Provide a triage level (urgent/semi-urgent/routine) with a calibrated confidence score
4. Keep the final recommendation simple and actionable
</system>

<user>
Patient: 58-year-old male. Acute chest pain, shortness of breath.
History of deep vein thrombosis. No known cardiac history.
</user>
```

### Turn Management

During multi-turn conversations, the system automatically **strips previous `<|channel>thought\n` blocks** from the context to prevent cyclical hallucination loops:

```python
def sanitize_context(conversation_history):
    """Remove previous thought blocks to prevent reasoning contamination."""
    sanitized = []
    for turn in conversation_history:
        cleaned = re.sub(
            r'<\|channel\>thought\\n.*?</\|channel\>',
            '', turn.content, flags=re.DOTALL
        )
        sanitized.append(cleaned)
    return sanitized
```

### Gemma 4 Delimiter Handling

| Delimiter | Purpose | P.R.I.S.M. Handling |
|---|---|---|
| `<\|channel>thought\n` | Internal reasoning / deliberation | Captured → Expert View (hidden by default) |
| `<\|tool_call>` | Function call invocation | Triggers RAG verification → source dots |
| `<\|"\|>` | Tool call argument delimiters | Parsed for claim text to verify |

---

## 🧠 Model Specifications

| Model | Active Params | Total Params | Context | Modalities | Role |
|---|---|---|---|---|---|
| **Gemma 4 E4B** ⭐ | 4.5B | 8.0B | 128K | Text, Image, Audio | **Primary — clinic laptop, Apple Silicon** |
| **Gemma 4 E2B** | 2.3B | 5.1B | 128K | Text, Image, Audio | Fallback — ultra-constrained devices |

### Adaptive Context Window

The 128K context window is a *maximum capability*, not a constant. P.R.I.S.M. adapts context size to hardware:

| Deployment | Effective Context | Rationale |
|---|---|---|
| Raspberry Pi / mobile | 4K–8K | Sufficient for triage questionnaire + brief history |
| Clinic laptop | 16K–32K | Handles multi-page lab reports and images |
| Workstation / server | Up to 128K | Full medical record analysis |

### Why Gemma 4 E4B?

- **Per-Layer Embeddings (PLE)** — Efficient inference on local hardware
- **Offline-first** — No internet required; critical for rural deployment
- **140+ languages** — CHWs can interact in local language
- **Multimodal** — Upload X-rays, lab reports; speak symptoms via voice

---

## ⚡ Fine-Tuning with Unsloth

> **Special Track: Unsloth** — *Best fine-tuned Gemma 4 model optimized for a specific, impactful task.*

[Unsloth](https://github.com/unslothai/unsloth) powers P.R.I.S.M.'s **medical triage fine-tuning and confidence calibration**:

### What We Fine-Tune

| Adapter | Purpose | Dataset |
|---|---|---|
| **Calibration Adapter** | Well-calibrated confidence scores | Custom dataset with known correctness labels |
| **Medical Triage Adapter** | Domain-specific reasoning with structured deliberation | MedReason, Syntech AI Triage 500, Medical Meadow Wikidoc |
| **Deliberation Adapter** | Structured `<\|think\|>` output with hypothesis enumeration | Synthetic deliberation traces |

### Training Efficiency

| Metric | Without Unsloth | With Unsloth |
|---|---|---|
| E4B fine-tune VRAM | ~24 GB | **~10 GB** |
| Training speed | Baseline | **2× faster** |
| Memory reduction | — | **~60%** |

### Techniques

- **Quantized LoRA (QLoRA)** — 4-bit NF4 quantization, rank-16
- **Attention layer tuning** — Calibration-focused attention head fine-tuning
- **Unsloth fused kernels** — 2× training speedup

```python
from unsloth import FastModel
from trl import SFTTrainer

model, tokenizer = FastModel.from_pretrained(
    model_name="google/gemma-4-e4b",
    max_seq_length=8192,
    load_in_4bit=True,
)

model = FastModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16,
    lora_dropout=0,
)

trainer = SFTTrainer(
    model=model,
    dataset=medical_triage_calibration_dataset,
    max_seq_length=8192,
)
trainer.train()

model.save_pretrained_merged("prism-triage-e4b", tokenizer)
```

---

## 📡 Edge Deployment

### Adaptive Stream Strategy

Not all four data streams run simultaneously on all hardware. The system **gracefully degrades** based on device capability:

| Hardware Tier | Active Streams | Context | Latency Target |
|---|---|---|---|
| **Constrained** (RPi, mobile) | Text + Certainty only | 4K–8K | < 3s first token |
| **Standard** (clinic laptop) | Text + Certainty + Verification | 16K–32K | < 1s first token |
| **Full** (workstation/server) | All four streams (+ Expert View) | Up to 128K | < 500ms first token |

On constrained hardware:
- Expert View (deliberation) is **disabled** — CHW gets Simple View only
- Source verification runs **asynchronously after response** — dots appear with slight delay
- Context window is **capped** to prevent memory/latency issues

This ensures the CHW **always gets a fast, actionable triage recommendation**, even on a Raspberry Pi.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CACTUS COMPUTE INFERENCE ENGINE                   │
│            (ARM CPU optimized · zero-copy · offline)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Stream 1: TEXT ───────────────► Triage recommendation             │
│   Stream 2: CERTAINTY ─────────► Confidence badges + bars           │
│   Stream 3: VERIFICATION ──────► Source dots (async on edge)        │
│   Stream 4: DELIBERATION ──────► Expert View (disabled on edge)     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│          NEXT.JS PROGRESSIVE DISCLOSURE UI                          │
│        Simple View (default) ←→ Expert View (toggle)                │
└─────────────────────────────────────────────────────────────────────┘
```

### Deployment Targets

| Platform | Model | RAM | Context | Features Available |
|---|---|---|---|---|
| Raspberry Pi 5 | E2B (quantized) | ~4 GB | 4K–8K | Simple View + certainty badges |
| Clinic laptop (Apple Silicon) | E4B | ~8 GB | 16K–32K | Full Simple View + async verification |
| Workstation / server | E4B | ~16 GB | Up to 128K | All features + Expert View |

---

## 🚀 Getting Started (Local Deployment)

### Prerequisites

- **macOS** (Apple Silicon recommended) or **Linux**
- Python 3.10+
- Node.js 18+

### 1. Clone the Repository

```bash
git clone https://github.com/chandan989/P.R.I.S.M..git
cd P.R.I.S.M.
```

### 2. Setup the Inference Backend

```bash
# Install Cactus Compute
brew install cactus-compute/cactus/cactus

# Download the Unsloth fine-tuned Gemma 4 E4B weights
cactus download chandan989/gemma-4-e4b-triage

# Start the local streaming server (with logprobs enabled)
python backend/server.py --model gemma-4-e4b-triage --port 8000
```

### 3. Setup the Frontend

```bash
cd frontend
npm install

# Start the Next.js development server
npm run dev
```

Navigate to **http://localhost:3000** to interact with The Glass Box.

### Quick Start (Pseudo-code)

```python
from prism import GlassBoxInterpreter

interpreter = GlassBoxInterpreter(
    model="gemma-4-e4b-triage",
    runtime="cactus",
    port=8000,
)

response = interpreter.query(
    "58-year-old male. Acute chest pain and dyspnea. History of DVT.",
    domain="triage"
)

# Simple View outputs
print(response.triage_level)        # 🔴 URGENT
print(response.suspected_condition) # Cardiac event
print(response.confidence)          # ✅ HIGH (0.87)
print(response.source_dots)         # [🟢, 🟡, 🔴] per claim

# Expert View outputs (for supervising clinician)
print(response.deliberation)        # Full hypothesis tree
print(response.calibration_metrics) # Brier: 0.12, ECE: 0.04
```

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
│   │   ├── deliberation.py      # <|channel>thought\n block parser
│   │   ├── tool_calls.py        # <|tool_call> / <|"|> parser
│   │   └── logprobs.py          # Logprobs → confidence score
│   ├── grounding/
│   │   ├── rag_pipeline.py      # RAG verification (medical KB)
│   │   └── vector_store.py      # WHO guidelines, clinical protocols
│   ├── triage/
│   │   ├── classifier.py        # Triage level determination
│   │   └── confidence.py        # Brier/ECE calibrated scoring
│   └── calibration/
│       ├── brier.py             # Brier Score
│       └── ece.py               # Expected Calibration Error
│
├── frontend/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── app/
│   │   ├── page.tsx             # Main Glass Box interface
│   │   ├── layout.tsx           # App layout
│   │   └── components/
│   │       ├── SimpleView.tsx         # Default CHW interface
│   │       ├── ExpertView.tsx         # Expandable deliberation
│   │       ├── ConfidenceBadge.tsx    # ✅ ⚠️ ❓ indicators
│   │       ├── ConfidenceBar.tsx      # Progress bar visualization
│   │       ├── SourceDot.tsx          # 🟢🟡🔴 inline badges
│   │       ├── TriageCard.tsx         # Triage recommendation card
│   │       └── StreamMultiplexer.tsx  # Multi-stream handler
│   └── public/
│
├── training/
│   ├── finetune.py              # Unsloth fine-tuning pipeline
│   ├── datasets/                # Medical triage training data
│   └── adapters/                # Exported LoRA adapters
│
├── knowledge_base/              # Local RAG data (preloaded)
│   ├── who_guidelines/          # WHO clinical protocols
│   ├── drug_references/         # Essential medicines
│   └── triage_protocols/        # Emergency triage standards
│
├── scripts/
│   ├── download_model.py
│   └── evaluate.py              # Calibration evaluation
│
└── tests/
```

---

## 🎯 Hackathon Alignment

### Main Track Criteria

| Criterion | P.R.I.S.M. Strategy |
|---|---|
| 🧪 **Innovation** | First transparent triage interface with progressive disclosure for edge LLMs |
| 🌍 **Problem Relevance** | One user (CHW), one workflow (triage), one real-world impact (trustworthy medical AI in rural clinics) |
| ⚙️ **Technical Execution** | Gemma 4 delimiter parsing + calibration pipeline + Cactus Compute + adaptive streaming |
| 📐 **Clarity** | Accessible confidence badges, colored dots, plain-language labels — no jargon |
| 🎨 **UI/UX** | Progressive disclosure prevents cognitive overload; Simple View works for low-literacy users |

### Main Track Categories

| Category | Fit |
|---|---|
| 🛡 **Safety & Trust** | Core mission — every feature exists to make AI triage auditable, verifiable, and calibrated |
| 🏥 **Health & Sciences** | Medical triage for underserved rural clinics with transparent AI reasoning |

### Special Technology Tracks ($50,000)

| Track | Prize | How P.R.I.S.M. Qualifies |
|---|---|---|
| 🌵 **Cactus** | $10,000 | Cactus Compute powers all on-device inference — zero-copy memory mapping on ARM, fully offline, logprobs streaming for confidence extraction |
| ⚡ **Unsloth** | $10,000 | Medical triage and calibration LoRA adapters fine-tuned with QLoRA at ~10 GB VRAM, 60% memory reduction, 2× speedup |
| 🦙 **llama.cpp** | $10,000 | Alternative backend for ultra-constrained hardware (RPi kiosks) via GGUF quantization with `--logprobs` |
| 📱 **LiteRT** | $10,000 | Future mobile deployment path — E2B as LiteRT model with direct logit access on Android/iOS |
| 🦙 **Ollama** | $10,000 | Developer-friendly local runtime for rapid prototyping and model switching |

---

## 🗺 Roadmap

- [x] Architectural design and brief
- [ ] Cactus Compute inference backend with logprobs streaming
- [ ] `<|channel>thought\n` deliberation parser
- [ ] `<|tool_call>` / `<|"|>` function-call parser
- [ ] RAG verification pipeline (local medical knowledge base)
- [ ] Confidence scoring engine (logprobs → badges/bars)
- [ ] Next.js frontend — Simple View (default)
- [ ] Next.js frontend — Expert View (toggle)
- [ ] Confidence badges and progress bars (accessible design)
- [ ] Traffic-Light source dots (inline)
- [ ] Turn management (thought block stripping)
- [ ] Unsloth fine-tuning (triage + calibration adapters)
- [ ] Adaptive context sizing (4K edge → 128K workstation)
- [ ] Graceful stream degradation on constrained hardware
- [ ] Voice interaction (local language input/output)
- [ ] Community evaluation and feedback

---

## 🤝 Contributing

Contributions are welcome! Whether you're a clinician, developer, designer, or public health researcher — there's a place for you.

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
- **[Cactus Compute](https://cactuscompute.com)** — On-device inference engine
- **[Unsloth](https://github.com/unslothai/unsloth)** — Memory-efficient fine-tuning
- **[Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)** — For catalyzing responsible AI development
- WHO, MedReason, and open clinical knowledge communities

---

<div align="center">

*Built with conviction that AI transparency is not a feature — it is a fundamental right.*

*One user. One workflow. One mission: trustworthy triage.*

**P.R.I.S.M.** · Probabilistic Reasoning and Interpretability System for Models

</div>
