from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db, get_current_user
from app.core.exceptions import http_exception_from_error
from app.schemas.auth import UserLogin, TokenResponse, UserCreate, UserOut, TokenRefresh
from app.services.auth_service import AuthService
from app.models.user import User

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


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: TokenRefresh, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        return AuthService(db).refresh(payload.refresh_token)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
    )

