import os
import stat
import shutil
import hashlib
import uuid
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.database import init_db, get_db_connection, get_version, get_child_versions
from backend.app.services.version_service import version_service
from backend.app.services.resolution_planner import resolution_planner
from backend.app.services.resource_estimator import resource_estimator
from ai_engine.processing.tile_engine import TileEngine, JobPausedException
from ai_engine.processing.tile_store import TileStore
from ai_engine.pipelines.progressive_pipeline import ProgressivePipeline

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
    test_dir = os.path.join(settings.STORAGE_PATH, "test_phase2_progressive")
    force_remove_tree(test_dir)
    os.makedirs(test_dir, exist_ok=True)
    yield
    force_remove_tree(test_dir)

def test_resource_estimator():
    # 4K -> 8K UHD estimation
    est = resource_estimator.estimate(
        source_w=3840, source_h=2160,
        target_w=7680, target_h=4320,
        tile_size=256
    )
    assert est["output_megapixels"] == 33.18
    assert est["peak_vram_mb"] > 0
    assert est["peak_ram_mb"] > 0
    assert est["required_disk_mb"] > 0
    assert est["peak_ram_mb"] < 6000  # Must fit in 8GB system RAM
    assert est["estimated_runtime_seconds"] > 0
    assert est["exceeds_output_cap"] is False

    # Over 100 MP rejection
    est_over = resource_estimator.estimate(
        source_w=8000, source_h=8000,
        target_w=16000, target_h=16000,
        tile_size=256
    )
    assert est_over["exceeds_output_cap"] is True
    assert len(est_over["warnings"]) > 0

def test_planner_plan_a_vs_plan_b():
    # Setup test project with original 1080p and derived 4K version
    run_id = uuid.uuid4().hex[:8]
    img_id = f"img_planner_{run_id}"
    proj_id = f"proj_{img_id}"

    # Create synthetic original 1080p image
    orig_path = os.path.join(settings.STORAGE_PATH, "test_phase2_progressive", f"orig_1080p_{run_id}.png")
    make_writable(orig_path)
    Image.new("RGB", (1920, 1080), color=(100, 120, 150)).save(orig_path)

    v_orig = version_service.create_project_from_image(
        image_id=img_id,
        filename=f"orig_1080p_{run_id}.png",
        image_path=orig_path,
        w=1920,
        h=1080,
        fmt="PNG"
    )
    orig_ver_id = v_orig["root_version_id"]

    # Register derived 4K version
    v_4k_path = os.path.join(settings.STORAGE_PATH, "test_phase2_progressive", f"derived_4k_{run_id}.png")
    make_writable(v_4k_path)
    Image.new("RGB", (3840, 2160), color=(110, 130, 160)).save(v_4k_path)

    v_4k = version_service.register_derived_version(
        project_id=proj_id,
        parent_version_id=orig_ver_id,
        output_image_path=v_4k_path,
        operation="upscale",
        mode="upscale",
        model_id="realesrgan-x4plus",
        scale=2,
        runtime_s=12.5
    )

    # Test Plan A: 1080p to 8K requests from original -> Plan A direct 4x upscale
    plan_from_orig = resolution_planner.generate_plan(
        project_id=proj_id,
        source_version_id=orig_ver_id,
        target_width=7680,
        target_height=4320
    )
    assert plan_from_orig["plan_type"] == "plan_a"
    assert len(plan_from_orig["stages"]) == 1
    assert plan_from_orig["stages"][0]["from_res"] == [1920, 1080]
    assert plan_from_orig["stages"][0]["to_res"] == [7680, 4320]

    # Test Plan B: 4K to 8K requests continuation from 4K -> Plan B per-tile adaptation
    plan_from_4k = resolution_planner.generate_plan(
        project_id=proj_id,
        source_version_id=v_4k["id"],
        target_width=7680,
        target_height=4320
    )
    assert plan_from_4k["plan_type"] == "plan_b"
    assert len(plan_from_4k["stages"]) == 1
    assert plan_from_4k["stages"][0]["from_res"] == [3840, 2160]
    assert plan_from_4k["stages"][0]["to_res"] == [7680, 4320]
    assert plan_from_4k["stages"][0]["target_scale"] == 2.0
    # Warning for same model chained
    assert len(plan_from_4k["warnings"]) > 0

def test_tile_store_checkpoint_and_resume():
    store = TileStore(base_dir=os.path.join(settings.STORAGE_PATH, "test_phase2_progressive", "tiles"))
    stage_id = "test_stage_chk_01"
    grid = [{"gx": 0, "gy": 0}, {"gx": 1, "gy": 0}, {"gx": 0, "gy": 1}, {"gx": 1, "gy": 1}]

    store.init_stage(
        stage_id=stage_id,
        job_id="job_chk_01",
        stage_index=1,
        operation="upscale",
        model="realesrgan-x4plus",
        from_size=(512, 512),
        to_size=(1024, 1024),
        tile_grid=grid
    )

    # Save 2 tiles
    t1 = Image.new("RGB", (256, 256), color=(200, 50, 50))
    t2 = Image.new("RGB", (256, 256), color=(50, 200, 50))
    p1 = store.save_tile(stage_id, 0, 0, t1)
    p2 = store.save_tile(stage_id, 1, 0, t2)

    # Check completed tiles
    completed = store.get_completed_tiles(stage_id)
    assert (0, 0) in completed
    assert (1, 0) in completed
    assert (0, 1) not in completed

    # Corrupt one tile and verify it resets
    make_writable(p1)
    with open(p1, "wb") as f:
        f.write(b"corrupted_tile_data")
    completed_after_corrupt = store.get_completed_tiles(stage_id)
    assert (0, 0) not in completed_after_corrupt
    assert (1, 0) in completed_after_corrupt

    store.cleanup_stage(stage_id)

def test_flagship_4k_to_8k_per_tile_scale_adaptation():
    """
    FLAGSHIP V2 TEST (FINAL_SPEC Part F4 & ADR 005):
    Take an existing processed 4K version (3840x2160), continue to 8K UHD (7680x4320)
    internally with NO browser round-trip without materializing a 16K intermediate in physical RAM.
    Verify:
    1. Output is exactly 7680x4320.
    2. Parent 4K version file SHA-256 is unchanged (immutability preserved).
    3. Derived version is registered under parent 4K version.
    """
    engine = TileEngine(default_tile_size=512, overlap=32)
    run_id = uuid.uuid4().hex[:8]

    # Create 4K source image
    in_w, in_h = 3840, 2160
    four_k_img = Image.new("RGB", (in_w, in_h), color=(80, 140, 200))
    four_k_path = os.path.join(settings.STORAGE_PATH, "test_phase2_progressive", f"flagship_4k_{run_id}.png")
    make_writable(four_k_path)
    four_k_img.save(four_k_path, format="PNG")

    # Register in version graph
    img_id = f"img_flagship_{run_id}"
    proj_id = f"proj_{img_id}"
    v_orig = version_service.create_project_from_image(
        image_id=img_id,
        filename=f"flagship_4k_{run_id}.png",
        image_path=four_k_path,
        w=in_w,
        h=in_h,
        fmt="PNG"
    )
    orig_ver_id = v_orig["root_version_id"]

    # Calculate SHA-256 before inference
    hasher = hashlib.sha256()
    with open(four_k_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    parent_sha_before = hasher.hexdigest()

    # Define 4x model mock that behaves like NCNN 4x runner
    # Note: 4x model turns 512x512 tile into 2048x2048
    def mock_4x_ncnn(tile: Image.Image) -> Image.Image:
        tw, th = tile.size
        return tile.resize((tw * 4, th * 4), Image.Resampling.BILINEAR)

    # Execute Per-Tile Scale Adaptation:
    # Model scale = 4, target_scale = 2.0 (4K -> 8K)
    # Output must be 7680 x 4320
    eight_k_img = engine.process(
        img=four_k_img,
        infer_fn=mock_4x_ncnn,
        scale=4,
        target_scale=2.0,
        tile_size=512,
        overlap=32
    )

    assert eight_k_img.size == (7680, 4320), f"Expected 7680x4320, got {eight_k_img.size}"

    # Save 8K output and register as derived version
    eight_k_path = os.path.join(settings.STORAGE_PATH, "test_phase2_progressive", f"flagship_8k_{run_id}.png")
    make_writable(eight_k_path)
    eight_k_img.save(eight_k_path, format="PNG")

    v_8k = version_service.register_derived_version(
        project_id=proj_id,
        parent_version_id=orig_ver_id,
        output_image_path=eight_k_path,
        operation="upscale_progressive",
        mode="progressive_upscale",
        model_id="realesrgan-x4plus",
        scale=2,
        runtime_s=18.2
    )

    assert v_8k["parent_version_id"] == orig_ver_id
    assert v_8k["width"] == 7680
    assert v_8k["height"] == 4320
    assert v_8k["megapixels"] == 33.18

    # Verify parent version SHA-256 is 100% UNCHANGED (Invariant E2)
    hasher = hashlib.sha256()
    with open(four_k_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    parent_sha_after = hasher.hexdigest()

    assert parent_sha_before == parent_sha_after, "Parent version was mutated! Invariant E2 violated."

def test_api_resolution_endpoints():
    # Setup test project
    run_id = uuid.uuid4().hex[:8]
    img_id = f"img_api_{run_id}"
    proj_id = f"proj_{img_id}"
    img_path = os.path.join(settings.STORAGE_PATH, "test_phase2_progressive", f"api_test_{run_id}.png")
    make_writable(img_path)
    Image.new("RGB", (1920, 1080), color=(120, 80, 90)).save(img_path)
    v_orig = version_service.create_project_from_image(
        image_id=img_id,
        filename=f"api_test_{run_id}.png",
        image_path=img_path,
        w=1920,
        h=1080,
        fmt="PNG"
    )
    orig_ver_id = v_orig["root_version_id"]

    # 1. POST /projects/{project_id}/plan
    plan_resp = client.post(f"/api/v1/projects/{proj_id}/plan", json={
        "target_width": 3840,
        "target_height": 2160,
        "source_version_id": orig_ver_id
    })
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert plan_data["plan_type"] in ("plan_a", "plan_b")
    assert plan_data["target_width"] == 3840

    # 2. POST /projects/{project_id}/versions/{version_id}/upscale
    up_resp = client.post(f"/api/v1/projects/{proj_id}/versions/{orig_ver_id}/upscale", json={
        "target_width": 3840,
        "target_height": 2160,
        "output_format": "png"
    })
    assert up_resp.status_code == 200
    up_data = up_resp.json()
    assert "job_id" in up_data
    assert up_data["status"] == "queued"

    job_id = up_data["job_id"]

    # 3. GET /jobs/{job_id}/stages
    stg_resp = client.get(f"/api/v1/jobs/{job_id}/stages")
    assert stg_resp.status_code == 200
    assert "stages" in stg_resp.json()

    # 4. POST /jobs/{job_id}/pause and resume
    pause_resp = client.post(f"/api/v1/jobs/{job_id}/pause")
    assert pause_resp.status_code == 200

    resume_resp = client.post(f"/api/v1/jobs/{job_id}/resume")
    assert resume_resp.status_code == 200
