import os
import stat
import shutil
import uuid
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.database import init_db, get_version
from backend.app.services.version_service import version_service
from ai_engine.registry.model_registry import model_registry

client = TestClient(app)

def make_writable(path: str):
    if os.path.exists(path):
        os.chmod(path, stat.S_IWRITE)

def force_remove_tree(dirpath: str):
    if os.path.exists(dirpath):
        for root, dirs, files in os.walk(dirpath):
            for fname in files:
                fpath = os.path.join(root, fname)
                make_writable(fpath)
            for dname in dirs:
                make_writable(os.path.join(root, dname))
        shutil.rmtree(dirpath, ignore_errors=True)

@pytest.fixture(scope="module", autouse=True)
def setup_test_env():
    init_db()
    test_dir = os.path.join(settings.STORAGE_PATH, "test_phase3_ui")
    force_remove_tree(test_dir)
    os.makedirs(test_dir, exist_ok=True)
    yield
    force_remove_tree(test_dir)

def test_frontend_dist_and_index_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "AETHER UPSCALE" in resp.text

def test_resolution_studio_aspect_ratio_safety():
    """Aspect ratio distortion must be rejected per Part A3.11."""
    run_id = uuid.uuid4().hex[:8]
    img_path = os.path.join(settings.STORAGE_PATH, "test_phase3_ui", f"aspect_{run_id}.png")
    make_writable(img_path)
    Image.new("RGB", (1920, 1080), color=(100, 100, 100)).save(img_path)

    v_orig = version_service.create_project_from_image(
        image_id=f"img_aspect_{run_id}",
        filename=f"aspect_{run_id}.png",
        image_path=img_path,
        w=1920,
        h=1080,
        fmt="PNG"
    )

    # 16:9 source (1920x1080 = 1.777) planned to 1:1 square (3000x3000 = 1.0) -> must fail!
    resp = client.post(f"/api/v1/projects/{v_orig['project_id']}/plan", json={
        "target_width": 3000,
        "target_height": 3000,
        "source_version_id": v_orig["root_version_id"]
    })
    assert resp.status_code == 400
    assert "aspect ratio" in resp.json()["detail"].lower()

def test_task_categories_mapping_validity():
    """Verify all task category models exist in registry and are available."""
    models = {m["id"]: m for m in model_registry.list_models()}

    categories = [
        {"id": "photo", "model": "realesrgan-x4plus"},
        {"id": "restore", "model": "realesrgan-x4plus"},
        {"id": "anime", "model": "realesrgan-x4plus-anime"},
        {"id": "lineart", "model": "realesr-animevideov3-x4"},
        {"id": "transparent", "model": "realesrgan-x4plus"}
    ]

    for cat in categories:
        m_id = cat["model"]
        assert m_id in models, f"Model {m_id} for task {cat['id']} not in registry"
        assert models[m_id]["weights_available"] is True, f"Model {m_id} weights not available"
        assert models[m_id]["license_class"] in ("permissive", "non-commercial / unclear")

def test_version_decision_accept_reject_flow():
    run_id = uuid.uuid4().hex[:8]
    img_path = os.path.join(settings.STORAGE_PATH, "test_phase3_ui", f"dec_{run_id}.png")
    make_writable(img_path)
    Image.new("RGB", (512, 512), color=(50, 150, 50)).save(img_path)

    v_orig = version_service.create_project_from_image(
        image_id=f"img_dec_{run_id}",
        filename=f"dec_{run_id}.png",
        image_path=img_path,
        w=512,
        h=512,
        fmt="PNG"
    )
    vid = v_orig["root_version_id"]

    # Reject
    resp = client.post(f"/api/v1/versions/{vid}/decision", json={"decision": "rejected"})
    assert resp.status_code == 200
    assert get_version(vid)["decision"] == "rejected"

    # Accept
    resp = client.post(f"/api/v1/versions/{vid}/decision", json={"decision": "accepted"})
    assert resp.status_code == 200
    assert get_version(vid)["decision"] == "accepted"
