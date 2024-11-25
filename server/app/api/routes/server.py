from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from server.app.core.models.online import LangChainChat
from server.utils.config import RAGPipeline
from server.utils.prompt import SYSTEM_PROMPT
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
    system_prompt: str = SYSTEM_PROMPT
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

async def get_rag_pipeline(request: Request) -> RAGPipeline:
    """Get RAG pipeline instance"""
    if not hasattr(request.app.state, 'rag_pipeline'):
        request.app.state.rag_pipeline = RAGPipeline.get_instance()
    return request.app.state.rag_pipeline

async def stream_generator(request: ChatRequest, rag: RAGPipeline) -> AsyncGenerator[str, None]:
    """
    Generate streaming chat response with RAG enhancement
    """
    try:
        # Get RAG-enhanced prompt
        rag_prompt = rag.get_enhanced_prompt(request.message)
        
        # Configure the model
        model.configure(
            base_url=request.base_url,
            api_key=request.api_key,
            model_name=request.model,
            system_prompt=request.system_prompt,
            max_messages=request.max_messages
        )
        
        # Use the RAG-enhanced prompt for chat
        async for chunk in model.astream_chat(rag_prompt):
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
async def stream_chat(
    request: ChatRequest, 
    req: Request,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """Stream chat endpoint with RAG enhancement"""
    await verify_auth(req)
    try:
        return StreamingResponse(
            stream_generator(request, rag),
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

