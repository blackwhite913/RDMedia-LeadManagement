"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.db import init_db
from src.api import router

# Create FastAPI app
app = FastAPI(
    title="RD Media Lead Management System",
    description="Internal lead management system for Apollo exports",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup
    """
    print("Starting RD Media Lead Management System...")
    init_db()
    print("Database initialized successfully")
    print("Server ready at http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")


@app.get("/")
def root():
    """
    Root endpoint
    """
    return {
        "message": "RD Media Lead Management System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
