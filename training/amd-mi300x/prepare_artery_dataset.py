"""
prepare_artery_dataset.py – Artery Training Data Preparation

Extracts functional, neutral conversations from D1 database and formats them
for LoRA fine‑tuning. Filters for Group B participants (low anthropomorphism).
"""

import json
import sys
from typing import Dict, List, Any

def prepare_artery_dataset(input_file: str, output_file: str):
    """Convert raw conversation logs to Artery training format."""
    examples = []
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    for session in data.get("sessions", []):
        if session.get("study_group") != "B":
            continue
        
        messages = session.get("messages", [])
        for i in range(len(messages) - 1):
            if messages[i]["role"] == "user" and messages[i+1]["role"] == "assistant":
                examples.append({
                    "input": messages[i]["content"],
                    "output": messages[i+1]["content"],
                    "metadata": {
                        "participant_id": session["participant_id"],
                        "day_number": session["day_number"],
                    }
                })
    
    with open(output_file, 'w') as f:
        for ex in examples:
            f.write(json.dumps(ex) + '\n')
    
    print(f"Prepared {len(examples)} Artery training examples")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python prepare_artery_dataset.py <input.json> <output.jsonl>")
        sys.exit(1)
    prepare_artery_dataset(sys.argv[1], sys.argv[2])
