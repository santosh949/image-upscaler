import os
import time
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def completed_job_id():
    fixture_path = os.path.abspath(r"tests\fixtures\test_input.png")
    with open(fixture_path, "rb") as f:
        up_res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    assert up_res.status_code == 200
    img_id = up_res.json()["image_id"]

    job_res = client.post("/api/v1/jobs", json={
        "image_id": img_id,
        "mode": "upscale",
        "scale": 4,
        "model": "realesrgan-x4plus",
        "output_format": "png"
    })
    assert job_res.status_code == 200
    job_id = job_res.json()["job_id"]

    # Wait for completion
    for _ in range(30):
        status_res = client.get(f"/api/v1/jobs/{job_id}")
        if status_res.json()["status"] == "completed":
            break
        time.sleep(1.0)

    assert client.get(f"/api/v1/jobs/{job_id}").json()["status"] == "completed"
    return job_id

def test_100_percent_crop_endpoint(completed_job_id):
    res = client.get(f"/api/v1/jobs/{completed_job_id}/crop?x=10&y=10&width=128&height=128")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    with Image.open(io.BytesIO(res.content)) as crop_img:
        assert crop_img.size == (128, 128)

def test_crop_preview_job_execution():
    fixture_path = os.path.abspath(r"tests\fixtures\test_input.png")
    with open(fixture_path, "rb") as f:
        up_res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    img_id = up_res.json()["image_id"]

    # Submit job for a 100x100 region only
    job_res = client.post("/api/v1/jobs", json={
        "image_id": img_id,
        "mode": "upscale",
        "scale": 4,
        "model": "realesrgan-x4plus",
        "output_format": "png",
        "crop_region": [0, 0, 100, 100]
    })
    assert job_res.status_code == 200
    crop_job_id = job_res.json()["job_id"]

    for _ in range(30):
        status = client.get(f"/api/v1/jobs/{crop_job_id}").json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(1.0)

    assert status == "completed"

    dl_res = client.get(f"/api/v1/jobs/{crop_job_id}/download")
    assert dl_res.status_code == 200
    with Image.open(io.BytesIO(dl_res.content)) as out_img:
        assert out_img.size == (400, 400)

def test_export_format_conversions(completed_job_id):
    # Test JPEG download conversion
    res_jpeg = client.get(f"/api/v1/jobs/{completed_job_id}/download?format=jpeg&quality=80")
    assert res_jpeg.status_code == 200
    assert res_jpeg.headers["content-type"] == "image/jpeg"
    with Image.open(io.BytesIO(res_jpeg.content)) as img:
        assert img.format == "JPEG"

    # Test WebP download conversion
    res_webp = client.get(f"/api/v1/jobs/{completed_job_id}/download?format=webp&quality=85")
    assert res_webp.status_code == 200
    assert res_webp.headers["content-type"] == "image/webp"
    with Image.open(io.BytesIO(res_webp.content)) as img:
        assert img.format == "WEBP"

def test_jobs_history_and_deletion(completed_job_id):
    # List jobs
    res = client.get("/api/v1/jobs?limit=10")
    assert res.status_code == 200
    jobs = res.json()
    assert len(jobs) >= 1
    assert any(j["job_id"] == completed_job_id for j in jobs)

    # Delete test job
    del_res = client.delete(f"/api/v1/jobs/{completed_job_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # Confirm 404 after deletion
    check_res = client.get(f"/api/v1/jobs/{completed_job_id}")
    assert check_res.status_code == 404

