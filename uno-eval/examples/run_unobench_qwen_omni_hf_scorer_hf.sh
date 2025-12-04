#!/bin/bash

# ---------------- Configuration Area ----------------
# 1. Inference Model Configuration
MODEL_NAME="Qwen-2.5-Omni-7B" # # requied, registered in ./models
EXP_MARKING="_20251127" # recommended
MODEL_PATH="/path/to/model" # requied
DATASET_NAME="UNO-Bench"

# Inference Backend Configuration
# Options: "hf" (local HF loading) or "vllm" (start VLLM service)
INFERENCE_BACKEND="hf" # requied
# Option 1: Use a local dataset path
DATASET_LOCAL_DIR="/path/to/dataset"
# Option 2: Use Hugging Face cache path and the program will download this dataset from Hugging Face
HF_CACHE_DIR="~/.cache/huggingface/hub"
TARGET_GPU_IDS="0,1"
TARGET_TP_SIZE=2
SCORER_MODEL_PATH="/path/to/scorer" # requied
# ------------------------------------------

CUDA_VISIBLE_DEVICES=$TARGET_GPU_IDS python3 eval.py \
    --mode inference \
    --model_name "$MODEL_NAME" \
    --model_path "$MODEL_PATH" \
    --dataset_name "$DATASET_NAME" \
    --exp_marking "$EXP_MARKING" \
    --hf_cache_dir "$HF_CACHE_DIR" \
    --dataset_local_dir "$DATASET_LOCAL_DIR" \
    --batch_size 1
# ==========================================
# Stage 2: Evaluation
# ==========================================
echo ">>> Stage 3: Running Evaluation/Scoring..."

CUDA_VISIBLE_DEVICES=$TARGET_GPU_IDS python3 eval.py \
    --mode scoring \
    --model_name "$MODEL_NAME" \
    --exp_marking "$EXP_MARKING" \
    --dataset_name "$DATASET_NAME" \
    --hf_cache_dir "$HF_CACHE_DIR" \
    --dataset_local_dir "$DATASET_LOCAL_DIR" \
    --scorer_model_path "$SCORER_MODEL_PATH" \
    --batch_size 8 \
    --save_batch_size 32

echo ">>> Benchmark Workflow Completed Successfully."