#!/bin/bash
# =============================================================================
# run‑training.sh – AMD MI300X Training Orchestrator
# =============================================================================

set -e

echo "🚀 Starting Revarie LoRA Training on AMD MI300X"
echo "==============================================="

# Configuration
SAMARA_DATA="${SAMARA_DATA:-/data/samara_training.jsonl}"
ARTERY_DATA="${ARTERY_DATA:-/data/artery_training.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"
HF_TOKEN="${HF_TOKEN:-}"

# Train both personas
echo "📚 Training Samara adapter..."
python train_persona_lora.py \
    --persona samara \
    --samara_data "$SAMARA_DATA" \
    --artery_data "$ARTERY_DATA"

echo "📚 Training Artery adapter..."
python train_persona_lora.py \
    --persona artery \
    --samara_data "$SAMARA_DATA" \
    --artery_data "$ARTERY_DATA"

# Export to ONNX
echo "📦 Exporting to ONNX..."
python export_to_onnx.py \
    --base_model "meta-llama/Llama-3.2-3B-Instruct" \
    --lora_path "$OUTPUT_DIR/samara_lora" \
    --output "$OUTPUT_DIR/samara_lora/model.onnx"

python export_to_onnx.py \
    --base_model "meta-llama/Llama-3.2-3B-Instruct" \
    --lora_path "$OUTPUT_DIR/artery_lora" \
    --output "$OUTPUT_DIR/artery_lora/model.onnx"

# Upload to Hugging Face (if token provided)
if [ -n "$HF_TOKEN" ]; then
    echo "📤 Uploading to Hugging Face..."
    huggingface-cli upload project-imace/revarie-samara-lora "$OUTPUT_DIR/samara_lora" . --token "$HF_TOKEN"
    huggingface-cli upload project-imace/revarie-artery-lora "$OUTPUT_DIR/artery_lora" . --token "$HF_TOKEN"
fi

echo "✅ Training complete!"
