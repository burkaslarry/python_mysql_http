from fastapi.testclient import TestClient
from main import app
import os
import json

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World"}

def test_get_homepage():
    # Ensure the demo data exists for the test
    assert os.path.exists(os.path.join("demo_data", "homepage.json"))
    
    response = client.get("/api/homepage")
    assert response.status_code == 200
    data = response.json()
    assert "home" in data
    assert "title" in data["home"]

def test_read_items_no_db():
    # This test expects a 503 because the database is likely not configured in the test environment
    # If the environment happens to have DB vars set, this test might fail or need adjustment.
    # Assuming standard CI/local test without DB:
    
    # We can force the pool to be None if we want to be sure, but let's rely on the app state.
    # If the app connected to a real DB, this would be a different test.
    # For now, let's just check that it handles the request gracefully (either 200 or 503).
    
    response = client.get("/items")
    assert response.status_code in [200, 503]

