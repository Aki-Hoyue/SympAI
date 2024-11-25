from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.app.api.routes import server
from server.utils.config import RAGPipeline

# Initialize RAG Pipeline at startup
rag_pipeline = RAGPipeline.get_instance()

app = FastAPI(title="SympAI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make RAG pipeline available to the app
app.state.rag_pipeline = rag_pipeline

app.include_router(server.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 
