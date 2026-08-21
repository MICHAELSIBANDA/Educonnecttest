import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    role: Mapped[str] = mapped_column(String(40))
    password_hash: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Record(Base):
    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    record_type: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SessionToken(Base):
    __tablename__ = "session_tokens"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./educonnect.db")
    return url.replace("postgres://", "postgresql+psycopg://", 1)


def create_database_engine():
    url = database_url()
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


def initialize_database(engine) -> None:
    Base.metadata.create_all(engine)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return f"pbkdf2_sha256$600000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
    return algorithm == "pbkdf2_sha256" and hmac.compare_digest(candidate.hex(), digest_hex)


def find_user(engine, number: str) -> User | None:
    with Session(engine) as session:
        return session.scalar(select(User).where(User.number == number))


def create_user(engine, number: str, name: str, role: str, password: str) -> User:
    with Session(engine) as session:
        user = User(number=number, name=name, role=role, password_hash=hash_password(password))
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def issue_token(engine, user: User) -> str:
    token = secrets.token_urlsafe(48)
    with Session(engine) as session:
        session.add(SessionToken(token=token, user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(hours=12)))
        session.commit()
    return token


def user_for_token(engine, token: str) -> User | None:
    with Session(engine) as session:
        session_token = session.get(SessionToken, token)
        if session_token is None or session_token.expires_at <= datetime.now(timezone.utc):
            return None
        return session.get(User, session_token.user_id)


def revoke_token(engine, token: str) -> None:
    with Session(engine) as session:
        session_token = session.get(SessionToken, token)
        if session_token:
            session.delete(session_token)
            session.commit()


def list_records(engine, record_type: str) -> list[dict[str, Any]]:
    with Session(engine) as session:
        records = session.scalars(select(Record).where(Record.record_type == record_type).order_by(Record.updated_at))
        return [record.payload for record in records]


def get_record(engine, record_id: str) -> Record | None:
    with Session(engine) as session:
        return session.get(Record, record_id)


def save_record(engine, record_id: str, record_type: str, payload: dict[str, Any]) -> None:
    with Session(engine) as session:
        record = session.get(Record, record_id)
        if record is None:
            session.add(Record(id=record_id, record_type=record_type, payload=payload))
        else:
            record.payload = payload
            record.record_type = record_type
        session.commit()
