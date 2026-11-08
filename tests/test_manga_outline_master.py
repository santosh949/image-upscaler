import os
import cv2
import numpy as np
import pytest
from PIL import Image
from ai_engine.processing.manga_outline_engine import MangaOutlineEngine
from ai_engine.pipelines.pipeline import pipeline

def test_manga_outline_engine_steepening():
    # Create test synthetic image with soft edge ramp
    arr = np.zeros((100, 100), dtype=np.uint8)
    arr[:, :45] = 20
    arr[:, 45:55] = np.linspace(20, 240, 10, dtype=np.uint8)
    arr[:, 55:] = 240
    img = Image.fromarray(arr, mode="L").convert("RGB")

    processed = MangaOutlineEngine.process(img, strength=1.0)
    p_arr = np.array(processed.convert("L"))

    # Edge gradient of processed should be higher than input
    orig_gx = cv2.Sobel(arr, cv2.CV_32F, 1, 0, ksize=3)
    proc_gx = cv2.Sobel(p_arr, cv2.CV_32F, 1, 0, ksize=3)
    assert np.max(proc_gx) > np.max(orig_gx)

def test_manga_outline_zero_halo():
    # Verify mathematically no pixel exceeds local bounds
    arr = np.random.randint(50, 200, (64, 64), dtype=np.uint8)
    img = Image.fromarray(arr, mode="L").convert("RGB")
    processed = MangaOutlineEngine.process(img, strength=1.0, clean_paper=False, deep_ink=False)
    p_arr = np.array(processed.convert("L"))

    # Local bounds check
    elem = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    local_min = cv2.erode(arr, elem)
    local_max = cv2.dilate(arr, elem)

    # All values in p_arr must be within [local_min, local_max] (allowing rounding tolerance +-1)
    assert np.all(p_arr >= (local_min.astype(np.int16) - 1))
    assert np.all(p_arr <= (local_max.astype(np.int16) + 1))

def test_manga_outline_paper_and_ink():
    arr = np.array([[10, 25, 128, 235, 250]], dtype=np.uint8)
    img = Image.fromarray(arr, mode="L").convert("RGB")
    processed = MangaOutlineEngine.process(img, strength=1.0, clean_paper=True, deep_ink=True)
    p_arr = np.array(processed.convert("L"))

    # Deep ink check: dark pixels pushed toward 0
    assert p_arr[0, 0] <= 5
    assert p_arr[0, 1] < 20
    # Paper purification check: bright pixels pushed toward 255
    assert p_arr[0, 3] > 235
    assert p_arr[0, 4] == 255

def test_manga_outline_screentone_protection():
    # Synthetic screentone: checkerboard / dot pattern
    arr = np.zeros((64, 64), dtype=np.uint8) + 128
    arr[::2, ::2] = 80
    arr[1::2, 1::2] = 180
    img = Image.fromarray(arr, mode="L").convert("RGB")

    orig_std = np.std(arr)
    processed = MangaOutlineEngine.process(img, strength=1.0, protect_screentones=True)
    p_arr = np.array(processed.convert("L"))
    proc_std = np.std(p_arr)

    # Screentone frequency must be preserved, not smudged or destroyed
    assert proc_std > 0.8 * orig_std

def test_pipeline_manga_crisp_stage_execution(tmp_path):
    # Minimal test running pipeline with manga_crisp preset
    in_file = tmp_path / "test_in.png"
    out_file = tmp_path / "test_out.png"
    test_img = Image.new("RGB", (32, 32), (255, 255, 255))
    test_img.save(str(in_file))

    res = pipeline.run(
        input_path=str(in_file),
        output_path=str(out_file),
        mode="upscale",
        model_name="realesrgan-x4plus-anime",
        scale=4,
        preset="manga_crisp"
    )
    assert res["mode"] == "upscale"
    assert "manga-outline-master-engine" in res["stages"]
    assert os.path.exists(str(out_file))

