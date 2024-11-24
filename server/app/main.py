from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.app.api.routes import router

app = FastAPI(title="SympAI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers without prefix to allow root path handling
app.include_router(router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"} 
