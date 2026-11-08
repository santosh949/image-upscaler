import os
import shutil
import pytest
import numpy as np
from PIL import Image

from backend.app.core.config import settings
from backend.app.services.preset_service import preset_service
from backend.app.services.resolution_planner import resolution_planner
from backend.app.services.storage_service import storage_service
from backend.app.services.version_service import version_service
from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.pipelines.pipeline import pipeline
from ai_engine.pipelines.progressive_pipeline import progressive_pipeline

def test_vulkan_device_nvidia_verification():
    adapter = NCNNRealESRGANAdapter()
    devs = adapter.get_vulkan_devices()
    assert 0 in devs
    assert any(k in devs[0].lower() for k in ("nvidia", "geforce", "rtx"))
    assert adapter.get_nvidia_device_id() == 0

def test_preset_service_resolution():
    presets = preset_service.list_presets()
    assert "natural" in presets
    assert "faithful" in presets
    assert "more_detail" in presets
    assert "smooth_clean" in presets
    assert "artwork" in presets

    nat = preset_service.resolve("natural")
    assert nat["pre_denoise"] == "none"
    assert nat["post_sharpen"] == "off"
    assert nat["texture_blend_weight"] == 0.20

    sc = preset_service.resolve("smooth_clean")
    assert sc["pre_denoise"] == "medium"
    assert len(sc["warnings"]) > 0

    art = preset_service.resolve("artwork")
    assert art["model"] == "realesrgan-x4plus-anime"
    assert art["pre_denoise"] == "none"

def test_resolution_planner_plan_c_selection():
    # Test project root version
    test_img = "tests/fixtures/test_input.png"
    reg = version_service.create_project_from_image("img_test_v3", "test.png", test_img, 256, 256, "PNG")
    proj_id = reg["project_id"]
    root_id = reg["root_version_id"]

    # Request Plan C
    plan_c = resolution_planner.generate_plan(
        project_id=proj_id,
        source_version_id=root_id,
        target_width=512,
        target_height=512,
        plan_choice="plan_c"
    )
    assert plan_c["plan_type"] == "plan_c"
    assert plan_c["stages"][0]["operation"] == "classical_resample"
    assert plan_c["stages"][0]["model_name"] == "lanczos"

def test_plan_c_execution_lanczos(tmp_path):
    test_img = "tests/fixtures/test_input.png"
    out_path = str(tmp_path / "plan_c_out.png")

    plan = {
        "project_id": "test_c",
        "target_width": 512,
        "target_height": 512,
        "plan_type": "plan_c",
        "stages": [
            {
                "stage_index": 1,
                "operation": "classical_resample",
                "model_name": "lanczos",
                "from_res": [256, 256],
                "to_res": [512, 512]
            }
        ]
    }

    res = progressive_pipeline.run(
        input_path=test_img,
        output_path=out_path,
        plan=plan,
        job_id="test_job_plan_c"
    )
    assert res["status"] == "completed"
    assert res["width"] == 512
    assert res["height"] == 512
    assert os.path.isfile(out_path)
    with Image.open(out_path) as im:
        assert im.size == (512, 512)

def test_preflight_free_disk_check():
    # Estimating 100 terabytes should fail
    with pytest.raises(RuntimeError):
        storage_service.check_disk_space(100 * 1024 * 1024 * 1024 * 1024)

def test_provenance_sidecar_generation(tmp_path):
    from ai_engine.processing.metadata_embedder import MetadataEmbedder
    out_jpg = str(tmp_path / "test_sidecar.jpg")
    img = Image.new("RGB", (64, 64), color="blue")
    meta = {"Aether-Software": "AETHER UPSCALE 2.0", "Aether-Preset": "Natural"}

    MetadataEmbedder.save_with_metadata(img, out_jpg, format_name="JPEG", metadata=meta)
    assert os.path.isfile(out_jpg)
    assert os.path.isfile(f"{out_jpg}.manifest.json")

