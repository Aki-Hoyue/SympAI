import os
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OnlineLLM():
    """
    Online LLM Model using OpenAI Formats.
    """
    def __init__(self, base_url: str = os.getenv("OPENAI_BASE_URL"), 
                 api_key: str = os.getenv("OPENAI_API_KEY"), 
                 model_name: str = os.getenv("OPENAI_MODEL_NAME")):
        """
        Initialize the OnlineLLM class.

        Args:
            base_url (str): The base URL of the OpenAI-Format API. (Endpoint) e.g. https://api.openai.com/v1
            api_key (str): The API key for calling your AI API.
            model_name (str): The name of the model to use.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        print(self.base_url, self.api_key, self.model_name)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def completion(self, messages: List[Dict[str, Any]]) -> str:
        """
        Generate a completion for the given messages.

        Args:
            messages (List[Dict[str, Any]]): The messages to send to the AI.
            e.g. [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ]

        Returns:
            str: The completion from the AI.
        """
        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
        }

        try:
            response = self.client.chat.completions.create(**data)
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Error in completion: {e}")
