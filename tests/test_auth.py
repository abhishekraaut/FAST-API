from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
import app.models
from app.models.user import User
from app.models.membership import Membership
from app.models.organization import Organization
from app.database.base import Base
from app.main import app
from app.api.v1.deps import get_db






@pytest.fixture()
def client() -> TestClient:
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()



def test_register_login_me_refresh(client: TestClient) -> None:
    # 1. Register user
    reg_res = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "full_name": "New User", "password": "mypassword"},
    )
    assert reg_res.status_code == 200
    assert reg_res.json()["email"] == "newuser@example.com"

    # 2. Login user
    login_res = client.post(
        "/auth/login",
        json={"email": "newuser@example.com", "password": "mypassword"},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 3. Access /auth/me
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "newuser@example.com"

    # 4. Refresh token
    refresh_res = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # 5. Access /auth/me with new token
    new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    new_me_res = client.get("/auth/me", headers=new_headers)
    assert new_me_res.status_code == 200
    assert new_me_res.json()["email"] == "newuser@example.com"
