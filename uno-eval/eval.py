import os
import sys
import argparse
import json
from tqdm import tqdm
import asyncio

from models import get_model, VLLMClient
from benchmarks import get_dataset

def setup_arg_parser():
    parser = argparse.ArgumentParser(description="Run evaluation on a given model and dataset.")
    parser.add_argument("--model_name", type=str, required=True, help="Registered name of the model type (e.g., 'Qwen-2.5-Omni-7B').")
    parser.add_argument("--model_path", type=str, default="", help="Path to the inference model.")
    parser.add_argument("--model_api_url", type=str, default="", help="API url for the model.")
    parser.add_argument("--system_prompt", type=str, default="", help="System prompt for the model.")
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size for model generation.")
    parser.add_argument("--save_batch_size", type=int, default=128, help="Batch size for saving results.")

    parser.add_argument("--dataset_name", type=str, required=True, help="Registered name of the dataset (e.g., 'UNO-Bench').")
    parser.add_argument("--subset_name", type=str, default="", help="Subset name of the dataset.")
    parser.add_argument("--dataset_local_dir", type=str, default="", help="Local path to the dataset.")
    parser.add_argument("--hf_cache_dir", type=str, default="~/.cache/huggingface/hub", help="Hugging Face cache directory.")
    
    parser.add_argument("--output_dir", type=str, default="./eval_results", help="Directory to save evaluation results.")
    parser.add_argument("--exp_marking", type=str, default="", help="Experiment marking.")
    parser.add_argument("--scorer_api_url", type=str, default="", help="The score model API url.")
    parser.add_argument("--scorer_model_path", type=str, default="", help="The scorer model path.")
    parser.add_argument("--mode", choices=["inference", "scoring"], default="inference")

    return parser.parse_args()

def main():
    args = setup_arg_parser()
    print("Evaluation starting with the following configuration:")
    print(json.dumps(vars(args), indent=2))
    if os.path.exists(args.output_dir) is False:
        os.makedirs(args.output_dir)
    save_file_path = os.path.join(args.output_dir, f"{args.model_name}{args.exp_marking}:{args.dataset_name}.json")
    
    # 1. Initialize dataset and prepare evaluation records
    try:
        dataset_handler = get_dataset(args.dataset_name)
        dataset_kwargs = {}
        if args.dataset_local_dir:
            dataset_kwargs['local_dir'] = args.dataset_local_dir
        if args.hf_cache_dir:
            dataset_kwargs['hf_cache_dir'] = args.hf_cache_dir
        if args.subset_name:
            dataset_kwargs['subset_name'] = args.subset_name
        dataset_handler.load_and_prepare(**dataset_kwargs)
        if os.path.exists(save_file_path):
            dataset_handler.load_results(save_file_path)
    except Exception as e:
        print(f"Error preparing dataset: {e}")
        return

    not_processed_records = [record for record in dataset_handler.evaluation_records 
                              if record.request_status != 'success' or record.response is None]

    # 2. Load model and generate evaluation responses
    if args.mode == "inference" and len(not_processed_records)>0:
        try:
            model_kwargs = {}
            if args.model_api_url != "":
                model_kwargs['api_url'] = args.model_api_url
            if args.system_prompt != "":
                model_kwargs['system_prompt'] = args.system_prompt
            model = get_model(args.model_name, args.model_path, **model_kwargs)
            model.load_model()
        except (ValueError, ImportError) as e:
            print(f"Error initializing model: {e}")
            return

        batch_size = args.batch_size
        
        if batch_size > 1:
            # Batch generation
            for batch_idx in tqdm(range(0, len(not_processed_records), batch_size),
                                  desc=f"Evaluating {args.model_name} on {args.dataset_name}",
                                  dynamic_ncols=True):
                batch_records = not_processed_records[batch_idx:batch_idx + batch_size]
                try:
                    messages = [record.message for record in batch_records]
                    responses = asyncio.run(model.generate_batch(messages))
                    for record, response in zip(batch_records, responses):
                        record.response = response
                        if record.response is None:
                            record.request_status = 'error'
                        else:
                            record.request_status = 'success'
                except Exception as e:
                    print(f"Error during batch generation: {e}")
                    for record in batch_records:
                        record.response = str(e)
                        record.request_status = 'error'
                
                if batch_idx % args.save_batch_size == 0:
                    dataset_handler.save_results(save_file_path)
        else:
            # Sequential generation
            for idx, record in tqdm(enumerate(not_processed_records), total=len(not_processed_records),
                                    desc=f"Evaluating {args.model_name} on {args.dataset_name}", 
                                    dynamic_ncols=True):
                if record.request_status == 'success':
                    continue
                try:
                    response = model.generate(record.message)
                    record.response = response
                    record.request_status = 'success'
                except Exception as e:
                    print(f"Error during model generation for record {record.id}: {e}")
                    record.response = str(e)
                    record.request_status = 'error'

                if idx % args.save_batch_size == 0:
                    dataset_handler.save_results(save_file_path)
        
        dataset_handler.save_results(save_file_path)
        
    # 3. Metric calculation
    elif args.mode == "scoring":
        if args.scorer_api_url != "":
            print("Loading scorer with vLLM API")
            score_client = get_model(
                model_name="VLLMClient", 
                model_path="",
                api_url=args.scorer_api_url,
                system_prompt="You are a helpful assistant."
            )
        else:
            print("Loading scorer with HuggingFace")
            score_client = get_model(model_name="UNOScorerHF", model_path=args.scorer_model_path)

        score_client.load_model()
        dataset_handler.compute_metrics(score_client, save_file_path)
        dataset_handler.save_results(save_file_path)

if __name__ == "__main__":
    main()