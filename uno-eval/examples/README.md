---
language:
- zh
- en
license: apache-2.0
base_model: Qwen/Qwen3-14B
library_name: transformers
tags:
- qwen
- scoring
- grading
- evaluation
- llm-judge
pipeline_tag: text-generation
---

# UNO-Scorer: A Unified General Scoring Model for UNO-Bench

<div align="center">

[![Paper](https://img.shields.io/badge/Paper-Arxiv%3A2510.18915-red)](https://arxiv.org/abs/2510.18915)
[![Base Model](https://img.shields.io/badge/Base%20Model-Qwen3--14B-blue)](https://huggingface.co/Qwen/Qwen3-14B)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)]()

</div>

## 📖 Introduction

**UNO-Scorer** is a lightweight yet high-precision general scoring model developed as part of **UNO-Bench**. It is designed to efficiently automate the evaluation of Large Multimodal Models (LMMs) with minimal computational overhead.

Built upon the powerful **Qwen3-14B** backbone, UNO-Scorer is fine-tuned on 13K high-quality in-house data. It overcomes the limitations of traditional Overall Reward Models (ORMs) by supporting **6 distinct question types**, with particular excellence in **Multi-Step Open-Ended Questions (MO)**.

## 📊 Performance

UNO-Scorer demonstrates superior performance in automated evaluation, particularly in handling complex **Multi-Step Open-Ended Questions**. We compared the accuracy of our scorer against other advanced evaluators:

| Model | Accuracy |
| :--- | :--- |
| Seed-1.5-VL | 0.9118 |
| GPT-4.1 | 0.9457 |
| **UNO-Scorer (Ours)** | **0.9505** |

Experiments show that UNO-Scorer surpasses even proprietary frontier models like GPT-4.1 in this specific evaluation domain with lower cost.



## 💻 Usage

### 0. Quick Start

```bash
pip install -U transformers
python3 test_scorer_hf.py --model-name /path/to/your/model
```

We recommend using vLLM for inference as it offers significantly better efficiency compared to the standard HuggingFace approach. Please follow the steps below to set up the environment and run the inference script provided in our official repository.


### 1. Clone the Repository
First, clone the UNO-Bench repository:

```bash
git clone https://github.com/meituan-longcat/UNO-Bench.git
cd UNO-Bench/uno_eval
```

### 2. Install Dependencies
Install the necessary Python libraries:

```bash
pip install -r requirement.txt
```

### 3. Run Inference
We provide an example script based on **vLLM** for efficient model inference. You can run the following command to test the scorer:

```bash
bash examples/test_scorer.sh
```

### 4. Adapt Your Reference Answer
The most critical aspect of utilizing the UNO-Scorer lies in the proper formatting of the Reference Answer. Specifically, it is required to:

1. Assign point values to the answer components. The total points for the question should typically sum to 10 points.
2. You may customize detailed scoring criteria for each reference answer to suit your needs(e.g., clarifying how to judge cases where the final choice is correct but the reasoning is flawed).

Note: Since the model is primarily trained on Chinese corpora, it adheres more accurately to instructions when these specific descriptions are written in Chinese.

You can structure the Reference Answer as follows:

| Question Type | Scenario | **Reference Answer** | Example |
| :--- | :--- | :--- | :--- |
| **Single Question** | The model only needs to check if the final result matches. | Format as a single sub-question (Sub-question 1) worth exactly 10 points.<br><br>Template:<br>`小问1：{Answer}，总分10分，无需关注推理过程，最终答案正确即可` | **Raw Answer:** "C"<br>**Input Answer:** `小问1：C，总分10分，无需关注推理过程，最终答案正确即可` |
| **Multiple Question** | The model needs to grade specific checkpoints. | Break down the answer into numbered sub-steps with assigned points (summing to exactly 10).<br><br>Template:<br>`1. {Sub-Answer A} ({X} points); 2. {Sub-Answer B} ({Y} points).` | **Raw Answer:** "5 apples, 6 bananas"<br>**Input Answer:** `1. 5 apples (4 points); 2. 6 bananas (6 points).` |


## 📜 Citation

If you find this model or the UNO-Bench useful for your research, please cite our paper:

```bibtex
@misc{chen2025unobench,
      title={UNO-Bench: A Unified Benchmark for Exploring the Compositional Law Between Uni-modal and Omni-modal in Omni Models},
      author={Chen Chen and ZeYang Hu and Fengjiao Chen and Liya Ma and Jiaxing Liu and Xiaoyu Li and Ziwen Wang and Xuezhi Cao and Xunliang Cai},
      year={2025},
      eprint={2510.18915},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2510.18915},
}
```

---

**Disclaimer:** This model is based on Qwen3-14B. Please strictly follow the license and usage policy of the original Qwen model series.