from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.services.chat_service import ChatService


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_conversational_chat_agent(session: Session) -> None:
    org = Organization(name="Chat Org", slug="chat-org", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    service = ChatService(session)

    # 1. Create a session
    sess = service.create_session(org.id)
    assert sess.id is not None
    assert sess.organization_id == org.id

    # 2. List sessions
    sessions = service.list_sessions(org.id)
    assert len(sessions) == 1
    assert sessions[0].id == sess.id

    # 3. Post a message to check fallback classifier
    response = service.handle_message(
        session_id=sess.id,
        organization_id=org.id,
        content="What is my current cash account balance?",
    )
    assert response.session_id == sess.id
    assert response.intent == "QUERY_BALANCE"
    assert response.confidence >= 0.7

    # 4. Check message log history contains user and assistant entries
    messages = service.get_messages(sess.id, org.id)
    assert len(messages) == 2
    assert messages[0].sender == "user"
    assert messages[0].intent == "QUERY_BALANCE"
    assert messages[1].sender == "assistant"

    # 5. Verify QUERY_INVOICES intent
    res_invoices = service.handle_message(
        session_id=sess.id,
        organization_id=org.id,
        content="Show unpaid invoices",
    )
    assert res_invoices.intent == "QUERY_INVOICES"

    # 6. Verify PAY_INVOICE intent
    res_pay = service.handle_message(
        session_id=sess.id,
        organization_id=org.id,
        content="Mark invoice #123 as paid",
    )
    assert res_pay.intent == "PAY_INVOICE"
    assert res_pay.entities.get("invoice_id") == 123

    # 7. Verify RECONCILE intent
    res_recon = service.handle_message(
        session_id=sess.id,
        organization_id=org.id,
        content="auto reconcile bank statements",
    )
    assert res_recon.intent == "RECONCILE"

