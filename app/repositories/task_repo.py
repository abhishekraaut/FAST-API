from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Task)

    def list_for_organization(self, organization_id: int) -> list[Task]:
        return self.session.query(Task).filter(Task.organization_id == organization_id).order_by(Task.id.desc()).all()

    def get_by_id_and_org(self, task_id: int, organization_id: int) -> Task | None:
        return self.session.query(Task).filter(Task.id == task_id, Task.organization_id == organization_id).first()

    def create(self, task: Task) -> Task:
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def update(self, task: Task) -> Task:
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
