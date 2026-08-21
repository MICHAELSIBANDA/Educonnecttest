import json
import os
from typing import Any

from sqlalchemy import JSON, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class AppState(Base):
    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON)


def database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set")
    return url.replace("postgres://", "postgresql+psycopg://", 1)


def create_database_engine():
    return create_engine(database_url(), pool_pre_ping=True)


def initialize_database(engine) -> None:
    Base.metadata.create_all(engine)


def load_state(engine, key: str) -> dict[str, Any] | None:
    with Session(engine) as session:
        state = session.scalar(select(AppState).where(AppState.key == key))
        return state.value if state else None


def save_state(engine, key: str, value: dict[str, Any]) -> None:
    with Session(engine) as session:
        state = session.get(AppState, key)
        if state is None:
            session.add(AppState(key=key, value=json.loads(json.dumps(value))))
        else:
            state.value = json.loads(json.dumps(value))
        session.commit()
