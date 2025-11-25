from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_home():
    """Test the root endpoint returns a 200 and correct message"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_health_check():
    """Simple health check"""
    response = client.get("/helth")
    assert response.status_code == 200
    assert response.json() == {"status" : "ok"}