"""
Database connection settings for the Multi-Agent AI Customer Support Assistant.

This module establishes a connection to the PostgreSQL database using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import settings

# SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarative base
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
