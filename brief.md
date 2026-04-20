# The Glass Box Interpreter

### Architectural Blueprint and Strategic Evaluation for the Gemma 4 Good Hackathon 

---

## Introduction: The Paradigm Shift Toward Transparent Artificial Intelligence

The deployment of large language models in high-stakes medical environments has been limited by their inherent opacity.

Traditional AI systems:

* Provide **assertive outputs**
* Hide **probabilistic reasoning**
* Obscure **uncertainty and source provenance**

This leads to:

* Increased hallucination risk
* Reduced clinician trust
* Poor suitability for high-accountability triage decisions

### The Glass Box Concept

The **Glass Box Interpreter** introduces a new paradigm:

> AI behaves like a **transparent system**, exposing its reasoning, uncertainty, and sources.

Instead of acting as a black-box oracle, it becomes:

* A **diagnostic overlay** for clinical reasoning
* A **collaborative triage assistant** that shows its work

### One User, One Workflow

The Glass Box targets a **single, specific user**: the **community health worker (CHW)** conducting medical triage in a rural or resource-limited clinic, offline, with limited formal medical training.

The **single workflow**: Patient walks in → CHW enters symptoms (voice or text) → Glass Box provides a triage recommendation → CHW sees *why* the AI reached that conclusion and *how confident* it is → CHW makes an informed decision.

---

## Strategic Alignment with the Gemma 4 Good Hackathon

The hackathon emphasizes:

* Real-world impact
* Technical depth
* Trust and explainability
* Offline-first systems

### Glass Box Alignment

| Criterion           | Requirement             | Glass Box Strategy                          |
| ------------------- | ----------------------- | ------------------------------------------- |
| Innovation          | Novel approach          | Transparent diagnostic interface for triage |
| Problem Relevance   | Real-world impact       | Trust in medical AI for underserved clinics |
| Technical Execution | Functional prototype    | Tool invocation + calibration pipeline      |
| Clarity             | Understandable solution | Accessible confidence indicators            |
| UI/UX               | User-friendly           | Progressive disclosure — simple by default  |

---

## The Imperative for Gemma 4 Edge Architecture

The system uses **Gemma 4 E4B** as its primary model because:

* Designed for **edge deployment**
* Supports **128K context** (used adaptively: 8K on edge, full 128K on workstation)
* Works **offline**
* Provides **multilingual capability (140+ languages)**

### Key Advantage: Per-Layer Embeddings

* Improves efficiency on constrained hardware
* Maintains high performance on ARM CPUs

---

## Model Specifications

| Model       | Parameters        | Context | Modalities         | Role in P.R.I.S.M.       |
| ----------- | ----------------- | ------- | ------------------ | ------------------------- |
| Gemma 4 E2B | 2.3B (5.1B total) | 128K    | Text, Image, Audio | Ultra-constrained fallback |
| Gemma 4 E4B | 4.5B (8.0B total) | 128K    | Text, Image, Audio | **Primary deployment**    |

### Adaptive Context Window Strategy

The 128K context window is a *maximum capability*, not a runtime constant. P.R.I.S.M. uses adaptive context sizing based on hardware:

| Deployment Target    | Effective Context | Rationale                                     |
| -------------------- | ----------------- | --------------------------------------------- |
| Constrained edge     | 4K–8K             | Sufficient for triage questionnaire + history |
| Laptop / clinic PC   | 16K–32K           | Handles multi-page lab reports                |
| Workstation / server | Up to 128K        | Full medical record analysis                  |

This prevents the latency and memory problems that would result from naively loading 128K context on a Raspberry Pi or low-RAM ARM device.

---

## Architectural Pillar I: Latent Deliberation Engine

### Problem

AI hides internal reasoning.

### Solution

Expose **internal thought process** using:

```
<|think|>
```

The UI intercepts `<|channel>thought\n` text blocks and presents them through **progressive disclosure** — not raw dumps.

### Progressive Disclosure Design

The deliberation engine has **two modes**, controlled by a single toggle:

1. **Simple View (Default):** The CHW sees only a clean triage recommendation with a confidence badge. No raw reasoning is shown. This is the view optimized for low-literacy, high-stress triage environments.

2. **Expert View (On Demand):** A supervising clinician or trained CHW can toggle to see the full deliberation: competing hypotheses, probability weights, and discarded reasoning paths.

### Example (Expert View)

**Medical Scenario:**

* Hypothesis A: Cardiac Ischemia — 72.3%
* Hypothesis B: Pulmonary Embolism — 21.8%
* Hypothesis C: Musculoskeletal — 5.9%

Displayed as:

* Visual branching diagram
* Probability-weighted reasoning
* Discarded hypotheses greyed out

### Example (Simple View — Default)

```
┌─────────────────────────────────────────────────┐
│  🔴 HIGH PRIORITY — Refer to physician urgently │
│                                                  │
│  Suspected: Cardiac event                       │
│  Confidence: ████████░░ HIGH                    │
│                                                  │
│  [Why?]  ← tap to expand reasoning              │
└─────────────────────────────────────────────────┘
```

---

## Architectural Pillar II: Source Grounding Visualizer

### Problem

AI hallucinates facts.

### Solution

Claim-by-claim verification pipeline using Gemma 4's native function calling (`<|tool_call>` and `<|"|>` delimiters):

#### Step 1: Claim Extraction

Break responses into:

* Individual factual statements

#### Step 2: Verification

Compare against:

* Local RAG vector database (medical literature, WHO guidelines)
* On-device clinical knowledge base

---

### Traffic-Light Interface

| Color     | Meaning                   |
| --------- | ------------------------- |
| 🟢 Green  | Fully verified            |
| 🟡 Yellow | Inference                 |
| 🔴 Red    | Unverified / hallucinated |

Claims are shown as **inline badges** next to each statement — not complex expandable panels. The CHW sees green/yellow/red dots; tapping a dot shows the source in a simple popup.

---

## Architectural Pillar III: Sliding Scale of Certainty

### Problem

AI sounds confident even when uncertain.

### Solution

Expose **token-level probability** via logprobs from the inference engine.

### Calibration Techniques

* Brier Score minimization
* Expected Calibration Error
* Reinforcement learning fine-tuning

---

### Accessible Visual Representation

**Previous approach (REMOVED — accessibility anti-pattern):**
~~Blur/fade text to show low confidence.~~ This was dropped because:
* Blurred text is unreadable in harsh lighting (field clinics)
* Faded text fails for users with visual impairments
* Low-literacy users cannot interpret opacity as a confidence signal

**New approach — Explicit Confidence Indicators:**

1. **Confidence Badges**

   * ✅ `HIGH CONFIDENCE` — solid green border, bold text
   * ⚠️ `MODERATE` — amber border, normal text
   * ❓ `LOW CONFIDENCE — verify independently` — red border, warning icon

2. **Progress Bar**

   * Visual fill bar (████████░░) next to each claim
   * Universally understandable regardless of literacy level

3. **Plain-Language Labels**

   * "The AI is confident about this"
   * "The AI is somewhat sure — double-check"
   * "The AI is guessing — do not rely on this alone"

4. **Audio Feedback (Voice Mode)**

   * Spoken confidence level alongside the recommendation
   * Tone and pacing vary with confidence level

---

## Optimization Strategy: Unsloth

* Reduces memory usage by ~60%
* Enables training on:

  * 8GB (E2B)
  * 10GB (E4B)

### Techniques Used

* Quantized LoRA (QLoRA) — 4-bit NF4 quantization
* Attention layer tuning for confidence calibration
* Gradient checkpointing

---

## Application Domain: Medical Triage

> **One user. One workflow. One domain.**

### Target User

The **Community Health Worker (CHW)** — a frontline healthcare provider in a rural or resource-limited setting, often with limited formal medical training, working offline.

### The Workflow

```
Patient arrives
    ↓
CHW enters symptoms (voice or text, local language)
    ↓
Glass Box processes via Gemma 4 E4B (on-device, offline)
    ↓
Simple View shows:
  • Triage level (🔴 Urgent / 🟡 Semi-urgent / 🟢 Routine)
  • Top suspected condition with confidence badge
  • Source verification dots (green/yellow/red)
    ↓
CHW makes informed referral decision
    ↓
[Optional] Supervising clinician reviews Expert View remotely
```

### Features

* Image-based report understanding (X-rays, lab reports)
* Voice interaction in local language (140+ languages)
* Transparent diagnosis reasoning via progressive disclosure
* Fully offline operation via Cactus Compute

### Datasets Used (Fine-Tuned via Unsloth)

* MedReason — Chain-of-thought medical reasoning
* Syntech AI Triage 500 — Emergency department triage scenarios
* Medical Meadow Wikidoc — Clinical knowledge base

### Future Domain Expansion

Legal rights navigation for marginalized communities is a natural future extension of the Glass Box framework, leveraging the same transparency pillars with domain-specific fine-tuning. This is explicitly out of scope for the hackathon submission to maintain focus.

---

## Edge Deployment Architecture

### Key Components

1. **Cactus Compute Inference Engine**

   * Ultra-low latency on ARM CPUs
   * Zero-copy memory mapping
   * Logprobs streaming for confidence extraction
   * Fully offline

2. **Streaming Pipeline**

   * Real-time response rendering via SSE/WebSocket

---

### Adaptive Stream Strategy

Not all four data streams run simultaneously on all hardware. The system gracefully degrades:

| Hardware Tier       | Active Streams                          | Latency Target |
| ------------------- | --------------------------------------- | -------------- |
| Constrained (RPi)   | Text + Certainty only                  | < 3s first token |
| Laptop / clinic PC  | Text + Certainty + Verification        | < 1s first token |
| Workstation / server | All four (+ Deliberation)              | < 500ms first token |

On constrained hardware:
* Deliberation stream is **disabled by default** (Expert View unavailable)
* Source verification runs **asynchronously after response** (badges appear with slight delay)
* Context window is capped at 4K–8K tokens

This ensures the CHW always gets a fast, actionable triage recommendation — even on a Raspberry Pi.

---

## Final Insight

The **Glass Box Interpreter** transforms AI from:

> ❌ Black-box authority
> ✅ Transparent collaborator

For one specific user — the community health worker — it enables:

* **Trust** through visible reasoning
* **Safety** through source verification
* **Accessibility** through progressive disclosure and explicit confidence indicators
* **Reliability** through honest hardware adaptation
