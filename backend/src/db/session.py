from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import structlog

from src.config import settings

log = structlog.get_logger()

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={settings.SQL_CONNECTION_STRING}",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=settings.ENVIRONMENT == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
