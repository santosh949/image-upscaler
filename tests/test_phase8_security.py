import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

def test_path_traversal_on_download():
    # Attempt path traversal via job_id
    resp = client.get("/api/v1/jobs/../../Windows/System32/drivers/etc/hosts/download")
    assert resp.status_code in (400, 404)

    # Attempt path traversal on job preview
    resp2 = client.get("/api/v1/jobs/..%2F..%2Fetc%2Fpasswd/preview")
    assert resp2.status_code in (400, 404)

def test_path_traversal_on_crop():
    # Attempt path traversal on crop endpoint
    resp = client.get("/api/v1/jobs/..\\..\\boot.ini/crop?x=0&y=0&width=64&height=64")
    assert resp.status_code in (400, 404)

def test_decompression_bomb_rejection():
    # Construct an image that declares excessive dimensions or malformed header
    resp = client.post(
        "/api/v1/images",
        files={"file": ("bomb.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x7f\x00\x00\x00\x7f\x00\x08\x02\x00\x00\x00", "image/png")}
    )
    assert resp.status_code == 400
    assert "Invalid image" in resp.json()["detail"]

def test_non_image_upload_rejected():
    # Upload binary executable or shell script
    fake_exe = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00")
    resp = client.post(
        "/api/v1/images",
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")}
    )
    assert resp.status_code == 400
    assert "Invalid image" in resp.json()["detail"]

def test_no_local_filesystem_paths_in_api_responses():
    # Upload legitimate image
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(20, 40, 60)).save(buf, format="PNG")
    buf.seek(0)

    upload_resp = client.post(
        "/api/v1/images",
        files={"file": ("safe.png", buf, "image/png")}
    )
    assert upload_resp.status_code == 200
    img_data = upload_resp.json()

    # Verify no raw disk path leaked
    assert "path" not in img_data
    assert "storage_path" not in img_data
    assert "C:\\" not in str(img_data)
    assert "/Users/" not in str(img_data)

def test_oversized_upload_rejected():
    # Attempt upload exceeding 50 MB
    huge_data = io.BytesIO(b"0" * (51 * 1024 * 1024))
    resp = client.post(
        "/api/v1/images",
        files={"file": ("huge.png", huge_data, "image/png")}
    )
    assert resp.status_code == 413
    assert "exceeds maximum allowed size" in resp.json()["detail"]
