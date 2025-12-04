# models/__init__.py

from .base_model import BaseModel
from .qwen_2d5_omni_7b import Qwen2_5Omni7B
from .vllm_client import VLLMClient
from .uno_scorer_hf import UNOScorerHF

# Model name to class mapping
MODEL_REGISTRY = {
    "Qwen-2.5-Omni-7B": Qwen2_5Omni7B,
    "VLLMClient": VLLMClient,
    "UNOScorerHF":UNOScorerHF
}

def get_model(model_name: str, model_path: str, **kwargs) -> BaseModel:
    """
    Model factory function.

    :param model_name: Registered model name (e.g., 'qwen_api')
    :param model_path: Actual model path or API identifier (e.g., 'qwen-turbo')
    :param kwargs: Other model initialization parameters
    :return: Instance of BaseModel
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model name: {model_name}. Available models: {list(MODEL_REGISTRY.keys())}")
        
    model_class = MODEL_REGISTRY[model_name]
    return model_class(model_name=model_name, model_path=model_path, **kwargs)