from .base_dataset import BaseDataset
from .unobench import UnoBenchDataset

# Dataset name to class mapping
DATASET_REGISTRY = {
    "UNO-Bench": UnoBenchDataset,
    # Add more datasets here, for example:
    # "MMMU": MMMUDataset,
}

def get_dataset(dataset_name: str) -> BaseDataset:
    """
    Dataset factory function.

    :param dataset_name: Registered dataset name (e.g., 'UNO-Bench')
    :param split: Dataset split
    :return: Instance of BaseDataset
    """
    if dataset_name not in DATASET_REGISTRY:
        raise ValueError(f"Unknown dataset: {dataset_name}. Available benchmarks: {list(DATASET_REGISTRY.keys())}")
    
    dataset_class = DATASET_REGISTRY[dataset_name]
    return dataset_class()