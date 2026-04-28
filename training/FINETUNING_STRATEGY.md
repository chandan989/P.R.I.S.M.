# P.R.I.S.M. Fine-Tuning Strategy Research

## Objective
To determine the optimal fine-tuning methodology for the **Gemma 4 A4B (26B MoE)** model to achieve structured deliberation (`<|think|>` block hypothesis enumeration) and calibrated confidence scores, while strictly adhering to the **16GB VRAM hardware constraint** specified in the P.R.I.S.M. architecture.

---

## 1. Candidate Methodologies

### Method A: Supervised Fine-Tuning (SFT)
*The traditional approach of training the model on high-quality pairs of (Prompt → Ideal Reasoning Trace + Final Answer).*

* **Pros:**
  * **Absolute Memory Efficiency:** Calculates gradients for a single forward pass per prompt. This is the **most VRAM-efficient method available**, allowing a heavily quantized 26B MoE model to fit comfortably within the 16GB target alongside an 8192-token sequence length.
  * **Direct Format Enforcement:** Highly effective at teaching structured syntax (e.g., specific JSON-like delimiters, bullet points, tool calls).
* **Cons:**
  * **No Explicit Penalization:** Does not actively penalize the model if it occasionally reverts to its pre-trained "black box" behavior (answering without thinking). It relies entirely on the density of the training data.

### Method B: Odds Ratio Preference Optimization (ORPO)
*A monolithic preference optimization technique that combines instruction tuning and alignment by providing a "chosen" (reasoned) and "rejected" (unreasoned) pair without requiring a reference model.*

* **Pros:**
  * **Behavioral Alignment:** Explicitly penalizes the base model's tendency to give authoritative, black-box answers. Actively teaches the model *not* to skip the `<|think|>` block.
  * **No Reference Model:** Unlike DPO, it doesn't require loading a frozen copy of the model, saving ~50% VRAM compared to traditional alignment.
* **Cons:**
  * **Double Activation Cost:** Processes two completions (Chosen + Rejected) per prompt simultaneously. While it avoids a reference model, the doubled sequence processing drastically increases the activation memory overhead.
  * **Hardware Risk:** When dealing with a 26B parameter model and an 8192 sequence length, the VRAM spike from processing dual completions is highly likely to **breach the strict 16GB VRAM ceiling**, leading to Out-Of-Memory (OOM) failures on consumer hardware.

### Method C: Direct Preference Optimization (DPO)
*Traditional preference learning using paired chosen/rejected responses.*

* **Pros:** Mathematically robust alignment.
* **Cons:** Requires a frozen reference model in memory. Even with Unsloth and 4-bit quantization, running two 26B models concurrently is **impossible on 16GB VRAM**.

### Method D: Group Relative Policy Optimization (GRPO)
*DeepSeek's RL approach for reasoning models that evaluates multiple completions against a reward function without a critic model.*

* **Pros:** Highly effective for deep reasoning and math logic.
* **Cons:** Requires complex reward function engineering (verifying clinical truth mathematically is difficult) and generates multiple rollouts simultaneously, which is computationally prohibitive on a single consumer GPU.

---

## 2. Architectural Constraints Analysis

The fundamental constraint of the P.R.I.S.M. architecture is **Zero-Data-Egress Local Execution on Clinical Workstations (16GB VRAM)**. 

To fine-tune the Gemma 4 A4B 26B MoE model:
1. **Base Weights:** ~14GB in 4-bit quantization.
2. **LoRA Adapters:** ~500MB (r=16 across Q, K, V, O projections).
3. **KV Cache & Activations (8192 Context):** ~1-1.5GB for a single forward/backward pass (SFT).

If we use **ORPO**, the activation memory required for the completion phase effectively doubles because it processes the `chosen` and `rejected` traces simultaneously. This pushes the total VRAM footprint to an estimated **17.5GB - 19GB**, immediately causing an OOM error on standard 16GB hardware (like Apple Silicon base models, RTX 4070, or Kaggle's free T4 GPUs).

---

## 3. Finalized Decision: Distilled Supervised Fine-Tuning (SFT)

Based on the hardware constraints and architectural design, **Supervised Fine-Tuning (SFT) via Unsloth is the strictly correct and finalized method.**

### Why SFT Wins for P.R.I.S.M.:
1. **Guaranteed 16GB VRAM Compliance:** By relying solely on high-quality instruction-response pairs, the activation memory is halved compared to ORPO, keeping the training safely within the hardware target.
2. **MoE Adaptability:** Mixture of Expert models are highly responsive to structural SFT. Because the model already possesses 26B parameters of latent medical knowledge, we are not teaching it *facts*, we are teaching it *syntax* (the deliberation trace). SFT is highly efficient at enforcing syntax.
3. **Alignment with README:** The established architecture explicitly defines an `SFTTrainer` pipeline to generate the **Deliberation Format Adapter**.
4. **Data Quality over Preference:** For clinical polypharmacy auditing, explicitly showing the model the correct logical chain (Drug A → Pathway B → Interaction C) is far more effective than just penalizing a bad answer. High-quality SFT data acts as an "expert demonstration" rather than a "preference alignment".

### Implementation Strategy
The existing `finetune.py` and `P_R_I_S_M_Unsloth_Finetuning.ipynb` scripts correctly implement the SFT methodology using Unsloth's highly optimized 4-bit loading, LoRA projections, and exact prompt templating, guaranteeing safe execution on consumer hardware.
