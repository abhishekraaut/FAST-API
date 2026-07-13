from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut)
def create_task(
    payload: TaskCreate,
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> TaskOut:
    try:
        return TaskService(db).create(payload, organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[TaskOut])
def list_tasks(
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> list[TaskOut]:
    try:
        return TaskService(db).list(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int = Path(...),
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> TaskOut:
    try:
        return TaskService(db).get(task_id, organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    payload: TaskUpdate,
    task_id: int = Path(...),
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> TaskOut:
    try:
        return TaskService(db).update(task_id, organization_id, payload)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc

