# P.R.I.S.M. Example Usage

This document provides comprehensive examples for using the P.R.I.S.M. (Polypharmacy Reasoning with Internal Structured Monitoring) model in various scenarios.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Complete Working Example](#complete-working-example)
- [Expected Output Format](#expected-output-format)
- [Parsing the Response](#parsing-the-response)
- [Usage with llama.cpp](#usage-with-llamacpp-quantized-model)
- [Batch Processing](#batch-processing)
- [Clinical Workflow Integration](#clinical-workflow-integration)
- [Advanced Usage](#advanced-usage)

## Basic Usage

### Quick Start

```python
import torch
from unsloth import FastModel

# Load the fine-tuned P.R.I.S.M. model
model, tokenizer = FastModel.from_pretrained(
    model_name = "chandan989/prism-gemma-4-26B-A4B-it-bf16-v3.6",
    max_seq_length = 8192,
    dtype = None,
    load_in_4bit = True,
)

# Enable optimized inference mode
FastModel.for_inference(model)

# Simple query
query = "Patient on Warfarin 5mg and Omeprazole 20mg. What are the interactions?"

# Format prompt
prompt = f"""You are a clinical deliberation AI. You must rigidly format your output exactly according to the following schema.

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

Recommendation: [Actionable advice]

<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

# Generate response
inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens = 2048, temperature = 0.3)
response = tokenizer.decode(outputs[0], skip_special_tokens = False)

print(response)
```

## Complete Working Example

### Full Implementation with Authentication

```python
import torch
from unsloth import FastModel
from huggingface_hub import login
from datetime import datetime

# Authenticate with Hugging Face (if using private models)
login(token="your_hf_token_here")

# Load the fine-tuned P.R.I.S.M. model
print("Loading P.R.I.S.M. model...")
model, tokenizer = FastModel.from_pretrained(
    model_name = "chandan989/prism-gemma-4-26B-A4B-it-bf16-v3.6",
    max_seq_length = 8192,
    dtype = None,
    load_in_4bit = True,
)

# Enable optimized inference mode
FastModel.for_inference(model)
print("Model loaded successfully!")

# Define the P.R.I.S.M. system prompt
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

# Example clinical query
clinical_query = """
Patient is a 72-year-old female with the following medication regimen:
- Warfarin 5mg daily (for atrial fibrillation)
- Fluconazole 200mg daily for 14 days (for fungal infection)
- Aspirin 81mg daily (for cardiovascular protection)

Please evaluate for potential drug-drug interactions and provide clinical recommendations.
"""

# Format the prompt with P.R.I.S.M. structure
prompt = f"""{system_prompt}
<bos><start_of_turn>user
{clinical_query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

# Generate the response
print("Generating P.R.I.S.M. analysis...")
inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")

start_time = datetime.now()

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens = 2048,
        temperature = 0.3,
        top_p = 0.85,
        use_cache = True,
        do_sample = True
    )

generation_time = (datetime.now() - start_time).total_seconds()

# Decode the response
response = tokenizer.decode(outputs[0], skip_special_tokens = False)

print(f"\n=== P.R.I.S.M. DELIBERATION OUTPUT ===")
print(f"Generation time: {generation_time:.2f} seconds")
print(f"=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
print(response)
print(f"\n=== END OF OUTPUT ===")
```

## Expected Output Format

The model will return a structured response following this pattern:

```
<unused0>
<unused1>
<unused5>
1. Target drugs: Warfarin (Vitamin K antagonist), Fluconazole (azole antifungal), Aspirin (antiplatelet).
2. Pharmacokinetics: Fluconazole is a potent CYP2C9 inhibitor; Warfarin is primarily metabolized by CYP2C9.
3. Pharmacodynamics: Inhibition of CYP2C9 reduces Warfarin clearance, raising INR. Aspirin adds antiplatelet effect.

<unused6>
Interpretation A: Severe bleeding risk from combined CYP2C9 inhibition and antiplatelet effect [94.0%]
├── Supporting: Fluconazole consistently raises Warfarin AUC by 90-100%; Aspirin disrupts GI mucosa.
└── Weakening: Aspirin dose is low (81mg); patient may be on cardioprotective indication.

Interpretation B: Manageable risk with close INR monitoring [6.0%]
├── Supporting: Short 14-day Fluconazole course; provider may adjust Warfarin empirically.
└── Weakening: Elderly female with likely comorbidities; lag in INR checks could be fatal.

<unused7>
<unused9> Discarded: No clinically meaningful interaction. (CYP2C9 inhibition by Fluconazole is well-documented).

<unused8> Selected: Interpretation A
<unused3>verify_claim<|"|>Fluconazole inhibits CYP2C9 and significantly increases Warfarin plasma levels<|"|>
<unused2>
🔴 Fluconazole potently inhibits CYP2C9, the primary metabolic pathway for S-Warfarin, causing a clinically dangerous rise in INR. Concurrent Aspirin further compounds hemorrhagic risk.

Confidence: ✅ HIGH

Recommendation: Reduce Warfarin dose empirically by 25-50% at Fluconazole initiation; check INR every 3-4 days during the antifungal course. Consider proton pump inhibitor co-therapy to protect GI mucosa.
```

## Parsing the Response

### Structured Response Parser

```python
import re
from typing import Dict, Optional

def parse_prism_response(response: str) -> Dict[str, Optional[str]]:
    """Parse a P.R.I.S.M. response into structured components.

    Args:
        response: Raw model response containing P.R.I.S.M. tokens

    Returns:
        Dictionary containing parsed components
    """

    # Extract deliberation section (before <unused2>)
    deliberation_match = re.search(r'<unused0>(.*?)<unused2>', response, re.DOTALL)
    deliberation = deliberation_match.group(1) if deliberation_match else ""

    # Extract clinical answer section (after <unused2>)
    answer_match = re.search(r'<unused2>(.*)', response, re.DOTALL)
    answer = answer_match.group(1) if answer_match else ""

    # Extract logical chain
    logical_chain_match = re.search(r'<unused5>(.*?)<unused6>', deliberation, re.DOTALL)
    logical_chain = logical_chain_match.group(1) if logical_chain_match else ""

    # Extract competing hypotheses
    hypotheses_match = re.search(r'<unused6>(.*?)<unused7>', deliberation, re.DOTALL)
    hypotheses = hypotheses_match.group(1) if hypotheses_match else ""

    # Extract discarded paths
    discarded_match = re.search(r'<unused7>(.*?)<unused8>', deliberation, re.DOTALL)
    discarded = discarded_match.group(1) if discarded_match else ""

    # Extract selected interpretation
    selected_match = re.search(r'<unused8>(.*?)<unused3>', deliberation, re.DOTALL)
    selected = selected_match.group(1) if selected_match else ""

    # Extract tool calls
    tool_call_match = re.search(r'<unused3>(.*?)', deliberation, re.DOTALL)
    tool_call = tool_call_match.group(1) if tool_call_match else ""

    # Extract severity signal
    severity = None
    for signal in ["🔴", "🟡", "🟢"]:
        if signal in answer:
            severity = signal
            break

    # Extract confidence level
    confidence_match = re.search(r'Confidence: ✅ (\w+)', answer)
    confidence = confidence_match.group(1) if confidence_match else "UNKNOWN"

    # Extract recommendation
    recommendation_match = re.search(r'Recommendation: (.*)', answer, re.DOTALL)
    recommendation = recommendation_match.group(1) if recommendation_match else ""

    return {
        "deliberation": deliberation.strip(),
        "answer": answer.strip(),
        "logical_chain": logical_chain.strip(),
        "hypotheses": hypotheses.strip(),
        "discarded": discarded.strip(),
        "selected": selected.strip(),
        "tool_call": tool_call.strip(),
        "severity": severity,
        "confidence": confidence,
        "recommendation": recommendation.strip()
    }

# Usage example
parsed = parse_prism_response(response)

print(f"=== Parsed P.R.I.S.M. Analysis ===")
print(f"Severity: {parsed['severity']}")
print(f"Confidence: {parsed['confidence']}")
print(f"\nSelected Interpretation:")
print(f"{parsed['selected']}")
print(f"\nRecommendation:")
print(f"{parsed['recommendation']}")
print(f"\nLogical Chain:")
print(f"{parsed['logical_chain']}")
```

### Enhanced Parser with Hypothesis Extraction

```python
def parse_hypotheses(hypotheses_text: str) -> list[dict]:
    """Parse competing hypotheses from the hypotheses section.

    Args:
        hypotheses_text: Raw hypotheses text from P.R.I.S.M. response

    Returns:
        List of hypothesis dictionaries with probability and evidence
    """

    hypotheses = []
    lines = hypotheses_text.split('\n')

    current_hypothesis = None

    for line in lines:
        # Check for hypothesis header
        match = re.match(r'Interpretation ([A-Z]): (.+?) \[(\d+\.?\d*)%\]', line)
        if match:
            if current_hypothesis:
                hypotheses.append(current_hypothesis)

            current_hypothesis = {
                "label": match.group(1),
                "description": match.group(2),
                "probability": float(match.group(3)),
                "supporting": [],
                "weakening": []
            }
            continue

        # Check for supporting evidence
        if line.strip().startswith('├── Supporting:'):
            if current_hypothesis:
                current_hypothesis["supporting"].append(
                    line.replace('├── Supporting:', '').strip()
                )

        # Check for weakening evidence
        if line.strip().startswith('└── Weakening:'):
            if current_hypothesis:
                current_hypothesis["weakening"].append(
                    line.replace('└── Weakening:', '').strip()
                )

    if current_hypothesis:
        hypotheses.append(current_hypothesis)

    return hypotheses

# Usage example
parsed = parse_prism_response(response)
hypotheses = parse_hypotheses(parsed['hypotheses'])

print("=== Competing Hypotheses ===")
for i, hyp in enumerate(hypotheses, 1):
    print(f"\nHypothesis {i} ({hyp['label']}):")
    print(f"  Description: {hyp['description']}")
    print(f"  Probability: {hyp['probability']:.1f}%")
    print(f"  Supporting Evidence:")
    for evidence in hyp['supporting']:
        print(f"    - {evidence}")
    print(f"  Weakening Evidence:")
    for evidence in hyp['weakening']:
        print(f"    - {evidence}")
```

## Usage with llama.cpp (Quantized Model)

### Loading and Using MXFP4 Model

```python
import llama_cpp
from huggingface_hub import snapshot_download
import time

# Download the MXFP4 quantized model
print("Downloading MXFP4 model...")
model_path = snapshot_download(
    repo_id="chandan989/prism-gemma-4-26B-A4B-it-MXFP4-v3.6",
    allow_patterns=["*.gguf"]
)

print(f"Model downloaded to: {model_path}")

# Load the quantized model
print("Loading MXFP4 model with llama.cpp...")
start_time = time.time()

llm = llama_cpp.Llama(
    model_path=model_path,
    n_ctx=8192,  # Full context window
    n_gpu_layers=32,  # Offload layers to GPU
    type_k=llama_cpp.GGML_TYPE_Q8_0,
    type_v=llama_cpp.GGML_TYPE_Q8_0,
    flash_attn=True,
    n_threads=4,
    verbose=False,
)

load_time = time.time() - start_time
print(f"Model loaded in {load_time:.2f} seconds")

# Define system prompt
system_prompt = """You are a clinical deliberation AI. You must rigidly format your output exactly according to the following schema.

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

# Example query
query = "Patient on Warfarin 5mg and Omeprazole 20mg. What are the interactions?"

# Format prompt
prompt = f"""{system_prompt}
<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
"""

# Generate response
print("Generating response...")
start_time = time.time()

output = llm(
    prompt,
    max_tokens=2048,
    temperature=0.3,
    top_p=0.85,
    stop=["<eos>", "<end_of_turn>"],
    echo=False
)

generation_time = time.time() - start_time

response = output['choices'][0]['text']

print(f"\n=== P.R.I.S.M. Response ===")
print(f"Generation time: {generation_time:.2f} seconds")
print(f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
print(response)
```

### Optimized llama.cpp Configuration

```python
import llama_cpp

# Optimized configuration for different hardware scenarios

def get_llama_config(hardware_type: str = "standard") -> dict:
    """Get optimized llama.cpp configuration based on hardware.

    Args:
        hardware_type: Type of hardware ('standard', 'high_end', 'low_end')

    Returns:
        Configuration dictionary for llama_cpp.Llama
    """

    configs = {
        "standard": {
            "n_ctx": 8192,
            "n_gpu_layers": 32,
            "type_k": llama_cpp.GGML_TYPE_Q8_0,
            "type_v": llama_cpp.GGML_TYPE_Q8_0,
            "flash_attn": True,
            "n_threads": 4,
            "n_batch": 512,
            "verbose": False,
        },
        "high_end": {
            "n_ctx": 8192,
            "n_gpu_layers": -1,  # All layers on GPU
            "type_k": llama_cpp.GGML_TYPE_Q8_0,
            "type_v": llama_cpp.GGML_TYPE_Q8_0,
            "flash_attn": True,
            "n_threads": 8,
            "n_batch": 1024,
            "verbose": False,
        },
        "low_end": {
            "n_ctx": 4096,  # Reduced context
            "n_gpu_layers": 16,  # Fewer GPU layers
            "type_k": llama_cpp.GGML_TYPE_Q4_0,
            "type_v": llama_cpp.GGML_TYPE_Q4_0,
            "flash_attn": False,
            "n_threads": 2,
            "n_batch": 256,
            "verbose": False,
        }
    }

    return configs.get(hardware_type, configs["standard"])

# Usage example
config = get_llama_config("high_end")

llm = llama_cpp.Llama(
    model_path=model_path,
    **config
)
```

## Batch Processing

### Processing Multiple Queries

```python
import torch
from typing import List, Dict
from datetime import datetime

def batch_analyze_interactions(queries: List[str]) -> List[Dict]:
    """Analyze multiple drug interaction queries in batch.

    Args:
        queries: List of clinical query strings

    Returns:
        List of analysis results with parsed components
    """

    results = []

    for i, query in enumerate(queries, 1):
        print(f"Processing query {i}/{len(queries)}...")

        prompt = f"""{system_prompt}
<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

        inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")

        start_time = datetime.now()

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens = 2048,
                temperature = 0.3,
                top_p = 0.85,
                use_cache = True
            )

        generation_time = (datetime.now() - start_time).total_seconds()

        response = tokenizer.decode(outputs[0], skip_special_tokens = False)
        parsed = parse_prism_response(response)

        results.append({
            "query": query,
            "severity": parsed["severity"],
            "confidence": parsed["confidence"],
            "recommendation": parsed["recommendation"],
            "full_response": response,
            "generation_time": generation_time,
            "timestamp": datetime.now().isoformat()
        })

    return results

# Example batch queries
queries = [
    "Patient on Simvastatin 80mg and Itraconazole 200mg. Evaluate for interactions.",
    "72yo female on Digoxin 0.25mg and Amiodarone 200mg. Review all interactions.",
    "Patient on Metformin 500mg and Atorvastatin 20mg. Any interaction?",
    "65yo male on Clopidogrel 75mg, Omeprazole 40mg, and Atorvastatin 80mg post-MI. Any concerns?",
    "Patient on Sertraline 100mg, Tramadol 50mg PRN, and Linezolid 600mg IV for MRSA. Evaluate for safety.",
]

# Process batch
results = batch_analyze_interactions(queries)

# Display results
print("\n=== BATCH ANALYSIS RESULTS ===")
for i, result in enumerate(results, 1):
    print(f"\n{'='*60}")
    print(f"Query {i}: {result['query'][:60]}...")
    print(f"{'='*60}")
    print(f"Severity: {result['severity']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Generation Time: {result['generation_time']:.2f}s")
    print(f"\nRecommendation:")
    print(f"{result['recommendation'][:200]}...")

# Summary statistics
total_time = sum(r['generation_time'] for r in results)
avg_time = total_time / len(results)

print(f"\n{'='*60}")
print(f"BATCH SUMMARY")
print(f"{'='*60}")
print(f"Total Queries: {len(results)}")
print(f"Total Time: {total_time:.2f}s")
print(f"Average Time: {avg_time:.2f}s")
print(f"Queries/Second: {1/avg_time:.2f}")
```

### Parallel Batch Processing (Advanced)

```python
from concurrent.futures import ThreadPoolExecutor
import threading

# Thread-safe model access
model_lock = threading.Lock()

def process_single_query(query: str, index: int) -> Dict:
    """Process a single query with thread-safe model access.

    Args:
        query: Clinical query string
        index: Query index for tracking

    Returns:
        Analysis result dictionary
    """

    with model_lock:
        prompt = f"""{system_prompt}
<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

        inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens = 2048,
                temperature = 0.3,
                top_p = 0.85,
                use_cache = True
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens = False)
        parsed = parse_prism_response(response)

        return {
            "index": index,
            "query": query,
            "severity": parsed["severity"],
            "confidence": parsed["confidence"],
            "recommendation": parsed["recommendation"],
            "full_response": response,
            "timestamp": datetime.now().isoformat()
        }

def parallel_batch_analyze(queries: List[str], max_workers: int = 2) -> List[Dict]:
    """Analyze multiple queries in parallel.

    Args:
        queries: List of clinical query strings
        max_workers: Maximum number of parallel workers

    Returns:
        List of analysis results
    """

    results = [None] * len(queries)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_query, query, i): i
            for i, query in enumerate(queries)
        }

        for future in futures:
            result = future.result()
            results[result['index']] = result

    return results

# Usage example
results = parallel_batch_analyze(queries, max_workers=2)
```

## Clinical Workflow Integration

### PRISM Clinical Assistant Class

```python
from typing import Dict, List, Optional
from datetime import datetime
import json

class PRISMClinicalAssistant:
    """Integration helper for clinical decision support systems.

    This class provides a high-level interface for integrating P.R.I.S.M.
    into clinical workflows and EHR systems.
    """

    def __init__(self, model_path: str = "chandan989/prism-gemma-4-26B-A4B-it-bf16-v3.6"):
        """Initialize the P.R.I.S.M. clinical assistant.

        Args:
            model_path: Hugging Face model path or identifier
        """

        print(f"Loading P.R.I.S.M. model from {model_path}...")
        self.model, self.tokenizer = FastModel.from_pretrained(
            model_name = model_path,
            max_seq_length = 8192,
            dtype = None,
            load_in_4bit = True,
        )
        FastModel.for_inference(self.model)

        self.system_prompt = """You are a clinical deliberation AI. You must rigidly format your output exactly according to the following schema. Do not deviate or add conversational filler.

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

        print("P.R.I.S.M. clinical assistant ready!")

    def analyze_medication_regimen(self, patient_data: Dict) -> Dict:
        """Analyze a patient's complete medication regimen.

        Args:
            patient_data: Dictionary containing patient information and medications

        Returns:
            Analysis result with parsed components
        """

        # Format patient data into clinical query
        medications = "\n".join([
            f"- {med['name']} {med['dose']} ({med['indication']})"
            for med in patient_data['medications']
        ])

        query = f"""
Patient is a {patient_data['age']}-year-old {patient_data['gender']} with the following medication regimen:

{medications}

Patient history: {patient_data.get('history', 'Not provided')}
Allergies: {patient_data.get('allergies', 'None reported')}
Lab values: {patient_data.get('lab_values', 'Not provided')}

Please evaluate for potential drug-drug interactions and provide clinical recommendations.
"""

        # Generate P.R.I.S.M. analysis
        prompt = f"""{self.system_prompt}
<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

        inputs = self.tokenizer([prompt], return_tensors = "pt").to("cuda")

        start_time = datetime.now()

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens = 2048,
                temperature = 0.3,
                top_p = 0.85,
                use_cache = True
            )

        generation_time = (datetime.now() - start_time).total_seconds()

        response = self.tokenizer.decode(outputs[0], skip_special_tokens = False)
        parsed = parse_prism_response(response)

        return {
            "patient_id": patient_data.get('id', 'UNKNOWN'),
            "analysis": parsed,
            "raw_response": response,
            "generation_time": generation_time,
            "timestamp": datetime.now().isoformat()
        }

    def analyze_single_interaction(self, drug1: str, dose1: str,
                                   drug2: str, dose2: str,
                                   context: str = "") -> Dict:
        """Analyze a single drug-drug interaction.

        Args:
            drug1: First drug name
            dose1: First drug dose
            drug2: Second drug name
            dose2: Second drug dose
            context: Additional clinical context

        Returns:
            Analysis result for the interaction
        """

        query = f"""
Patient on {drug1} {dose1} and {drug2} {dose2}.
{context if context else ''}
Please evaluate for potential drug-drug interactions.
"""

        prompt = f"""{self.system_prompt}
<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

        inputs = self.tokenizer([prompt], return_tensors = "pt").to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens = 2048,
                temperature = 0.3,
                top_p = 0.85,
                use_cache = True
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens = False)
        parsed = parse_prism_response(response)

        return {
            "drugs": [drug1, drug2],
            "doses": [dose1, dose2],
            "analysis": parsed,
            "raw_response": response,
            "timestamp": datetime.now().isoformat()
        }

    def export_analysis_report(self, analysis: Dict, format: str = "json") -> str:
        """Export analysis result in specified format.

        Args:
            analysis: Analysis result dictionary
            format: Export format ('json', 'text', 'html')

        Returns:
            Formatted report string
        """

        if format == "json":
            return json.dumps(analysis, indent=2, default=str)

        elif format == "text":
            parsed = analysis['analysis']
            report = f"""
P.R.I.S.M. Clinical Analysis Report
=====================================
Patient ID: {analysis.get('patient_id', 'N/A')}
Timestamp: {analysis['timestamp']}
Generation Time: {analysis.get('generation_time', 0):.2f}s

Severity Assessment: {parsed['severity']}
Confidence Level: {parsed['confidence']}

CLINICAL RECOMMENDATION:
{parsed['recommendation']}

DETAILED ANALYSIS:
Logical Chain:
{parsed['logical_chain']}

Selected Interpretation:
{parsed['selected']}

Competing Hypotheses:
{parsed['hypotheses']}

Discarded Paths:
{parsed['discarded']}
"""
            return report.strip()

        elif format == "html":
            parsed = analysis['analysis']
            severity_colors = {
                "🔴": "#dc3545",  # Red
                "🟡": "#ffc107",  # Yellow
                "🟢": "#28a745"   # Green
            }
            severity_color = severity_colors.get(parsed['severity'], "#6c757d")

            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>P.R.I.S.M. Clinical Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .severity {{ color: {severity_color}; font-weight: bold; font-size: 1.2em; }}
        .section {{ margin: 20px 0; }}
        .recommendation {{ background-color: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; }}
        .logical-chain {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>P.R.I.S.M. Clinical Analysis Report</h1>
        <p>Patient ID: {analysis.get('patient_id', 'N/A')}</p>
        <p>Timestamp: {analysis['timestamp']}</p>
    </div>

    <div class="section">
        <h2>Severity Assessment</h2>
        <p class="severity">{parsed['severity']} - Confidence: {parsed['confidence']}</p>
    </div>

    <div class="section">
        <h2>Clinical Recommendation</h2>
        <div class="recommendation">
            {parsed['recommendation'].replace(chr(10), '<br>')}
        </div>
    </div>

    <div class="section">
        <h2>Detailed Analysis</h2>
        <h3>Logical Chain</h3>
        <div class="logical-chain">
            {parsed['logical_chain'].replace(chr(10), '<br>')}
        </div>

        <h3>Selected Interpretation</h3>
        <p>{parsed['selected'].replace(chr(10), '<br>')}</p>

        <h3>Competing Hypotheses</h3>
        <p>{parsed['hypotheses'].replace(chr(10), '<br>')}</p>

        <h3>Discarded Paths</h3>
        <p>{parsed['discarded'].replace(chr(10), '<br>')}</p>
    </div>
</body>
</html>
"""
            return html

        else:
            raise ValueError(f"Unsupported format: {format}")

# Usage example
assistant = PRISMClinicalAssistant()

# Analyze complete medication regimen
patient_data = {
    "id": "PATIENT_001",
    "age": 72,
    "gender": "female",
    "history": "Atrial fibrillation, hypertension, type 2 diabetes",
    "allergies": "Penicillin",
    "lab_values": "INR 2.1, Creatinine 1.2 mg/dL",
    "medications": [
        {"name": "Warfarin", "dose": "5mg daily", "indication": "Atrial fibrillation"},
        {"name": "Lisinopril", "dose": "10mg daily", "indication": "Hypertension"},
        {"name": "Metformin", "dose": "1000mg twice daily", "indication": "Type 2 diabetes"},
        {"name": "Aspirin", "dose": "81mg daily", "indication": "Cardiovascular protection"},
    ]
}

analysis = assistant.analyze_medication_regimen(patient_data)

# Display results
print(f"\n=== P.R.I.S.M. Analysis for {analysis['patient_id']} ===")
print(f"Severity: {analysis['analysis']['severity']}")
print(f"Confidence: {analysis['analysis']['confidence']}")
print(f"Generation Time: {analysis['generation_time']:.2f}s")
print(f"\nRecommendation:")
print(f"{analysis['analysis']['recommendation']}")

# Export report
json_report = assistant.export_analysis_report(analysis, format="json")
text_report = assistant.export_analysis_report(analysis, format="text")
html_report = assistant.export_analysis_report(analysis, format="html")

# Save reports
with open(f"prism_report_{analysis['patient_id']}.json", "w") as f:
    f.write(json_report)

with open(f"prism_report_{analysis['patient_id']}.txt", "w") as f:
    f.write(text_report)

with open(f"prism_report_{analysis['patient_id']}.html", "w") as f:
    f.write(html_report)
```

## Advanced Usage

### Custom System Prompts

```python
def create_custom_system_prompt(
    focus_area: str = "general",
    confidence_threshold: str = "MODERATE",
    include_references: bool = True
) -> str:
    """Create a custom system prompt for specific use cases.

    Args:
        focus_area: Clinical focus area ('general', 'cardiology', 'geriatrics', etc.)
        confidence_threshold: Minimum confidence level to report
        include_references: Whether to include reference citations

    Returns:
        Custom system prompt string
    """

    base_prompt = """You are a clinical deliberation AI. You must rigidly format your output exactly according to the following schema."""

    focus_instructions = {
        "general": "Provide comprehensive drug interaction analysis for all clinical scenarios.",
        "cardiology": "Focus on cardiovascular drug interactions, anticoagulant management, and arrhythmia risks.",
        "geriatrics": "Pay special attention to age-related pharmacokinetic changes, polypharmacy risks, and fall prevention.",
        "oncology": "Focus on chemotherapy drug interactions, supportive care medications, and immunotherapy considerations.",
        "psychiatry": "Emphasize psychotropic drug interactions, metabolic considerations, and behavioral health risks."
    }

    confidence_instructions = {
        "HIGH": "Only report interactions with strong clinical evidence.",
        "MODERATE": "Report interactions with moderate to strong clinical evidence.",
        "LOW": "Report all potential interactions regardless of evidence strength."
    }

    reference_instruction = """
Include specific references to clinical guidelines, FDA warnings, or peer-reviewed studies when available.
""" if include_references else ""

    custom_prompt = f"""{base_prompt}

Focus Area: {focus_area}
{focus_instructions.get(focus_area, focus_instructions['general'])}

Confidence Threshold: {confidence_threshold}
{confidence_instructions.get(confidence_threshold, confidence_instructions['MODERATE'])}

{reference_instruction}

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

    return custom_prompt

# Usage example
custom_prompt = create_custom_system_prompt(
    focus_area="geriatrics",
    confidence_threshold="MODERATE",
    include_references=True
)

prompt = f"""{custom_prompt}
<bos><start_of_turn>user
85-year-old patient on multiple medications. Evaluate for interactions.<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""
```

### Streaming Responses

```python
def stream_prism_response(query: str, model, tokenizer) -> None:
    """Stream P.R.I.S.M. response token by token.

    Args:
        query: Clinical query string
        model: Loaded P.R.I.S.M. model
        tokenizer: Model tokenizer
    """

    system_prompt = """You are a clinical deliberation AI. You must rigidly format your output exactly according to the following schema."""

    prompt = f"""{system_prompt}
<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

    inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")

    print("Streaming P.R.I.S.M. response...")
    print("=" * 60)

    # Stream generation
    streamer = tokenizer.decode(
        model.generate(
            **inputs,
            max_new_tokens = 2048,
            temperature = 0.3,
            top_p = 0.85,
            use_cache = True,
            streamer = True
        ),
        skip_special_tokens = False
    )

    for token in streamer:
        print(token, end='', flush=True)

    print("\n" + "=" * 60)
    print("Streaming complete!")

# Usage example
stream_prism_response(
    "Patient on Warfarin 5mg and Omeprazole 20mg. What are the interactions?",
    model,
    tokenizer
)
```

### Evaluation and Testing

```python
def evaluate_prism_model(test_cases: List[Dict]) -> Dict:
    """Evaluate P.R.I.S.M. model on test cases.

    Args:
        test_cases: List of test case dictionaries with 'query' and 'expected' fields

    Returns:
        Evaluation results with metrics
    """

    results = {
        "total_tests": len(test_cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }

    for i, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected = test_case.get('expected', {})

        # Generate response
        prompt = f"""{system_prompt}
<bos><start_of_turn>user
{query}<end_of_turn>
<start_of_turn>model
<unused0>
<unused1>"""

        inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens = 2048,
                temperature = 0.3,
                top_p = 0.85,
                use_cache = True
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens = False)
        parsed = parse_prism_response(response)

        # Evaluate against expected results
        test_passed = True
        failures = []

        if 'severity' in expected:
            if parsed['severity'] != expected['severity']:
                test_passed = False
                failures.append(f"Severity mismatch: expected {expected['severity']}, got {parsed['severity']}")

        if 'confidence' in expected:
            if parsed['confidence'] != expected['confidence']:
                test_passed = False
                failures.append(f"Confidence mismatch: expected {expected['confidence']}, got {parsed['confidence']}")

        # Check structural compliance
        required_components = ['logical_chain', 'hypotheses', 'discarded', 'selected', 'recommendation']
        for component in required_components:
            if not parsed[component]:
                test_passed = False
                failures.append(f"Missing component: {component}")

        if test_passed:
            results['passed'] += 1
        else:
            results['failed'] += 1

        results['details'].append({
            "test_case": i,
            "query": query,
            "passed": test_passed,
            "failures": failures,
            "parsed": parsed
        })

    results['pass_rate'] = results['passed'] / results['total_tests'] * 100

    return results

# Example test cases
test_cases = [
    {
        "query": "Patient on Warfarin 5mg and Fluconazole 200mg. Evaluate for interactions.",
        "expected": {
            "severity": "🔴",
            "confidence": "HIGH"
        }
    },
    {
        "query": "Patient on Metformin 500mg and Atorvastatin 20mg. Any interaction?",
        "expected": {
            "severity": "🟢",
            "confidence": "HIGH"
        }
    },
    {
        "query": "72yo female on Digoxin 0.25mg and Amiodarone 200mg. Review all interactions.",
        "expected": {
            "severity": "🟡",
            "confidence": "HIGH"
        }
    }
]

# Run evaluation
evaluation = evaluate_prism_model(test_cases)

# Display results
print("\n=== P.R.I.S.M. Model Evaluation ===")
print(f"Total Tests: {evaluation['total_tests']}")
print(f"Passed: {evaluation['passed']}")
print(f"Failed: {evaluation['failed']}")
print(f"Pass Rate: {evaluation['pass_rate']:.1f}%")

# Display detailed results
print("\n=== Detailed Results ===")
for detail in evaluation['details']:
    status = "✅ PASS" if detail['passed'] else "❌ FAIL"
    print(f"\nTest {detail['test_case']}: {status}")
    print(f"Query: {detail['query'][:60]}...")
    if not detail['passed']:
        print("Failures:")
        for failure in detail['failures']:
            print(f"  - {failure}")
```

---

## Additional Resources

- **Model Documentation**: See `MODEL_DETAILS.md` for comprehensive model information
- **Training Notebook**: `training/P_R_I_S_M_Finetune_Two.ipynb` for training details
- **API Reference**: Hugging Face model page for additional parameters and options
- **Clinical Guidelines**: Always consult current clinical guidelines and drug interaction databases

## Support

For questions or issues related to P.R.I.S.M. usage, please refer to the project repository or contact the development team.

---

**Version**: 3.6 (Phase Two - The Clean Stack)
**Last Updated**: May 9, 2026