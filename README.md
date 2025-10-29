<h1> UNO-Bench: A Unified Benchmark for Exploring the Compositional Law Between Uni-modal and Omni-modal in OmniModels</h1>
<p align="center" width="100%">
<img src="assets/uno-bench-title.jpg"  width="80%" height="100%">
</p>

<font size=7><div align='center' >  
[[📑 Paper](./UNO-Bench.pdf)] 
[🌐 [Project](https://meituan-longcat.github.io/UNO-Bench)]
[📊 ArXiv(updating)]
[[🤗 Data](https://huggingface.co/datasets/meituan-longcat/UNO-Bench)] 
</div></font>

## 👀 UNO-Bench Overview
Multimodal Large Language Models are advancing from uni-modal to omni-modal understanding, integrating visual, audio, and language modalities. However, the relationship between uni-modal and omni-modal performance needs clarification, necessitating thorough evaluation to enhance omni model intelligence. We introduce **UNO-Bench**, a novel benchmark that evaluates both uni-modal and omni-modal capabilities. It includes 3730 human curated samples, with 98% cross-modality solvability, across 44 task types, and features an innovative multi-step open-ended question type for assessing complex reasoning. Additionally, we propose a general scoring model supporting 6 question types for automatic evaluation with 95% accuracy. Experimental results reveal a **Compositional Law** between omni-modal and uni-modal performance, with omni-modal capability acting as a bottleneck for weak models but promoting synergy in strong models.

<div>
<p align="center">
  <img src="./assets/omni-ability.png" width="80%" height="100%" />
</p>
</div>

<!-- The MultiModal Benchmarks compare image (I), audio (A), video (V), and text (T) modalities, reporting omni-modal solution accuracy (Acc.) and percentage (Solvable). Source origin affects data contamination, with private sources being safer. QA types are multi-choice (MC) and multi-step open-ended (MO), in English (EN) and Chinese (CH). UNO-Bench features 1250 omni-modal (-omni) and 2480 uni-modal (-uni) samples. -->

<div>
<p align="center">
  <img src="./assets/data-statistics.png" width="80%" height="100%" />
</p>
</div>

**Main Contributions**

- 🌟 **Propose UNO-Bench, the first unified omni model benchmark**, efficiently assessing uni-modal and omni-modal understanding. It verifies the compositional law between these capabilities, acting as a bottleneck for weaker models and enhancing stronger ones.

- 🌟 **Establish a high-quality dataset pipeline** with human-centric processes and automated compression. UNO-Bench contains 1250 omni-modal samples with 98% cross-modality solvability and 2480 uni-modal samples across 44 task types and 6 question types. The dataset excels in real-world scenarios, especially in China, and offers a 90% speed increase while maintaining 98% consistency across 18 benchmarks.

- 🌟 **Introduce Multi-Step Open-Ended Questions (MO)** for complex reasoning evaluation, providing realistic results. A General Scoring Model supports 6 question types with 95% accuracy on OOD models and benchmarks.


## 📊 Dataset Construction

**Material Collection**

Our materials feature three key characteristics: **a. Diverse Sources**—primarily real-world photos and videos from crowdsourcing, supplemented by copyright-free websites and high-quality public datasets . **b. Rich and Diverse Topics**—spanning society, culture, art, life, literature, and science. **c. Live-Recorded Audio**—dialogue recorded by over 20 human speakers, ensuring rich audio features that mirror real-world vocal diversity.

**QA Annotation**

Our annotators include human experts and skilled crowd-sourced users. Human experts bring extensive experience in cross-modal data and model understanding, ensuring professional and specific data. Crowd-sourced users, mainly college students, offer authentic and diverse data due to their experience with multi-modal models and varied backgrounds.

**Quality Inspection**

To ensure data quality, we use a multi-stage quality assurance system combining automated tools and manual review. Each question undergoes three independent inspections: a preliminary model check filters out ambiguous or non-conforming questions; modality ablation experiments test cross-modality solvability by removing one modality; and final manual inspection and revision ensure accuracy.

**Data Compression**

Regarding automated data compression, we propose a cluster-guided stratified sampling method to compress the scale of 18 public benchmarks and achieve a 90% dataset compression with 98% ranking consistency.

<div>
<p align="center">
  <img src="./assets/omni-data-pipeline.png" width="80%" height="100%" />
</p>
</div>

## 📍 Dataset Examples

The capabilities of UNO-Bench are systematically categorized into two primary dimensions: Perception and Reasoning. Please click [data link](https://huggingface.co/datasets/meituan-longcat/UNO-Bench) to download UNO-Bench. 

Below shows some examples from UNO-Bench:

<p align="center">
<img alt="image2" src="./assets/omni-perception-cases.png" />
</p>

---

<p align="center">
<img alt="image2" src="./assets/omni-reasoning-cases.png" />
</p>

For more samples, please refer to [project page](https://meituan-longcat.github.io/UNO-Bench).

## 🔍 Results

Our main evaluation reveals a clear performance hierarchy where proprietary models, particularly Gemini-2.5-Pro, establish the state-of-the-art across all benchmarks.
<p align="center">
  <img src="./assets/cross-modal-results.png" width="60%" height="100%" />
</p>

**Finding 1. 📍Gemini-2.5-Pro demonstrates human-like perception in omni-modal understanding but lags in reasoning ability.** The model's performance is only 8.3% lower than human experts, indicating comparable intelligence. Interestingly, humans excel more in reasoning (81.3%) than perception (74.3%), contrasting with the model's strengths.

<p align="center">
  <img src="./assets/gemini-2.5-vs-human.png" width="60%" height="100%" />
</p>

**Finding 2. 📍Compositional Law: Omni-modal capability effectiveness correlates with the product of individual modality performances following a power-law.** The observed omni-modal scores align closely with the product of uni-modal scores, as shown by the fitted law (dashed line), achieving an impressive $R^2=0.9759$. The convex, accelerating curve illustrates the power-law synergy.

$$
P_{\text{Omni}} = C \cdot (P_{\text{Audio}} \times P_{\text{Visual}})^{\alpha} + b
$$
<p align="center">
  <img src="./assets/compositional-law.png" width="60%" height="100%" />
</p>

## 📌 Checklist

- **Data**
  - ✅ Paper
  - ✅ Dataset Examples
  - 🚧 Benchmark Leaderboard
  - 🚧 UNO-Bench Dataset
- **Code**
  - 🚧 Evaluation Toolkit
  - 🚧 Model Weights and Configurations

## 🖊️ Citation

If you find our work helpful for your research, please consider citing our work.
```bash
@misc{chen2025unobench,
      title={UNO-Bench: A Unified Benchmark for Exploring the Compositional Law Between Uni-modal and Omni-modal in OmniModels}, 
      author={Chen Chen and ZeYang Hu and Fengjiao Chen and Liya Ma and Jiaxing Liu and Xiaoyu Li and Xuezhi Cao and Xunliang Cai},
      year={2025},
      eprint={2510.18915},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={arxiv}, 
}
```

## 🔮 Data Statements

The majority of our materials are real-world photos and videos collected through crowdsourcing, while a small fraction comes from high-quality public datasets such as [MMVU](https://arxiv.org/abs/2501.12380), [LongVideoBench](https://arxiv.org/abs/2407.15754), [VideoVista](https://arxiv.org/abs/2504.17821), [WorldSense](https://arxiv.org/abs/2502.04326) and [AV-Odyssey](https://arxiv.org/abs/2412.02611). Additionally, We employ 18 publicly available benchmarks for compressing visual datasets and audio datasets, including [RealWorldQA](https://huggingface.co/datasets/xai-org/RealworldQA), [MME](https://arxiv.org/abs/2306.13394), [SeedBench](https://arxiv.org/abs/2307.16125), [OCRBench](https://arxiv.org/abs/2305.07895), [Fox](https://arxiv.org/abs/2405.14295), [DocLocal4k](https://arxiv.org/abs/2307.02499), [MMMU](https://arxiv.org/abs/2311.16502), [MMMU-Pro](https://arxiv.org/abs/2409.02813), [CMMMU](https://arxiv.org/abs/2401.11944), [MathVista](https://arxiv.org/abs/2310.02255), [MathVision](https://arxiv.org/abs/2402.14804), [ScienceVista](https://arxiv.org/abs/2501.12599), [GMAI-MMBench](https://arxiv.org/abs/2408.03361), [ReMi](https://arxiv.org/abs/2406.09175),  [MuirBench](https://arxiv.org/abs/2406.09411), [MMAU](https://arxiv.org/abs/2410.19168), [MMSU](https://arxiv.org/abs/2506.04779) and [SDQA](https://arxiv.org/abs/2109.12072).

## 📐 Acknowledgments

We hereby express our appreciation to the LongCat Team EVA Committee for their valuable assistance, guidance, and suggestions throughout the course of this work.






