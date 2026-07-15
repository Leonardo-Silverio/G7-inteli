from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    return create_engine(settings.DATABASE_URL, pool_pre_ping=True)


@lru_cache
def get_sessionmaker():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db():
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
