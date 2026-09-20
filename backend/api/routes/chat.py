"""Chat routes for the customer support AI assistant.

Endpoints:
    POST   /chat/message             — Send a message through the multi-agent pipeline
    GET    /chat/history/{session_id} — Retrieve full conversation history for a session
    GET    /chat/sessions             — List all sessions for the current user
    POST   /chat/new-session          — Create a new chat session
    GET    /chat/tickets              — List all tickets for the current user
"""

import logging
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func as sa_func

from backend.agents.router import route_and_respond
from backend.auth_utils import get_current_user, generate_session_id
from backend.database.connection import get_db
from backend.database.models import Conversation, User, Session as UserSession, Ticket
from backend.memory import (
    get_conversation_history,
    save_message,
    get_session_summary,
    create_ticket,
    get_user_tickets,
    delete_user_ticket,
)
from backend.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_session_ownership(
    session_id: str, user: User, db: DBSession
) -> None:
    """Verify that session_id belongs to the given user. Auto-creates session if not yet in DB."""
    existing = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if existing is not None:
        if existing.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this session.",
            )
    else:
        try:
            new_session = UserSession(
                session_id=session_id,
                user_id=user.id,
                title="Support Chat",
            )
            db.add(new_session)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning("Auto-creating session failed: %s", e)


# ---------------------------------------------------------------------------
# POST /chat/message
# ---------------------------------------------------------------------------

@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Send Message",
    description="Process a user chat message through the multi-agent pipeline.\n\n"
                "Flow: User → Intent Detection → Router → RAG → Agent → Groq → Response",
)
def send_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> ChatResponse:
    start = time.perf_counter()

    try:
        # 1. Validate session ownership
        _validate_session_ownership(payload.session_id, current_user, db)

        # 2. Load conversation history (capped at 6 messages)
        conversation_history = get_conversation_history(
            session_id=payload.session_id,
            db=db,
            limit=6,
        )

        # 3. Route through multi-agent pipeline with graceful fallback
        try:
            result = route_and_respond(
                message=payload.message,
                conversation_history=conversation_history,
                session_id=payload.session_id,
            )
        except Exception as e:
            logger.error("Multi-agent routing failed: %s", e, exc_info=True)
            result = {
                "response": "I understand your query, but encountered a temporary delay processing parts of our system. How else can I assist you with your order, billing, or device?",
                "agents_used": ["SupportAgent"],
                "intents_detected": ["general"],
                "context_sources": [],
            }


        agents_str = ", ".join(result.get("agents_used", []))
        intents_str = ", ".join(result.get("intents_detected", []))
        now = datetime.now(timezone.utc)

        # 4. Save user message
        save_message(
            session_id=payload.session_id,
            user_id=current_user.id,
            role="user",
            message=payload.message,
            db=db,
            agent_used=None,
            intent_detected=intents_str,
        )

        # 5. Save assistant response
        save_message(
            session_id=payload.session_id,
            user_id=current_user.id,
            role="assistant",
            message=result["response"],
            db=db,
            agent_used=agents_str,
            intent_detected=intents_str,
        )

        # 6. Auto-create ticket only if genuine complaint/escalation and no open ticket exists for this session
        ticket_number = None
        if "ComplaintAgent" in agents_str:
            try:
                # Prevent spamming tickets: only 1 ticket per session
                existing_ticket = (
                    db.query(Ticket)
                    .filter(
                        Ticket.user_id == current_user.id,
                        Ticket.session_id == payload.session_id,
                        Ticket.status != "closed",
                    )
                    .first()
                )
                if not existing_ticket:
                    # Check if the query is an actual complaint or escalation request
                    complaint_indicators = [
                        "complaint", "escalat", "manager", "unacceptable", "terrible",
                        "worst", "cheat", "fraud", "scam", "sue", "legal", "ticket",
                        "dispute", "horrible", "damaged", "broken"
                    ]
                    msg_lower = payload.message.lower()
                    is_direct_complaint = any(ind in msg_lower for ind in complaint_indicators)

                    # Only auto-create if user directly expressed a complaint/escalation or intent was specifically complaint
                    if is_direct_complaint or intents_str == "complaint":
                        ticket = create_ticket(
                            user_id=current_user.id,
                            session_id=payload.session_id,
                            issue_summary=payload.message[:200],
                            db=db,
                            priority="high",
                        )
                        ticket_number = ticket["ticket_number"]
            except Exception as e:
                logger.warning("Auto-ticket creation failed: %s", e)

        elapsed = time.perf_counter() - start
        logger.info(
            "Chat processed — session=%s, user=%s, intents=%s, agents=%s, "
            "ticket=%s, time=%.2fs",
            payload.session_id,
            current_user.username,
            intents_str,
            agents_str,
            ticket_number or "none",
            elapsed,
        )

        return ChatResponse(
            response=result["response"],
            agent_used=agents_str,
            intent_detected=intents_str,
            session_id=payload.session_id,
            timestamp=now,
            ticket_number=ticket_number,
        )

    except HTTPException:
        raise
    except Exception as e:
        elapsed = time.perf_counter() - start
        logger.error(
            "Chat processing failed for session %s (%.2fs): %s",
            payload.session_id,
            elapsed,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message. Please try again.",
        )


# ---------------------------------------------------------------------------
# GET /chat/history/{session_id}
# ---------------------------------------------------------------------------

@router.get(
    "/history/{session_id}",
    summary="Get Conversation History",
    description="Return full conversation history for a specific session.",
)
def get_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    _validate_session_ownership(session_id, current_user, db)

    rows = (
        db.query(Conversation)
        .filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user.id,
        )
        .order_by(Conversation.timestamp.asc())
        .all()
    )

    messages = [
        {
            "role": r.role,
            "content": r.message,
            "agent_used": r.agent_used,
            "intent_detected": r.intent_detected,
            "timestamp": str(r.timestamp) if r.timestamp else None,
        }
        for r in rows
    ]

    return {"session_id": session_id, "messages": messages}


# ---------------------------------------------------------------------------
# GET /chat/sessions
# ---------------------------------------------------------------------------

@router.get(
    "/sessions",
    summary="List User Sessions",
    description="Return all chat sessions for the authenticated user with message counts.",
)
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    # Find all sessions that have conversation messages for this user
    session_rows = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id)
        .order_by(UserSession.created_at.desc())
        .all()
    )

    sessions = []
    for s in session_rows:
        summary = get_session_summary(s.session_id, db)
        sessions.append({
            "session_id": s.session_id,
            "created_at": str(s.created_at) if s.created_at else None,
            "total_messages": summary["total_messages"],
            "first_message_at": str(summary["first_message_at"]) if summary["first_message_at"] else None,
            "last_message_at": str(summary["last_message_at"]) if summary["last_message_at"] else None,
            "agents_used": summary["agents_used"],
        })

    return {"sessions": sessions}


# ---------------------------------------------------------------------------
# POST /chat/new-session
# ---------------------------------------------------------------------------

@router.post(
    "/new-session",
    summary="Create New Session",
    description="Generate a new chat session and persist it in the sessions table.",
    status_code=status.HTTP_201_CREATED,
)
def create_new_session(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    new_sid = generate_session_id()

    session_record = UserSession(
        user_id=current_user.id,
        session_id=new_sid,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(session_record)
    db.commit()

    logger.info(
        "New session created — session=%s, user=%s",
        new_sid,
        current_user.username,
    )

    return {"session_id": new_sid}


# ---------------------------------------------------------------------------
# DELETE /chat/session/{session_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/session/{session_id}",
    summary="Delete Chat Session",
    description="Delete a chat session and all its associated conversation messages.",
)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    # Delete conversation messages for this session
    deleted_msgs = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id, Conversation.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    # Delete session record
    deleted_sessions = (
        db.query(UserSession)
        .filter(UserSession.session_id == session_id, UserSession.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    # Unlink session_id from any tickets associated with this session so tickets are preserved
    db.query(Ticket).filter(
        Ticket.session_id == session_id,
        Ticket.user_id == current_user.id
    ).update({"session_id": None}, synchronize_session=False)

    db.commit()

    logger.info(
        "Session deleted — session=%s, user=%s, deleted_messages=%d",
        session_id,
        current_user.username,
        deleted_msgs,
    )

    return {
        "status": "success",
        "message": "Session deleted successfully",
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# GET /chat/tickets
# ---------------------------------------------------------------------------

@router.get(
    "/tickets",
    summary="List User Tickets",
    description="Return all support tickets for the authenticated user.",
)
def list_tickets(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    tickets = get_user_tickets(current_user.id, db)
    return {"tickets": tickets}


# ---------------------------------------------------------------------------
# DELETE /chat/ticket/{ticket_number}
# ---------------------------------------------------------------------------

@router.delete(
    "/ticket/{ticket_number}",
    summary="Delete Support Ticket",
    description="Delete a support ticket belonging to the current user.",
)
def delete_ticket(
    ticket_number: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    success = delete_user_ticket(ticket_number, current_user.id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or you do not have permission to delete it.",
        )
    logger.info(
        "Ticket deleted via API — ticket=%s, user=%s",
        ticket_number,
        current_user.username,
    )
    return {"status": "success", "message": f"Ticket {ticket_number} deleted."}

