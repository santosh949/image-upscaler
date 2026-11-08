import os
import time
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_capabilities_endpoint():
    res = client.get("/api/v1/system/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["gpu"] == "NVIDIA GeForce RTX 2050"
    assert data["vulkan_device_index"] == 0

def test_models_registry_endpoint():
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert len(data["models"]) >= 1
    m = data["models"][0]
    assert m["id"] in ("realesrgan-x4plus", "realesrgan-x4plus-ncnn")
    assert m["scale"] == 4
    assert m["available"] is True
    assert m["code_license"] == "BSD-3-Clause"

def test_upload_inference_download_lifecycle():
    fixture_path = os.path.abspath(r"tests\fixtures\test_input.png")
    assert os.path.isfile(fixture_path), "Input fixture missing"

    with Image.open(fixture_path) as orig_img:
        orig_w, orig_h = orig_img.size
        orig_bytes = os.path.getsize(fixture_path)

    # 1. Upload image
    with open(fixture_path, "rb") as f:
        res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    assert res.status_code == 200
    up_data = res.json()
    image_id = up_data["image_id"]
    assert up_data["width"] == orig_w
    assert up_data["height"] == orig_h

    # 2. Create Job
    job_req = {
        "image_id": image_id,
        "mode": "upscale",
        "scale": 4,
        "model": "realesrgan-x4plus",
        "tile_size": 0
    }
    res = client.post("/api/v1/jobs", json=job_req)
    assert res.status_code == 200
    job_data = res.json()
    job_id = job_data["job_id"]
    assert job_data["status"] == "queued"

    # 3. Wait for worker execution (poll status)
    max_wait = 30
    start = time.time()
    final_status = None
    while time.time() - start < max_wait:
        res = client.get(f"/api/v1/jobs/{job_id}")
        assert res.status_code == 200
        status_data = res.json()
        final_status = status_data["status"]
        if final_status in ("completed", "failed", "cancelled"):
            break
        time.sleep(1.0)

    assert final_status == "completed", f"Job failed to complete. Data: {status_data}"

    # 4. Download Result
    res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"

    # Verify downloaded image dimensions
    test_download_tmp = os.path.join(settings.STORAGE_ROOT, "temp", f"verify_{job_id}.png")
    with open(test_download_tmp, "wb") as f:
        f.write(res.content)

    with Image.open(test_download_tmp) as out_img:
        assert out_img.size == (orig_w * 4, orig_h * 4)

    # Clean test temp file
    if os.path.exists(test_download_tmp):
        os.remove(test_download_tmp)

    # 5. Verify Original Image was untouched
    assert os.path.getsize(fixture_path) == orig_bytes

def test_invalid_upload_returns_structured_error():
    # Send non-image file
    res = client.post("/api/v1/images", files={"file": ("corrupt.png", b"NOT_AN_IMAGE_DATA", "image/png")})
    assert res.status_code == 400
    data = res.json()
    assert "detail" in data
    assert "Invalid image file" in data["detail"]

def test_job_cancel_flow():
    fixture_path = os.path.abspath(r"tests\fixtures\test_input.png")
    with open(fixture_path, "rb") as f:
        res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    img_id = res.json()["image_id"]

    res = client.post("/api/v1/jobs", json={"image_id": img_id, "scale": 4})
    job_id = res.json()["job_id"]

    # Cancel immediately
    res = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert res.status_code == 200
    cancel_data = res.json()
    assert cancel_data["job_id"] == job_id

