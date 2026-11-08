import os
import time
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from ai_engine.analysis.analyzer import analyzer
from ai_engine.routing.router import router
from ai_engine.registry.model_registry import model_registry

client = TestClient(app)

def test_model_registry_integrity():
    models = model_registry.list_models()
    assert len(models) >= 2, "Expected at least 2 models in registry"
    
    model_ids = [m["id"] for m in models]
    assert "realesrgan-x4plus" in model_ids
    assert "realesrgan-x4plus-anime" in model_ids

    available_models = model_registry.list_models(only_available=True)
    for m in available_models:
        assert m["weights_available"] is True, f"Weights missing for {m['id']}"
        assert m["smoke_tested"] is True, f"Model {m['id']} not smoke tested"
        assert m["code_license"] == "BSD-3-Clause"
        assert "weight_license" in m

def test_analyzer_real_signals():
    fixture_path = os.path.abspath(r"tests\fixtures\test_input.png")
    assert os.path.isfile(fixture_path)

    res = analyzer.analyze(fixture_path)
    assert res["width"] == 256
    assert res["height"] == 256
    assert res["format"] == "PNG"
    assert isinstance(res["estimated_blur_score"], float)
    assert isinstance(res["estimated_noise_sigma"], float)
    assert 1 <= res["jpeg_quality_estimate"] <= 100
    assert res["detected_category"] in ("photo", "anime")
    assert 0.0 <= res["category_confidence"] <= 1.0

def test_router_decision_rules():
    # 1. Synthetic anime profile
    anime_analysis = {
        "detected_category": "anime",
        "category_confidence": 0.85,
        "is_blurry": False,
        "estimated_noise_sigma": 1.2
    }
    anime_route = router.route(anime_analysis)
    assert anime_route["selected_model"] == "realesrgan-x4plus-anime"
    assert "anime" in anime_route["reasoning"].lower()

    # 2. Synthetic photo profile
    photo_analysis = {
        "detected_category": "photo",
        "category_confidence": 0.90,
        "is_blurry": True,
        "estimated_noise_sigma": 5.0
    }
    photo_route = router.route(photo_analysis)
    assert photo_route["selected_model"] == "realesrgan-x4plus"
    assert "photo" in photo_route["reasoning"].lower()

    # 3. Manual override
    override = router.route(photo_analysis, requested_model="realesrgan-x4plus-anime")
    assert override["selected_model"] == "realesrgan-x4plus-anime"
    assert "manual override" in override["reasoning"].lower()

def test_api_analyze_and_anime_inference():
    fixture_path = os.path.abspath(r"tests\fixtures\test_input.png")
    with open(fixture_path, "rb") as f:
        up_res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    assert up_res.status_code == 200
    img_id = up_res.json()["image_id"]

    # 1. Analyze endpoint
    ana_res = client.post(f"/api/v1/images/{img_id}/analyze")
    assert ana_res.status_code == 200
    ana_data = ana_res.json()
    assert "analysis" in ana_data
    assert "recommendation" in ana_data
    assert ana_data["recommendation"]["selected_model"] in ("realesrgan-x4plus", "realesrgan-x4plus-anime")

    # 2. Run real anime inference job
    job_res = client.post("/api/v1/jobs", json={
        "image_id": img_id,
        "mode": "upscale",
        "scale": 4,
        "model": "realesrgan-x4plus-anime"
    })
    assert job_res.status_code == 200
    job_id = job_res.json()["job_id"]

    for _ in range(30):
        status = client.get(f"/api/v1/jobs/{job_id}").json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(1.0)

    assert status == "completed", "Anime model inference failed to complete"

