from abc import ABC, abstractmethod
from typing import AsyncGenerator, Generator, List, Optional
from pathlib import Path

class BaseLLM(ABC):
    """
    Abstract base class for LLM implementations
    """
    
    def __init__(
        self,
        model_name: str,
        system_prompt: str = "You are a helpful AI assistant.",
        history_dir: Optional[Path] = None,
        max_messages: int = 6,
        **kwargs
    ):
        """
        Initialize the LLM.
        
        Args:
            model_name: Name or path of the model
            system_prompt: System prompt to guide model behavior
            history_dir: Directory to store chat histories
            max_messages: Maximum number of messages before summarization
            **kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.history_dir = history_dir
        self.max_messages = max_messages
    
    @abstractmethod
    def configure(self, **kwargs):
        """Configure the model"""
        pass
    
    @abstractmethod
    async def achat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Async chat with the model"""
        pass
    
    @abstractmethod
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Synchronous chat with the model"""
        pass
    
    @abstractmethod
    async def astream_chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Async streaming chat with the model"""
        pass
    
    @abstractmethod
    def stream_chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Synchronous streaming chat with the model"""
        pass
    
    @abstractmethod
    def get_history(self, session_id: str) -> List:
        """Get chat history for a session"""
        pass
    
    @abstractmethod
    def clear_history(self, session_id: str) -> None:
        """Clear chat history for a session"""
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[str]:
        """List all available chat sessions"""
        pass
    
    @abstractmethod
    def clear_all_histories(self) -> None:
        """Clear all chat histories"""
        pass
    
    def list_models(self) -> List[str]:
        """
        List all available models
        """
        return [
            "gpt-4o-mini",
            "claude-3-haiku-20240307",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "X-D-Lab/Sunsimiao-Qwen-7B",
        ]
