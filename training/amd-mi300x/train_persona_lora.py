"""
train_persona_lora.py – AMD MI300X LoRA Fine‑Tuning

Trains distinct LoRA adapters for Samara (high anthropomorphism) and Artery (low
anthropomorphism) using the AMD MI300X 8‑GPU instance. Leverages ROCm‑optimized
PyTorch and DeepSpeed for maximum throughput.

Theoretical Foundations:
- Hu et al. (2021): LoRA – Low‑Rank Adaptation of Large Language Models
- Dettmers et al. (2023): QLoRA – Efficient Finetuning of Quantized LLMs
- Rasley et al. (2020): DeepSpeed – Extreme‑Scale Model Training
"""

import os
import json
import argparse
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import deepspeed
import wandb
from datetime import datetime
from typing import Dict, Optional, List
import glob

# =============================================================================
# CONFIGURATION
# =============================================================================
class TrainingConfig:
    """Hyperparameters optimized for MI300X 8‑GPU training."""
    
    # Model
    base_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    max_seq_length: int = 2048
    
    # LoRA
    lora_r_samara: int = 16
    lora_alpha_samara: int = 32
    lora_r_artery: int = 8
    lora_alpha_artery: int = 16
    lora_dropout: float = 0.05
    target_modules: List[str] = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    
    # Training
    per_device_batch_size: int = 8
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.03
    num_epochs: int = 3
    max_steps: int = 2500
    
    # Quantization (QLoRA)
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16"
    bnb_4bit_quant_type: str = "nf4"
    
    # DeepSpeed
    use_deepspeed: bool = True
    deepspeed_stage: int = 3
    
    # Output
    output_dir: str = "./output"
    hf_repo_samara: str = "project-imace/revarie-samara-lora"
    hf_repo_artery: str = "project-imace/revarie-artery-lora"
    hf_token: Optional[str] = None


config = TrainingConfig()


# =============================================================================
# DATASET
# =============================================================================
class PersonaDataset(Dataset):
    """Dataset for persona‑specific fine‑tuning."""
    
    def __init__(self, data_path: str, tokenizer: AutoTokenizer, max_length: int):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []
        
        with open(data_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.examples.append(json.loads(line))
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        prompt = example["input"]
        response = example["output"]
        
        text = f"### User: {prompt}\n### Assistant: {response}"
        tokenized = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        
        return {
            "input_ids": tokenized["input_ids"].squeeze(),
            "attention_mask": tokenized["attention_mask"].squeeze(),
            "labels": tokenized["input_ids"].squeeze(),
        }


def prepare_model_and_tokenizer(persona: str):
    """Load base model with QLoRA quantization."""
    tokenizer = AutoTokenizer.from_pretrained(config.base_model)
    tokenizer.pad_token = tokenizer.eos_token
    
    bnb_config = None
    if config.use_4bit:
        compute_dtype = getattr(torch, config.bnb_4bit_compute_dtype)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=config.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
    
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )
    
    model = prepare_model_for_kbit_training(model)
    
    # LoRA config
    lora_r = config.lora_r_samara if persona == "samara" else config.lora_r_artery
    lora_alpha = config.lora_alpha_samara if persona == "samara" else config.lora_alpha_artery
    
    peft_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    return model, tokenizer


def get_deepspeed_config():
    """DeepSpeed ZeRO‑3 configuration for MI300X."""
    return {
        "train_batch_size": config.per_device_batch_size * config.gradient_accumulation_steps * 8,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "optimizer": {
            "type": "AdamW",
            "params": {
                "lr": config.learning_rate,
                "betas": [0.9, 0.95],
                "eps": 1e-8,
                "weight_decay": 0.1,
            }
        },
        "scheduler": {
            "type": "WarmupDecayLR",
            "params": {
                "warmup_min_lr": 0,
                "warmup_max_lr": config.learning_rate,
                "warmup_num_steps": int(config.max_steps * config.warmup_ratio),
                "total_num_steps": config.max_steps,
            }
        },
        "zero_optimization": {
            "stage": config.deepspeed_stage,
            "offload_optimizer": {"device": "cpu"},
            "offload_param": {"device": "cpu"},
            "overlap_comm": True,
            "contiguous_gradients": True,
            "reduce_bucket_size": 5e8,
            "stage3_prefetch_bucket_size": 5e8,
            "stage3_param_persistence_threshold": 1e6,
        },
        "fp16": {"enabled": False},
        "bf16": {"enabled": True},
        "gradient_clipping": 1.0,
        "steps_per_print": 10,
        "wall_clock_breakdown": False,
    }


def train_persona(persona: str, data_path: str):
    """Train LoRA adapter for a specific persona."""
    print(f"🚀 Starting {persona} training on AMD MI300X...")
    
    model, tokenizer = prepare_model_and_tokenizer(persona)
    dataset = PersonaDataset(data_path, tokenizer, config.max_seq_length)
    
    output_dir = os.path.join(config.output_dir, f"{persona}_lora")
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=config.per_device_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        warmup_ratio=config.warmup_ratio,
        num_train_epochs=config.num_epochs,
        max_steps=config.max_steps,
        learning_rate=config.learning_rate,
        bf16=True,
        logging_steps=10,
        save_steps=500,
        save_total_limit=3,
        remove_unused_columns=False,
        report_to="wandb",
        run_name=f"revarie-{persona}-lora-{datetime.now().strftime('%Y%m%d-%H%M')}",
        deepspeed=get_deepspeed_config() if config.use_deepspeed else None,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    
    trainer.train()
    
    # Save final adapter
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"✅ {persona} training complete. Model saved to {output_dir}")
    
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Train Revarie LoRA adapters on AMD MI300X")
    parser.add_argument("--persona", choices=["samara", "artery", "both"], default="both")
    parser.add_argument("--samara_data", type=str, required=True)
    parser.add_argument("--artery_data", type=str, required=True)
    parser.add_argument("--upload_hf", action="store_true")
    args = parser.parse_args()
    
    if args.persona in ["samara", "both"]:
        train_persona("samara", args.samara_data)
    
    if args.persona in ["artery", "both"]:
        train_persona("artery", args.artery_data)
    
    if args.upload_hf:
        from huggingface_hub import HfApi
        api = HfApi(token=config.hf_token or os.environ.get("HF_TOKEN"))
        if args.persona in ["samara", "both"]:
            api.upload_folder(folder_path=f"{config.output_dir}/samara_lora", repo_id=config.hf_repo_samara)
        if args.persona in ["artery", "both"]:
            api.upload_folder(folder_path=f"{config.output_dir}/artery_lora", repo_id=config.hf_repo_artery)
        print("📤 Uploaded adapters to Hugging Face")


if __name__ == "__main__":
    main()
