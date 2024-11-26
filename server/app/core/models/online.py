import os
import uuid
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    RemoveMessage
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from server.app.core.models.base import BaseLLM
from server.app.utils.prompt import SUMMARY_PROMPT, SYSTEM_PROMPT

load_dotenv()

HISTORY_DIR = PROJECT_ROOT / "server" / "app" / "core" / "models" / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_PROMPT_TEMPLATE = SUMMARY_PROMPT

class ChatState:
    """
    State class for managing chat history and summary
    """
    def __init__(self):
        self.messages: List[BaseMessage] = []
        self.summary: str = ""

class ChatMessageManager:
    """
    Manages chat message histories for different sessions using file storage
    """
    def __init__(
        self, 
        history_dir: Path = HISTORY_DIR,
        max_messages: int = 6,
        llm: Optional[ChatOpenAI] = None
    ):
        self.history_dir = history_dir
        self.max_messages = max_messages
        self.llm = llm
        self._histories: Dict[str, BaseChatMessageHistory] = {}
        self._states: Dict[str, ChatState] = {}
    
    def get_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        Get or create history for a session
        """
        if session_id not in self._histories:
            history_file = self.history_dir / f"{session_id}.json"
            self._histories[session_id] = FileChatMessageHistory(str(history_file))
            self._states[session_id] = ChatState()
        return self._histories[session_id]
    
    def should_summarize(self, messages: List[BaseMessage]) -> bool:
        """
        Check if we should summarize the conversation
        """
        return len(messages) > self.max_messages
    
    async def create_summary(self, messages: List[BaseMessage], summary_prompt: str = SUMMARY_PROMPT_TEMPLATE) -> str:
        """
        Create a summary of the conversation
        """
        if not self.llm:
            raise ValueError("LLM not initialized for summarization")
        
        conversation = "\n".join([
            f"{msg.type}: {msg.content}" for msg in messages
        ])
        
        # Create messages for the summary prompt
        summary_messages = [
            SystemMessage(content=summary_prompt),
            HumanMessage(content=conversation)
        ]
        
        try:
            # Call LLM directly with messages
            response = await self.llm.ainvoke(summary_messages)
            if not response or not response.content:
                return "No summary available"
            return response.content
        except Exception as e:
            print(f"Error creating summary: {e}")
            raise
    
    async def process_messages(self, session_id: str, summary_prompt: str = SUMMARY_PROMPT_TEMPLATE) -> List[BaseMessage]:
        """
        Process messages and create summary if needed
        """
        history = self.get_history(session_id)
        state = self._states[session_id]
        messages = history.messages
        
        if self.should_summarize(messages):
            try:
                # Create summary
                summary = await self.create_summary(messages, summary_prompt)
                state.summary = summary
                
                # Keep only the last 2 exchanges (4 messages)
                keep_messages = messages[-4:]
                
                # Create remove messages for the old ones
                remove_messages = [
                    RemoveMessage(id=msg.id)
                    for msg in messages[:-4]
                ]
                
                # Clear the history
                history.clear()
                
                # Add the summary as system message first
                summary_msg = SystemMessage(
                    content=f"Previous conversation summary:\n{summary}"
                )
                history.add_message(summary_msg)
                
                # Add back the kept messages
                for msg in keep_messages:
                    history.add_message(msg)
                
                # Update state
                state.messages = [summary_msg] + keep_messages
                
                return state.messages
                
            except Exception as e:
                print(f"Error in processing messages: {e}")
                return messages
                
        return messages
    
    def clear_history(self, session_id: str):
        """
        Clear history for a specific session and remove the file
        """
        if session_id in self._histories:
            history_file = self.history_dir / f"{session_id}.json"
            if history_file.exists():
                history_file.unlink()  # Delete the file
            del self._histories[session_id]
    
    def clear_all_histories(self):
        """
        Clear all histories and remove all history files
        """
        for file in self.history_dir.glob("*.json"):
            file.unlink()
        self._histories.clear()
    
    def list_sessions(self) -> List[str]:
        """
        List all available session IDs
        """
        return [f.stem for f in self.history_dir.glob("*.json")]

class LangChainChat(BaseLLM):
    """
    Modern LangChain chat implementation with summarization
    """
    def __init__(
        self,
        base_url: str = os.getenv("OPENAI_BASE_URL"),
        api_key: str = os.getenv("OPENAI_API_KEY"),
        model_name: str = os.getenv("OPENAI_MODEL_NAME"),
        system_prompt: str = "You are a helpful AI assistant.",
        summary_prompt: str = SUMMARY_PROMPT_TEMPLATE,
        history_dir: Path = HISTORY_DIR,
        max_messages: int = 6,
        **kwargs
    ):
        """
        Initialize the chat system with summarization capability
        """
        super().__init__(
            model_name=model_name,
            system_prompt=system_prompt,
            history_dir=history_dir,
            max_messages=max_messages
        )
        
        self.llm = ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key=api_key,
            streaming=True
        )
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            MessagesPlaceholder(variable_name="input"),
        ])
        
        # Store summary prompt
        self.summary_prompt = summary_prompt
        
        # Create the chain
        self.chain = self.prompt | self.llm
        
        # Initialize message manager with summarization capability
        self.message_manager = ChatMessageManager(
            history_dir=history_dir,
            max_messages=max_messages,
            llm=self.llm
        )
        
        # Create runnable with history
        self.runnable_chain = RunnableWithMessageHistory(
            self.chain,
            lambda session_id: self.message_manager.get_history(session_id),
            input_messages_key="input",
            history_messages_key="history"
        )

    def configure(self, 
                  base_url: str = os.getenv("OPENAI_BASE_URL"),
                  api_key: str = os.getenv("OPENAI_API_KEY"),
                  model_name: str = os.getenv("OPENAI_MODEL_NAME"),
                  system_prompt: str = SYSTEM_PROMPT,
                  summary_prompt: str = SUMMARY_PROMPT_TEMPLATE,
                  history_dir: Path = HISTORY_DIR,
                  max_messages: int = 6,
                  **kwargs):
        """Configure the model"""
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.summary_prompt = summary_prompt
        self.history_dir = history_dir
        self.max_messages = max_messages
        
        # Update LLM configuration
        self.llm = ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key=api_key,
            streaming=True
        )
        
        # Update prompt template with new system prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            MessagesPlaceholder(variable_name="input"),
        ])
        
        # Update the chain with new prompt and llm
        self.chain = self.prompt | self.llm
        
        # Update runnable chain
        self.runnable_chain = RunnableWithMessageHistory(
            self.chain,
            lambda session_id: self.message_manager.get_history(session_id),
            input_messages_key="input",
            history_messages_key="history"
        )
        
        # Update message manager
        self.message_manager = ChatMessageManager(
            history_dir=history_dir,
            max_messages=max_messages,
            llm=self.llm
        )

    async def achat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Async chat with summary support"""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        config = {"configurable": {"session_id": session_id}}
        messages = [HumanMessage(content=message)]
        
        try:
            # Process messages and get summary if needed
            await self.message_manager.process_messages(session_id, self.summary_prompt)
            
            # Get response using the configured chain
            response = await self.runnable_chain.ainvoke(
                {"input": messages},
                config,
                **kwargs
            )
            return response.content
        except Exception as e:
            print(f"Error in chat completion: {e}")
            return "Error occurred. Please try again."

    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Synchronous wrapper for achat
        """
        import asyncio
        return asyncio.run(self.achat(message, session_id, **kwargs))

    async def astream_chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """Async streaming chat with summary support"""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        config = {"configurable": {"session_id": session_id}}
        messages = [HumanMessage(content=message)]
        
        try:
            # Process messages and get summary if needed
            await self.message_manager.process_messages(session_id, self.summary_prompt)
            
            # Stream response using the configured chain
            async for chunk in self.runnable_chain.astream(
                {"input": messages},
                config,
                **kwargs
            ):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            print(f"Error in streaming chat: {e}")
            yield "Error occurred. Please try again."

    def stream_chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """
        Synchronous wrapper for streaming chat with summary support
        """
        
        async def async_generator():
            async for chunk in self.astream_chat(message, session_id, **kwargs):
                yield chunk
        
        return async_generator()

    def get_history(self, session_id: str) -> List[BaseMessage]:
        """
        Get chat history for a session
        """
        return self.message_manager.get_history(session_id).messages

    def clear_history(self, session_id: str):
        """
        Clear chat history for a session and remove the history file
        """
        self.message_manager.clear_history(session_id)

    def list_sessions(self) -> List[str]:
        """
        List all available chat sessions
        """
        return self.message_manager.list_sessions()

    def clear_all_histories(self):
        """
        Clear all chat histories and remove all history files
        """
        self.message_manager.clear_all_histories()
