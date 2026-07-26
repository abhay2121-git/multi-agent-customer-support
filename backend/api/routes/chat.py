"""Chat routes for the customer support AI assistant."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.agents.router import route_and_respond
from backend.auth_utils import get_current_user
from backend.database.connection import get_db
from backend.database.models import Conversation, User
from backend.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
def send_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a user chat message through the multi-agent pipeline.

    Flow: User → Intent Detection → Router → RAG → Agent → Groq → Response
    """
    try:
        # Load conversation history for this session
        history_records = (
            db.query(Conversation)
            .filter(
                Conversation.session_id == payload.session_id,
                Conversation.user_id == current_user.id,
            )
            .order_by(Conversation.timestamp.asc())
            .limit(20)
            .all()
        )

        conversation_history = []
        for record in history_records:
            conversation_history.append(
                {"role": record.role, "content": record.message}
            )

        # Route through multi-agent pipeline
        result = route_and_respond(
            message=payload.message,
            conversation_history=conversation_history,
            session_id=payload.session_id,
        )

        now = datetime.now(timezone.utc)

        # Save user message to conversation history
        user_record = Conversation(
            session_id=payload.session_id,
            user_id=current_user.id,
            role="user",
            message=payload.message,
            agent_used=None,
            intent_detected=", ".join(result.get("intents_detected", [])),
            timestamp=now,
        )
        db.add(user_record)

        # Save assistant response to conversation history
        agents_str = ", ".join(result.get("agents_used", []))
        intents_str = ", ".join(result.get("intents_detected", []))

        assistant_record = Conversation(
            session_id=payload.session_id,
            user_id=current_user.id,
            role="assistant",
            message=result["response"],
            agent_used=agents_str,
            intent_detected=intents_str,
            timestamp=now,
        )
        db.add(assistant_record)
        db.commit()

        logger.info(
            "Chat processed — session=%s, user=%s, intents=%s, agents=%s",
            payload.session_id,
            current_user.username,
            intents_str,
            agents_str,
        )

        return ChatResponse(
            response=result["response"],
            agent_used=agents_str,
            intent_detected=intents_str,
            session_id=payload.session_id,
            timestamp=now,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Chat processing failed for session %s: %s",
            payload.session_id,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message. Please try again.",
        )
