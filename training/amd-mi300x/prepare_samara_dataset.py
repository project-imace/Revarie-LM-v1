"""
prepare_samara_dataset.py – Samara Training Data Preparation

Extracts empathetic, warm conversations from D1 database and formats them
for LoRA fine‑tuning. Filters for Group A participants (high anthropomorphism).
"""

import json
import sys
import os
from typing import Dict, List, Any

def prepare_samara_dataset(input_file: str, output_file: str):
    """Convert raw conversation logs to Samara training format."""
    examples = []
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    for session in data.get("sessions", []):
        if session.get("study_group") != "A":
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
                        "emotional_tone": session.get("emotional_tone", "neutral"),
                    }
                })
    
    with open(output_file, 'w') as f:
        for ex in examples:
            f.write(json.dumps(ex) + '\n')
    
    print(f"Prepared {len(examples)} Samara training examples")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python prepare_samara_dataset.py <input.json> <output.jsonl>")
        sys.exit(1)
    prepare_samara_dataset(sys.argv[1], sys.argv[2])
