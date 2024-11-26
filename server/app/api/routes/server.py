from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from server.app.core.models.online import LangChainChat
from server.app.utils.config import RAGPipeline
from server.app.utils.prompt import SYSTEM_PROMPT, TITLE_SYSTEM_PROMPT
import json
import os
from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SYMPAI_API_KEY_PREFIX = "sk-hoyue-sympai"

router = APIRouter()

# Initialize model with default settings
model = LangChainChat()

class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    base_url: str = os.getenv("OPENAI_BASE_URL")
    api_key: str = os.getenv("OPENAI_API_KEY")
    model: str = os.getenv("OPENAI_MODEL_NAME")
    system_prompt: str = SYSTEM_PROMPT
    max_messages: int = 6

class TitleRequest(BaseModel):
    message: str
    base_url: str = os.getenv("OPENAI_BASE_URL")
    api_key: str = os.getenv("OPENAI_API_KEY")
    model: str = os.getenv("OPENAI_MODEL_NAME")

async def verify_auth(request: Request):
    """
    Verify Bearer token for authentication
    """
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or auth.replace("Bearer ", "") != SYMPAI_API_KEY_PREFIX:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized access. Invalid API key."
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
        async for chunk in model.astream_chat(rag_prompt, request.session_id):
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

@router.post("/api/generate_title")
async def generate_title(
    request: TitleRequest,
    req: Request,
):
    """Generate a title for the conversation"""
    await verify_auth(req)
    try:
        # Configure the model for title generation
        model.configure(
            base_url=request.base_url,
            api_key=request.api_key,
            model_name=request.model,
            system_prompt=TITLE_SYSTEM_PROMPT,
            max_messages=1  # We only need one message for title generation
        )
        
        # Generate title using non-streaming chat
        title = await model.achat(request.message)
        
        return {
            "status": "success",
            "code": 200,
            "title": title.strip()  # Remove any extra whitespace
        }
        
    except Exception as e:
        if DEBUG:
            print(f"Error in generate_title endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

