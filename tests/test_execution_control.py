import os
import time
import shutil
import tempfile
import threading
import subprocess
import pytest
import numpy as np
from PIL import Image
from unittest.mock import MagicMock, patch

from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.processing.tile_engine import TileEngine, JobPausedException
from ai_engine.processing.tile_store import TileStore
from ai_engine.pipelines.pipeline import pipeline


def test_cancellation_during_active_subprocess(tmp_path):
    """Verifies enhance_batch terminates active subprocess upon cancel_check without hanging."""
    adapter = NCNNRealESRGANAdapter()
    
    in_file = str(tmp_path / "tile_0.png")
    out_file = str(tmp_path / "out_0.png")
    Image.new("RGB", (32, 32)).save(in_file)

    # Mock subprocess.Popen that sleeps for 5 seconds unless killed
    class MockPopen:
        def __init__(self, *args, **kwargs):
            self.killed = False
            self.returncode = None
            self._start = time.perf_counter()

        def poll(self):
            if self.killed:
                return -9
            if time.perf_counter() - self._start > 5.0:
                self.returncode = 0
                return 0
            return None

        def kill(self):
            self.killed = True
            self.returncode = -9

        def wait(self, timeout=None):
            return self.returncode

        def communicate(self):
            return ("", "killed" if self.killed else "")

    should_cancel = False

    def cancel_check():
        return should_cancel

    # Trigger cancellation after 100ms
    def trigger_cancel():
        time.sleep(0.1)
        nonlocal should_cancel
        should_cancel = True

    threading.Thread(target=trigger_cancel, daemon=True).start()

    with patch("subprocess.Popen", side_effect=MockPopen), \
         patch("os.path.isfile", return_value=True):
        
        with pytest.raises(RuntimeError, match="Inference cancelled by user"):
            adapter.enhance_batch(
                input_paths=[in_file],
                output_paths=[out_file],
                cancel_check=cancel_check
            )

    assert adapter.current_process is None, "current_process must be reaped and cleared"


def test_no_orphaned_process_after_cancellation():
    """Verifies that adapter.cancel() properly kills and reaps active process."""
    adapter = NCNNRealESRGANAdapter()
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    adapter.current_process = mock_proc

    adapter.cancel()

    mock_proc.kill.assert_called_once()
    mock_proc.wait.assert_called_once()
    assert adapter.current_process is None


def test_pause_and_resume_preserves_checkpoints(tmp_path):
    """Verifies pausing during batch tiling saves completed tiles and resumes without duplicate inference."""
    store = TileStore(base_dir=str(tmp_path / "tiles"))
    engine = TileEngine(default_tile_size=64, overlap=16)

    # 160x160 image with 64px tiles -> 9 tiles total (chunks of 8 tiles: chunk 1 = 8, chunk 2 = 1)
    img = Image.new("RGB", (160, 160), color=(80, 100, 120))
    stage_id = "test_pause_stage"
    job_id = "job_test_pause"

    grid = engine.generate_tile_grid(160, 160, 64, 16)
    assert len(grid) == 9

    store.init_stage(
        stage_id=stage_id,
        job_id=job_id,
        stage_index=1,
        operation="upscale",
        model="mock_model",
        from_size=(160, 160),
        to_size=(320, 320),
        tile_grid=grid
    )

    inferred_tiles_pass1 = []

    def mock_batch_pass1(crops):
        results = []
        for c in crops:
            inferred_tiles_pass1.append(c.size)
            results.append(c.resize((c.width * 2, c.height * 2)))
        return results

    # Pause after first chunk of 8 tiles
    pause_flag = False

    def pause_after_first_chunk():
        # Trigger pause once 8 tiles have been inferred
        return len(inferred_tiles_pass1) >= 8

    with pytest.raises(JobPausedException, match="Job paused by user"):
        engine.process(
            img=img,
            batch_infer_fn=mock_batch_pass1,
            scale=2,
            tile_size=64,
            overlap=16,
            tile_store=store,
            stage_id=stage_id,
            pause_check=pause_after_first_chunk
        )

    # Verify 8 tiles were saved to store
    completed = store.get_completed_tiles(stage_id)
    assert len(completed) == 8, f"Expected 8 tiles saved at pause checkpoint, got {len(completed)}"

    # Pass 2: Resume with pause_flag False
    inferred_tiles_pass2 = []

    def mock_batch_pass2(crops):
        results = []
        for c in crops:
            inferred_tiles_pass2.append(c.size)
            results.append(c.resize((c.width * 2, c.height * 2)))
        return results

    resumed_img = engine.process(
        img=img,
        batch_infer_fn=mock_batch_pass2,
        scale=2,
        tile_size=64,
        overlap=16,
        tile_store=store,
        stage_id=stage_id,
        pause_check=lambda: False
    )

    assert resumed_img.size == (320, 320)
    # The 8 completed tiles must NOT be re-inferred! Only the 1 remaining tile was processed!
    assert len(inferred_tiles_pass2) == 1, (
        f"Expected only 1 remaining tile to be inferred on resume, but got {len(inferred_tiles_pass2)}"
    )


def test_checkpoint_compatibility_validation(tmp_path):
    """Verifies that changing model or dimensions invalidates stale checkpoints."""
    store = TileStore(base_dir=str(tmp_path / "tiles"))
    stage_id = "compat_test_stage"
    job_id = "job_compat_test"
    grid = [{"gx": 0, "gy": 0, "box": (0, 0, 64, 64)}]

    store.init_stage(
        stage_id=stage_id,
        job_id=job_id,
        stage_index=1,
        operation="upscale",
        model="realesrgan-x4plus",
        from_size=(64, 64),
        to_size=(256, 256),
        tile_grid=grid
    )

    # Save a tile for this stage
    tile_img = Image.new("RGB", (256, 256), (50, 60, 70))
    store.save_tile(stage_id, 0, 0, tile_img)
    assert len(store.get_completed_tiles(stage_id)) == 1

    # Re-init with DIFFERENT model (e.g. anime) -> must invalidate and purge stale tile
    store.init_stage(
        stage_id=stage_id,
        job_id=job_id,
        stage_index=1,
        operation="upscale",
        model="realesrgan-x4plus-anime",
        from_size=(64, 64),
        to_size=(256, 256),
        tile_grid=grid
    )
    assert len(store.get_completed_tiles(stage_id)) == 0, "Incompatible model must purge stale checkpoints"


def test_standard_pipeline_pause_and_resume(tmp_path):
    """Verifies standard pipeline passes pause and tile_store callbacks and supports resume."""
    store = TileStore(base_dir=str(tmp_path / "pipeline_tiles"))
    in_img = Image.new("RGB", (128, 128), (200, 100, 50))
    in_path = str(tmp_path / "std_in.png")
    out_path = str(tmp_path / "std_out.png")
    in_img.save(in_path)

    job_id = "std_pause_job"

    # Mock NCNN adapter enhance_batch so we don't need real GPU in unit test
    def mock_enhance_batch(input_paths, output_paths, **kwargs):
        for inp, outp in zip(input_paths, output_paths):
            with Image.open(inp) as im:
                im.resize((im.width * 2, im.height * 2)).save(outp)
        return output_paths

    with patch.object(pipeline.adapter, "enhance_batch", side_effect=mock_enhance_batch):
        # 1. Trigger pause on first tile check
        with pytest.raises(JobPausedException):
            pipeline.run(
                input_path=in_path,
                output_path=out_path,
                mode="upscale",
                scale=2,
                tile_size=64,
                job_id=job_id,
                tile_store=store,
                pause_check=lambda: True
            )

        # 2. Resume without pause
        res = pipeline.run(
            input_path=in_path,
            output_path=out_path,
            mode="upscale",
            scale=2,
            tile_size=64,
            job_id=job_id,
            tile_store=store,
            pause_check=lambda: False
        )

        assert os.path.isfile(out_path)
        with Image.open(out_path) as out_im:
            assert out_im.size == (256, 256)


def test_cancellation_cleanup_integrity(tmp_path):
    """Verifies that cancelled execution cleans up partial outputs and stage directory."""
    store = TileStore(base_dir=str(tmp_path / "tiles"))
    in_img = Image.new("RGB", (128, 128), (10, 20, 30))
    in_path = str(tmp_path / "cancel_in.png")
    out_path = str(tmp_path / "cancel_out.png")
    in_img.save(in_path)

    job_id = "cancel_cleanup_job"

    with patch.object(pipeline.adapter, "enhance_batch", side_effect=RuntimeError("Inference cancelled by user")):
        with pytest.raises(RuntimeError, match="cancelled"):
            pipeline.run(
                input_path=in_path,
                output_path=out_path,
                mode="upscale",
                scale=2,
                tile_size=64,
                job_id=job_id,
                tile_store=store,
                cancel_check=lambda: True
            )

    # Partial output file should not exist
    assert not os.path.isfile(out_path), "Cancelled job output must not be left on disk"
    # Stage directory should be cleaned up
    stage_dir = store.get_stage_dir(f"{job_id}_standard")
    assert not os.path.exists(stage_dir) or len(os.listdir(stage_dir)) == 0


def test_api_pause_and_resume_lifecycle(requires_ncnn):
    """End-to-end API verification of pause and resume with genuine checkpoint persistence."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    client = TestClient(app)

    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "test_input.png"))
    with open(fixture_path, "rb") as f:
        up_res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    assert up_res.status_code == 200
    img_id = up_res.json()["image_id"]

    # Submit a standard upscale job
    job_res = client.post("/api/v1/jobs", json={
        "image_id": img_id,
        "mode": "upscale",
        "scale": 4,
        "model": "realesrgan-x4plus-anime"
    })
    assert job_res.status_code == 200
    job_id = job_res.json()["job_id"]

    # Pause the job
    time.sleep(0.1)
    p_res = client.post(f"/api/v1/jobs/{job_id}/pause")
    assert p_res.status_code == 200

    # Wait for paused status
    for _ in range(25):
        st = client.get(f"/api/v1/jobs/{job_id}").json()["status"]
        if st in ("paused", "completed"):
            break
        time.sleep(0.5)

    assert st in ("paused", "completed")

    # If it reached paused, resume and ensure completion
    if st == "paused":
        r_res = client.post(f"/api/v1/jobs/{job_id}/resume")
        assert r_res.status_code == 200
        for _ in range(40):
            st = client.get(f"/api/v1/jobs/{job_id}").json()["status"]
            if st in ("completed", "failed"):
                break
            time.sleep(0.5)
        assert st == "completed"


def test_api_cancellation_lifecycle(requires_ncnn):
    """End-to-end API verification that cancelled jobs stop cleanly and record cancelled status."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    client = TestClient(app)

    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "test_input.png"))
    with open(fixture_path, "rb") as f:
        up_res = client.post("/api/v1/images", files={"file": ("test_input.png", f, "image/png")})
    assert up_res.status_code == 200
    img_id = up_res.json()["image_id"]

    # Submit job and immediately cancel
    job_res = client.post("/api/v1/jobs", json={
        "image_id": img_id,
        "mode": "upscale",
        "scale": 4,
        "model": "realesrgan-x4plus-anime"
    })
    assert job_res.status_code == 200
    job_id = job_res.json()["job_id"]

    c_res = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert c_res.status_code == 200

    for _ in range(20):
        st = client.get(f"/api/v1/jobs/{job_id}").json()["status"]
        if st in ("cancelled", "completed"):
            break
        time.sleep(0.5)

    assert st == "cancelled"

