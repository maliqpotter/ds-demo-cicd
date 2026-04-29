from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_notes():
    response = client.get("/")
    assert response.status_code == 200
    assert "My Notes" in response.text

def test_add_note():
    response = client.post("/add", data={"title": "Test Note", "content": "Test Content"})
    assert response.status_code == 303 # Redirect
    
    response = client.get("/")
    assert "Test Note" in response.text
