import os
import re
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from utils import EvaluationRecord

class BaseDataset(ABC):
    def __init__(self, **kwargs):
        self.evaluation_records: List[EvaluationRecord] = []
        self.kwargs = kwargs
    def __len__(self):
        return len(self.evaluation_records)

    @abstractmethod
    def load_and_prepare(self):
        """
        Load data and populate the self.evaluation_records list.
        Each element is an EvaluationRecord object.
        """
        pass

    @abstractmethod
    def build_message(self) -> dict:
        """ Prepare the request message for inference and the format is OpenAI Chat Message Format: 

        {"role": "user", "content": [{"type": "text", "text":"xxx"}, {"type": "image", "image": "xx.png"}, {"type":"audio", "audio":"xx.mp3"}]}
        """
        pass

    @abstractmethod
    def build_score_message(self, record: EvaluationRecord) -> dict:
        """ Prepare the request message for scorer and the format is OpenAI Chat Message Format: 

        {"role": "user", "content": [{"type": "text", "text":"xxx"}}
        """
        pass

    @abstractmethod
    def compute_score(self, record: EvaluationRecord) -> float:
        """
        Compute score for a single completed record.

        :param record: An EvaluationRecord object with prediction filled.
        :return: Score (float).
        """
        pass

    @abstractmethod
    def compute_metrics(self) -> Dict[str, Any]:
        """Compute final aggregated metrics based on all records."""
        pass

    def save_results(self, file_path: str):
        """Save detailed results and final scores."""
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        EvaluationRecord.save_records_to_json(self.evaluation_records, file_path)
        print(f"Results saved to {file_path}")

    def load_results(self, file_path: str):
        """Load data from JSON file into evaluation_records."""
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.evaluation_records = []
        for item in data:
            record = EvaluationRecord(
                id=item['id'],
                question=item['question'],
                message=item['message'],
                answer=item['answer'],
                response=item.get('response'),
                request_status=item.get('request_status', 'pending'),
                score_response=item.get('score_response'),
                score_status=item.get('score_status', 'pending'),
                score=item.get('score'),
                extra_info=item.get('extra_info', {})
            )
            self.evaluation_records.append(record)
        
        print(f"Loaded {len(self.evaluation_records)} records from {file_path}")