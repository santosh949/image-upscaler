import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from ai_engine.registry.model_registry import model_registry

client = TestClient(app)

def test_model_registry_tier3_isolation(requires_weights):
    models = model_registry.list_models()
    model_ids = {m["id"] for m in models}

    # Core Tier 1 models must be available
    assert "realesrgan-x4plus" in model_ids
    assert "realesrgan-x4plus-anime" in model_ids
    assert model_registry.get_model("realesrgan-x4plus")["weights_available"] is True
    assert model_registry.get_model("realesrgan-x4plus-anime")["weights_available"] is True

    # Tier 3 Generative models must be cataloged as unavailable on 4GB Profile A
    assert "diffbir" in model_ids
    assert "supir" in model_ids
    diffbir = model_registry.get_model("diffbir")
    assert diffbir["tier"] == 3
    assert diffbir["weights_available"] is False
    assert "unsupported_reason" in diffbir
    assert "4GB" in diffbir["unsupported_reason"]

def test_models_api_surfaces_unsupported_reasons():
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    data = resp.json()["models"]

    diffbir = next(m for m in data if m["id"] == "diffbir")
    assert diffbir["available"] is False
    assert diffbir["unsupported_reason"] is not None
    assert "Profile A" in diffbir["unsupported_reason"]

    supir = next(m for m in data if m["id"] == "supir")
    assert supir["available"] is False
    assert supir["unsupported_reason"] is not None

