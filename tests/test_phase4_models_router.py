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
    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "test_input.png"))
    assert os.path.isfile(fixture_path)

    res = analyzer.analyze(fixture_path)
    assert res["width"] == 256
    assert res["height"] == 256
    assert res["format"] == "PNG"
    assert isinstance(res["estimated_blur_score"], float)
    assert isinstance(res["estimated_noise_sigma"], float)
    assert 1 <= res["jpeg_quality_estimate"] <= 100
    assert res["detected_category"] in ("photo", "anime", "manga", "document")
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

def test_api_analyze_and_anime_inference(requires_ncnn):
    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "test_input.png"))
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

def test_document_vs_manga_discrimination(tmp_path):
    import numpy as np
    from PIL import Image

    # 1. Synthetic scanned text document (pure white page with black text lines, 0 midtones)
    doc_arr = np.full((300, 300, 3), 255, dtype=np.uint8)
    for y in range(30, 270, 20):
        doc_arr[y:y+3, 30:270] = 10  # text line
    doc_path = str(tmp_path / "scanned_doc.png")
    Image.fromarray(doc_arr).save(doc_path)

    doc_analysis = analyzer.analyze(doc_path)
    assert doc_analysis["detected_category"] == "document", f"Expected document, got {doc_analysis['detected_category']}"
    doc_route = router.route(doc_analysis)
    assert doc_route["preset"] == "faithful"

    # 2. Synthetic manga panel (ink strokes + screentone midtones)
    manga_arr = np.full((300, 300, 3), 245, dtype=np.uint8)
    # Halftone screentone region (30% area with alternating dots)
    manga_arr[50:200, 50:200:2] = 130
    manga_arr[50:200, 51:200:2] = 230
    # Black line borders and character ink
    manga_arr[40:55, 40:260] = 15
    manga_arr[40:260, 40:55] = 15
    manga_arr[100:200, 100:110] = 15
    manga_path = str(tmp_path / "manga_panel.png")
    Image.fromarray(manga_arr).save(manga_path)

    manga_analysis = analyzer.analyze(manga_path)
    assert manga_analysis["detected_category"] == "manga", f"Expected manga, got {manga_analysis['detected_category']}"
    manga_route = router.route(manga_analysis)
    assert manga_route["preset"] == "manga_crisp"
    assert manga_route["selected_model"] == "realesrgan-x4plus-anime"

def test_degradation_overrides_wiring(tmp_path):
    from ai_engine.pipelines.pipeline import pipeline
    test_img = Image.new("RGB", (64, 64), (120, 130, 140))
    in_path = str(tmp_path / "wiring_in.png")
    out_path = str(tmp_path / "wiring_out.png")
    test_img.save(in_path)

    # Run with degradation overrides enabled
    res = pipeline.run(
        input_path=in_path,
        output_path=out_path,
        mode="restore",
        scale=1,
        overrides={"pre_denoise": "medium", "post_sharpen": "low"}
    )
    assert any("classical-restoration" in s for s in res["stages_executed"])

def test_job_worker_recommended_parameters_execution(requires_ncnn, tmp_path):
    """Verifies standard job with recommended_parameters routes to pipeline.run and completes."""
    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "test_input.png"))
    with open(fixture_path, "rb") as f:
        up_res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    assert up_res.status_code == 200
    img_id = up_res.json()["image_id"]

    # Submit job with recommended_parameters and NO plan_json
    job_res = client.post("/api/v1/jobs", json={
        "image_id": img_id,
        "mode": "upscale",
        "scale": 4,
        "model": "realesrgan-x4plus-anime",
        "recommended_parameters": {
            "pre_denoise": "medium",
            "deblock_jpeg": True,
            "denoise_strength": 6.0,
            "post_sharpen": "low"
        }
    })
    assert job_res.status_code == 200
    job_id = job_res.json()["job_id"]

    # Wait for completion
    for _ in range(40):
        status_res = client.get(f"/api/v1/jobs/{job_id}").json()
        if status_res["status"] in ("completed", "failed"):
            break
        time.sleep(1.0)

    assert status_res["status"] == "completed", f"Job failed unexpectedly: {status_res.get('error')}"

def test_progressive_pipeline_recommended_parameters(tmp_path):
    """Verifies multi-stage progressive pipeline consumes pre-denoise and post-sharpen."""
    from ai_engine.pipelines.progressive_pipeline import progressive_pipeline
    test_img = Image.new("RGB", (64, 64), (100, 150, 200))
    in_path = str(tmp_path / "prog_in.png")
    out_path = str(tmp_path / "prog_out.png")
    test_img.save(in_path)

    plan = {
        "plan_type": "plan_a",
        "target_width": 128,
        "target_height": 128,
        "pre_denoise": "medium",
        "denoise_strength": 5.0,
        "deblock_jpeg": True,
        "post_sharpen": "low",
        "sharpen_amount": 0.35,
        "stages": [
            {
                "stage_index": 1,
                "operation": "classical_resample",
                "model_name": "lanczos",
                "from_res": [64, 64],
                "to_res": [128, 128],
                "target_scale": 2.0
            }
        ]
    }

    res = progressive_pipeline.run(
        input_path=in_path,
        output_path=out_path,
        plan=plan,
        job_id="test_prog_degrad",
        format_name="PNG"
    )

    assert res["status"] == "completed"
    assert "classical-restoration-prepass" in res["stages_executed"]
    assert "conservative-post-polish" in res["stages_executed"]


