[English](README.md) | [中文](README-zh.md)

---
# UNO评估框架

为了更通用地评估各种Omni评测集，我们构建了一个轻量级的Omni评估框架，并发布了一个高性能的打分模型用以支持评分，你可以自由且便捷地基于此框架新增数据集或评测模型。接下来，我们将以**UNO-Bench**和**Qwen-2.5-Omni-7B**为例，介绍如何运行框架。
# 🚀 快速开始

## 🛠️ 环境准备

运行前请确保安装以下Python核心依赖。注意：由于vLLM的安装涉及PyTorch、CUDA等复杂依赖，建议在新的虚拟环境中进行安装，以避免潜在的依赖冲突问题。

```bash
pip install -r requirements.txt
```

接下来你可以通过以下命令下载必要的模型权重和数据集：
```bash
huggingface-cli download meituan-longcat/UNO-Bench --repo-type dataset --local-dir /path/to/UNO-Bench
huggingface-cli download meituan-longcat/UNO-Scorer-Qwen3-14B --local-dir /path/to/UNO-Scorer
huggingface-cli download Qwen/Qwen2.5-Omni-7B --local-dir /path/to/Qwen2.5-Omni
```

## 🎯  实验复现
通过执行如下代码，你可以复现论文中Qwen-2.5-Omni-7B的实验结果。记得将**MODEL_PATH**、**DATASET_LOCAL_DIR**和**SCORER_MODEL_PATH**替换为你本地数据集路径。
```bash
bash examples/run_unobench_qwen_omni_hf.sh
```
更推荐执行vLLM版本的推理服务，具有更好的性能表现。
```bash
bash examples/run_unobench_qwen_omni_vllm.sh
```
*   程序采用串行逻辑进行评估，依次执行：`启动推理服务 -> 结果生成 -> 资源释放 -> 启动打分服务 -> 计算分数 -> 资源释放`
*   支持断点续评，推理进度和打分进度均会以一定间隔保存到本地。

## 📈 Compositional Law
Compositional Law的拟合曲线可以参考如下代码。
```python
python3 compositional_law.py
```

## 🤖 只使用打分模型
我们推荐使用vLLM以获取更高的效率，你可以参考：
```bash
bash examples/test_scorer_vllm.sh
```
或者基于transformers，但是效率较低：
```python
python3 examples/test_scorer_hf.py
```
## ⚙️ 配置指南

在运行之前，**必须** 修改 `run_unobench_qwen_omni_*.sh` 顶部的配置区域以适配你的环境。

### 1. 推理模型配置 (Target Model)

| 变量名 | 说明 | 示例 |
| :--- | :--- | :--- |
| `MODEL_NAME` | 模型注册名称 (对应 `models` 代码中定义的名称) | `"Qwen-2.5-Omni-7B" "VLLMClient"` |
| `MODEL_PATH` | 模型权重所在的本地绝对路径 | `/path/to/Qwen2.5-Omni` |
| `INFERENCE_BACKEND` | 推理后端选择：`"vllm"` 或 `"hf"` | `"vllm"` |
| `TARGET_GPU_IDS` | 推理阶段使用的 GPU 编号 | `"0,1"` |
| `TARGET_TP_SIZE` | 推理模型的 Tensor Parallelism 大小 | `2` |
| `TARGET_PORT` | vLLM 服务端口 | `8000` |

### 2. 打分模型配置 (Scorer Model)

| 变量名 | 说明 | 示例 |
| :--- | :--- | :--- |
| `SCORER_MODEL_PATH` | 打分模型UNO-Scorer的路径 | `/path/to/UNO-Scorer` |
| `SCORER_GPU_IDS` | 打分阶段使用的 GPU 编号 | `"0,1"` |
| `SCORER_PORT` | 打分服务vLLM端口 | `8001` |

### 3. 数据集与路径

| 变量名 | 说明 |
| :--- | :--- |
| `DATASET_NAME` | 评测数据集名称 (如 `"UNO-Bench"`) |
| `HF_CACHE_DIR` | HuggingFace 缓存或多媒体数据目录，自动下载的数据集会保存在此处 |
|`DATASET_LOCAL_DIR`|数据集本地路径， 程序会优先从DATASET_LOCAL_DIR读取数据，否则自动下载至HF_CACHE_DIR|
| `EXP_MARKING` | 实验标记后缀 (如 `_test`)，用于区分实验设置以及输出文件名 |

## 🌀 运行评测

配置完成后，授予脚本执行权限并运行：

```bash
bash run_eval.sh
```

### 脚本执行流程详解

1.  **Stage 1: Inference (推理)**
    *   若选择 `vllm` 模式，脚本将在后台启动目标模型的 API Server。
    *   运行 `eval.py --mode inference` 进行数据推理。
    *   **关键步骤**：推理完成后，脚本会自动 kill 掉目标模型的 vLLM 进程，完全释放 GPU 显存。
2.  **Stage 2: Scorer Setup (启动打分)**
    *   在后台启动打分模型（Scorer）的 vLLM 服务。
3.  **Stage 3: Evaluation (评分)**
    *   运行 `eval.py --mode scoring`，将生成结果发送给打分模型进行评估。
4.  **Cleanup (清理)**
    *   任务结束，自动关闭打分模型服务。

## 📊 结果输出

评测结果将生成 JSON 文件，默认保存在 `./eval_results/` 目录下。

*   **文件名格式**: `{MODEL_NAME}{EXP_MARKING}:{DATASET_NAME}.json`


## 📂 极简开发指南

```text
.
├── run_eval.sh    # [主程序] 负责配置参数、服务生命周期管理及流程控制
├── eval.py             # [执行脚本] 负责数据加载、API交互及结果存储
├── utils/              # [依赖] 通用工具函数集
├── models/             # [依赖] 模型注册与加载
└── benchmarks/         # [依赖] 数据集注册与加载
```

项目主要分为评测集和评测模型两部分，你可以在benchmarks/下注册新数据集，在models/下注册新模型。

### 新增评测集
1. 在benchmarks/下新建一个新数据集.py文件，如unobench.py，内部继承BaseDataset类，并实现其中的抽象方法。
    - `load_and_prepare`，下载并加载评测集，并将每条数据组织为`utils.EvaluationRecord`格式。
    - `build_message`，构建发送到模型侧的消息，格式为OpenAI Chat Message。
    - `build_score_message`，构建发送到打分模型的消息，格式为OpenAI Chat Message。
    - `compute_score`，计算单条数据的分数。
    - `compute_metrics`，计算整个数据集的所有指标。
2. 在__init__.py中注册该数据集。

### 新增评测模型
1. 在models/下新建一个新模型.py文件，如何qwen_2d5_omni_7b.py，内部继承BaseModel类，并实现其中的抽象方法。
    - `load_model`，加载模型。
    - `generate`，单次调用模型接口生成文本。
    - `generate_batch`，批量调用模型接口生成文本。
2. 在__init__.py中注册该模型。

## ⚠️ 注意事项

*   **路径检查**: 请确保脚本中的路径已修改为你服务器上的实际路径。