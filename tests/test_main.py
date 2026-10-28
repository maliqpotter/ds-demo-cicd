"""Tests for the notes app."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Provide a fresh in-memory database session per test."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create and tear down the in-memory database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app, follow_redirects=False)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_read_notes() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "My Notes" in response.text


def test_add_note() -> None:
    response = client.post(
        "/add",
        data={"title": "Test Note", "content": "Test Content"},
    )
    assert response.status_code == 303

    response = client.get("/")
    assert response.status_code == 200
    assert "Test Note" in response.text


def test_delete_note() -> None:
    client.post(
        "/add",
        data={"title": "Note to Delete", "content": "Delete me"},
    )

    response = client.get("/")
    assert "Note to Delete" in response.text

    response = client.post("/delete/1")
    assert response.status_code == 303

    response = client.get("/")
    assert "Note to Delete" not in response.text


def test_add_note_validation() -> None:
    response = client.post("/add", data={"title": "", "content": ""})
    assert response.status_code == 422


def test_delete_nonexistent_note() -> None:
    response = client.post("/delete/999")
    assert response.status_code == 303
