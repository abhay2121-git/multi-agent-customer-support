"""
Main entry point for the Multi-Agent AI Customer Support Assistant.

This module initializes the FastAPI application, sets up database connections,
configures CORS, and includes API routes.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings, validate_settings
from backend.database.connection import engine
from backend.database.models import Base
from backend.api.routes import auth, chat

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    # --- Startup ---
    logger.info("Starting Customer Support AI v1.0.0")

    # Validate configuration
    validate_settings()

    # 1. Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")

    # 2 & 3. Load FAISS index or auto-run build_index pipeline
    try:
        from backend.rag.retriever import vector_store
        if not vector_store.load_index():
            logger.warning("FAISS index not found at startup. Auto-building index...")
            from backend.rag.build_index import build_index
            build_index()
            vector_store.load_index()
        # 4. Log "RAG pipeline ready" when done
        logger.info("RAG pipeline ready")
    except Exception as e:
        logger.error("Error setting up RAG pipeline: %s", e)

    # 5. Log "All agents initialized"
    try:
        from backend.agents.router import AGENT_MAP
        logger.info("All agents initialized: %s", list(AGENT_MAP.keys()))
    except Exception as e:
        logger.warning("Could not log agent initialization: %s", e)

    # Log registered routes
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            logger.info("Route: %s %s", route.methods, route.path)

    # 6. Log server ready message with port
    logger.info("Server ready on http://0.0.0.0:8000")
    logger.info("Startup complete.")
    yield
    # --- Shutdown ---
    logger.info("Shutting down Customer Support AI.")


# Initialize FastAPI app
app = FastAPI(
    title="Customer Support AI",
    description="A multi-agent AI system for customer support.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)


import os
from fastapi.staticfiles import StaticFiles

# Mount frontend directory for direct web UI access
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Customer Support AI API!",
        "status": "running",
        "frontend": "/frontend/",
        "docs": "/docs",
        "health": "/health",
    }



# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "project": "Customer Support AI",
        "version": "1.0.0",
        "model": settings.GROQ_MODEL,
    }


# Run with uvicorn on port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
