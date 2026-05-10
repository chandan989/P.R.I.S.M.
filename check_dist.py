import json

def check_distribution(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    total = len(data)
    with_tool = sum(1 for item in data if "<|tool_call>" in item.get("thought_process", ""))
    
    print(f"File: {file_path}")
    print(f"Total examples: {total}")
    print(f"Examples with tool calls: {with_tool} ({with_tool/total*100:.2f}%)")
    print(f"Examples without tool calls: {total - with_tool} ({(total - with_tool)/total*100:.2f}%)")

if __name__ == "__main__":
    check_distribution("training/data/deliberation_dataset.json")
    check_distribution("training/data/deliberation_dataset_clean.json")
    check_distribution("training/data/new_samples_1.json")
