from openai import BaseModel
import pytest
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from server.app.main import app
from dotenv import load_dotenv

load_dotenv()
client = TestClient(app)


# Test data
TEST_API_KEY = os.getenv("OPENAI_API_KEY")
HEADERS = {"Authorization": f"Bearer {TEST_API_KEY}"}

def test_chat_completion():
    """
    Test OpenAI-compatible chat completion endpoint
    """
    data = {
        "model": os.getenv("OPENAI_MODEL_NAME"),
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    if os.getenv("DEBUG", "false").lower() == "true":
        print(f"Request data: {json.dumps(data, indent=2)}")
        print(f"Headers: {json.dumps(HEADERS, indent=2)}")
    
    response = client.post("/v1/chat/completions", headers=HEADERS, json=data)
    
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
        
    assert response.status_code == 200
    result = response.json()
    assert result["object"] == "chat.completion"
    assert len(result["choices"]) > 0
    assert "message" in result["choices"][0]
    assert "content" in result["choices"][0]["message"]

def test_chat_completion_stream():
    """Test OpenAI-compatible streaming chat completion"""
    data = {
        "model": os.getenv("OPENAI_MODEL_NAME"),
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    with client.stream("POST", "/v1/chat/completions", headers=HEADERS, json=data) as response:
        assert response.status_code == 200
        
        for line in response.iter_lines():
            if line:
                if isinstance(line, bytes):
                    line = line.decode()
                if line.startswith("data: "):
                    if line.strip() == "data: [DONE]":
                        break
                    event = json.loads(line.replace("data: ", ""))
                    assert event["object"] == "chat.completion.chunk"
                    assert "choices" in event
                    assert len(event["choices"]) > 0
                    assert "delta" in event["choices"][0]

def test_chat_completion_without_auth():
    """Test chat completion endpoint without authentication"""
    data = {
        "model": os.getenv("OPENAI_MODEL_NAME"),
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
    response = client.post("/v1/chat/completions", json=data)
    assert response.status_code == 401
    assert "Missing API key" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main(["-v", "test_openai.py"]) 
