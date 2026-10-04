import os
import pytest
from fastapi.testclient import TestClient

# Ensure test uses SQLite in-memory and mock LLM
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["USE_MOCK_LLM"] = "true"

from app.database import Base, engine, SessionLocal, init_db
from app.policies.engine import policy_engine
from app.main import create_app

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function", autouse=True)
def reset_policy_engine():
    policy_engine.load_policies()
    yield
    policy_engine.load_policies()

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def db(db_session):
    return db_session

@pytest.fixture(scope="function")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
