#!/bin/bash
# One-click Google Colab Setup Script for Eli Fine-Tuning
set -e

export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0

echo "=== 1. INSTALLING UNSLOTH & DEPENDENCIES ==="
pip install --quiet "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --quiet --no-deps xformers "trl<0.9.0" peft accelerate bitsandbytes datasets

echo "=== 2. PREPARING DATASET ==="
python3 collector/prepare_training_data.py

echo "=== 3. LAUNCHING UNSLOTH FINE-TUNING ==="
python3 train_eli_colab.py

echo "=== 4. LAUNCHING HELD-OUT EMERGENCE EVALUATION ==="
python3 eval_emergence.py --lora_path ./models/eli-tone-lora
