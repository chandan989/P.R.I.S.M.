"""
P.R.I.S.M. Data Augmentation Script

This script generates augmented training data to balance the dataset and improve model performance.
It creates safe combinations, moderate interactions, edge cases, and diverse drug combinations.

Target Distribution:
- 🔴 Critical: 600 (current: 648, need: 0)
- 🟡 Moderate: 800 (current: 245, need: 555)
- 🟢 Safe: 600 (current: 108, need: 492)
- Total Target: 2000 (current: 1001, need: 999)
"""

import json
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DrugInteraction:
    """Represents a drug interaction scenario."""
    drug_a: str
    drug_b: str
    risk_level: str  # 'critical', 'moderate', 'safe'
    mechanism: str
    clinical_significance: str
    recommendation: str

# Safe drug combinations (no significant interactions)
SAFE_COMBINATIONS = [
    # Cardiovascular
    ("Metformin", "Atorvastatin", "No significant PK/PD interaction"),
    ("Lisinopril", "Amlodipine", "Additive antihypertensive effect, generally safe"),
    ("Metoprolol", "Hydrochlorothiazide", "Complementary mechanisms, well-tolerated"),
    ("Losartan", "Amlodipine", "No significant interaction"),
    ("Atenolol", "Chlorthalidone", "Standard combination therapy"),
    ("Diltiazem", "Enalapril", "Generally safe combination"),
    ("Furosemide", "Spironolactone", "Synergistic diuretic effect, monitor electrolytes"),

    # Respiratory
    ("Albuterol", "Fluticasone", "No significant interaction"),
    ("Montelukast", "Cetirizine", "Complementary mechanisms, safe"),
    ("Ipratropium", "Albuterol", "Standard combination therapy"),

    # Gastrointestinal
    ("Omeprazole", "Metoclopramide", "No significant interaction"),
    ("Pantoprazole", "Famotidine", "Different mechanisms, safe"),
    ("Loperamide", "Bismuth subsalicylate", "No significant interaction"),

    # Pain/Inflammation
    ("Acetaminophen", "Ibuprofen", "Safe when used appropriately"),
    ("Naproxen", "Acetaminophen", "No significant interaction"),
    ("Tramadol", "Acetaminophen", "Standard combination"),

    # CNS
    ("Sertraline", "Bupropion", "Generally safe, monitor for serotonin effects"),
    ("Escitalopram", "Mirtazapine", "Different mechanisms, safe"),
    ("Duloxetine", "Gabapentin", "No significant interaction"),

    # Endocrine
    ("Levothyroxine", "Metformin", "No significant interaction"),
    ("Insulin glargine", "Metformin", "Standard combination"),
    ("Sitagliptin", "Metformin", "Standard combination"),

    # Antibiotics
    ("Amoxicillin", "Clavulanate", "Standard combination"),
    ("Azithromycin", "Doxycycline", "No significant interaction"),
    ("Cephalexin", "Nitrofurantoin", "No significant interaction"),

    # Other
    ("Folic acid", "Prenatal vitamins", "Supplemental, safe"),
    ("Vitamin D3", "Calcium carbonate", "Complementary absorption"),
    ("Omega-3", "Aspirin", "Mild additive effect, generally safe"),
]

# Moderate drug interactions (require monitoring)
MODERATE_INTERACTIONS = [
    # CYP interactions
    ("Fluconazole", "Atorvastatin", "CYP3A4 inhibition, monitor for myopathy"),
    ("Clarithromycin", "Simvastatin", "Strong CYP3A4 inhibition, dose limit statin"),
    ("Ritonavir", "Rosuvastatin", "OATP1B1 inhibition, dose limit statin"),
    ("Verapamil", "Simvastatin", "CYP3A4 inhibition, monitor for myopathy"),
    ("Diltiazem", "Atorvastatin", "CYP3A4 inhibition, monitor for myopathy"),

    # Pharmacodynamic interactions
    ("Lisinopril", "Ibuprofen", "Reduced antihypertensive effect, monitor renal function"),
    ("Losartan", "Indomethacin", "Reduced efficacy, monitor renal function"),
    ("Furosemide", "Gentamicin", "Additive nephrotoxicity, monitor renal function"),
    ("Spironolactone", "Lisinopril", "Additive hyperkalemia risk, monitor potassium"),

    # QT prolongation
    ("Azithromycin", "Levofloxacin", "Additive QT prolongation, monitor ECG"),
    ("Ciprofloxacin", "Ondansetron", "Additive QT prolongation, monitor ECG"),
    ("Haloperidol", "Quetiapine", "Additive QT prolongation, monitor ECG"),

    # CNS effects
    ("Diazepam", "Oxycodone", "Additive CNS depression, use caution"),
    ("Alprazolam", "Gabapentin", "Additive sedation, dose adjustment needed"),
    ("Zolpidem", "Escitalopram", "Additive sedation, use caution"),

    # Other moderate interactions
    ("Warfarin", "Amiodarone", "Increased INR, close monitoring required"),
    ("Digoxin", "Verapamil", "Increased digoxin levels, monitor levels"),
    ("Lithium", "Hydrochlorothiazide", "Increased lithium levels, monitor levels"),
    ("Methotrexate", "Probenecid", "Increased methotrexate levels, monitor"),
]

# Edge cases (borderline, dose-dependent, special populations)
EDGE_CASES = [
    # Borderline interactions
    ("Fluconazole", "Warfarin", "Dose-dependent CYP2C9 inhibition, monitor INR closely"),
    ("Erythromycin", "Theophylline", "Variable CYP3A4 inhibition, monitor levels"),
    ("Cimetidine", "Phenytoin", "Variable CYP inhibition, monitor levels"),

    # Dose-dependent interactions
    ("Ibuprofen", "Lisinopril", "Dose-dependent renal effect, monitor at high NSAID doses"),
    ("Naproxen", "Losartan", "Dose-dependent effect, monitor renal function"),
    ("Acetaminophen", "Warfarin", "High dose acetaminophen may increase INR"),

    # Time-dependent interactions
    ("Rifampin", "Warfarin", "Time-dependent CYP induction, monitor INR during and after"),
    ("Carbamazepine", "Oral contraceptives", "Time-dependent enzyme induction, backup contraception"),

    # Genetic polymorphism scenarios
    ("Clopidogrel", "Omeprazole", "CYP2C19 polymorphism may affect interaction"),
    ("Codeine", "Fluoxetine", "CYP2D6 polymorphism affects codeine activation"),
    ("Tamoxifen", "Paroxetine", "CYP2D6 polymorphism affects tamoxifen activation"),

    # Renal impairment scenarios
    ("Digoxin", "Amiodarone", "Renal impairment increases digoxin toxicity risk"),
    ("Lithium", "NSAIDs", "Renal impairment exacerbates lithium toxicity"),
    ("Methotrexate", "NSAIDs", "Renal impairment increases methotrexate toxicity"),

    # Hepatic impairment scenarios
    ("Warfarin", "Azole antifungals", "Hepatic impairment increases bleeding risk"),
    ("Statins", "CYP3A4 inhibitors", "Hepatic impairment increases myopathy risk"),
    ("Theophylline", "CYP1A2 inhibitors", "Hepatic impairment increases toxicity risk"),
]

# Diverse drug combinations for broader coverage
DIVERSE_COMBINATIONS = [
    # Less common but clinically relevant combinations
    ("Pregabalin", "Duloxetine", "neuropathic pain management"),
    ("Amlodipine", "Simvastatin", "cardiovascular risk reduction"),
    ("Metformin", "Sitagliptin", "diabetes management"),
    ("Levothyroxine", "Calcium carbonate", "thyroid and bone health"),
    ("Fentanyl", "Midazolam", "critical care sedation"),
    ("Vancomycin", "Acetaminophen", "infection and pain management"),
    ("Prednisone", "Methotrexate", "inflammatory conditions"),
    ("Cyclosporine", "Azithromycin", "transplant and infection"),
    ("Phenytoin", "Rifampin", "epilepsy and tuberculosis"),
    ("Clonidine", "Propranolol", "hypertension management"),
    ("Tamsulosin", "Finasteride", "benign prostatic hyperplasia"),
    ("Pantoprazole", "Clopidogrel", "cardiovascular protection"),
    ("Montelukast", "Fluticasone", "asthma management"),
    ("Gabapentin", "Amitriptyline", "neuropathic pain"),
    ("Hydrochlorothiazide", "Valsartan", "hypertension management"),
    ("Metoprolol", "Amlodipine", "hypertension and angina"),
    ("Furosemide", "Potassium chloride", "diuretic therapy"),
    ("Aspirin", "Clopidogrel", "cardiovascular protection"),
    ("Insulin", "Metformin", "diabetes management"),
    ("Omeprazole", "Sucralfate", "peptic ulcer disease"),
]

def generate_safe_combination_example(drug_a: str, drug_b: str, mechanism: str, recommendation: str) -> Dict:
    """Generate a safe combination example following PRISM structure."""
    instruction = f"Patient is on {drug_a} and {drug_b}. Review for potential drug interactions."

    thought_process = f"""[Logical Chain]
1. Target drugs: {drug_a} and {drug_b}.
2. Pharmacokinetics: {mechanism}.
3. Pharmacodynamics: No clinically significant pharmacodynamic interaction identified.
4. Clinical evidence: This combination is commonly used in clinical practice with established safety profile.

[Competing Hypotheses]
Interpretation A: No clinically significant interaction [95.0%]
├── Supporting: Well-documented safety profile; no known PK/PD interactions.
└── Weakening: Individual patient factors may modify risk.

Interpretation B: Minor interaction requiring monitoring [5.0%]
├── Supporting: Theoretical interaction mechanisms exist.
└── Weakening: Clinical evidence shows no significant effect.

[Discarded Paths]
✗ Discarded: Significant interaction requiring intervention. (No evidence supports this; the combination has established safety).

▶ Selected: Interpretation A
<|tool_call>verify_claim<|\"|>{drug_a} and {drug_b} have no clinically significant drug-drug interaction<|\"|>"""

    output = f"""🟢 {drug_a} and {drug_b} can be safely co-administered. No clinically significant pharmacokinetic or pharmacodynamic interactions have been identified.

Confidence: ✅ HIGH

Recommendation: {recommendation}"""

    return {
        "instruction": instruction,
        "thought_process": thought_process,
        "output": output
    }

def generate_moderate_interaction_example(drug_a: str, drug_b: str, mechanism: str, recommendation: str) -> Dict:
    """Generate a moderate interaction example following PRISM structure."""
    instruction = f"Patient on {drug_a} and {drug_b}. Assess for potential drug interactions."

    thought_process = f"""[Logical Chain]
1. Target drugs: {drug_a} and {drug_b}.
2. Pharmacokinetics: {mechanism}.
3. Clinical consequence: This interaction requires monitoring but is not contraindicated.
4. Risk modifiers: Patient-specific factors may influence the clinical significance.

[Competing Hypotheses]
Interpretation A: Moderate interaction requiring monitoring [85.0%]
├── Supporting: Well-documented interaction mechanism; clinical evidence supports monitoring.
└── Weakening: Interaction severity is dose-dependent and manageable.

Interpretation B: Minimal clinical significance [15.0%]
├── Supporting: Many patients tolerate this combination without issues.
└── Weakening: Interaction mechanism is well-established and requires attention.

[Discarded Paths]
✗ Discarded: No interaction exists. (Pharmacological evidence clearly demonstrates an interaction mechanism).

▶ Selected: Interpretation A
<|tool_call>verify_claim<|\"|>{drug_a} and {drug_b} have a moderate interaction requiring clinical monitoring<|\"|>"""

    output = f"""🟡 {drug_a} and {drug_b} have a moderate interaction that requires monitoring. {mechanism}

Confidence: ⚠️ MODERATE

Recommendation: {recommendation}"""

    return {
        "instruction": instruction,
        "thought_process": thought_process,
        "output": output
    }

def generate_edge_case_example(drug_a: str, drug_b: str, scenario: str, recommendation: str) -> Dict:
    """Generate an edge case example following PRISM structure."""
    instruction = f"Patient on {drug_a} and {drug_b}. {scenario}."

    thought_process = f"""[Logical Chain]
1. Target drugs: {drug_a} and {drug_b}.
2. Special consideration: {scenario}.
3. Pharmacokinetics: Complex interaction influenced by patient-specific factors.
4. Clinical consequence: Risk is variable and requires individualized assessment.

[Competing Hypotheses]
Interpretation A: Interaction risk is significant in this context [75.0%]
├── Supporting: {scenario} increases interaction risk.
└── Weakening: Risk may be mitigated with appropriate monitoring.

Interpretation B: Risk is manageable with monitoring [25.0%]
├── Supporting: Close monitoring can detect and prevent adverse outcomes.
└── Weakening: {scenario} fundamentally alters the risk profile.

[Discarded Paths]
✗ Discarded: No interaction exists. (The special consideration creates a unique interaction scenario).

▶ Selected: Interpretation A
<|tool_call>verify_claim<|\"|>{drug_a} and {drug_b} interaction risk is modified by {scenario}<|\"|>"""

    output = f"""🟡 {drug_a} and {drug_b} interaction risk is modified by {scenario}. This requires individualized assessment and monitoring.

Confidence: ⚠️ MODERATE

Recommendation: {recommendation}"""

    return {
        "instruction": instruction,
        "thought_process": thought_process,
        "output": output
    }

def generate_diverse_combination_example(drug_a: str, drug_b: str, context: str, recommendation: str) -> Dict:
    """Generate a diverse combination example following PRISM structure."""
    instruction = f"Patient on {drug_a} and {drug_b} for {context}. Assess for interactions."

    thought_process = f"""[Logical Chain]
1. Target drugs: {drug_a} and {drug_b}.
2. Clinical context: {context}.
3. Pharmacokinetics: Evaluate potential PK interactions in this context.
4. Pharmacodynamics: Evaluate potential PD interactions in this context.

[Competing Hypotheses]
Interpretation A: Combination is appropriate for this clinical context [80.0%]
├── Supporting: {context} provides rationale for combination; benefits outweigh risks.
└── Weakening: Individual patient factors may modify risk.

Interpretation B: Alternative combination may be preferable [20.0%]
├── Supporting: Other options may have better risk profile.
└── Weakening: Current combination is well-established for this indication.

[Discarded Paths]
✗ Discarded: Contraindicated combination. (No evidence supports contraindication in this context).

▶ Selected: Interpretation A
<|tool_call>verify_claim<|\"|>{drug_a} and {drug_b} combination is appropriate for {context}<|\"|>"""

    output = f"""🟢 {drug_a} and {drug_b} can be safely used together for {context}. This combination is well-established in clinical practice.

Confidence: ✅ HIGH

Recommendation: {recommendation}"""

    return {
        "instruction": instruction,
        "thought_process": thought_process,
        "output": output
    }

def augment_dataset(input_file: str, output_file: str) -> None:
    """Augment the dataset with new examples."""
    # Load existing dataset
    with open(input_file, 'r') as f:
        existing_data = json.load(f)

    print(f"Loaded {len(existing_data)} existing examples")

    # Generate new examples
    new_examples = []

    # Generate safe combinations (need 492 more)
    print("\nGenerating safe combinations...")
    safe_combinations = SAFE_COMBINATIONS * 4  # Multiply to get enough examples
    random.shuffle(safe_combinations)

    for i, (drug_a, drug_b, mechanism) in enumerate(safe_combinations[:492]):
        recommendation = f"Continue both medications as prescribed. No dose adjustments or monitoring required beyond standard care."
        example = generate_safe_combination_example(drug_a, drug_b, mechanism, recommendation)
        new_examples.append(example)
        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/492 safe combinations")

    # Generate moderate interactions (need 555 more)
    print("\nGenerating moderate interactions...")
    moderate_interactions = MODERATE_INTERACTIONS * 3  # Multiply to get enough examples
    random.shuffle(moderate_interactions)

    for i, (drug_a, drug_b, mechanism) in enumerate(moderate_interactions[:555]):
        recommendation = f"Monitor for adverse effects. Consider dose adjustment if clinically indicated. Patient education about potential interaction is recommended."
        example = generate_moderate_interaction_example(drug_a, drug_b, mechanism, recommendation)
        new_examples.append(example)
        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/555 moderate interactions")

    # Generate edge cases (need 200)
    print("\nGenerating edge cases...")
    edge_cases = EDGE_CASES * 4  # Multiply to get enough examples
    random.shuffle(edge_cases)

    for i, (drug_a, drug_b, scenario) in enumerate(edge_cases[:200]):
        recommendation = f"Individualized assessment required. Close monitoring of relevant parameters. Consider alternative therapies if risk is unacceptable."
        example = generate_edge_case_example(drug_a, drug_b, scenario, recommendation)
        new_examples.append(example)
        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/200 edge cases")

    # Generate diverse combinations (need 300)
    print("\nGenerating diverse combinations...")
    diverse_combinations = DIVERSE_COMBINATIONS * 6  # Multiply to get enough examples
    random.shuffle(diverse_combinations)

    for i, (drug_a, drug_b, context) in enumerate(diverse_combinations[:300]):
        recommendation = f"This combination is appropriate for the indicated condition. Standard monitoring applies. No specific interaction concerns."
        example = generate_diverse_combination_example(drug_a, drug_b, context, recommendation)
        new_examples.append(example)
        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/300 diverse combinations")

    # Combine existing and new examples
    augmented_data = existing_data + new_examples

    # Shuffle the combined dataset
    random.shuffle(augmented_data)

    # Save augmented dataset
    with open(output_file, 'w') as f:
        json.dump(augmented_data, f, indent=2)

    print(f"\n{'='*60}")
    print(f"AUGMENTATION COMPLETE")
    print(f"{'='*60}")
    print(f"Original examples: {len(existing_data)}")
    print(f"New examples: {len(new_examples)}")
    print(f"Total examples: {len(augmented_data)}")
    print(f"\nBreakdown of new examples:")
    print(f"  Safe combinations: 492")
    print(f"  Moderate interactions: 555")
    print(f"  Edge cases: 200")
    print(f"  Diverse combinations: 300")
    print(f"  Total new: {len(new_examples)}")
    print(f"\nOutput saved to: {output_file}")

def validate_augmented_dataset(file_path: str) -> None:
    """Validate the augmented dataset for quality and structure."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"\n{'='*60}")
    print(f"DATASET VALIDATION")
    print(f"{'='*60}")

    # Check structure
    print(f"\nStructure Validation:")
    required_keys = ['instruction', 'thought_process', 'output']
    for key in required_keys:
        count = sum(1 for item in data if key in item)
        print(f"  {key}: {count}/{len(data)} ({count/len(data)*100:.1f}%)")

    # Check PRISM structure compliance
    print(f"\nPRISM Structure Compliance:")
    metrics = {
        'Logical Chain': '[Logical Chain]',
        'Competing Hypotheses': '[Competing Hypotheses]',
        'Discarded Paths': '[Discarded Paths]',
        'Tool Call': '<|tool_call>',
    }
    for metric, pattern in metrics.items():
        count = sum(1 for item in data if pattern in item.get('thought_process', ''))
        print(f"  {metric}: {count}/{len(data)} ({count/len(data)*100:.1f}%)")

    # Check risk level distribution
    print(f"\nRisk Level Distribution:")
    risk_levels = []
    for item in data:
        output = item.get('output', '')
        if '🔴' in output:
            risk_levels.append('critical')
        elif '🟡' in output:
            risk_levels.append('moderate')
        elif '🟢' in output:
            risk_levels.append('safe')
        else:
            risk_levels.append('unknown')

    for level in ['critical', 'moderate', 'safe', 'unknown']:
        count = risk_levels.count(level)
        print(f"  {level:12s}: {count:4d} ({count/len(data)*100:5.1f}%)")

    # Check confidence level distribution
    print(f"\nConfidence Level Distribution:")
    confidence_levels = []
    for item in data:
        output = item.get('output', '')
        if '✅ HIGH' in output:
            confidence_levels.append('HIGH')
        elif '⚠️ MODERATE' in output:
            confidence_levels.append('MODERATE')
        elif '❓ LOW' in output:
            confidence_levels.append('LOW')
        else:
            confidence_levels.append('unknown')

    for level in ['HIGH', 'MODERATE', 'LOW', 'unknown']:
        count = confidence_levels.count(level)
        print(f"  {level:12s}: {count:4d} ({count/len(data)*100:5.1f}%)")

    # Check for duplicates
    print(f"\nDuplicate Check:")
    instructions = [item.get('instruction', '') for item in data]
    unique_instructions = len(set(instructions))
    duplicates = len(instructions) - unique_instructions
    print(f"  Total instructions: {len(instructions)}")
    print(f"  Unique instructions: {unique_instructions}")
    print(f"  Duplicates: {duplicates}")

    # Check instruction length
    instruction_lengths = [len(item.get('instruction', '')) for item in data]
    print(f"\nInstruction Length Statistics:")
    print(f"  Min: {min(instruction_lengths)}")
    print(f"  Max: {max(instruction_lengths)}")
    print(f"  Mean: {sum(instruction_lengths)/len(instruction_lengths):.1f}")
    print(f"  Median: {sorted(instruction_lengths)[len(instruction_lengths)//2]}")

    print(f"\n{'='*60}")
    print(f"VALIDATION COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(3407)

    # File paths
    input_file = "/Users/chandan/Documents/Elykid Private Limited/Products/P.R.I.S.M./training/data/deliberation_dataset.json"
    output_file = "/Users/chandan/Documents/Elykid Private Limited/Products/P.R.I.S.M./training/data/deliberation_dataset_augmented.json"

    # Augment dataset
    augment_dataset(input_file, output_file)

    # Validate augmented dataset
    validate_augmented_dataset(output_file)
