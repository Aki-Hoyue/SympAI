import pytest
import json
from fastapi.testclient import TestClient
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from server.app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SympAI API is running"}

def test_models_without_auth():
    """Test models endpoint without authentication"""
    response = client.get("/api/models")
    assert response.status_code == 403
    assert "Unauthorized access" in response.json()["detail"]

def test_models_with_auth():
    """Test models endpoint with authentication"""
    headers = {"user-agent": "sympai"}
    response = client.get("/api/models", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert isinstance(response.json()["models"], list)

def test_chat_without_auth():
    """Test chat endpoint without authentication"""
    data = {
        "message": "Test message",
    }
    response = client.post("/api/chat", json=data)
    assert response.status_code == 403
    assert "Unauthorized access" in response.json()["detail"]

def test_chat_with_auth():
    """Test chat endpoint with authentication"""
    headers = {
        "user-agent": "sympai",
        "accept": "text/event-stream"
    }
    data = {
        "message": "message",
    }

    with client.stream("POST", "/api/chat", headers=headers, json=data) as response:
        assert response.status_code == 200

        # Read and check the streaming response
        for line in response.iter_lines():
            if line:
                if isinstance(line, str):
                    text = line.replace('data: ', '')
                else:
                    text = line.decode('utf-8').replace('data: ', '')
                    
                try:
                    parsed_text = json.loads(text)
                    assert isinstance(parsed_text, (str, dict))
                except json.JSONDecodeError:
                    assert isinstance(text, str)

if __name__ == "__main__":
    pytest.main(["-v", "test_api.py"]) 
