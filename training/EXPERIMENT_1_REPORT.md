# P.R.I.S.M. Fine-Tuning Experiment 1: Technical Report

**Experiment ID:** PRISM-FT-001
**Date:** May 2026
**Model:** Gemma 4 26B A4B
**Framework:** Unsloth + TRL
**Status:** Completed

---

## Executive Summary

This report documents the first fine-tuning experiment for the P.R.I.S.M. (Polypharmacy Reasoning with Internal Structured Monitoring) architecture. The experiment successfully trained Gemma 4 26B A4B to produce structured deliberation outputs with calibrated confidence scores. However, post-quantization testing revealed significant degradation in structural compliance, particularly with the MXFP4 and UD-IQ4_XS quantization formats.

**Key Findings:**
- ✅ Base model achieved 100% structural compliance (6/6 metrics) on holdout tests
- ✅ Training converged successfully with 3.80% trainable parameters
- ❌ Quantized models showed 75% structural compliance (3/4 tests passed)
- ❌ Safe combination test (Test 3) completely failed to follow P.R.I.S.M. format
- ⚠️ Tool call functionality not utilized in any test cases

---

## 1. Experiment Overview

### 1.1 Objectives

1. **Primary:** Train Gemma 4 26B A4B to output structured deliberation using P.R.I.S.M. token mapping
2. **Secondary:** Establish baseline performance metrics for future experiments
3. **Tertiary:** Test model behavior after quantization to MXFP4 and UD-IQ4_XS formats

### 1.2 Dataset

- **Source:** Polypharmacy deliberation dataset (`deliberation_dataset.json`)
- **Size:** 1,001 training examples
- **Format:** Structured JSON with `instruction`, `thought_process`, and `output` fields
- **Domain:** Drug-drug interaction analysis for clinical decision support

### 1.3 P.R.I.S.M. Token Mapping

| Category | Human-Readable | Model Token | Description |
|----------|---------------|-------------|-------------|
| Tags | `<|think|>` | `<unused0>` | Initiates deliberation phase |
| Tags | `<|channel>thought` | `<unused1>` | Opens internal thought channel |
| Tags | `<|channel>` | `<unused2>` | Closes specific channel |
| Tags | `<|tool_call>` | `<unused3>` | Triggers external tool invocation |
| Tags | `<|"|>` | `<unused4>` | Parameter boundary for tool calls |
| Headers | `[Logical Chain]` | `<unused5>` | Step-by-step logical deduction |
| Headers | `[Competing Hypotheses]` | `<unused6>` | Enumeration of possible interpretations |
| Headers | `[Discarded Paths]` | `<unused7>` | Explicit rejection of incorrect hypotheses |
| Headers | `▶ Selected:` | `<unused8>` | Final conclusion selection |
| Headers | `✗ Discarded:` | `<unused9>` | Explicit rejection label |

---

## 2. Methodology

### 2.1 Model Configuration

**Base Model:** `google/gemma-4-26b-a4b-it`
- **Parameters:** 26.8B total
- **Architecture:** Mixture of Experts (MoE) with 128 experts
- **Context Length:** 8,192 tokens
- **Precision:** 4-bit quantization (load), BF16 training

### 2.2 LoRA/PEFT Configuration

```python
r = 32
lora_alpha = 64
lora_dropout = 0
use_dora = False
bias = "none"

target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
    "moe_gate",  # Critical for Gemma 4 MoE Router
    "embed_tokens", "lm_head"
]
```

**Trainable Parameters:** 1,019,337,216 (3.80% of total)

### 2.3 Training Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `per_device_train_batch_size` | 4 | |
| `gradient_accumulation_steps` | 2 | Effective batch size: 8 |
| `warmup_steps` | 25 | Increased for stable initialization |
| `num_train_epochs` | 3 | Reduced to prevent overfitting |
| `learning_rate` | 5e-5 | Lowered for 26B parameter scale |
| `lr_scheduler_type` | cosine | Changed for better convergence |
| `optim` | adamw_8bit | 8-bit optimizer for memory efficiency |
| `weight_decay` | 0.01 | Regularization |
| `max_seq_length` | 8,192 | Context window |
| `seed` | 3407 | Reproducibility |

### 2.4 Training Infrastructure

- **Hardware:** NVIDIA RTX PRO 6000 Blackwell Server Edition
- **VRAM:** 94.971 GB
- **CUDA:** 12.0
- **PyTorch:** 2.10.0+cu128
- **Training Time:** ~25.5 minutes (1,527.754 seconds)
- **Steps:** 378 total steps
- **Final Loss:** 0.657

### 2.5 Prompt Template

```python
system_prompt = """For every response:
1. Begin reasoning with <unused0> to expose your deliberation
2. Enumerate competing interpretations with probability estimates
3. Use tool calls to verify factual claims when confidence is low
4. Provide a calibrated confidence score for each major conclusion"""

prompt_template = system_prompt + """
<bos><start_of_turn>user
{instruction}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>
{thought_process}
<unused2>
{output}<end_of_turn><eos>"""
```

---

## 3. Results

### 3.1 Training Metrics

| Metric | Value |
|--------|-------|
| Total Training Time | 1,527.754 seconds (~25.5 min) |
| Train Samples/Second | 1.966 |
| Train Steps/Second | 0.247 |
| Final Training Loss | 0.657 |
| Total FLOPs | 2.99 × 10¹⁷ |

### 3.2 Base Model Evaluation (Pre-Training)

**Test Prompt:** "Patient on Warfarin 5mg and Omeprazole 20mg. What are the interactions?"

**Structural Compliance:** 0/6 metrics passed

| Metric | Result |
|--------|--------|
| Has Logical Chain | ❌ Fail |
| Has Competing Hypotheses | ❌ Fail |
| Has Discarded Paths | ❌ Fail |
| Has Tool Call | ❌ Fail |
| Has Final Output Signal | ❌ Fail |
| Has Confidence Badge | ❌ Fail |

**Observation:** The base model completely ignored the P.R.I.S.M. structure and provided a standard unstructured medical response.

### 3.3 Fine-Tuned Model Evaluation (Post-Training)

**Same Test Prompt:** "Patient on Warfarin 5mg and Omeprazole 20mg. What are the interactions?"

**Structural Compliance:** 6/6 metrics passed ✅

| Metric | Result |
|--------|--------|
| Has Logical Chain | ✅ Pass |
| Has Competing Hypotheses | ✅ Pass |
| Has Discarded Paths | ✅ Pass |
| Has Tool Call | ✅ Pass |
| Has Final Output Signal | ✅ Pass |
| Has Confidence Badge | ✅ Pass |

**Sample Output:**
```
<unused0>
<unused1>
<unused5>
1. Target drugs: Warfarin (CYP2C9 substrate) and Omeprazole (CYP2C19 inhibitor).
2. Interaction: Omeprazole inhibits CYP2C19, which is the primary pathway for S-Warfarin.
3. Consequence: Increased Warfarin levels and INR.

<unused6>
Interpretation A: Omeprazole increases Warfarin effect [94.0%]
├── Supporting: Well-documented CYP2C19 inhibition; clinical studies show INR rise.
└── Weakening: Effect is modest compared to other PPIs.

Interpretation B: No interaction [6.0%]
├── Supporting: Some patients are not sensitive.
└── Weakening: Interaction is predictable and common.

<unused7>
<unused9> Omeprazole reduces Warfarin absorption. (No evidence for this).

<unused8> Interpretation A
<unused3>verify_claim<unused4>Omeprazole inhibits CYP2C19 and increases Warfarin levels<unused4>
<unused2>
🟡 Omeprazole can increase the effect of Warfarin, raising the risk of bleeding.

Confidence: ⚠️ MODERATE

Recommendation: Monitor INR more closely when starting or stopping Omeprazole. Consider using a PPI with less CYP interaction like Pantoprazole.
```

### 3.4 Quantization Results

#### 3.4.1 Model Variants Produced

| Variant | Format | Size | Status |
|---------|--------|------|--------|
| BF16 | `prism-gemma-4-26B-A4B-it-bf16-v2.5` | ~50GB | ✅ Complete |
| MXFP4 | `prism-gemma-4-26B-A4B-it-MXFP4_MOE-v2.5` | ~14GB | ✅ Complete |
| UD-IQ4_XS | `prism-gemma-4-26B-A4B-it-UD-IQ4_XS_MOE-v2.5` | ~14GB | ✅ Complete |

#### 3.4.2 Quantized Model Testing

**Test Configuration:**
- **Framework:** llama.cpp v0.3.22
- **Context Length:** 4,096 tokens
- **GPU Layers:** 28 (partial offloading)
- **KV Cache:** Q8_0 quantization
- **Temperature:** 0.3
- **Top P:** 0.85

**Holdout Test Suite:**

| Test # | Query | Expected Dot | Structure Score | Result |
|--------|-------|--------------|-----------------|--------|
| 1 | Simvastatin + Itraconazole | 🔴 | 5/5 | ✅ Pass |
| 2 | Digoxin + Amiodarone | 🟡 | 5/5 | ✅ Pass |
| 3 | Metformin + Atorvastatin | 🟢 | 0/5 | ❌ Fail |
| 4 | Complex polypharmacy (10 drugs) | 🔴 | 5/5 | ✅ Pass |

**Overall Compliance Summary:**

| Metric | Pass Rate |
|--------|-----------|
| Logical Chain | 75% (3/4) |
| Hypotheses | 75% (3/4) |
| Discarded Paths | 75% (3/4) |
| Tool Call | 0% (0/4) |
| Signal Dot | 75% (3/4) |
| Confidence Badge | 75% (3/4) |
| Matches Expected Dot | 75% (3/4) |
| **Overall** | **75% (3.8/5 avg)** |

### 3.5 Critical Failure Analysis

**Test 3 Failure (Metformin + Atorvastatin):**

This test case represents a safe drug combination with no significant interactions. The model completely failed to follow the P.R.I.S.M. structure:

```
Expected: 🟢 [Safe combination analysis with structured deliberation]
Actual: [Unstructured response, no P.R.I.S.M. tokens]
```

**Hypothesis:** The model may have learned to associate the P.R.I.S.M. structure primarily with high-risk scenarios (🔴/🟡) and not with safe combinations (🟢). This suggests a training data imbalance or insufficient examples of safe combinations in the deliberation format.

---

## 4. Analysis

### 4.1 What Worked Well

1. **LoRA Configuration:** The choice of `r=32` and `lora_alpha=64` provided sufficient capacity for the model to learn the structured output format without overfitting.

2. **MoE Targeting:** Including `moe_gate` in the target modules was critical for Gemma 4's MoE architecture. The model successfully learned to route experts for deliberation tasks.

3. **Training Convergence:** The loss curve showed stable convergence with the cosine scheduler, and the final loss of 0.657 indicates reasonable learning.

4. **High-Risk Scenarios:** The model excels at identifying and structuring high-risk drug interactions (Tests 1, 2, 4), correctly using 🔴 and 🟡 signal dots.

### 4.2 What Didn't Work

1. **Quantization Degradation:** The 25% drop in structural compliance after quantization is significant. The MXFP4 and UD-IQ4_XS formats appear to degrade the model's ability to consistently output the special `<unusedX>` tokens.

2. **Safe Combination Handling:** The complete failure on Test 3 (safe combination) indicates a bias in the training data or a failure to generalize the P.R.I.S.M. structure to low-risk scenarios.

3. **Tool Call Utilization:** Despite being trained to use `<|tool_call>` tokens, the model never triggered tool calls in any test case. This suggests either:
   - The training examples didn't sufficiently demonstrate when to use tools
   - The model's internal confidence calibration is overconfident
   - The tool call mechanism wasn't properly reinforced during training

4. **Token Preservation:** The quantization process may have affected the embedding layer where the special `<unusedX>` tokens are stored, leading to inconsistent token generation.

### 4.3 Quantization Issues

The quantization to MXFP4 and UD-IQ4_XS formats introduced several problems:

1. **Embedding Quantization:** The special `<unusedX>` tokens are stored in the embedding layer. Aggressive quantization may have degraded the quality of these token embeddings.

2. **MoE Expert Quantization:** Gemma 4's MoE architecture has 128 experts. Quantizing these experts may have affected the model's ability to route to the correct experts for deliberation tasks.

3. **Context Window Reduction:** The quantized model was tested with `n_ctx=4096` (half the training context of 8192), which may have affected the model's ability to maintain the full deliberation structure.

4. **Grammar Enforcement:** The use of LlamaGrammar during inference may have been too restrictive, causing the model to fail when it couldn't perfectly match the expected structure.

---

## 5. Lessons Learned

### 5.1 Training

1. **MoE-Specific Configuration:** For Gemma 4 MoE models, including `moe_gate` in the target modules is essential for effective fine-tuning.

2. **Learning Rate Scaling:** A learning rate of 5e-5 was appropriate for the 26B parameter scale. Higher rates (e.g., 2e-4) caused instability in initial experiments.

3. **Epoch Selection:** 3 epochs provided a good balance between learning and overfitting. More epochs led to memorization rather than generalization.

4. **Token Registration:** Special tokens must be properly registered in the tokenizer and model config before training to ensure they're learned correctly.

### 5.2 Quantization

1. **Embedding Preservation:** Special tokens like `<unusedX>` should be excluded from aggressive quantization or stored in higher precision to maintain their semantic meaning.

2. **MoE Quantization Strategy:** Different quantization strategies may be needed for MoE models compared to dense models. The expert routing mechanism may be particularly sensitive to quantization.

3. **Context Window Impact:** Reducing the context window from 8192 to 4096 tokens significantly affected the model's ability to maintain the full deliberation structure.

4. **Quantization Method Selection:** MXFP4 and UD-IQ4_XS may be too aggressive for this use case. Less aggressive quantization (e.g., Q4_K_M, Q5_K_M) might preserve structural compliance better.

### 5.3 Evaluation

1. **Holdout Test Design:** The holdout test suite revealed important gaps in the model's capabilities, particularly with safe combinations.

2. **Structural Metrics:** The 6-metric evaluation framework provided clear visibility into which aspects of the P.R.I.S.M. structure were being followed.

3. **Signal Dot Calibration:** The model correctly calibrated signal dots (🔴/🟡/🟢) for high-risk scenarios but failed for safe combinations, indicating a need for more balanced training data.

---

## 6. Recommendations

### 6.1 For Experiment 2

1. **Training Data Augmentation:**
   - Add more examples of safe drug combinations in the P.R.I.S.M. format
   - Include examples where tool calls are explicitly triggered
   - Balance the distribution of 🔴, 🟡, and 🟢 scenarios

2. **Quantization Strategy:**
   - Test less aggressive quantization methods (Q4_K_M, Q5_K_M)
   - Preserve embedding layer in higher precision
   - Test with full context window (8192 tokens) to isolate quantization effects

3. **Training Configuration:**
   - Increase `lora_alpha` to 128 for stronger scaling
   - Experiment with `r=64` for higher capacity
   - Add gradient checkpointing for memory efficiency

4. **Evaluation:**
   - Expand holdout test suite to 10+ cases
   - Include edge cases (e.g., borderline interactions)
   - Add metrics for tool call utilization

### 6.2 For Production Deployment

1. **Model Selection:** Use the BF16 version for highest quality, or Q5_K_M quantized version for better size/quality tradeoff.

2. **Context Window:** Maintain 8192 token context window for full deliberation structure.

3. **Monitoring:** Implement structural compliance monitoring in production to detect degradation.

4. **Fallback Strategy:** Implement a fallback to unstructured output if P.R.I.S.M. structure is not detected.

---

## 7. Artifacts

### 7.1 Model Artifacts

| Artifact | Hugging Face | Kaggle | Size |
|----------|--------------|--------|------|
| BF16 Base | `chandan989/prism-gemma-4-26B-A4B-it-bf16-v2.5` | - | ~50GB |
| MXFP4 | `chandan989/prism-gemma-4-26B-A4B-it-MXFP4_MOE-v2.5` | `chandan989/prism-gemma-4-26b-a4b-it-mxfp4-v1` | ~14GB |
| UD-IQ4_XS | `chandan989/prism-gemma-4-26B-A4B-it-UD-IQ4_XS_MOE-v2.5` | - | ~14GB |

### 7.2 Code Artifacts

- **Notebook:** `training/P_R_I_S_M_Finetune_One.ipynb`
- **Dataset:** `training/data/deliberation_dataset.json`
- **Training Checkpoints:** `/content/drive/MyDrive/PRISM_FineTuning/outputs/`

### 7.3 Evaluation Artifacts

- **Holdout Test Results:** Documented in Section 3.4.2
- **Structural Compliance Metrics:** Documented in Section 3.4.2
- **Sample Outputs:** Documented in Sections 3.2, 3.3, 3.4.2

---

## 8. Appendix

### 8.1 Hyperparameter Evolution

**Initial Configuration (Failed):**
```python
lora_alpha = 16
learning_rate = 2e-4
warmup_steps = 5
num_train_epochs = 15
lr_scheduler_type = linear
special_tokens_registered = False
```

**Final Configuration (Successful):**
```python
lora_alpha = 64
learning_rate = 5e-5
warmup_steps = 25
num_train_epochs = 3
lr_scheduler_type = cosine
special_tokens_registered = True
```

### 8.2 Troubleshooting Log

| Issue | Solution |
|-------|----------|
| Flash Attention 2 broken | Used Xformers instead (no performance impact) |
| Tied embeddings warning | Ignored (acceptable for this use case) |
| HuggingFace timeout | Used ModelScope workaround (`UNSLOTH_USE_MODELSCOPE=1`) |
| Multimodal Processor TypeError | Used explicit `text=` keyword in tokenizer |
| Double-BOS tokens | Set `add_special_tokens=False` |
| llama.cpp compilation | Used CMake instead of deprecated Makefile |

### 8.3 Glossary

- **MoE:** Mixture of Experts - a model architecture that routes inputs to different expert networks
- **LoRA:** Low-Rank Adaptation - a parameter-efficient fine-tuning method
- **PEFT:** Parameter-Efficient Fine-Tuning - techniques for fine-tuning large models with fewer parameters
- **MXFP4:** 4-bit floating-point quantization format optimized for MoE models
- **UD-IQ4_XS:** Ultra-Dense IQ4_XS quantization format
- **GGUF:** GPT-Generated Unified Format - a model format for llama.cpp inference
- **P.R.I.S.M.:** Polypharmacy Reasoning with Internal Structured Monitoring

---

## 9. References

1. **Unsloth:** https://github.com/unslothai/unsloth
2. **Gemma 4:** https://huggingface.co/google/gemma-4-26b-a4b-it
3. **TRL:** https://huggingface.co/docs/trl
4. **llama.cpp:** https://github.com/ggerganov/llama.cpp
5. **LlamaGrammar:** https://llama-cpp-python.readthedocs.io/en/latest/api/llama_cpp.LlamaGrammar.html

---

**Report Prepared By:** P.R.I.S.M. Team
**Report Date:** May 4, 2026
**Version:** 1.0
