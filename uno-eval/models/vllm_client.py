from typing import List, Dict, Any, Optional
import requests
import time
import aiohttp
import asyncio
import numpy as np
from tqdm.asyncio import tqdm
from .base_model import BaseModel

class VLLMClient(BaseModel):
    """
    Wrapper class for VLLM OpenAI-Compatible API, supporting aiohttp asynchronous batch requests.
    """
    DEFAULT_API_URL = "http://127.0.0.1:8000/v1/chat/completions"
    DEFAULT_TIMEOUT = 600 

    def __init__(
        self, 
        model_name: str, 
        model_path: str = "",
        max_tokens: int = 8192,
        temperature: float = 0.7,
        repeat_penalty: float = 0.2,
        api_url: Optional[str] = None,
        system_prompt: str = None,
        max_concurrent_requests = 20
    ) -> None:
        """
        Initialize VLLM client.
        
        :param model_name: Model name for the "model" field in API requests, optional.
        :param api_url: Complete URL of VLLM API server.
        """
        self.model_name = model_name
        self.api_url = api_url if api_url else self.DEFAULT_API_URL
        self.default_max_tokens = max_tokens
        self.default_temperature = temperature
        if system_prompt is not None:
            self.system_message: Dict[str, str] = {
            "role": "system",
            "content": system_prompt
            }
        else:
            self.system_message = None
        self.max_concurrent_requests = max_concurrent_requests

    def load_model(self):
        self.headers = {"Content-Type": "application/json"}
        self.check_vllm_service(self.api_url)
        

    def check_vllm_service(self, api_url: str) -> bool:
        """
        Check if VLLM service is running normally
        Args:
            api_url: Base URL of VLLM service (e.g., http://localhost:8000/v1/chat/completions)
        
        Returns:
            True if service responds normally within 5 minutes, False otherwise
        """
        # Construct complete URL for check endpoint
        check_url = api_url.replace("v1/chat/completions", "v1/models")

        total_timeout = 1200
        retry_interval = 10
        max_retries = total_timeout // retry_interval
        
        for _ in range(max_retries):
            try:
                # Send GET request with 5-second timeout (avoid hanging too long)
                response = requests.get(check_url, timeout=5)
                # If status code is 200, service is normal
                if response.status_code == 200:
                    print("VLLM service started successfully")
                    return True
            except (requests.exceptions.ConnectionError,  # Connection failed (service not started)
                    requests.exceptions.Timeout,          # Request timeout (service not responding)
                    requests.exceptions.RequestException): # Other request exceptions
                pass  # Ignore exceptions, continue retrying
            
            # Wait for retry interval
            time.sleep(retry_interval)
            print(f"Connecting to VLLM Serving: {check_url}")
        
        # Still failed after maximum retries, return False
        raise ValueError("Failed to connect to VLLM service")

    def _build_conversation(self, query_message: Dict) -> List[Dict]:
        """Build complete conversation list including System Prompt and User Message."""

        user_message = {"role": "user", "content": []}
        for content in query_message["content"]:
            if content["type"] == "text":
                user_message["content"].append(content)
            elif content["type"] == "image":
                user_message["content"].append({"type": "image_url", "image_url": {"url": "file://"+content["image"]}})
            elif content["type"] == "audio":
                user_message["content"].append({"type": "audio_url", "audio_url": {"url": "file://"+content["audio"]}})
            elif content["type"] == "video":
                user_message["content"].append({"type": "video_url", "video_url": {"url": "file://"+content["video"]}})
            else:
                raise ValueError(f"Unknown content type: {content['type']}")
            
        full_message = []
        if self.system_message is not None:
            full_message = [self.system_message.copy(), user_message]
        else:
            full_message = [user_message]
        return full_message

    async def _async_call_api(
        self, 
        session: aiohttp.ClientSession, 
        user_message: Dict,
        message_idx: int,
        timeout: int = DEFAULT_TIMEOUT
    ) -> tuple[int, Any, Optional[str]]:
        """
        Send single API request asynchronously.
        
        Returns (index, model_text, error_message).
        """
        conversation = self._build_conversation(user_message)
        
        data = {
            # "model": self.model_name,
            "messages": conversation,
            "max_tokens": self.default_max_tokens,
            "temperature": self.default_temperature
        }
        
        try:
            # Use aiohttp async POST request
            async with session.post(
                self.api_url, 
                headers=self.headers, 
                json=data, 
                timeout=timeout
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"🚨 [{message_idx}] API Request failed with status {response.status}. Error: {error_text[:200]}..."
                    print(error_msg)
                    return message_idx, None, error_msg # Return None and error message
                
                response_json = await response.json()
                
                # Parse OpenAI-Compatible API response structure
                if response_json and response_json.get("choices"):
                    response_text = response_json["choices"][0]["message"]["content"]
                    # Simplified handling: return index and generated text
                    return message_idx, response_text, None 
                else:
                    error_msg = f"❌ [{message_idx}] API response format error."
                    print(error_msg)
                    return message_idx, None, error_msg
                

        except asyncio.TimeoutError:
            error_msg = f"⏱️ [{message_idx}] API Request timed out after {timeout} seconds."
            print(error_msg)
            return message_idx, None, error_msg
        except Exception as e:
            error_msg = f"❌ [{message_idx}] An unexpected error occurred: {e}. Data: {user_message['content'][:50]}..."
            print(error_msg)
            return message_idx, None, error_msg

    async def generate_batch(
        self, 
        messages: List[Dict],
        show_progress: bool = True,
        progress_desc: str = "Processing"
    ) -> List[Any]:
        """
        Send batch requests using aiohttp async concurrency with optional progress bar.
        
        :param messages: List of user messages.
        :param show_progress: Whether to show progress bar (default: True).
        :param progress_desc: Description text for progress bar (default: "Processing").
        :return: Result list in original order (containing generated text or None).
        """
        
        all_results = []
        
        # Create progress bar if needed
        pbar = tqdm(total=len(messages), desc=progress_desc, disable=not show_progress)
        
        async with aiohttp.ClientSession() as session:
            
            for batch_start in range(0, len(messages), self.max_concurrent_requests):
                batch_end = min(batch_start + self.max_concurrent_requests, len(messages))
                batch_messages = messages[batch_start:batch_end]
                
                # Create tasks for current batch
                tasks = [
                    self._async_call_api(session, msg, idx) 
                    for idx, msg in enumerate(batch_messages, start=batch_start)
                ]
                
                # Execute current batch requests
                batch_results = await asyncio.gather(*tasks)
                
                all_results.extend(batch_results)
                
                # Update progress bar
                if show_progress:
                    pbar.update(len(batch_results))
            
            pbar.close()
        
        # Sort results to ensure order consistency with input
        sorted_results = sorted(all_results, key=lambda x: x[0])
        
        # Extract model text
        final_outputs = [res[1] for res in sorted_results]
        return final_outputs
    
    def generate(self, message: Dict) -> str:
        """
        Synchronous call for single request.
        
        Note: Running async code in class requires asyncio.run(), not recommended for library code abuse.
        """
        print("Warning: Synchronous call to 'generate' method, recommend using '_async_call_api' or 'generate_batch' directly.")
        
        async def run_single():
            async with aiohttp.ClientSession() as session:
                # Assume index is 0
                _, text_output, _ = await self._async_call_api(session, message, 0)
                return text_output

        return asyncio.run(run_single())


# --- Example Usage (External Run) ---

if __name__ == '__main__':
    vllm_client = VLLMClient(
        model_name="qwen-2.5-omni-7b", 
        api_url="http://127.0.0.1:8000/v1/chat/completions"
    )

    batch_messages = [
        {"role": "user", "content": [{"type": "text", "text": "Why is the sky blue?"}]},
        {"role": "user", "content": [{"type": "text", "text": "What is photosynthesis?"}]},
        {"role": "user", "content": [{"type": "text", "text": "Please write a Fibonacci sequence function in Python."}]}
    ]

    async def main_batch_run():
        print("\n--- Starting async batch requests ---")
        results = await vllm_client.generate_batch(batch_messages)
        
        print("\n--- Batch request results ---")
        for i, res in enumerate(results):
            if isinstance(res, str):
                print(f"Request {i+1}: Success. Result: {res[:50]}...")
            else: # None or other non-string results
                print(f"Request {i+1}: Failed/Timeout.")
        return results

    # Run main async function
    final_results = asyncio.run(main_batch_run())