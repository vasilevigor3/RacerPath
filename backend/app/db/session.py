from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
