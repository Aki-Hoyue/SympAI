from typing import AsyncGenerator, List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import time
import json
import os
from dotenv import load_dotenv
from server.app.core.models.online import LangChainChat

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

router = APIRouter(prefix="/v1")
model = LangChainChat()

class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{int(time.time())}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Dict[str, Any]]
    usage: Usage

async def verify_auth(request: Request):
    """
    Verify API key from header
    """
    api_key = request.headers.get("authorization", "").replace("Bearer ", "")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )
    # Here you can add your own API key validation logic
    return api_key

async def stream_generator(request: ChatCompletionRequest, api_key: str) -> AsyncGenerator[str, None]:
    """
    Generate streaming chat response in OpenAI format
    """
    try:
        # Configure model
        model.configure(
            api_key=api_key,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Get the last user message
        last_message = next((msg.content for msg in reversed(request.messages) 
                           if msg.role == "user"), None)
        if not last_message:
            raise ValueError("No user message found")

        async for chunk in model.astream_chat(last_message):
            if DEBUG:
                print(f"Streaming chunk: {chunk}")
            
            response = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": chunk
                    },
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(response)}\n\n"
            
        # Send the final [DONE] message
        yield "data: [DONE]\n\n"
    except Exception as e:
        if DEBUG:
            print(f"Error in stream_generator: {e}")
        error_response = {
            "error": {
                "message": str(e),
                "type": "internal_error",
                "code": 500
            }
        }
        yield f"data: {json.dumps(error_response)}\n\n"

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    raw_request: Request,
    request: ChatCompletionRequest
):
    """
    OpenAI-compatible chat completion endpoint
    
    Args:
        raw_request (Request): Raw request object
        request (ChatCompletionRequest): Chat completion request
    """
    if DEBUG:
        print(f"Received request body: {await raw_request.json()}")
        print(f"Parsed request: {request}")
        print(f"Headers: {raw_request.headers}")
    
    try:
        api_key = await verify_auth(raw_request)
    except HTTPException as e:
        if e.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key"}
            )
        raise e
    
    try:
        if request.stream:
            return StreamingResponse(
                stream_generator(request, api_key),
                media_type="text/event-stream"
            )
        
        # For non-streaming responses
        model.configure(
            api_key=api_key,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Get the last user message
        last_message = next((msg.content for msg in reversed(request.messages) 
                           if msg.role == "user"), None)
        if not last_message:
            raise ValueError("No user message found")

        response = await model.achat(last_message)
        
        return ChatCompletionResponse(
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop"
            }],
            usage=Usage()
        )

    except Exception as e:
        if DEBUG:
            print(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models(request: Request):
    """List available models"""
    await verify_auth(request)
    try:
        models = model.list_models()
        return {
            "object": "list",
            "data": [
                {
                    "id": model_id,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "sympai"
                }
                for model_id in models
            ]
        }
    except Exception as e:
        if DEBUG:
            print(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
