import os
import io
import time
import zipfile
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import get_job, update_job_status
from backend.app.services.job_manager import job_manager

client = TestClient(app)

@pytest.fixture
def sample_images(tmp_path):
    files = []
    for i in range(3):
        p = tmp_path / f"img_{i}.png"
        img = Image.new("RGB", (32, 32), (i * 50, 100, 150))
        img.save(str(p))
        files.append(str(p))
    return files

def test_batch_upload_images(sample_images):
    upload_files = []
    for p in sample_images:
        upload_files.append(("files", (os.path.basename(p), open(p, "rb"), "image/png")))

    res = client.post("/api/v1/images/batch", files=upload_files)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    assert all("image_id" in item for item in data)
    assert all(item["width"] == 32 and item["height"] == 32 for item in data)

def test_batch_jobs_creation_and_queue(sample_images):
    # Upload first
    upload_files = [("files", (os.path.basename(p), open(p, "rb"), "image/png")) for p in sample_images]
    u_res = client.post("/api/v1/images/batch", files=upload_files).json()
    image_ids = [item["image_id"] for item in u_res]

    batch_payload = {
        "jobs": [
            {
                "image_id": img_id,
                "mode": "upscale",
                "scale": 2,
                "model": "realesrgan-x4plus",
                "preset": "faithful",
                "output_format": "png",
                "quality": 90
            }
            for img_id in image_ids
        ]
    }

    res = client.post("/api/v1/jobs/batch", json=batch_payload)
    assert res.status_code == 200
    created_jobs = res.json()
    assert len(created_jobs) == 3
    assert all(j["status"] == "queued" for j in created_jobs)

    # Queue status
    q_res = client.get("/api/v1/jobs/queue")
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert "total_queued" in q_data

def test_batch_zip_download(tmp_path):
    import uuid
    job_ids = []
    for i in range(2):
        fake_id = f"test_zip_job_{uuid.uuid4().hex[:8]}"
        out_file = tmp_path / f"{fake_id}_out.png"
        img = Image.new("RGB", (64, 64), (100, 200, 50))
        img.save(str(out_file))

        from backend.app.database import create_job
        create_job(
            job_id=fake_id,
            image_id="fake_img",
            input_path=str(out_file),
            mode="upscale",
            scale=2,
            model="realesrgan-x4plus"
        )
        update_job_status(
            fake_id,
            status="completed",
            stage="done",
            progress=1.0,
            output_path=str(out_file)
        )
        job_ids.append(fake_id)

    zip_res = client.post("/api/v1/jobs/batch/download-zip", json={"job_ids": job_ids})
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Verify ZIP structure
    zf = zipfile.ZipFile(io.BytesIO(zip_res.content))
    namelist = zf.namelist()
    assert len(namelist) >= 2
    assert any(job_ids[0] in name for name in namelist)

def test_clear_queue():
    from backend.app.database import create_job
    fake_id = f"test_clear_job_{int(time.time())}"
    create_job(
        job_id=fake_id,
        image_id="fake_img",
        input_path="fake_path",
        mode="upscale",
        scale=2,
        model="realesrgan-x4plus"
    )

    res = client.post("/api/v1/jobs/queue/clear")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["cancelled_count"] >= 1

    job = get_job(fake_id)
    assert job["status"] == "cancelled"

