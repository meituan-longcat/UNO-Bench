from typing import List, Dict, Any
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
from qwen_omni_utils import process_mm_info

from .base_model import BaseModel

class Qwen2_5Omni7B(BaseModel):
    def __init__(self, model_name: str, model_path: str, system_prompt: str = "") -> None:
        super().__init__(model_name, model_path)
        self.system_prompt = system_prompt

    def load_model(self):
        self.model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            self.model_path,
            torch_dtype="auto",
            device_map="auto",
            attn_implementation="flash_attention_2",
        )
        self.model.disable_talker()
        self.processor = Qwen2_5OmniProcessor.from_pretrained(self.model_path)

    def generate(self, message: Dict) -> str:
        system_message = {
            "role": "system",
            "content": [
                {"type": "text", "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech." \
                 if self.system_prompt=="" else self.system_prompt}
            ]
        }
        conversation = [system_message, message]
        print(conversation)
        # set use audio in video
        USE_AUDIO_IN_VIDEO = False

        # Preparation for inference
        text = self.processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(conversation, use_audio_in_video=USE_AUDIO_IN_VIDEO)
        inputs = self.processor(text=text, audio=audios, images=images, videos=videos, return_tensors="pt", padding=True, use_audio_in_video=USE_AUDIO_IN_VIDEO)
        inputs = inputs.to(self.model.device).to(self.model.dtype)

        # Inference: Generation of the output text and audio
        text_ids = self.model.generate(**inputs, use_audio_in_video=USE_AUDIO_IN_VIDEO)

        text = self.processor.batch_decode(text_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False, return_audio=False)[0]
        if "assistant\n" in text:
            text = text.split("assistant\n", 1)[1]
        print(text)
        return text
    
    def generate_batch(self, messages: List) -> List[str]:
        conversations = []
        system_prompt = {
            "role": "system",
            "content": [
                {"type": "text", "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech."}
            ]
        }
        for message in messages:
            conversations.append([system_prompt, message])
        
        # set use audio in video
        USE_AUDIO_IN_VIDEO = False
        
        # Preparation for batch inference
        text = self.processor.apply_chat_template(conversations, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(conversations, use_audio_in_video=USE_AUDIO_IN_VIDEO)
        inputs = self.processor(text=text, audio=audios, images=images, videos=videos, return_tensors="pt", padding=True, use_audio_in_video=USE_AUDIO_IN_VIDEO)
        inputs = inputs.to(self.model.device).to(self.model.dtype)
        
        # Batch inference
        text_ids = self.model.generate(**inputs, use_audio_in_video=USE_AUDIO_IN_VIDEO)
        
        # Batch decode
        results = self.processor.batch_decode(text_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False, return_audio=False)
        
        # Clean up results by removing "assistant\n" prefix
        cleaned_results = []
        for text in results:
            if "assistant\n" in text:
                text = text.split("assistant\n", 1)[1]
            cleaned_results.append(text)
        
        return cleaned_results