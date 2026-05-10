# Model Summary

P.R.I.S.M. (Polypharmacy Reasoning with Internal Structured Monitoring) is a fine-tuned version of Google's Gemma 4 26B A4B model specifically designed for transparent, auditable clinical decision support in polypharmacy contraindication auditing. The model transforms high-stakes clinical AI queries from black-box interactions into auditable, verifiable, and trust-calibrated outputs.

**Architecture**: Mixture of Experts (MoE) with 128 experts, 25.8B total parameters (~4B active per inference)
**Base Model**: `google/gemma-4-26b-a4b-it`
**Fine-tuning Method**: rsLoRA (Rank-Stabilized LoRA) using Unsloth framework with Triton MoE kernels
**Training Data**: 1,011 curated polypharmacy deliberation examples with structured reasoning traces (1,001 original + 10 safe combinations)
**Context Window**: 8,192 tokens (training), 8,192 tokens (MXFP4 inference with I-Matrix calibration)
**License**: Apache 2.0 (inherited from Gemma 4)

The model outputs structured deliberation using a proprietary token mapping system that exposes competing hypotheses, discarded reasoning paths, logical chains, tool calls, and calibrated confidence scores. This "Glass Box" approach enables clinicians to see not just the model's conclusions, but the complete reasoning process behind them.

**Phase Two Improvements**: The Clean Stack implementation removes conflicting optimization techniques (DoRA, LoRA+, NEFTune) and introduces rsLoRA, standard 8-bit AdamW, and I-Matrix calibration to stabilize gradients and prevent "quantization amnesia" of custom special tokens.

## Usage

### Loading the Model

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from unsloth import FastModel

# Load the fine-tuned model
model, tokenizer = FastModel.from_pretrained(
    model_name = "chandan989/prism-gemma-4-26B-A4B-it-bf16-v3.6",
    max_seq_length = 8192,
    dtype = None,
    load_in_4bit = True,
)

# Enable faster inference
FastModel.for_inference(model)

# Prepare input
system_prompt = """You are a clinical deliberation AI. You must rigidly format your output exactly according to the following schema. Do not deviate or add conversational filler.

EXPECTED OUTPUT SCHEMA:
<unused0>
<unused1>
<unused5>
[Numbered step-by-step logical chain]

<unused6>
[Enumerate competing interpretations with probability estimates, including supporting and weakening evidence]

<unused7>
<unused9> Discarded: [Explanation of discarded paths]

<unused8> Selected: [Final chosen interpretation]
<unused3> [Optional tool calls to verify claims]
<unused2>
[🔴, 🟡, or 🟢] [Clinical reasoning summary]

Confidence: ✅ [LEVEL]

Recommendation: [Actionable advice]"""

instruction = "Patient is a 68yo male on Warfarin 5mg daily, Fluconazole 200mg for 14 days, and Aspirin 81mg. Review for interactions."

prompt = f"""{system_prompt}
<bos><start_of_turn>user
{instruction}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

# Generate response
inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens = 2048, temperature = 0.3)
response = tokenizer.decode(outputs[0], skip_special_tokens = False)
```

### Input/Output Shapes

**Input:**
- `instruction`: String (clinical query about drug interactions)
- `max_seq_length`: 8,192 tokens
- Format: Gemma chat template with special tokens

**Output:**
- Structured deliberation with P.R.I.S.M. token mapping
- Components: Logical Chain, Competing Hypotheses, Discarded Paths, Tool Calls, Final Output
- Confidence badges: HIGH/MODERATE/LOW
- Signal dots: 🔴 (Severe), 🟡 (Moderate), 🟢 (Safe)

### Known Failures

1. **Safe Combination Bias**: The model shows reduced structural compliance for safe drug combinations (🟢) compared to high-risk scenarios (🔴/🟡). This indicates training data imbalance favoring dangerous interactions, though improved with 10 additional safe combination examples.

2. **Quantization Sensitivity**: While I-Matrix calibration protects special tokens, aggressive quantization formats may still affect structural compliance. MXFP4 with I-Matrix is the recommended format.

3. **Tool Call Underutilization**: Despite being trained to use `<|tool_call>` tokens, the model rarely triggers tool calls in practice, suggesting overconfidence or insufficient reinforcement.

4. **Context Window Limitation**: While MXFP4 maintains 8,192 token context, extremely complex polypharmacy cases may still approach token limits.

## System

P.R.I.S.M. is a **standalone model** designed for integration into a broader clinical decision support system. It operates as the core reasoning engine within a three-tier architecture:

### System Components

1. **Model Layer**: P.R.I.S.M. Gemma 4 26B A4B (local execution via llama.cpp/Ollama)
2. **Verification Layer**: CPU-based dense embedding model (ONNX-optimized MiniLM-L6) for claim verification against curated knowledge base
3. **Interface Layer**: Progressive disclosure UI (Next.js) showing default view (answer + confidence + sources) and expert view (full deliberation)

### Input Requirements

- **Format**: Clinical queries about drug-drug interactions, typically polypharmacy regimens
- **Domain**: Pharmacology, drug metabolism, CYP450 pathways, contraindications
- **Language**: English (clinical terminology)
- **Length**: Up to 8,192 tokens (training and MXFP4 inference)

### Downstream Dependencies

1. **Knowledge Base**: FDA Drug Labels, DrugBank, PubMed, MIMIC-IV (local vector index)
2. **Verification Pipeline**: Claim extraction → vector search → source grounding
3. **UI Components**: Deliberation parser, confidence badge renderer, source dot visualizer
4. **Update Protocol**: Nightly encrypted delta pulls for knowledge base currency

### Integration Points

- **Ollama API**: Local model hosting and streaming inference
- **FastAPI Backend**: Thought block parsing, claim extraction, logprob extraction
- **Next.js Frontend**: Progressive disclosure UI rendering
- **TPM/HSM**: Encrypted audit logging for compliance

## Implementation Requirements

### Training Hardware

**Primary Training Environment:**
- **GPU**: NVIDIA RTX PRO 6000 Blackwell Server Edition
- **VRAM**: 94.971 GB
- **CUDA**: 12.0
- **PyTorch**: 2.10.0+cu128
- **Training Time**: ~30-35 minutes (508 steps)
- **Training Steps**: 508 total steps
- **Final Loss**: Not explicitly documented (convergence achieved)

**Alternative Training (Kaggle):**
- **GPU**: 2x T4 GPUs or P100
- **VRAM**: ~16 GB per GPU (via rsLoRA)
- **Training Time**: ~45-60 minutes

### Training Software

- **Framework**: Unsloth + TRL (Transformer Reinforcement Learning)
- **Base Model**: `google/gemma-4-26b-a4b-it`
- **Fine-tuning**: rsLoRA with completion-only masking
- **Optimizer**: AdamW 8-bit (standard, not LoRA+)
- **Scheduler**: Cosine with warmup
- **Precision**: 4-bit load, BF16 training
- **MoE Kernels**: Unsloth Triton MoE with grouped_mm enabled

### Inference Hardware

**Local Workstation (Recommended):**
- **GPU**: RTX 4070 or better (16GB VRAM)
- **CPU**: Modern multi-core processor (for verification pipeline)
- **RAM**: 32GB minimum
- **Storage**: 50GB for BF16 model, 15.4GB for MXFP4 model

**Consumer Hardware (Minimum):**
- **GPU**: Apple Silicon M2/M3 or RTX 3060 (8GB VRAM)
- **CPU**: Any modern processor
- **RAM**: 16GB minimum
- **Storage**: 15.4GB for MXFP4 model

### Inference Software

- **Engine**: llama.cpp v0.3.22+ or Ollama
- **Quantization**: MXFP4 with I-Matrix calibration (recommended)
- **KV Cache**: Q8_0 quantization for keys and values
- **Context**: 8,192 tokens (MXFP4 with I-Matrix)
- **GPU Layers**: 32 layers for optimal performance

### Compute Requirements

**Training:**
- **Trainable Parameters**: 2,759,914,496 (9.92% of total)
- **Memory Footprint**: ~16 GB VRAM (rsLoRA)
- **Energy Consumption**: ~0.6 kWh per training run

**Inference:**
- **Latency**: ~45-55 seconds for complex polypharmacy audit (15 drugs)
- **Throughput**: ~0.02 samples/second (inference)
- **Memory**: 15.4GB (MXFP4), 50GB (BF16)
- **Energy**: ~0.1 kWh per complex query

# Model Characteristics

## Model Initialization

**Fine-tuned from pre-trained model**: P.R.I.S.M. is not trained from scratch. It is built upon Google's Gemma 4 26B A4B, a state-of-the-art Mixture of Experts model pre-trained on diverse text corpora.

**Fine-tuning approach**: rsLoRA (Rank-Stabilized LoRA) with completion-only masking, preserving the foundational pre-trained clinical weights while mastering the P.R.I.S.M. structural output format.

**Training epochs**: 4 epochs (increased from 3 in phase one)
**Learning rate**: 2e-5 (lowered from 5e-5 in phase one for 26B parameter scale)
**Warmup steps**: 50 (increased from 25 in phase one for stable initialization)

**Phase Two Improvements**:
- **rsLoRA**: Rank-Stabilized LoRA for gradient stability at high rank (r=64)
- **Standard 8-bit AdamW**: Replaced LoRA+ to prevent overwriting rigid formatting templates
- **Triton MoE Kernels**: Leverages `torch._grouped_mm` for memory savings
- **I-Matrix Calibration**: Protects special `<unusedX>` tokens during quantization
- **DoRA Disabled**: Prevents grouped_mm coalescing issues

## Model Stats

**Size and Parameters:**
- **Total Parameters**: 25.8B
- **Active Parameters (per inference)**: ~4B (MoE routing)
- **Trainable Parameters**: 2,759,914,496 (9.92% of total)
- **Model Size (BF16)**: ~50GB
- **Model Size (MXFP4)**: 15.4GB

**Architecture Details:**
- **Layers**: 42 transformer layers
- **Experts**: 128 Mixture of Experts
- **Attention Heads**: 32
- **Hidden Size**: 4,608
- **Context Window**: 8,192 tokens (training and MXFP4 inference)
- **Vocabulary Size**: 256,000 tokens

**Latency Metrics:**
- **Training Speed**: ~1.97 samples/second
- **Inference Speed (BF16)**: ~30-40 seconds per complex query
- **Inference Speed (MXFP4)**: ~45-55 seconds per complex query
- **Verification Time**: ~10 seconds (CPU-based)

## Other Details

**Quantization**:
- **Primary Format**: MXFP4 (Microscaling Formats 4-bit) with I-Matrix calibration
- **I-Matrix Calibration**: Protects special tokens by heavily weighting their activation pathways
- **Embedding Preservation**: Output tensors and embeddings locked at F16 to prevent amnesia
- **Quality Impact**: Improved structural compliance vs. phase one quantization

**Pruning**: Not applied. All 128 experts remain active in the model.

**Differential Privacy**: Not implemented. The model was trained on curated clinical data without formal differential privacy guarantees. However, the training data was de-identified and does not contain Protected Health Information (PHI).

**Special Techniques**:
- **Reserved Token Strategy**: P.R.I.S.M. structural boundaries mapped to Gemma's pre-allocated `<unused0>` through `<unused9>` tokens
- **MoE-Specific Configuration**: `moe_gate` included in target modules for effective expert routing
- **Completion-Only Masking**: Gradients calculated only for reasoning and answers, preserving pre-trained weights
- **rsLoRA**: Rank-Stabilized LoRA with alpha = rank for gradient stability
- **I-Matrix Calibration**: Importance matrix calculation to protect special tokens during quantization

# Data Overview

## Training Data

**Source**: Curated polypharmacy deliberation dataset (`deliberation_dataset.json` + `safe_combinations_augmented.json`)
**Size**: 1,011 training examples (1,001 original + 10 safe combinations)
**Format**: Structured JSON with `instruction`, `thought_process`, and `output` fields
**Domain**: Drug-drug interaction analysis for clinical decision support

**Data Collection**:
- **Primary Sources**: FDA Drug Labels, DrugBank interaction profiles, PubMed pharmacovigilance abstracts, MIMIC-IV clinical notes (de-identified)
- **Curation Process**: Manual review by clinical pharmacologists to ensure accuracy and safety
- **Quality Control**: Structured validation ensuring all examples contain required P.R.I.S.M. components

**Pre-processing**:
1. **Token Mapping**: Conversion of P.R.I.S.M. markers to atomic `<unusedX>` tokens
2. **Format Standardization**: Ensuring consistent structure across all examples
3. **Quality Filtering**: Removal of examples with missing fields or incomplete reasoning
4. **Balancing**: Addition of 10 safe combination examples to address severity imbalance

**Data Characteristics**:
- **Average Age**: 68 years (range: 52-78)
- **Gender Distribution**: Slight male bias (~55% male, ~45% female)
- **Severity Distribution**: Still skewed toward high-risk interactions (🔴/🟡), but improved with safe combinations
- **Drug Classes**: Focus on CYP450 interactions, anticoagulants, antiplatelets, antibiotics, psychotropics

## Demographic Groups

**Age Distribution**:
- **Mean**: 68 years
- **Median**: 67 years
- **Range**: 52-78 years
- **Focus**: Elderly patients (65+ years) who are most vulnerable to polypharmacy errors

**Gender Distribution**:
- **Male**: ~55% of examples
- **Female**: ~45% of examples
- **Rationale**: Reflects typical polypharmacy demographics in clinical practice

**Clinical Populations**:
- **Post-MI Patients**: Cardiac patients on dual antiplatelet therapy
- **Elderly with Multiple Comorbidities**: Patients on 10+ medications
- **Psychiatric Patients**: Individuals on psychotropic regimens
- **Infectious Disease Patients**: Patients on antibiotic/antifungal therapy

**Limitations**:
- **Geographic Bias**: Primarily US/European drug formularies
- **Racial/Ethnic Data**: Not explicitly captured in training examples
- **Pediatric Population**: Not represented (focus on adult/geriatric)
- **Pregnancy/Lactation**: Limited coverage

## Evaluation Data

**Train/Test Split**: 80/20 split (808 training, 203 test examples)
**Validation**: Holdout test suite with 6 representative cases

**Holdout Test Suite**:

| Test # | Query | Expected Severity | Structure Score | Result |
|--------|-------|-------------------|-----------------|--------|
| 1 | Simvastatin + Itraconazole | 🔴 Severe | 5/5 | ✅ Pass |
| 2 | Digoxin + Amiodarone | 🟡 Moderate | 5/5 | ✅ Pass |
| 3 | Metformin + Atorvastatin | 🟢 Safe | 5/5 | ✅ Pass |
| 4 | Complex polypharmacy (10 drugs) | 🔴 Severe | 5/5 | ✅ Pass |
| 5 | Lisinopril + Hydrochlorothiazide | 🟢 Safe | 5/5 | ✅ Pass |
| 6 | Levothyroxine + Omeprazole | 🟢 Safe | 5/5 | ✅ Pass |

**Notable Differences**:
- **Training Data**: Improved balance with addition of 10 safe combination examples
- **Test Data**: Includes multiple safe combinations (🟢) to assess generalization
- **Structural Compliance**: 100% on all test cases including safe combinations
- **Quantization Impact**: MXFP4 with I-Matrix shows improved structural compliance vs. phase one

**Evaluation Metrics**:
- **Structural Compliance**: 5-metric framework (Discarded Paths, Selected Path, Signal Dot, Confidence Badge, Recommendation)
- **Confidence Calibration**: Brier Score, Expected Calibration Error (ECE)
- **Source Grounding**: Verification accuracy against curated knowledge base

# Evaluation Results

## Summary

**Base Model Performance (Pre-Training)**:
- **Structural Compliance**: 0/6 metrics passed
- **Behavior**: Standard unstructured medical response, no P.R.I.S.M. structure

**Fine-Tuned Model Performance (Post-Training)**:
- **Structural Compliance**: 6/6 metrics passed (100%)
- **Training Steps**: 508 total steps
- **Trainable Parameters**: 2,759,914,496 (9.92% of total)
- **Training Time**: ~30-35 minutes

**MXFP4 Model Performance (with I-Matrix Calibration)**:
- **Structural Compliance**: 100% (5/5 metrics on holdout tests)
- **MXFP4 Format**: 15.4GB, 100% compliance
- **I-Matrix Calibration**: Protects special tokens during quantization
- **Safe Combination Handling**: Improved with additional training examples

**Overall Assessment**: The phase two fine-tuning successfully taught the model to output structured deliberation with calibrated confidence scores. The Clean Stack implementation (rsLoRA, standard 8-bit AdamW, I-Matrix calibration) significantly improved structural compliance, particularly for safe combinations and quantized models.

## Subgroup Evaluation Results

**Severity-Based Subgroups**:

| Severity | Training Examples | Test Performance | Structural Compliance |
|----------|-------------------|------------------|----------------------|
| 🔴 Severe | ~60% | 2/2 tests passed | 100% |
| 🟡 Moderate | ~30% | 1/1 test passed | 100% |
| 🟢 Safe | ~10% (improved) | 3/3 tests passed | 100% |

**Key Findings**:
1. **High-Risk Excellence**: Model excels at identifying and structuring dangerous drug interactions
2. **Safe Combination Improvement**: Complete structural compliance for safe combinations (improved from phase one)
3. **Training Data Balance**: Addition of 10 safe combination examples improved generalization

**Drug Class Subgroups**:

| Drug Class | Examples | Performance | Notes |
|------------|----------|------------|-------|
| CYP450 Inhibitors | ~40% | Excellent | Well-represented in training |
| Anticoagulants | ~25% | Excellent | High-stakes scenarios prioritized |
| Antibiotics | ~20% | Good | Moderate representation |
| Psychotropics | ~10% | Fair | Limited coverage |
| Others | ~5% | Variable | Sparse data |

**Known Failures**:
1. **Tool Call Utilization**: Despite training, model rarely triggers `<|tool_call>` tokens
2. **Quantization Sensitivity**: While improved, aggressive quantization formats may still affect structural compliance
3. **Context Window**: Extremely complex regimens may approach 8,192 token limits

## Fairness

**Fairness Definition**: P.R.I.S.M. defines fairness as consistent performance across demographic groups and clinical scenarios, with particular attention to avoiding systematic bias that could lead to differential patient harm.

**Metrics Used**:
- **Structural Compliance**: Consistency of P.R.I.S.M. format application
- **Confidence Calibration**: Accuracy of confidence scores across subgroups
- **Source Verification**: Reliability of claim grounding across drug classes
- **Severity Distribution**: Balance of 🔴/🟡/🟢 classifications

**Baselines**:
- **Base Model**: Unstructured Gemma 4 26B A4B (no P.R.I.S.M. structure)
- **Clinical Standard**: Manual drug interaction review by pharmacists
- **Rule-Based Systems**: Traditional drug interaction databases (e.g., Micromedex)

**Results**:
- **Age Bias**: Model performs better for elderly patients (65+) who are overrepresented in training data
- **Gender Bias**: Slight male bias (~55% vs. 45%) but minimal performance difference
- **Severity Bias**: Improved balance with addition of safe combination examples
- **Drug Class Bias**: Excellent performance for well-represented classes (CYP450, anticoagulants), variable for others

**Fairness Limitations**:
1. **Demographic Coverage**: Limited racial/ethnic diversity in training data
2. **Geographic Bias**: Primarily US/European drug formularies
3. **Special Populations**: Minimal coverage for pediatric, pregnant, or lactating patients
4. **Severity Imbalance**: Training data still weighted toward dangerous interactions (though improved)

## Usage Limitations

**Sensitive Use Cases**:
- **Clinical Decision Support**: Model is designed for polypharmacy auditing, not emergency triage
- **High-Stakes Scenarios**: Should be used as a decision support tool, not a replacement for clinical judgment
- **Regulatory Compliance**: Not FDA-cleared or CE-marked; requires institutional validation

**Performance Limitations**:
1. **Tool Call Underutilization**: Model rarely triggers verification tools despite training
2. **Quantization Sensitivity**: While improved with I-Matrix, aggressive quantization may still affect compliance
3. **Context Window**: 8,192 token limit may truncate extremely complex deliberations
4. **Safe Combination Handling**: Improved but still limited training data for benign drug pairs

**Conditions for Use**:
- **Hardware**: Minimum 16GB VRAM for MXFP4 model, 50GB for BF16
- **Knowledge Base**: Requires current FDA Drug Labels, DrugBank, PubMed index
- **Update Protocol**: Nightly delta pulls to maintain knowledge base currency
- **Clinical Oversight**: Must be used under supervision of qualified healthcare professionals

**Contraindications**:
- **Emergency Triage**: Not suitable for time-critical clinical decisions
- **Pediatric Patients**: Limited training data for pediatric populations
- **Pregnancy/Lactation**: Insufficient coverage for these special populations
- **Novel Therapeutics**: May not recognize recently approved drugs or interactions

**Failure Modes**:
1. **Stale Knowledge Base**: >7 days without updates triggers warning banner
2. **Quantization Artifacts**: Special token generation may fail without I-Matrix calibration
3. **Context Overflow**: Extremely complex regimens may exceed token limits
4. **Overconfidence**: Model may express high confidence for poorly studied interactions

## Ethics

**Ethical Considerations Addressed**:

1. **Transparency**: P.R.I.S.M. exposes the model's reasoning process, enabling clinicians to understand and audit conclusions
2. **Calibration**: Confidence badges (HIGH/MODERATE/LOW) help users gauge reliability
3. **Source Grounding**: Verification dots (🟢🟡🔴) indicate claim support in curated sources
4. **Progressive Disclosure**: Default view shows clean answer; expert view reveals full deliberation

**Risks Identified**:
1. **Automation Bias**: Users may over-rely on model outputs without critical review
2. **False Confidence**: Confidence badges may be miscalibrated for novel interactions
3. **Knowledge Staleness**: Outdated drug interaction data could lead to incorrect recommendations
4. **Demographic Bias**: Limited representation of certain populations could lead to differential care

**Mitigations Implemented**:
1. **Glass Box Interface**: Full deliberation trace available for audit
2. **Source Verification**: Claims checked against curated knowledge base
3. **Staleness Safeguards**: Warning banner if knowledge base >7 days old
4. **Clinical Oversight**: Designed for use under qualified healthcare professional supervision
5. **I-Matrix Calibration**: Protects special tokens during quantization to maintain structural integrity

**Remediation Strategies**:
1. **Training Data Augmentation**: Added 10 safe combination examples to address severity bias
2. **Quantization Optimization**: MXFP4 with I-Matrix calibration for improved structural compliance
3. **Demographic Diversification**: Expanding training data to include underrepresented populations
4. **Continuous Monitoring**: Structural compliance monitoring in production to detect degradation

**Ethical Framework**:
- **Beneficence**: Designed to reduce polypharmacy errors, a leading cause of preventable hospital deaths
- **Non-Maleficence**: Includes safeguards to prevent harm from incorrect recommendations
- **Autonomy**: Preserves clinician decision-making authority through transparent reasoning
- **Justice**: Aims to provide equitable care across demographic groups (though limitations exist)

**Future Ethical Work**:
1. **Formal Bias Auditing**: Systematic evaluation across demographic subgroups
2. **External Validation**: Independent assessment of clinical accuracy and safety
3. **Regulatory Engagement**: Pursuit of appropriate regulatory clearances
4. **Community Involvement**: Engagement with patient advocacy groups and clinicians

---

**Model Version**: 3.6 (Phase Two - The Clean Stack)
**Last Updated**: May 9, 2026
**Contact**: P.R.I.S.M. Team
**License**: Apache 2.0
**Citation**: If you use P.R.I.S.M. in your research, please cite appropriately.