import os
import tempfile
import pytest
import numpy as np
from PIL import Image

from ai_engine.processing.alpha_handler import AlphaHandler
from ai_engine.processing.restoration import RestorationEngine
from ai_engine.processing.consistency import ConsistencyChecker
from ai_engine.processing.metadata_embedder import MetadataEmbedder
from ai_engine.pipelines.pipeline import pipeline

def test_alpha_bleed_and_recombine():
    # Create 64x64 transparent RGBA image with red circle in center
    arr = np.zeros((64, 64, 4), dtype=np.uint8)
    yy, xx = np.ogrid[:64, :64]
    mask = (xx - 32)**2 + (yy - 32)**2 <= 20**2
    arr[mask] = [255, 0, 0, 255]
    rgba_in = Image.fromarray(arr, mode="RGBA")

    # Prepare RGB and Alpha
    rgb_bled, alpha_chan, has_alpha = AlphaHandler.prepare_rgb_and_alpha(rgba_in)
    assert has_alpha is True
    assert alpha_chan is not None
    assert rgb_bled.size == (64, 64)

    # Check that colors bled outward into formerly black transparent areas
    bled_arr = np.array(rgb_bled)
    # Right outside the radius (e.g. radius 22), it should now have non-zero red color instead of 0
    border_sample = bled_arr[32, 54]  # distance 22 from center (32, 32)
    assert border_sample[0] > 0, "Color should bleed outward under transparent pixels"

    # Recombine at 2x scale (128x128)
    recombined = AlphaHandler.recombine(rgb_bled, alpha_chan, (128, 128))
    assert recombined.size == (128, 128)
    assert recombined.mode == "RGBA"
    recombined_arr = np.array(recombined)
    # Check that center is opaque and outer corner is transparent
    assert recombined_arr[64, 64, 3] == 255
    assert recombined_arr[0, 0, 3] == 0

def test_restoration_filters():
    # Create synthetic noisy blocky image
    base = np.full((128, 128, 3), 128, dtype=np.uint8)
    # Add artificial Gaussian noise
    noise = np.random.normal(0, 15, base.shape).astype(np.int16)
    noisy = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    noisy_img = Image.fromarray(noisy, mode="RGB")

    restored = RestorationEngine.restore(noisy_img, noise_score=8.0, has_jpeg_artifacts=True, apply_sharpen=True)
    assert restored.size == (128, 128)
    restored_arr = np.array(restored, dtype=np.float32)

    # Noise variance should be substantially reduced
    orig_var = np.var(noisy)
    restored_var = np.var(restored_arr)
    assert restored_var < orig_var * 0.75, "Restoration should reduce noise variance"

def test_consistency_checker():
    # Test identical images
    img1 = Image.new("RGB", (64, 64), color=(100, 120, 140))
    res = ConsistencyChecker.evaluate(img1, img1)
    assert res["is_faithful"] is True
    assert res["psnr_db"] >= 99.0
    assert res["mae"] == 0.0

    # Test modified image
    img2 = Image.new("RGB", (256, 256), color=(105, 125, 145))
    res2 = ConsistencyChecker.evaluate(img1, img2)
    assert res2["mae"] == 5.0
    assert "channel_drifts" in res2

    diff_map = ConsistencyChecker.generate_diff_map(img1, img2)
    assert diff_map.size == (64, 64)

def test_metadata_embedder(tmp_path):
    img = Image.new("RGB", (64, 64), color=(50, 100, 150))
    meta = MetadataEmbedder.build_provenance_dict(
        mode="restore_upscale",
        model_name="realesrgan-x4plus",
        scale=4,
        stages=["prepass", "neural-sr", "post-sharpen"],
        consistency={"psnr_db": 34.5, "mae": 3.2}
    )
    out_file = str(tmp_path / "test_meta.png")
    MetadataEmbedder.save_with_metadata(img, out_file, format_name="PNG", metadata=meta)

    # Read back and inspect PNG text metadata
    re_opened = Image.open(out_file)
    assert re_opened.text.get("Aether-Mode") == "restore_upscale"
    assert re_opened.text.get("Aether-Model") == "realesrgan-x4plus"
    assert "prepass" in re_opened.text.get("Aether-Stages", "")
    assert re_opened.text.get("Aether-Consistency-PSNR") == "34.5 dB"

def test_distinct_pipeline_modes(tmp_path):
    # Create small test fixture
    fixture_path = os.path.join("tests", "fixtures", "test_input.png")
    if not os.path.exists(fixture_path):
        pytest.skip("Fixture not found")

    # 1. Restore mode (1x)
    restore_out = str(tmp_path / "restore_out.png")
    res_restore = pipeline.run(
        input_path=fixture_path,
        output_path=restore_out,
        mode="restore",
        scale=1
    )
    assert res_restore["scale"] == 1
    assert "classical-restoration-prepass" in res_restore["stages"]
    with Image.open(restore_out) as img_r:
        assert img_r.size == tuple(res_restore["input_dimensions"])

    # 2. Upscale mode (4x)
    upscale_out = str(tmp_path / "upscale_out.png")
    res_upscale = pipeline.run(
        input_path=fixture_path,
        output_path=upscale_out,
        mode="upscale",
        model_name="realesrgan-x4plus",
        scale=4
    )
    assert res_upscale["scale"] == 4
    assert "neural-sr-upscale" in res_upscale["stages"]
    with Image.open(upscale_out) as img_u:
        assert img_u.size == (res_upscale["input_dimensions"][0] * 4, res_upscale["input_dimensions"][1] * 4)

    # 3. Restore + Upscale mode (4x)
    comb_out = str(tmp_path / "comb_out.png")
    res_comb = pipeline.run(
        input_path=fixture_path,
        output_path=comb_out,
        mode="restore_upscale",
        model_name="realesrgan-x4plus",
        scale=4
    )
    assert res_comb["scale"] == 4
    assert "classical-restoration-prepass" in res_comb["stages"]
    assert "neural-sr-upscale" in res_comb["stages"]
    assert "conservative-post-polish" in res_comb["stages"]

    # Verify that upscale and restore_upscale produce distinct real results
    with Image.open(upscale_out) as img_u, Image.open(comb_out) as img_c:
        arr_u = np.array(img_u, dtype=np.float32)
        arr_c = np.array(img_c, dtype=np.float32)
        mae = float(np.mean(np.abs(arr_u - arr_c)))
        assert mae > 0.05, f"Upscale and Combined modes must produce distinct outputs (MAE: {mae})"

