import re
import os
import ast
import math
from typing import Dict, Any, Optional
from collections import defaultdict
from datasets import load_dataset
from huggingface_hub import snapshot_download
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.translate.bleu_score import sentence_bleu
import jieba
import asyncio
from tqdm.asyncio import tqdm
from .base_dataset import BaseDataset
from models import VLLMClient
from utils import EvaluationRecord, process_score_prompt

VIDEO_MIN_PIXELS = 128 * 28 * 28
VIDEO_MAX_PIXELS = 768 * 28 * 28
VIDEO_TOTAL_PIXELS = 32000 * 28 * 28 * 0.9

class UnoBenchDataset(BaseDataset):

    def load_and_prepare(self, hf_cache_dir: str = "~/.cache/huggingface/hub", local_dir: str = "", subset_name: str = ""):
        """
        Load UNO-Bench data and initialize evaluation record list.
        """
        if local_dir != "" and os.path.exists(local_dir):
            main_path = local_dir
            print(f"Loading datasets from local dir:\n{main_path}")
        else:
            print(f"Downloading datasets from HuggingFace...")
            main_path = snapshot_download(
                repo_id="meituan-longcat/UNO-Bench",
                repo_type="dataset",
                cache_dir=hf_cache_dir,
                max_workers=32
            )
            print(f"Datasets has been download to:\n{main_path}")

        df_info = pd.read_parquet(os.path.join(main_path, "validation.parquet"))
        if subset_name != "":
            df_info = df_info[df_info["subset_name"] == subset_name].reset_index(drop=True)
        for idx, example in df_info.iterrows():
            extra_info = dict(example)
            message = self.build_message(example, main_path)
            # Create the EvaluationRecord instance
            record = EvaluationRecord(
                id=example['qid'],
                question=example['question'],
                message=message,
                answer=example['answer'],
                extra_info=extra_info
            )
            self.evaluation_records.append(record)
        print(f"Prepared {len(self.evaluation_records)} records for evaluation.")

    def build_message(self, example, main_path) -> Dict:
        """ Prepare the request message for evaluation and return message like: 

        {"role": "user", "content": [{"type": "text", "text":"xxx"}, {"type": "image", "image": "xx.png"}, {"type":"audio", "audio":"xx.mp3"}]}
        """
        remove_empty = lambda x: {key:value for key,value in x.items() if value is not None}
        question = example['question']
        audios = remove_empty(example["audios"])
        images = remove_empty(example["images"])
        videos = remove_empty(example["videos"])

        content = []
        for part in re.split(r"(<(?:image|video|audio)_\d+>)", question):
            if re.match(r"(<image_\d+>)", part) and part in images:
                image_path = os.path.join(main_path, images[part])
                if not os.path.exists(image_path):
                    raise ValueError(f"Image file not found: {image_path}")
                content.append({
                    "type": "image",
                    "image": image_path
                    })
            elif re.match(r"(<video_\d+>)", part) and part in videos:
                video_path = os.path.join(main_path, videos[part])
                if not os.path.exists(video_path):
                    raise ValueError(f"Video file not found: {video_path}")
                content.append({
                    "type": "video",
                    "video": video_path,
                    "total_pixels": VIDEO_TOTAL_PIXELS,
                    "min_pixels": VIDEO_MIN_PIXELS,
                    "max_pixels": VIDEO_MAX_PIXELS

                })
            elif re.match(r"(<audio_\d+>)", part) and part in audios:
                audio_path = os.path.join(main_path, audios[part])
                if not os.path.exists(audio_path):
                   raise ValueError(f"Audio file not found: {audio_path}")
                content.append({
                    "type": "audio",
                    "audio": audio_path
                    })
            elif len(part) > 0:
                content.append({
                    "type": "text",
                    "text": part
                    })
        message = {"role": "user", "content": content}
        return message

    def build_score_message(self, record: EvaluationRecord, score_type: int):
        if score_type == 0:
            # MC (Multiple Choice)
            score_rule = f"小问1：{record.answer}，总分10分，无需关注推理过程，最终答案正确即可"
            score_prompt = process_score_prompt(question=record.question, reference=score_rule, response=record.response)
        elif score_type == 1:
            # MO (Multiple Options)
            score_rule= record.answer
            score_prompt = process_score_prompt(question=record.question, reference=score_rule, response=record.response)
        elif score_type == 4:
            # SDQA (Structured Data Question Answering)
            all_finded = re.findall(r'\[\[\[(.*?)\]\]\]', record.answer)
            question, answer = all_finded[0], all_finded[-1]
            score_rule = f"小问1：{answer}，总分10分，无需关注推理过程，最终答案正确即可"
            score_prompt = process_score_prompt(question=question, reference=score_rule, response=record.response)
        else:
            score_rule = f"小问1：{record.answer}，总分10分，无需关注推理过程，最终答案正确即可"
            score_prompt = process_score_prompt(question=record.question, reference=score_rule, response=record.response)
        content = [{"type": "text", "text": score_prompt}]
        message = {"role": "user", "content": content}
        return message

    def compute_metrics(self, score_client: VLLMClient, save_file_path: str, batch_size: int = 100) -> Dict[str, Any]:
        
        # Process in batches
        total_batch = math.ceil(len(self.evaluation_records) / batch_size)
        stats = {}
        
        for batch_start in tqdm(range(0, len(self.evaluation_records), batch_size), total=total_batch):
            batch_end = min(batch_start + batch_size, len(self.evaluation_records))
            batch_records = [record for record in self.evaluation_records[batch_start:batch_end] if record.request_status == "success"]
            score_messages = []
            score_ids = []
            
            # Build scoring messages for current batch
            for record in batch_records:
                score_type = record.extra_info["score_type"]
                if score_type not in [2, 3] and record.score_status != "success":
                    score_message = self.build_score_message(record, score_type)
                    score_messages.append(score_message)
                    score_ids.append(record.id)
            
            # Batch request for scoring
            if score_messages:
                # score_responses = asyncio.run(score_client.generate_batch(score_messages))
                result = score_client.generate_batch(score_messages)
                # 检测是否为协程
                if asyncio.iscoroutine(result):
                    score_responses = asyncio.run(result)
                else:
                    score_responses = result
                id2score_response = dict(zip(score_ids, score_responses))
                
                # Update scoring responses for current batch
                for record in batch_records:
                    score_type = record.extra_info["score_type"]
                    if score_type not in [2, 3] and record.score_status != "success":
                        if record.id in id2score_response:
                            record.score_response = id2score_response[record.id]
            
            # Calculate scores for current batch
            for record in batch_records:
                score_type = record.extra_info["score_type"]
                score = self.compute_score(record, score_type)
                subset_name = record.extra_info["subset_name"]
                stats[subset_name] = stats.get(subset_name, []) + [score]
            
            # Save current batch results
            self.save_results(save_file_path)
            
        self.save_results(save_file_path)
        stats_agg = {k: {"count": len(v), "avg": sum(v) / len(v)} for k, v in stats.items()}
        print("=========Evalusion Result=========")
        print(stats_agg)

        # Print records that failed to score
        fail_records = []
        for record in self.evaluation_records:
            if record.score_status != "success":
                fail_records.append(record)
        if len(fail_records) > 0:
            print(f"Failed records: {len(fail_records)}/{len(self.evaluation_records)}")
        return stats_agg

    def compute_score(self, record: EvaluationRecord, score_type: int) -> float:

        map_score_type = {
            0: self.compute_score_type_mc,
            1: self.compute_score_type_mo,
            2: self.compute_score_type_ocr_short,
            3: self.compute_score_type_ocr_long,
            4: self.compute_score_type_sdqa
        }
        score_func = map_score_type[score_type]
        score = score_func(record)
        record.score = score
        return score

    def compute_score_type_mc(self, record: EvaluationRecord) -> float:
        try:
            score = parse_from_score_model(record.score_response)
            record.score_status = "success"
        except:
            score = 0.0
            record.score_status = "error"
            raise ValueError(f"Invalid score response: {record.score_response}")
        return score

    def compute_score_type_mo(self, record: EvaluationRecord) -> float:
        """ Just reuse the score of MC.
        """
        return self.compute_score_type_mc(record)

    def compute_score_type_ocr_short(self, record: EvaluationRecord) -> float:
        try:
            score = cal_ocr_contain(target=record.answer, predict=record.response)
            record.score_status = "success"
        except:
            score = 0.0
            record.score_status = "error"
            raise ValueError(f"Invalid score response: {record.score_response}")
        return score

    def compute_score_type_ocr_long(self, record: EvaluationRecord) -> float:
        try:
            score = bleu_1(target=record.answer, predict=record.response)
            record.score_status = "success"
        except:
            score = 0.0
            record.score_status = "error"
            raise ValueError(f"Invalid score response: {record.score_response}")
        return score

    def compute_score_type_sdqa(self, record: EvaluationRecord) -> float:
        """ Just reuse the score of MC.
        """
        return self.compute_score_type_mc(record)



def extract_last_boxed(text):
    try:
        pattern = r'<score>([\d.]+)</score>'
        matches = re.findall(pattern, text)
        if matches:
            return float(matches[-1])
        else:
            return 0.0
    except Exception as e:
        print(f"Error extracting boxed content: {e}")
        return 0.0

def parse_from_score_model(response: str, scale_factor=10) -> float:
    score = extract_last_boxed(response)
    score = score / scale_factor
    return score

def cal_ocr_contain(target: str, predict: str) -> int:
    target_list = literal_eval_list(target)

    # Remove spaces and commas from each target for standardized data comparison
    normalized_target_list = [t.strip().lower().replace("\n", " ") for t in target_list]
    normalized_predict = predict.strip().lower().replace("\n", " ")

    # Check if predict appears in target_list
    for normalized_target in normalized_target_list:
        if normalized_target in normalized_predict:
            return 1
    return 0

def literal_eval_list(target: str):
    if (target.startswith('[') and target.endswith(']')):
        try:
            # Try to parse target as a list
            target_list = ast.literal_eval(target)
            if not isinstance(target_list, list):
                # If the parsed result is not a list, treat it as a single answer
                target_list = [target]
            return target_list
        except (ValueError, SyntaxError):
            # If parsing fails, target is a single answer
            target_list = [target]
            return target_list
    else:
        return [target]

def bleu_1(target: str, predict: str) -> float:
    try:
        target = " ".join(jieba.cut(target))
        predict = " ".join(jieba.cut(predict))
    except:
        target = target
        predict = predict
    score = sentence_bleu([word_tokenize(target)], word_tokenize(predict), weights=(1, 0, 0, 0))
    score = float(f"{score:.4f}")
    return score