from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base

# engine_kwargs = {}

# if settings.database_url.startswith("sqlite"):
#     engine_kwargs["connect_args"] = {"check_same_thread": False}

# engine = create_engine(
#     settings.database_url,
#     **engine_kwargs,
# )

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()