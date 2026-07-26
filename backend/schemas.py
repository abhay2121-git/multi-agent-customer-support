"""Pydantic request and response models for API endpoints."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request body for creating a new user account."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT and session metadata returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    session_id: str
    username: str


class UserResponse(BaseModel):
    """Safe user profile response model without password fields."""

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class ChatRequest(BaseModel):
    """Request body for submitting a chat message to the assistant."""

    message: str = Field(min_length=1, max_length=1000)
    session_id: str


class ChatResponse(BaseModel):
    """Response model for chat output from the selected support agent."""

    response: str
    agent_used: str
    intent_detected: str
    session_id: str
    timestamp: datetime
