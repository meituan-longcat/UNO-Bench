#!/bin/bash

# ---------------- Configuration Area ----------------
# 1. Inference Model Configuration
MODEL_NAME="Qwen-2.5-Omni-7B" # # requied, registered in ./models
EXP_MARKING="_20251024" # recommended
MODEL_PATH="/path/to/model" # requied
DATASET_NAME="UNO-Bench"
# Option 1: Use a local dataset path
DATASET_LOCAL_DIR="/path/to/dataset"
# Option 2: Use Hugging Face cache path and the program will download this dataset from Hugging Face
HF_CACHE_DIR="~/.cache/huggingface/hub"

# Inference Backend Configuration
# Options: "hf" (local HF loading) or "vllm" (start VLLM service)
INFERENCE_BACKEND="hf" # requied
TARGET_PORT=8000
TARGET_GPU_IDS="0,1"
TARGET_TP_SIZE=2

# 2. Scorer Model Configuration (UNO-Scorer)
SCORER_MODEL_PATH="/path/to/scorer" # requied
SCORER_PORT=8001
SCORER_GPU_IDS="0,1"
SCORER_TP_SIZE=2
# ------------------------------------------

set -e

# Global variables to store PIDs for cleanup
TARGET_VLLM_PID=""
SCORER_VLLM_PID=""

# === Cleanup Function ===
cleanup() {
    echo "--- [Cleanup] Checking for background processes... ---"
    if [ -n "$TARGET_VLLM_PID" ]; then
        if ps -p $TARGET_VLLM_PID > /dev/null; then
            echo "Stopping Target Inference VLLM (PID: $TARGET_VLLM_PID)..."
            kill $TARGET_VLLM_PID
            wait $TARGET_VLLM_PID 2>/dev/null || true
            echo "Target VLLM stopped."
        fi
    fi
    if [ -n "$SCORER_VLLM_PID" ]; then
        if ps -p $SCORER_VLLM_PID > /dev/null; then
            echo "Stopping Scorer VLLM (PID: $SCORER_VLLM_PID)..."
            kill $SCORER_VLLM_PID
            wait $SCORER_VLLM_PID 2>/dev/null || true
            echo "Scorer VLLM stopped."
        fi
    fi
}
trap cleanup EXIT SIGINT SIGTERM

# ==========================================
# Stage 1: Inference
# ==========================================
echo ">>> Stage 1: Running Inference ($INFERENCE_BACKEND mode)..."

if [ "$INFERENCE_BACKEND" == "vllm" ]; then
    # --- 1.1 Set environment variables specific to Qwen2.5-Omni ---

    export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
    
    echo "Starting Target Model VLLM Server..."
    echo "VIDEO_MAX_PIXELS set to: $VIDEO_MAX_PIXELS"

    # --- 1.2 Start VLLM (based on your parameters) ---
    CUDA_VISIBLE_DEVICES=$TARGET_GPU_IDS vllm serve "$MODEL_PATH" \
        --port $TARGET_PORT \
        --allowed-local-media-path "$HF_CACHE_DIR" \
        --limit_mm_per_prompt image=8 \
        --max-model-len 131072 \
        --tensor-parallel-size $TARGET_TP_SIZE \
        --trust-remote-code \
        > target_vllm.log 2>&1 &
    
    TARGET_VLLM_PID=$!
    echo "Target VLLM PID: $TARGET_VLLM_PID"

    # --- 1.3 Run Client for inference ---
    # Note: eval.py does not require a GPU, and --dataset_local_dir should preferably point to the media directory or its parent.
    CUDA_VISIBLE_DEVICES="" python3 eval.py \
        --mode inference \
        --model_name "$MODEL_NAME" \
        --model_path "$MODEL_PATH" \
        --model_api_url "http://localhost:$TARGET_PORT/v1/chat/completions" \
        --dataset_name "$DATASET_NAME" \
        --hf_cache_dir "$HF_CACHE_DIR" \
        --dataset_local_dir "$DATASET_LOCAL_DIR" \
        --exp_marking "$EXP_MARKING" \
        --batch_size 16

    echo ">>> Inference finished. Stopping Target VLLM to release GPUs..."
    
    # --- 1.4 Force release of resources (critical step) ---
    kill $TARGET_VLLM_PID
    wait $TARGET_VLLM_PID 2>/dev/null || true
    TARGET_VLLM_PID=""
    
    unset VLLM_ALLOW_LONG_MAX_MODEL_LEN
    
    echo ">>> Target GPU resources released."

else
    # --- Local HF Mode ---
    CUDA_VISIBLE_DEVICES=$TARGET_GPU_IDS python3 eval.py \
        --mode inference \
        --model_name "$MODEL_NAME" \
        --model_path "$MODEL_PATH" \
        --dataset_name "$DATASET_NAME" \
        --exp_marking "$EXP_MARKING" \
        --hf_cache_dir "$HF_CACHE_DIR" \
        --dataset_local_dir "$DATASET_LOCAL_DIR" \
        --batch_size 1
fi

# ==========================================
# Stage 2: Start Scorer Service (VLLM Scorer)
# ==========================================
echo ">>> Stage 2: Starting Scorer VLLM Server..."

# The Scorer does not need those special Omni environment variables and parameters
CUDA_VISIBLE_DEVICES=$SCORER_GPU_IDS vllm serve "$SCORER_MODEL_PATH" \
    --port $SCORER_PORT \
    --max-model-len 32768 \
    --tensor-parallel-size $SCORER_TP_SIZE \
    --trust-remote-code \
    --gpu-memory-utilization 0.9 \
    > scorer_vllm.log 2>&1 &

SCORER_VLLM_PID=$!
echo "Scorer VLLM PID: $SCORER_VLLM_PID"

# ==========================================
# Stage 3: Evaluation
# ==========================================
echo ">>> Stage 3: Running Evaluation/Scoring..."

CUDA_VISIBLE_DEVICES="" python3 eval.py \
    --mode scoring \
    --model_name "$MODEL_NAME" \
    --exp_marking "$EXP_MARKING" \
    --scorer_api_url "http://localhost:$SCORER_PORT/v1/chat/completions" \
    --dataset_name "$DATASET_NAME" \
    --hf_cache_dir "$HF_CACHE_DIR" \
    --dataset_local_dir "$DATASET_LOCAL_DIR"

echo ">>> Benchmark Workflow Completed Successfully."