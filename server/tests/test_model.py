import time
import uuid
import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from server.app.core.models.online import LangChainChat
from server.app.core.models.local import LocalLLM

@pytest.fixture
def online_llm():
    return LangChainChat(max_messages=3)

@pytest.fixture
def local_llm():
    return LocalLLM()

def test_online_model_streaming_chat(online_llm: LangChainChat):
    import asyncio
    
    async def test_chat():
        chat = online_llm
        
        session_id = str(int(time.time())) + "-" + str(uuid.uuid4())
        
        messages = [
            "Hello! I'm Hoyue!",
            "1 + 1 = ?",
            "What's your favorite color?",
            "2 + 3 = ?",
            "What's my name?"
        ]
        
        for msg in messages:
            print(f"\nUser: {msg}")
            async for chunk in chat.astream_chat(msg, session_id=session_id):
                assert chunk is not None
                print(chunk, end="", flush=True)
            print("\n")
        
        # Get history with summary
        history = chat.get_history(session_id)
        print("\nFinal chat history:")
        for message in history:
            assert message is not None
            print(f"{message.type}: {message.content}")
        
        # Clean up
        chat.clear_all_histories()
    
    # Run the test
    asyncio.run(test_chat())

def test_local_model_basic_chat(local_llm: LocalLLM):
    """
    Test basic chat functionality of local LLM
    """
    try:
        local_llm.load_model()
        query = "I had fever yesterday, what should I do?"
        system_prompt = "You are a helpful assistant specialized in Traditional Chinese Medicine."
        response = local_llm.generate_response(query, system_prompt)
        print(f"User query: {query}")
        print(f"Answer: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    pytest.main(["-v", "--disable-warnings", __file__]) 
    