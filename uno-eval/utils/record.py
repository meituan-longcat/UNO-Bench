import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class EvaluationRecord:
    """
    A standardized data structure for storing a single evaluation record and its results.
    """
    # --- Core Fields ---
    id: Any  # Unique identifier for the sample
    question: str
    message: Dict  # ShareGPT format request message list
    answer: Any  # The expected correct answer (Ground Truth)

    # --- Fields populated during evaluation ---
    response: Optional[str] = None  # Raw text output from the model
    request_status: str = 'pending'  # Evaluation status: 'pending', 'success', 'error'
    score_response: Optional[str] = None  # Output from the scoring model
    score_status: str = 'pending'
    score: Optional[float] = None  # Score for a single sample (e.g., 0 or 1 for multiple-choice questions)

    # --- Extra Information ---
    extra_info: Dict[str, Any] = field(default_factory=dict)  # For storing dataset-specific metadata, such as subject, difficulty, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "question":  self.question,
            "message": self.message,
            "answer": self.answer,
            "response": self.response,
            "score_response": self.score_response,
            "score": self.score,
            "request_status": self.request_status,
            "score_status": self.score_status,
            "extra_info": self.extra_info,
        }
    
    @staticmethod
    def save_records_to_json(records: List['EvaluationRecord'], filepath: str) -> None:
        """Saves multiple records to a JSON file."""
        data = [record.to_dict() for record in records]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
