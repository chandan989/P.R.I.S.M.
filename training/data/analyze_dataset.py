import json
import re
from collections import Counter
import statistics

def analyze_dataset(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    total_samples = len(data)
    print(f"Total Samples: {total_samples}\n")
    
    # Quality metrics
    missing_fields = []
    short_thought_process = 0
    missing_logical_chain = 0
    missing_competing_hypotheses = 0
    missing_tool_call = 0
    
    # Skewness metrics
    ages = []
    genders = Counter()
    emojis = Counter()
    confidences = Counter()
    drugs_mentioned = Counter()
    
    for i, sample in enumerate(data):
        # 1. Quality Checks
        if not all(k in sample for k in ("instruction", "thought_process", "output")):
            missing_fields.append(i)
            continue
            
        tp = sample["thought_process"]
        if len(tp) < 200:
            short_thought_process += 1
        if "[Logical Chain]" not in tp:
            missing_logical_chain += 1
        if "[Competing Hypotheses]" not in tp:
            missing_competing_hypotheses += 1
        if "<|tool_call>verify_claim<|" not in tp:
            missing_tool_call += 1
            
        # 2. Skewness Checks
        # Extract age
        age_match = re.search(r"(\d{2})yo", sample["instruction"])
        if age_match:
            ages.append(int(age_match.group(1)))
            
        # Extract gender
        if "male" in sample["instruction"].lower() and "female" not in sample["instruction"].lower():
            genders["male"] += 1
        elif "female" in sample["instruction"].lower():
            genders["female"] += 1
            
        # Extract emoji
        output = sample["output"]
        if "🔴" in output:
            emojis["🔴 (Severe)"] += 1
        elif "🟡" in output:
            emojis["🟡 (Moderate)"] += 1
        elif "🟢" in output:
            emojis["🟢 (Safe/Minor)"] += 1
            
        # Extract confidence
        conf_match = re.search(r"Confidence:\s*(.*?)\n", output)
        if conf_match:
            confidences[conf_match.group(1).strip()] += 1
            
        # Extract drugs (simple heuristic: capitalized words in instruction that aren't common words)
        words = re.findall(r'\b[A-Z][a-z]+\b', sample["instruction"])
        for w in words:
            if w not in ["Patient", "A", "Evaluate"]:
                drugs_mentioned[w] += 1
                
    # Reporting
    print("--- Quality Check ---")
    print(f"Missing essential fields (instruction/thought_process/output): {len(missing_fields)}")
    print(f"Short thought process (< 200 chars): {short_thought_process}")
    print(f"Missing [Logical Chain]: {missing_logical_chain}")
    print(f"Missing [Competing Hypotheses]: {missing_competing_hypotheses}")
    print(f"Missing tool call tag: {missing_tool_call}")
    
    print("\n--- Skewness: Demographics ---")
    if ages:
        print(f"Age: Mean={statistics.mean(ages):.1f}, Median={statistics.median(ages)}, Min={min(ages)}, Max={max(ages)}")
    print(f"Gender Distribution: {dict(genders)}")
    
    print("\n--- Skewness: Clinical Outcomes ---")
    print(f"Severity Emoji Distribution: {dict(emojis)}")
    print(f"Confidence Distribution: {dict(confidences)}")
    
    print("\n--- Skewness: Top 15 Most Mentioned Capitalized Entities (Likely Drugs/Conditions) ---")
    for drug, count in drugs_mentioned.most_common(15):
        print(f"{drug}: {count}")

if __name__ == "__main__":
    analyze_dataset("training/data/deliberation_dataset.json")
