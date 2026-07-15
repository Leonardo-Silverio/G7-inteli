import pytest
from sqlalchemy import text

from app.database.database import get_engine, get_sessionmaker
from app.database.database import Base


@pytest.fixture(scope="session")
def engine():
    return get_engine()


@pytest.fixture(scope="session")
def session_factory(engine):
    return get_sessionmaker()


@pytest.fixture
def db(session_factory):
    """Create a new database session for each test with transaction rollback."""
    session = session_factory()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def clean_db(db):
    """Clean all tables before each test. Use this fixture explicitly in tests that need it."""
    from sqlalchemy.engine import Engine
    from sqlalchemy import inspect
    
    # Check if we're using PostgreSQL (not SQLite)
    inspector = inspect(db.bind)
    if inspector.engine.dialect.name != 'postgresql':
        yield
        return
        
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
    db.commit()
    yield
    db.rollback()