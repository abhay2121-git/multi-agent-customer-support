"""
Database models for the Multi-Agent AI Customer Support Assistant.

This module defines the database tables for users, sessions, conversations, and tickets.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    session_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    expires_at = Column(TIMESTAMP, nullable=False)

    user = relationship('User', back_populates='sessions')

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    agent_used = Column(String(50))
    intent_detected = Column(String(50))
    timestamp = Column(TIMESTAMP, server_default=func.now())

    user = relationship('User', back_populates='conversations')

class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_number = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    session_id = Column(String(255))
    issue_summary = Column(Text, nullable=False)
    status = Column(String(20), default='open')
    priority = Column(String(20), default='medium')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship('User', back_populates='tickets')

User.sessions = relationship('Session', order_by=Session.id, back_populates='user')
User.conversations = relationship('Conversation', order_by=Conversation.id, back_populates='user')
User.tickets = relationship('Ticket', order_by=Ticket.id, back_populates='user')
