from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError, UnauthorizedError
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, UserCreate, UserOut


class AuthService:
    def __init__(self, session: Session) -> None:
        self.repo = UserRepository(session)

    def register(self, payload: UserCreate) -> UserOut:
        if self.repo.get_by_email(payload.email):
            raise DuplicateResourceError("User already exists")
        user = User(
            email=str(payload.email),
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        saved_user = self.repo.create(user)
        return UserOut(id=saved_user.id, email=saved_user.email, full_name=saved_user.full_name, is_active=saved_user.is_active)

    def login(self, payload: UserCreate) -> TokenResponse:
        user = self.repo.get_by_email(str(payload.email))
        if not user or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
