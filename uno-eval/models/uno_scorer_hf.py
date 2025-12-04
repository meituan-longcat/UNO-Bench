import os
from tqdm import tqdm
from typing import List, Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .base_model import BaseModel

class UNOScorerHF(BaseModel):
    def __init__(self, model_name: str, model_path: str, system_prompt: str = "") -> None:
        super().__init__(model_name, model_path)
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.model_path = model_path

    def load_model(self):
        if not os.path.exists(self.model_path):
            self.model_path = self.model_name
            
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype="auto",
            device_map="auto"
        )

    def generate(self, message: Dict) -> str:
        conversion = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": message["content"][0]["text"]
            }
        ]

        text = self.tokenizer.apply_chat_template(
            conversion,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # conduct text completion
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=8192,
            do_sample=False
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

        content = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        return content

    def generate_batch(self, messages: List[Dict]) -> List[str]:
        contents = []
        for message in tqdm(messages, total=len(messages), desc="Generating..."):
            content = self.generate(message)
            contents.append(content)
        return contents
