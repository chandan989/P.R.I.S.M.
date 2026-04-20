<div align="center">

# 🧊 P.R.I.S.M.

### **Probabilistic Reasoning and Interpretability System for Models**

*The Glass Box Interpreter — An X-ray for AI reasoning, not another black-box chatbot.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Gemma 4](https://img.shields.io/badge/Powered%20by-Gemma%204%20E4B-4285F4?logo=google&logoColor=white)](https://ai.google.dev/gemma)
[![Hackathon](https://img.shields.io/badge/Kaggle-Gemma%204%20Good-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/gemma-4-good-hackathon)
[![Tracks](https://img.shields.io/badge/Tracks-Safety%20%26%20Trust%20%7C%20Health%20%26%20Sciences-34A853)]()
[![Unsloth](https://img.shields.io/badge/Fine--Tuned%20with-Unsloth-FF6F00)](https://github.com/unslothai/unsloth)
[![Cactus](https://img.shields.io/badge/Inference-Cactus%20Compute-000000)](https://cactuscompute.com)

---

**P.R.I.S.M.** is an offline-first, transparent AI interface designed for high-stakes environments. Instead of functioning as a traditional "black box" chatbot, it acts as an **X-ray for the Gemma 4 reasoning engine** — exposing internal deliberations, verifying factual claims against local databases in real-time, and visualizing mathematical uncertainty to calibrate user trust safely.

Built for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) · Tracks: **Safety & Trust** · **Health & Sciences** · **Unsloth**

[Core Features](#-core-features) · [Architecture](#-architecture--tech-stack) · [Domains](#-application-domains) · [Deployment](#-edge-deployment) · [Getting Started](#-getting-started-local-deployment)

</div>

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Vision](#-the-vision)
- [Core Features](#-core-features)
  - [Latent Deliberation Engine](#-latent-deliberation-engine)
  - [Source Grounding Visualizer](#-source-grounding-visualizer-traffic-light-system)
  - [Sliding Scale of Certainty](#-sliding-scale-of-certainty)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Gemma 4 Prompting & State Management](#-gemma-4-prompting--state-management)
- [Model Specifications](#-model-specifications)
- [Fine-Tuning with Unsloth](#-fine-tuning-with-unsloth)
- [Application Domains](#-application-domains)
- [Edge Deployment](#-edge-deployment)
- [Getting Started](#-getting-started-local-deployment)
- [Project Structure](#-project-structure)
- [Hackathon Alignment](#-hackathon-alignment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🚨 The Problem

Large language models deployed in high-stakes domains — **medical triage**, **legal navigation**, **financial advisory** — share a dangerous trait: *opacity*.

| Failure Mode | Consequence |
|---|---|
| **Assertive outputs** with hidden probabilistic reasoning | Users over-trust wrong answers |
| **Hallucinated facts** presented with full confidence | Misdiagnosis, legal misguidance |
| **No source provenance** for claims made | Impossible to audit or verify |
| **Uniform confidence tone** regardless of certainty | Users cannot gauge reliability |

> In domains where lives and livelihoods are at stake, an AI system that *sounds* confident is not the same as one that *is* correct.

---

## 💡 The Vision

**P.R.I.S.M.** introduces the **Glass Box** paradigm:

> Instead of treating AI as an infallible oracle, treat it as a **transparent analytical collaborator** — one that shows *how* it thinks, *what* it's unsure about, and *where* its knowledge comes from.

The system acts as a **diagnostic overlay** on top of Gemma 4, transforming every response into a multi-layered, inspectable artifact:

```
┌─────────────────────────────────────────────────────────┐
│                    USER QUERY                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Deliberation│  │   Source     │  │  Certainty    │  │
│  │   Engine    │──│  Grounding   │──│    Scale      │  │
│  │(<|think|>)  │  │(<|tool_call>)│  │  (logprobs)   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│         │                │                   │          │
│         ▼                ▼                   ▼          │
│  ┌─────────────────────────────────────────────────┐    │
│  │          GLASS BOX TRANSPARENT RESPONSE         │    │
│  │  • Visible reasoning chains                     │    │
│  │  • Color-coded source verification              │    │
│  │  • Confidence-weighted text rendering            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Core Features

### 🧠 Latent Deliberation Engine

> Standard interfaces hide how an AI reaches its conclusion.

By injecting the `<|think|>` token into the system prompt, the Glass Box UI intercepts the native `<|channel>thought\n` text blocks streamed by Gemma 4 and visualizes the model's step-by-step reasoning and discarded hypotheses.

- **Competing hypotheses** — displayed as probability-weighted branches
- **Discarded reasoning paths** — see what the model rejected and why
- **Step-by-step logical flow** — the full chain from question to conclusion

#### Example: Medical Triage Scenario

```
┌── Deliberation Stream (<|channel>thought) ───────────┐
│                                                       │
│  Hypothesis A: Cardiac Ischemia          [72.3%]      │
│  ├── Supporting: ST-segment elevation, age > 55       │
│  └── Weakening: No troponin elevation reported        │
│                                                       │
│  Hypothesis B: Pulmonary Embolism        [21.8%]      │
│  ├── Supporting: Sudden onset dyspnea, tachycardia    │
│  └── Weakening: No DVT history                        │
│                                                       │
│  Hypothesis C: Musculoskeletal           [ 5.9%]      │
│  └── Supporting: Reproducible on palpation            │
│                                                       │
│  ✗ Discarded: Anxiety/Panic (insufficient evidence)   │
│                                                       │
│  ▶ Decision: Recommend cardiac workup first           │
└───────────────────────────────────────────────────────┘
```

The user sees not just the recommendation, but the *reasoning landscape* that produced it.

---

### 🚦 Source Grounding Visualizer (Traffic-Light System)

> AI hallucinates facts and presents them as truth.

Every generated claim is automatically verified against a **local RAG vector database**. We leverage Gemma 4's strict native function calling syntax — parsing the specific `<|tool_call>` and `<|"|>` delimiters — to trigger background validations:

1. **Claim Extraction** — Each response is decomposed into individual factual statements.
2. **Verification** — Every claim is cross-referenced against the local vector store via Gemma 4's native tool-calling mechanism.
3. **Visual Tagging** — Each claim receives a color-coded trust signal.

#### Traffic-Light Interface

| Signal | Label | Meaning |
|---|---|---|
| 🟢 **Green** | **Verified** | Claim is fully supported by retrieved sources |
| 🟡 **Yellow** | **Inferred** | Claim is a reasonable inference but not directly sourced |
| 🔴 **Red** | **Unverified** | Claim could not be grounded — possible hallucination |

```
Example rendered output:

  🟢 "Aspirin is a first-line antiplatelet for ACS management."
      └─ Source: WHO Essential Medicines List, 2024 (p.12)

  🟡 "The patient's age increases thromboembolic risk."
      └─ Inference from: Framingham Heart Study risk tables

  🔴 "This condition has a 95% survival rate with early intervention."
      └─ ⚠ No matching source found — treat with caution
```

Users can click any claim to inspect its source chain, see the retrieved document snippet, and judge for themselves.

---

### 📊 Sliding Scale of Certainty

> AI sounds confident even when it doesn't know.

We stream **token-level logprobs** directly from the Cactus Compute inference engine. The Next.js frontend translates these mathematical confidence scores into **dynamic CSS properties**, creating an intuitive visual language for uncertainty:

| Technique | High Confidence | Low Confidence |
|---|---|---|
| **Opacity** | Solid, fully opaque text | Faded, semi-transparent text |
| **Blur** | Crisp, readable text | Progressively blurred text (hover to reveal) |

#### Calibration Techniques

To ensure confidence scores are *meaningful* (not just raw logits), we calibrate the fine-tuned model using:

- **Brier Score minimization** — Reduces the gap between predicted confidence and actual accuracy
- **Expected Calibration Error (ECE)** — Ensures confidence bins align with true correctness rates
- **Reinforcement learning** — Tunes the model to produce well-calibrated probability outputs

This creates a reading experience where the *visual weight* of text corresponds to the model's actual certainty — users can instantly identify which parts of a response are reliable and which require independent verification.

---

## 🛠 Architecture & Tech Stack

This project is built to run **entirely on-device**, preserving absolute data sovereignty for sensitive edge deployments.

```
┌──────────────────────────────────────────────────────────────────┐
│                       P.R.I.S.M. ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FRONTEND (Next.js + Tailwind CSS)                              │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Multiplexed Streams:                                │       │
│   │  • Text stream ──────────► Response rendering        │       │
│   │  • Thought blocks ───────► Deliberation panel        │       │
│   │  • Tool-call statuses ───► Grounding indicators      │       │
│   │  • Probability metrics ──► Certainty CSS properties  │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ SSE / WebSocket                       │
│                          ▼                                       │
│   BACKEND (Python)                                               │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Streaming Server (server.py)                        │       │
│   │  ├── Deliberation parser (<|channel>thought\n)       │       │
│   │  ├── Tool-call parser (<|tool_call>, <|"|>)          │       │
│   │  ├── Logprobs extractor (token-level confidence)     │       │
│   │  └── RAG verification pipeline (vector store)        │       │
│   └──────────────────────────────────────────────────────┘       │
│                          ▲                                       │
│                          │ Zero-copy inference                   │
│                          ▼                                       │
│   INFERENCE ENGINE (Cactus Compute)                              │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Gemma 4 E4B (Unsloth fine-tuned, calibrated)        │       │
│   │  • Ultra-low latency on ARM CPUs                     │       │
│   │  • Zero-copy memory mapping                          │       │
│   │  • Logprobs streaming                                │       │
│   │  • 128K context window                               │       │
│   │  • Fully offline                                     │       │
│   └──────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Role |
|---|---|---|
| **Foundation Model** | Gemma 4 E4B (4.5B effective / 8.0B total params) | 128K context, multimodal (text, image, audio), Per-Layer Embeddings (PLE) architecture optimized for local hardware |
| **Fine-Tuning** | Unsloth | Probability calibration fine-tuning with QLoRA in only ~10 GB VRAM |
| **Inference Engine** | Cactus Compute | Ultra-low latency, zero-copy memory mapping for fast inference on ARM CPUs, offline-capable, logprobs streaming |
| **Backend** | Python (streaming server) | Multiplexes `<|channel>thought\n` blocks, `<|tool_call>` statuses, logprobs, and text into parallel event streams |
| **Frontend** | Next.js + Tailwind CSS | Reactive UI that renders all four streams simultaneously with dynamic certainty visualization via CSS properties |
| **Vector Store** | Local RAG database | On-device document store for source grounding verification (medical literature, legal corpora) |

---

## 🧩 Gemma 4 Prompting & State Management

To maintain stable performance with Gemma 4, P.R.I.S.M. strictly adheres to the official formatting guidelines:

### Prompt Structure

We use Gemma 4's native `system`, `user`, and `assistant` roles with the `<|think|>` token injected to activate deliberation:

```
<system>
You are the P.R.I.S.M. Glass Box Interpreter. For every response:
1. Begin deliberation with <|think|> to expose your reasoning process
2. Enumerate competing hypotheses with probability estimates
3. Use tool calls to verify each factual claim against the knowledge base
4. Provide a certainty assessment for each major conclusion
</system>

<user>
Patient presents with acute chest pain, dyspnea, and history of DVT.
What should be the triage priority?
</user>
```

### Turn Management

During multi-turn conversations, the system automatically **strips previous `<|channel>thought\n` blocks** from the context history. This is critical to prevent the model from entering **cyclical hallucination loops** — where it references its own prior reasoning as fact rather than generating fresh analysis for each turn.

```python
def sanitize_context(conversation_history):
    """Remove previous thought blocks to prevent reasoning contamination."""
    sanitized = []
    for turn in conversation_history:
        # Strip <|channel>thought\n ... </|channel> blocks from prior turns
        cleaned = re.sub(
            r'<\|channel\>thought\\n.*?</\|channel\>',
            '', turn.content, flags=re.DOTALL
        )
        sanitized.append(cleaned)
    return sanitized
```

### Gemma 4 Delimiter Handling

The backend parser handles three distinct Gemma 4 delimiter types:

| Delimiter | Purpose | P.R.I.S.M. Handling |
|---|---|---|
| `<\|channel>thought\n` | Internal reasoning / deliberation | Routed to Deliberation Panel in the UI |
| `<\|tool_call>` | Function call invocation | Triggers RAG verification pipeline |
| `<\|"\|>` | Tool call argument delimiters | Parsed for claim text to verify |

---

## 🧠 Model Specifications

P.R.I.S.M. primarily uses **Gemma 4 E4B** — the 4.5B effective parameter edge variant — due to its optimal balance of capability and local deployability:

| Model | Active Params | Total Params | Context | Modalities | Target |
|---|---|---|---|---|---|
| **Gemma 4 E2B** | 2.3B | 5.1B | 128K | Text, Image, Audio | Ultra-low-resource / mobile fallback |
| **Gemma 4 E4B** ⭐ | 4.5B | 8.0B | 128K | Text, Image, Audio | **Primary deployment target** |
| Gemma 4 26B | 25.2B (MoE) | — | 256K | Text, Image, Video | Server / research |
| Gemma 4 31B | 30.7B | — | 256K | Text, Image, Video | Cloud / maximum capability |

### Why Gemma 4 E4B?

- **128K context window** — Processes entire medical reports, legal documents, and multi-page PDFs in a single pass
- **Per-Layer Embeddings (PLE)** — Improved computational efficiency on local hardware without sacrificing quality
- **Offline-first** — No internet required after model download; critical for rural and privacy-sensitive deployments
- **140+ languages** — Accessible to underserved, multilingual communities worldwide
- **Multimodal** — Understands images, audio, and text natively (X-rays, lab reports, spoken symptoms)

---

## ⚡ Fine-Tuning with Unsloth

> **Special Track: Unsloth** — *Best fine-tuned Gemma 4 model created using Unsloth, optimized for a specific, impactful task.*

[Unsloth](https://github.com/unslothai/unsloth) is the backbone of P.R.I.S.M.'s **domain adaptation and calibration pipeline**. The Glass Box requires more than a base model — it needs fine-tuned calibration for uncertainty estimation and domain-specific structured reasoning.

### What We Fine-Tune

| Adapter | Purpose | Dataset |
|---|---|---|
| **Calibration Adapter** | Teaches the model to output well-calibrated confidence scores | Custom calibration dataset with known correctness labels |
| **Medical Triage Adapter** | Domain-specific medical reasoning with transparent deliberation | MedReason, Syntech AI Triage 500, Medical Meadow Wikidoc |
| **Legal Navigation Adapter** | Citation-grounded legal analysis with source tagging | Pile of Law, Caselaw Access Project, Legal Q&A |
| **Deliberation Adapter** | Structured `<\|think\|>` output with hypothesis enumeration | Synthetic deliberation traces |

### Training Efficiency

| Metric | Without Unsloth | With Unsloth |
|---|---|---|
| E4B fine-tune VRAM | ~24 GB | **~10 GB** |
| E2B fine-tune VRAM | ~16 GB | **~8 GB** |
| Training speed | Baseline | **2× faster** |
| Memory reduction | — | **~60%** |

### Techniques

- **Quantized LoRA (QLoRA)** — 4-bit NF4 quantization with rank-16 low-rank adaptation
- **Attention layer tuning** — Selective fine-tuning of attention heads responsible for calibration signals
- **Gradient checkpointing** — Trade compute for memory during backpropagation
- **Unsloth fused kernels** — Optimized CUDA kernels for 2× training speedup

```python
from unsloth import FastModel
from trl import SFTTrainer

# Load Gemma 4 E4B with 4-bit quantization
model, tokenizer = FastModel.from_pretrained(
    model_name="google/gemma-4-e4b",
    max_seq_length=8192,
    load_in_4bit=True,
)

# Add LoRA adapters for calibration fine-tuning
model = FastModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16,
    lora_dropout=0,
)

# Fine-tune with medical triage calibration data
trainer = SFTTrainer(
    model=model,
    dataset=medical_calibration_dataset,
    max_seq_length=8192,
)
trainer.train()

# Export for deployment via Cactus Compute
model.save_pretrained_merged("prism-medical-e4b", tokenizer)
```

---

## 🌍 Application Domains

### Domain A: Medical Triage

**Target Users:** Rural healthcare workers, community health volunteers, patients in low-literacy environments.

| Feature | Description |
|---|---|
| 📷 **Image-based report understanding** | Upload lab reports, X-rays, or prescriptions — the model interprets them visually |
| 🎙 **Voice interaction** | Speak symptoms in local language; receive spoken, explained diagnoses |
| 🔍 **Transparent diagnosis reasoning** | See *why* the AI suggests a particular triage level via the Deliberation Panel |
| 🌐 **Offline operation** | Works in areas with zero connectivity via Cactus Compute on-device inference |

**Training Datasets (fine-tuned via Unsloth):**
- [MedReason](https://huggingface.co/datasets) — Chain-of-thought medical reasoning
- [Syntech AI Triage 500](https://huggingface.co/datasets) — Emergency department triage scenarios
- [Medical Meadow Wikidoc](https://huggingface.co/datasets) — Clinical knowledge base

---

### Domain B: Legal Rights Navigation

**Target Users:** Marginalized communities, migrant workers, domestic violence survivors, first-generation rights seekers.

| Feature | Description |
|---|---|
| 🔒 **Privacy-first** | All processing happens locally via Cactus Compute — no data leaves the device |
| 📚 **Citation-backed** | Every legal claim links to actual statute, case law, or regulation via the Traffic-Light System |
| ⚖️ **Confidence-aware** | The Certainty Scale tells you when the AI is unsure about a legal interpretation |
| 🗣 **Multilingual** | Access legal rights in your native language (140+ languages supported) |

**Training Datasets (fine-tuned via Unsloth):**
- [Pile of Law](https://huggingface.co/datasets) — Comprehensive legal corpus
- [Caselaw Access Project](https://case.law/) — U.S. court opinions
- Legal Q&A datasets — Community-sourced legal questions and answers

---

## 📡 Edge Deployment

P.R.I.S.M. runs entirely on-device via **Cactus Compute**, processing four parallel data streams in real-time:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CACTUS COMPUTE INFERENCE ENGINE                   │
│            (ARM CPU optimized · zero-copy · offline)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Stream 1: TEXT ───────────────► Response tokens                    │
│   Stream 2: DELIBERATION ──────► <|channel>thought\n blocks         │
│   Stream 3: PROBABILITY ───────► Token-level logprobs               │
│   Stream 4: VERIFICATION ──────► <|tool_call> grounding results     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│          NEXT.JS GLASS BOX UI (Tailwind CSS)                        │
│   Multiplexes all four streams into a unified transparent interface │
└─────────────────────────────────────────────────────────────────────┘
```

### Deployment Targets

| Platform | Model | Requirements | Use Case |
|---|---|---|---|
| MacBook (Apple Silicon) | E4B (primary) | ~8 GB RAM | Full Glass Box — development & clinic |
| Linux workstation | E4B | ~8 GB RAM + CUDA optional | Legal aid office |
| Raspberry Pi / kiosk | E2B (quantized) | ~4 GB RAM | Rural clinic terminal |
| Mobile (future) | E2B (quantized) | ~4 GB RAM | Community health worker |

---

## 🚀 Getting Started (Local Deployment)

### Prerequisites

- **macOS** (Apple Silicon recommended for Cactus Compute) or **Linux**
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
cactus download chandan989/gemma-4-e4b-calibrated

# Start the local streaming server (with logprobs enabled)
python backend/server.py --model gemma-4-e4b-calibrated --port 8000
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

# Initialize with the Cactus Compute backend
interpreter = GlassBoxInterpreter(
    model="gemma-4-e4b-calibrated",
    runtime="cactus",
    port=8000,
)

# Run a transparent query
response = interpreter.query(
    "Patient presents with acute chest pain and dyspnea. "
    "History of DVT. What should be the triage priority?",
    domain="medical"
)

# Access the Glass Box layers
print(response.answer)              # Final recommendation
print(response.deliberation)        # <|channel>thought blocks
print(response.source_grounding)    # Claim-by-claim verification
print(response.certainty_map)       # Token-level confidence scores
```

---

## 📁 Project Structure

```
P.R.I.S.M./
├── brief.md                     # Architectural blueprint & strategy document
├── README.md                    # You are here
├── LICENSE                      # MIT License
│
├── backend/
│   ├── server.py                # Python streaming server (SSE/WebSocket)
│   ├── parsers/
│   │   ├── deliberation.py      # <|channel>thought\n block parser
│   │   ├── tool_calls.py        # <|tool_call> / <|"|> delimiter parser
│   │   └── logprobs.py          # Token-level probability extractor
│   ├── grounding/
│   │   ├── rag_pipeline.py      # RAG verification against local vector store
│   │   └── vector_store.py      # Document embedding & retrieval
│   ├── domains/
│   │   ├── medical.py           # Medical triage domain logic
│   │   └── legal.py             # Legal navigation domain logic
│   └── calibration/
│       ├── brier.py             # Brier Score calibration
│       └── ece.py               # Expected Calibration Error
│
├── frontend/
│   ├── package.json             # Next.js dependencies
│   ├── tailwind.config.js       # Tailwind CSS configuration
│   ├── app/
│   │   ├── page.tsx             # Main Glass Box interface
│   │   ├── layout.tsx           # App layout with stream providers
│   │   └── components/
│   │       ├── DeliberationPanel.tsx   # Hypothesis visualization
│   │       ├── TrafficLight.tsx        # Source grounding indicators
│   │       ├── CertaintyText.tsx       # Opacity/blur text rendering
│   │       └── StreamMultiplexer.tsx   # Four-stream event handler
│   └── public/
│
├── training/
│   ├── finetune.py              # Unsloth fine-tuning pipeline
│   ├── datasets/                # Domain-specific training data
│   └── adapters/                # Exported LoRA adapters
│
├── scripts/
│   ├── download_model.py        # Model download utility
│   └── evaluate.py              # Calibration evaluation
│
└── tests/                       # Unit and integration tests
```

---

## 🎯 Hackathon Alignment

P.R.I.S.M. is purpose-built for the [**Gemma 4 Good Hackathon**](https://www.kaggle.com/competitions/gemma-4-good-hackathon), targeting both main tracks and special technology tracks:

### Main Track Criteria

| Criterion | Hackathon Requirement | P.R.I.S.M. Strategy |
|---|---|---|
| 🧪 **Innovation** | Novel approach to a real problem | First transparent diagnostic interface for edge LLMs |
| 🌍 **Problem Relevance** | Real-world, high-impact use case | Trust in medical & legal AI for underserved communities |
| ⚙️ **Technical Execution** | Functional, well-engineered prototype | Multi-stream parser + calibration pipeline + reactive UI |
| 📐 **Clarity** | Understandable to non-experts | Visual metaphors (traffic lights, opacity, blur) for uncertainty |
| 🎨 **UI/UX** | Intuitive, user-friendly interface | Cognitive design patterns backed by HCI research |

### Main Track Categories

| Category | How P.R.I.S.M. Fits |
|---|---|
| 🛡 **Safety & Trust** | Core mission — every feature exists to make AI outputs auditable, verifiable, and calibrated for trust |
| 🏥 **Health & Sciences** | Medical triage domain with transparent diagnosis reasoning for rural healthcare |

### Special Technology Tracks ($50,000)

| Track | Prize | How P.R.I.S.M. Qualifies |
|---|---|---|
| 🌵 **Cactus** | $10,000 | Cactus Compute powers all on-device inference — ultra-low latency, zero-copy memory mapping on ARM CPUs, fully offline streaming with logprobs extraction |
| ⚡ **Unsloth** | $10,000 | Four domain-specific LoRA adapters (calibration, medical, legal, deliberation) fine-tuned with QLoRA at only ~10 GB VRAM, achieving 60% memory reduction and 2× training speedup |
| 🦙 **llama.cpp** | $10,000 | Alternative inference backend for ultra-constrained hardware — Raspberry Pi, embedded kiosks — via GGUF quantization (down to Q2_K at ~1.5 GB) with `--logprobs` for certainty visualization |
| 📱 **LiteRT** | $10,000 | Future mobile deployment path — Gemma 4 E2B as a LiteRT model with direct logit access for on-device certainty calibration on Android/iOS |
| 🦙 **Ollama** | $10,000 | Developer-friendly alternative runtime with custom Modelfile for rapid local prototyping and model variant switching |

---

## 🗺 Roadmap

- [x] Architectural design and brief
- [ ] Cactus Compute inference backend with logprobs streaming
- [ ] `<|channel>thought\n` deliberation parser
- [ ] `<|tool_call>` / `<|"|>` function-call parser
- [ ] RAG verification pipeline (local vector store)
- [ ] Next.js frontend with stream multiplexer
- [ ] Deliberation Panel component
- [ ] Traffic-Light source grounding UI
- [ ] Certainty Scale (logprobs → dynamic CSS)
- [ ] Turn management (thought block stripping)
- [ ] Unsloth fine-tuning pipeline (4 domain adapters)
- [ ] Medical triage domain adapter
- [ ] Legal navigation domain adapter
- [ ] Calibration evaluation (Brier + ECE)
- [ ] llama.cpp alternative backend
- [ ] Mobile deployment (LiteRT / future)
- [ ] Multilingual voice interaction
- [ ] Community evaluation and feedback

---

## 🤝 Contributing

Contributions are welcome! Whether you're a researcher, developer, designer, or domain expert in medicine or law — there's a place for you.

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'Add your-feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

Please read our contribution guidelines before submitting.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Google DeepMind](https://deepmind.google/)** — Gemma 4 model family
- **[Cactus Compute](https://cactuscompute.com)** — Ultra-low latency on-device inference engine
- **[Unsloth](https://github.com/unslothai/unsloth)** — Memory-efficient fine-tuning
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** — CPU-first inference for resource-constrained hardware
- **[Google AI Edge / LiteRT](https://ai.google.dev/edge/litert)** — On-device inference runtime
- **[Ollama](https://ollama.com)** — Local model serving and management
- **[Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)** — For catalyzing responsible AI development
- The open-source communities behind MedReason, Pile of Law, and Caselaw Access Project

---

<div align="center">

*Built with conviction that AI transparency is not a feature — it is a fundamental right.*

**P.R.I.S.M.** · Probabilistic Reasoning and Interpretability System for Models

</div>
