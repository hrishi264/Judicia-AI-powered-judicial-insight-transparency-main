
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLITE_DATABASE_URL = "sqlite:///./judicial_ai.db"

engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Modern SQLAlchemy declarative base class."""
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
