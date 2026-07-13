from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService


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


def test_task_crud_lifecycle(session: Session) -> None:
    org = Organization(name="Test Org", slug="test-org", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    service = TaskService(session)

    # 1. Create task
    task = service.create(
        TaskCreate(title="Complete GST Filing", description="Prepare Q1 tax report", due_date="2026-07-31"),
        organization_id=org.id,
    )
    assert task.title == "Complete GST Filing"
    assert task.status == "pending"

    # 2. Get task
    fetched = service.get(task.id, organization_id=org.id)
    assert fetched.id == task.id
    assert fetched.description == "Prepare Q1 tax report"

    # 3. Update task
    updated = service.update(
        task.id,
        organization_id=org.id,
        payload=TaskUpdate(status="in_progress", description="Updated description"),
    )
    assert updated.status == "in_progress"
    assert updated.description == "Updated description"

    # 4. List tasks
    all_tasks = service.list(organization_id=org.id)
    assert len(all_tasks) == 1
    assert all_tasks[0].id == task.id
