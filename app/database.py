from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from app.config import settings


class Base(DeclarativeBase):
    """Shared declarative base — all ORM models inherit from this."""
    pass


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    import app.models.esg  # noqa: F401
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    import app.models.esg  # noqa: F401
    Base.metadata.drop_all(bind=engine)
