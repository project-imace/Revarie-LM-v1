"""
export_to_onnx.py – Export Trained LoRA to ONNX Format

Converts the fine‑tuned LoRA adapter to ONNX for efficient inference.
"""

import torch
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import onnx
import onnxruntime as ort


def export_lora_to_onnx(base_model: str, lora_path: str, output_path: str):
    """Export LoRA‑adapted model to ONNX."""
    print(f"Loading base model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="cpu",
    )
    
    print(f"Loading LoRA adapter from: {lora_path}")
    model = PeftModel.from_pretrained(model, lora_path)
    model = model.merge_and_unload()
    model.eval()
    
    # Dummy input
    dummy_input = tokenizer("Hello, how are you?", return_tensors="pt")
    
    print(f"Exporting to ONNX: {output_path}")
    torch.onnx.export(
        model,
        (dummy_input["input_ids"], dummy_input["attention_mask"]),
        output_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "logits": {0: "batch", 1: "sequence"},
        },
        opset_version=17,
    )
    
    # Verify ONNX model
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)
    
    print(f"✅ ONNX model exported successfully to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", required=True)
    parser.add_argument("--lora_path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    export_lora_to_onnx(args.base_model, args.lora_path, args.output)
