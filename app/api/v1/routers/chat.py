from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.chat import ChatSessionOut, ChatMessageCreate, ChatMessageOut, ChatQueryResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionOut)
def create_chat_session(
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> ChatSessionOut:
    try:
        return ChatService(db).create_session(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/sessions", response_model=list[ChatSessionOut])
def list_chat_sessions(
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> list[ChatSessionOut]:
    try:
        return ChatService(db).list_sessions(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def get_chat_messages(
    session_id: int = Path(...),
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[ChatMessageOut]:
    try:
        return ChatService(db).get_messages(session_id, organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/sessions/{session_id}/messages", response_model=ChatQueryResponse)
def post_chat_message(
    session_id: int = Path(...),
    payload: ChatMessageCreate = None,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> ChatQueryResponse:
    try:
        if not payload:
            raise ValueError("Message payload is required")
        return ChatService(db).handle_message(session_id, organization_id, payload.content)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
