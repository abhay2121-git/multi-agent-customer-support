"""Conversation memory and ticket management functions.

This module provides database-backed conversation history retrieval,
message persistence, session summaries, and ticket CRUD operations.
"""

import logging
import random
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from backend.database.models import Conversation, Ticket

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task 1 — Conversation Memory
# ---------------------------------------------------------------------------

def get_conversation_history(
    session_id: str,
    db: Session,
    limit: int = 6,
) -> list[dict]:
    """Load the most recent conversation messages for a session.

    Returns a chronologically ordered list of dicts suitable for the
    Groq chat completions API::

        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    try:
        rows = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.timestamp.desc())
            .limit(limit)
            .all()
        )
        # Reverse so the list is in chronological order
        rows.reverse()
        history = [{"role": r.role, "content": r.message} for r in rows]
        logger.debug(
            "Loaded %d history messages for session %s", len(history), session_id
        )
        return history
    except Exception as e:
        logger.error("Failed to load conversation history for session %s: %s", session_id, e)
        return []


def save_message(
    session_id: str,
    user_id: int,
    role: str,
    message: str,
    db: Session,
    agent_used: str | None = None,
    intent_detected: str | None = None,
) -> None:
    """Persist a single conversation message to the database."""
    try:
        record = Conversation(
            session_id=session_id,
            user_id=user_id,
            role=role,
            message=message,
            agent_used=agent_used,
            intent_detected=intent_detected,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        logger.info(
            "Saved %s message — session=%s, user_id=%d",
            role,
            session_id,
            user_id,
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to save %s message for session %s: %s",
            role,
            session_id,
            e,
            exc_info=True,
        )
        raise


def get_session_summary(session_id: str, db: Session) -> dict:
    """Return a summary of a conversation session.

    Returns::

        {
            "session_id": "...",
            "total_messages": 12,
            "first_message_at": datetime,
            "last_message_at": datetime,
            "agents_used": ["FAQAgent", "BillingAgent"],
        }
    """
    try:
        total = (
            db.query(sa_func.count(Conversation.id))
            .filter(Conversation.session_id == session_id)
            .scalar()
        )
        first_ts = (
            db.query(sa_func.min(Conversation.timestamp))
            .filter(Conversation.session_id == session_id)
            .scalar()
        )
        last_ts = (
            db.query(sa_func.max(Conversation.timestamp))
            .filter(Conversation.session_id == session_id)
            .scalar()
        )
        agents_rows = (
            db.query(Conversation.agent_used)
            .filter(
                Conversation.session_id == session_id,
                Conversation.agent_used.isnot(None),
                Conversation.agent_used != "",
            )
            .distinct()
            .all()
        )
        # Flatten and deduplicate (agent_used can be comma-separated)
        agents: list[str] = []
        for (raw,) in agents_rows:
            for name in raw.split(", "):
                name = name.strip()
                if name and name not in agents:
                    agents.append(name)

        return {
            "session_id": session_id,
            "total_messages": total or 0,
            "first_message_at": first_ts,
            "last_message_at": last_ts,
            "agents_used": agents,
        }
    except Exception as e:
        logger.error("Failed to get session summary for %s: %s", session_id, e)
        return {
            "session_id": session_id,
            "total_messages": 0,
            "first_message_at": None,
            "last_message_at": None,
            "agents_used": [],
        }


# ---------------------------------------------------------------------------
# Task 2 — Ticket Management
# ---------------------------------------------------------------------------

def create_ticket(
    user_id: int,
    session_id: str,
    issue_summary: str,
    db: Session,
    priority: str = "medium",
) -> dict:
    """Create a support ticket and return its details.

    Generates a ticket number in the format ``TKT-XXXXXX`` (6 random digits).
    """
    try:
        ticket_number = f"TKT-{random.randint(100000, 999999)}"

        ticket = Ticket(
            ticket_number=ticket_number,
            user_id=user_id,
            session_id=session_id,
            issue_summary=issue_summary,
            status="open",
            priority=priority,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        logger.info(
            "Ticket created — %s (user_id=%d, session=%s, priority=%s)",
            ticket_number,
            user_id,
            session_id,
            priority,
        )

        return {
            "ticket_number": ticket.ticket_number,
            "issue_summary": ticket.issue_summary,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": str(ticket.created_at) if ticket.created_at else None,
        }
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create ticket for user %d, session %s: %s",
            user_id,
            session_id,
            e,
            exc_info=True,
        )
        raise


def get_user_tickets(user_id: int, db: Session) -> list[dict]:
    """Return all tickets for a user, most recent first."""
    try:
        tickets = (
            db.query(Ticket)
            .filter(Ticket.user_id == user_id)
            .order_by(Ticket.created_at.desc())
            .all()
        )
        return [
            {
                "ticket_number": t.ticket_number,
                "issue_summary": t.issue_summary,
                "status": t.status,
                "priority": t.priority,
                "session_id": t.session_id,
                "created_at": str(t.created_at) if t.created_at else None,
                "updated_at": str(t.updated_at) if t.updated_at else None,
            }
            for t in tickets
        ]
    except Exception as e:
        logger.error("Failed to fetch tickets for user %d: %s", user_id, e)
        return []
