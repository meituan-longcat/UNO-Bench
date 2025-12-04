[English](README.md) | [中文](README-zh.md)

---

# UNO Evaluation Framework

To facilitate generalized evaluation of various Omni benchmarks, we have constructed a lightweight Omni evaluation framework and released a high-performance scoring model to support it. You can freely and easily add new datasets or evaluation models based on this framework. Below, we will use **UNO-Bench** and **Qwen-2.5-Omni-7B** as examples to demonstrate how to run the framework.

# 🚀 Quick Start

## 🛠️ Environment Preparation

Before running, please ensure the following Python core dependencies are installed. Note: Since vLLM installation involves PyTorch, CUDA, and other complex dependencies, it is recommended to set up the environment in a fresh virtual environment to avoid potential conflicts.
```bash
pip install -r requirements.txt
```
Download the necessary models and datasets using the following commands:
```bash
huggingface-cli download meituan-longcat/UNO-Bench --repo-type dataset --local-dir /path/to/UNO-Bench
huggingface-cli download meituan-longcat/UNO-Scorer-Qwen3-14B --local-dir /path/to/UNO-Scorer
huggingface-cli download Qwen/Qwen2.5-Omni-7B --local-dir /path/to/Qwen2.5-Omni
```
## 🎯 Reproducing Experimental Results

By executing the following code, you can reproduce the experimental results of **Qwen-2.5-Omni-7B** presented in the paper. Remember to replace **MODEL_PATH**, **DATASET_LOCAL_DIR**, and **SCORER_MODEL_PATH** with your local path.
```bash
bash examples/run_unobench_qwen_omni_hf.sh
```

We recommend you to execute the vLLM version of the inference service for better performance.

```bash
bash examples/run_unobench_qwen_omni_vllm.sh
```

*   The program employs sequential logic for evaluation, executing in the following order: `Start Inference Service -> Generate Results -> Release Resources -> Start Scoring Service -> Calculate Scores -> Release Resources`.
*   It supports **resuming from breakpoints** (checkpointing); both inference progress and scoring progress are saved locally at regular intervals.

## 📈 Compositional Law
You can refer to the following code for the fitting curve of the Compositional Law.

```python
python3 compositional_law.py
```

## 🤖 Using Only the Scoring Model
We recommend using vLLM for higher efficiency. You can refer to:
```bash
bash examples/test_scorer_vllm.sh
```
Or use transformers-based approach, but with lower efficiency:
```python
python3 examples/test_scorer_hf.py
```

## ⚙️ Configuration Guide

Before running, you **must** modify the configuration section at the top of `run_unobench_qwen_omni_*.sh` to adapt to your environment.

### 1. Inference Model Configuration (Target Model)

| Variable Name | Description | Example |
| :--- | :--- | :--- |
| `MODEL_NAME` | Model registration name (corresponds to the name defined in `models` code) | `"Qwen-2.5-Omni-7B"` `"VLLMClient"` |
| `MODEL_PATH` | Local absolute path to the model weights | `/path/to/Qwen2.5-Omni` |
| `INFERENCE_BACKEND` | Inference backend selection: `"vllm"` or `"hf"` | `"vllm"` |
| `TARGET_GPU_IDS` | GPU IDs used for the inference stage | `"0,1"` |
| `TARGET_TP_SIZE` | Tensor Parallelism size for the inference model | `2` |
| `TARGET_PORT` | vLLM service port | `8000` |

### 2. Scorer Model Configuration (Scorer Model)

| Variable Name | Description | Example |
| :--- | :--- | :--- |
| `SCORER_MODEL_PATH` | Path to the scoring model (e.g., UNO-Scorer) | `/path/to/UNO-Scorer` |
| `SCORER_GPU_IDS` | GPU IDs used for the scoring stage | `"0,1"` |
| `SCORER_PORT` | vLLM service port for the scorer | `8001` |

### 3. Dataset and Paths

| Variable Name | Description |
| :--- | :--- |
| `DATASET_NAME` | Evaluation dataset name (e.g., `"UNO-Bench"`) |
| `HF_CACHE_DIR` | HuggingFace cache or multimedia data directory; automatically downloaded datasets will be saved here |
| `DATASET_LOCAL_DIR` | Local path for the dataset. The program prioritizes reading from `DATASET_LOCAL_DIR`; otherwise, it automatically downloads to `HF_CACHE_DIR` |
| `EXP_MARKING` | Experiment marking suffix (e.g., `_20251024`), used to distinguish experimental settings and output filenames |

## 🌀 Running Evaluation

After configuration, grant execution permissions to the script and run it:

```bash
bash run_eval.sh
```

### Detailed Script Execution Flow

1.  **Stage 1: Inference**
    *   If `vllm` mode is selected, the script starts the target model's API Server in the background.
    *   Runs `eval.py --mode inference` to perform data inference.
    *   **Key Step**: After inference is complete, the script automatically kills the target model's vLLM process to fully release GPU memory.
2.  **Stage 2: Scorer Setup**
    *   Starts the Scoring Model's (Scorer) vLLM service in the background.
3.  **Stage 3: Evaluation (Scoring)**
    *   Runs `eval.py --mode scoring` to send the generated results to the scoring model for evaluation.
4.  **Cleanup**
    *   Upon task completion, automatically shuts down the scoring model service.

## 📊 Output Results

Evaluation results will be generated as JSON files, saved by default in the `./eval_results/` directory.

*   **Filename Format**: `{MODEL_NAME}{EXP_MARKING}:{DATASET_NAME}.json`

## 📂 Minimalist Development Guide

```text
.
├── run_eval.sh         # [Main Program] Manages config parameters, service lifecycle, and flow control
├── eval.py             # [Execution Script] Handles data loading, API interaction, and result storage
├── utils/              # [Dependencies] General utility functions
├── models/             # [Dependencies] Model registration and loading
└── benchmarks/         # [Dependencies] Dataset registration and loading
```

The project is mainly divided into benchmarks (evaluation sets) and evaluation models. You can register new datasets in `benchmarks/` and new models in `models/`.

### Adding New Datasets
1.  Create a new dataset `.py` file in `benchmarks/`, such as `unobench.py`. Inherit from the `BaseDataset` class and implement the abstract methods:
    *   `load_and_prepare`: Download and load the dataset, organizing each item into the `utils.EvaluationRecord` format.
    *   `build_message`: Construct the message sent to the model side (OpenAI Chat Message format).
    *   `build_score_message`: Construct the message sent to the scoring model (OpenAI Chat Message format).
    *   `compute_score`: Calculate the score for a single data item.
    *   `compute_metrics`: Calculate metrics for the entire dataset.
2.  Register the dataset in `__init__.py`.

### Adding New Models
1.  Create a new model `.py` file in `models/`, such as `qwen_2d5_omni_7b.py`. Inherit from the `BaseModel` class and implement the abstract methods:
    *   `load_model`: Load the model.
    *   `generate`: Call the model interface once to generate text.
    *   `generate_batch`: Batch call the model interface to generate text.
2.  Register the model in `__init__.py`.

## ⚠️ Precautions
*   **Path Check**: Please ensure that the paths in the script have been modified to match the actual paths on your server.