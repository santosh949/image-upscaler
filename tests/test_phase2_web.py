import os
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_frontend_dist_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "AETHER UPSCALE" in res.text or "<div id=\"root\">" in res.text

def test_frontend_assets_served():
    res = client.get("/")
    assert res.status_code == 200
    # Assets directory accessible
    frontend_dist = os.path.abspath(r"frontend\dist")
    assert os.path.isdir(frontend_dist)
    assert os.path.isfile(os.path.join(frontend_dist, "index.html"))

