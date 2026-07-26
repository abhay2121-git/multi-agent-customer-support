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

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")

    # Attempt to pre-load FAISS index (non-blocking)
    try:
        from backend.rag.retriever import vector_store
        if vector_store.load_index():
            logger.info("FAISS index pre-loaded at startup.")
        else:
            logger.warning(
                "FAISS index not found at startup. "
                "It will be auto-built on first retrieval request, or you can run: "
                "python -m backend.rag.build_index"
            )
    except Exception as e:
        logger.warning("Could not pre-load FAISS index: %s", e)

    # Log registered routes
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            logger.info("Route: %s %s", route.methods, route.path)

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
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)


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
