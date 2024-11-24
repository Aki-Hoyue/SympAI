"""
Load local LLM Model: X-D-Lab/Sunsimiao-Qwen-7B

https://github.com/X-D-Lab/Sunsimiao

Problem to solve:
- Unexpected token with pad token same as eos token
- Warning: The attention mask is not set and cannot be inferred from input because pad token is same as eos token. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
If you can solve these problems, please raise an issue or a PR. Thank you!
- Agent Functions in Online LLM, you can refer to server/app/core/models/base.py and server/app/core/models/online.py

"""
from modelscope.hub.snapshot_download import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
import torch
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

class LocalLLM:
    def __init__(self, cache_dir: str = './local/', model_id: str = 'X-D-Lab/Sunsimiao-Qwen-7B'):
        self.cache_dir = cache_dir
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        """
        Load the model and tokenizer.
        """
        try:
            model_dir = snapshot_download(self.model_id, cache_dir=self.cache_dir)
            model_path = os.path.join(self.cache_dir, self.model_id)
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            self.tokenizer.pad_token = self.tokenizer.eos_token  # May cause unexpected behavior
            
            model_kwargs = {
                'trust_remote_code': True,
                'device_map': 'cuda' if torch.cuda.is_available() else 'cpu',
                'torch_dtype': torch.float16 if torch.cuda.is_available() else torch.float32,
                'use_flash_attn': False,  # Disable flash attention for default, see: https://github.com/Dao-AILab/flash-attention
                'offload_folder': None,
                'offload_state_dict': False,
            }
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **model_kwargs
            )
            
            if torch.cuda.is_available():
                for param in self.model.parameters():
                    if param.device.type != 'cuda':
                        param.data = param.data.to('cuda')
                        if param.grad is not None:
                            param.grad.data = param.grad.data.to('cuda')
            
            # Set generation configuration
            generation_config = GenerationConfig.from_pretrained(model_path)
            generation_config.chat_format = "chatml"
            generation_config.max_window_size = 6144
            generation_config.max_new_tokens = 512
            generation_config.do_sample = True
            generation_config.top_p = 0.8
            generation_config.temperature = 0.7
            self.model.generation_config = generation_config
            
            if DEBUG:
                print("Model loaded to CUDA device" if torch.cuda.is_available() else "Model loaded to CPU")
            return True
            
        except Exception as e:
            print(f"Model loading failed: {str(e)}")
            return False
    
    def generate_response(self, query: str, system_prompt: str, max_length: int = 2048):
        """
        Generate a response from the model.
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Please call load_model() to load the model first.")
            
        try:
            response = self.model.chat(
                self.tokenizer,
                query,
                history=[],
                system=system_prompt,
            )
            return response
            
        except Exception as e:
            if DEBUG:
                print(f"Error generating response: {str(e)}")
            return None

if __name__ == "__main__":
    model = LocalLLM()
    
    if model.load_model():
        query = "I had fever yesterday, what should I do?"
        system_prompt = "You are a helpful assistant specialized in Traditional Chinese Medicine."
        response = model.generate_response(query, system_prompt)
        if DEBUG:
            print(f"User query: {query}")
            print(f"Answer: {response}")
