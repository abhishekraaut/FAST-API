from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.models.task import Task
from app.repositories.task_repo import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut


class TaskService:
    def __init__(self, session: Session) -> None:
        self.repo = TaskRepository(session)

    def create(self, payload: TaskCreate, organization_id: int) -> TaskOut:
        task = Task(
            organization_id=organization_id,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            status="pending",
        )
        saved = self.repo.create(task)
        return TaskOut.model_validate(saved)

    def list(self, organization_id: int) -> list[TaskOut]:
        tasks = self.repo.list_for_organization(organization_id)
        return [TaskOut.model_validate(t) for t in tasks]

    def get(self, task_id: int, organization_id: int) -> TaskOut:
        task = self.repo.get_by_id_and_org(task_id, organization_id)
        if not task:
            raise ResourceNotFoundError(f"Task with ID {task_id} not found")
        return TaskOut.model_validate(task)

    def update(self, task_id: int, organization_id: int, payload: TaskUpdate) -> TaskOut:
        task = self.repo.get_by_id_and_org(task_id, organization_id)
        if not task:
            raise ResourceNotFoundError(f"Task with ID {task_id} not found")

        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description
        if payload.status is not None:
            task.status = payload.status
        if payload.due_date is not None:
            task.due_date = payload.due_date

        updated = self.repo.update(task)
        return TaskOut.model_validate(updated)
