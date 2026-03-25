import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app

# import models so metadata includes tables
from app.models.headline import Headline  # noqa: F401
from app.models.token_usage import TokenUsage  # noqa: F401


@pytest.fixture(scope="session")
def db_engine():
    # Create a temporary file for the SQLite database
    db_fd, db_path = tempfile.mkstemp(prefix="test_", suffix=".db")
    os.close(db_fd)  # Close the file descriptor
    test_db_url = f"sqlite:///{db_path}"

    db_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=db_engine)
    yield db_engine
    Base.metadata.drop_all(bind=db_engine)
    os.remove(db_path)


@pytest.fixture()
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    session = TestingSessionLocal()

    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
