from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.auth import UserLogin, TokenResponse, UserCreate, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    try:
        return AuthService(db).register(payload)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        return AuthService(db).login(payload)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
