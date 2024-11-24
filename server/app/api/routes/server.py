from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from server.app.core.models.online import LangChainChat
import json
import os
from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

router = APIRouter()

# Initialize model with default settings
model = LangChainChat()

class ChatRequest(BaseModel):
    message: str
    base_url: str = os.getenv("OPENAI_BASE_URL")
    api_key: str = os.getenv("OPENAI_API_KEY")
    model: str = os.getenv("OPENAI_MODEL_NAME")
    system_prompt: str = "You are a helpful assistant specialized in Traditional Chinese Medicine."
    max_messages: int = 6

async def verify_auth(request: Request):
    """
    Verify user-agent for authentication
    TODO: Implement SessionID verification
    """
    user_agent = request.headers.get("user-agent", "").lower()
    if user_agent != "sympai":
        raise HTTPException(
            status_code=403,
            detail="Unauthorized access. Invalid user-agent."
        )

async def stream_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Generate streaming chat response
    """
    try:
        model.configure(
            base_url=request.base_url,
            api_key=request.api_key,
            model_name=request.model,
            system_prompt=request.system_prompt,
            max_messages=request.max_messages
        )
        
        async for chunk in model.astream_chat(request.message):
            if DEBUG:
                print(f"Streaming chunk: {chunk}")
            yield f"data: {json.dumps({'text': chunk})}\n\n"
    except Exception as e:
        if DEBUG:
            print(f"Error in stream_generator: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@router.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "SympAI API is running"}

@router.post("/api/chat")
async def stream_chat(request: ChatRequest, req: Request):
    """
    Stream chat endpoint that returns chunks of generated text
    
    Args:
        request (ChatRequest): Chat request containing message and model configuration
        ChatRequest:
          - message (str): User message
          - base_url (str): Base URL for the OpenAI API
          - api_key (str): API key for the OpenAI API
          - model_name (str): Name of the OpenAI model
          - system_prompt (str): System prompt for the model
          - max_messages (int): Maximum number of messages before summarization
    
    Returns:
        StreamingResponse: Server-sent events stream of generated text chunks
    """
    await verify_auth(req)
    try:
        return StreamingResponse(
            stream_generator(request),
            media_type="text/event-stream"
        )
    except Exception as e:
        if DEBUG:
            print(f"Error in stream_chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/models")
async def get_models(request: Request):
    """
    Get available models
    
    Returns:
        dict: Dictionary containing status, code, and list of models
    """
    await verify_auth(request)
    return {
        "status": "success",
        "code": 200,
        "models": model.list_models()
    }

