from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import Config
from app.api.routes import router

# Validate configuration
Config.validate()

# Initialize FastAPI app
app = FastAPI(
    title="LeetCode Chatbot", 
    version="1.0.0",
    description="An intelligent chatbot for analyzing LeetCode student performance data"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOW_ORIGINS,
    allow_credentials=Config.ALLOW_CREDENTIALS,
    allow_methods=Config.ALLOW_METHODS,
    allow_headers=Config.ALLOW_HEADERS,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routes
app.include_router(router, prefix="/api/v1")

# Root endpoint - serve the chatbot interface
@app.get("/")
async def root():
    """Serve the chatbot interface"""
    return FileResponse("app/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=Config.HOST, 
        port=Config.PORT,
        log_level="info"
    ) 