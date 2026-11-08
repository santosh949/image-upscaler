import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_frontend_dist_served(requires_frontend):
    res = client.get("/")
    assert res.status_code == 200
    assert "<div id=\"root\">" in res.text or "html" in res.text.lower()

def test_frontend_assets_served(requires_frontend):
    res = client.get("/")
    assert res.status_code == 200
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dist = os.path.join(root, "frontend", "dist")
    assert os.path.isdir(frontend_dist)
    assert os.path.isfile(os.path.join(frontend_dist, "index.html"))

