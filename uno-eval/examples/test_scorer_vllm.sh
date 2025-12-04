#!/bin/bash

# Scorer Model Configuration (Qwen3-14B-Scorer)
SCORER_MODEL_PATH="/path/to/scorer" # requied
SCORER_PORT=8000
SCORER_GPU_IDS="0,1"
SCORER_TP_SIZE=2
SCORER_VLLM_PID=""
# ------------------------------------------
set -e
# ==========================================
# Stage 1: Start Scorer Service (vLLM Scorer)
# ==========================================
echo ">>> Stage 1: Starting Scorer vLLM Server..."

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
# Stage 2: Test Scorer Service (vLLM Scorer)
# ==========================================
echo ">>> Stage 2: Testing Scorer Service..."
python3 examples/test_scorer.py --scorer_api_url "http://localhost:$SCORER_PORT/v1/chat/completions"

# === Cleanup Function ===
cleanup() {
    echo "--- [Cleanup] Checking for background processes... ---"
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

