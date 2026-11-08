import pytest
import numpy as np
from PIL import Image
from ai_engine.processing.tile_engine import TileEngine
from ai_engine.memory.memory_manager import memory_manager

def test_tile_grid_coverage():
    engine = TileEngine(default_tile_size=128, overlap=32)
    tiles = engine.generate_tile_grid(img_w=300, img_h=250, tile_size=128, overlap=32)
    assert len(tiles) > 1

    # Verify bounds coverage
    covered_mask = np.zeros((250, 300), dtype=bool)
    for t in tiles:
        x1, y1, x2, y2 = t["box"]
        assert x2 <= 300 and y2 <= 250
        assert x2 > x1 and y2 > y1
        covered_mask[y1:y2, x1:x2] = True

    assert np.all(covered_mask), "All pixels must be covered by tile grid"

def test_feather_window_boundary_properties():
    engine = TileEngine()
    # Boundary tile (top-left)
    w_tl = engine.compute_feather_window(
        height=64, width=64,
        is_top=True, is_bottom=False, is_left=True, is_right=False,
        overlap=16
    )
    # Top-left corner must be 1.0
    assert np.isclose(w_tl[0, 0], 1.0)
    # Bottom-right corner must decay towards 0
    assert w_tl[-1, -1] < 0.1

    # Internal tile
    w_int = engine.compute_feather_window(
        height=64, width=64,
        is_top=False, is_bottom=False, is_left=False, is_right=False,
        overlap=16
    )
    # Internal corners should decay towards 0
    assert w_int[0, 0] < 0.1
    # Center should be 1.0
    assert np.isclose(w_int[32, 32], 1.0)

def test_seamless_reconstruction():
    engine = TileEngine(default_tile_size=128, overlap=32)
    # Create gradient synthetic test image
    x = np.linspace(0, 255, 310, dtype=np.uint8)
    y = np.linspace(0, 255, 270, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    arr = np.stack([xx, yy, (xx // 2 + yy // 2).astype(np.uint8)], axis=-1)
    img = Image.fromarray(arr, mode="RGB")

    # Scale 2x with bicubic
    scale = 2
    def infer_fn(tile: Image.Image) -> Image.Image:
        tw, th = tile.size
        return tile.resize((tw * scale, th * scale), Image.Resampling.BICUBIC)

    reconstructed = engine.process(
        img=img,
        infer_fn=infer_fn,
        scale=scale,
        tile_size=128,
        overlap=32
    )

    ground_truth = img.resize((310 * scale, 270 * scale), Image.Resampling.BICUBIC)
    diff = np.abs(np.array(reconstructed, dtype=np.float32) - np.array(ground_truth, dtype=np.float32))

    # Mean absolute error across all pixels including seam boundaries must be extremely low
    mae = np.mean(diff)
    max_err = np.max(diff)
    assert mae < 1.0, f"Reconstruction MAE too high: {mae}"
    assert max_err < 5.0, f"Max seam discrepancy too high: {max_err}"

def test_automatic_oom_retry():
    engine = TileEngine(default_tile_size=256, overlap=32)
    img = Image.new("RGB", (400, 400), color=(100, 150, 200))

    attempt_sizes = []

    def mock_infer_fn(tile: Image.Image) -> Image.Image:
        tw, th = tile.size
        attempt_sizes.append(tw)
        if tw > 150:
            raise RuntimeError("CUDA out of memory while allocating tensor")
        return tile.resize((tw * 2, th * 2), Image.Resampling.NEAREST)

    # Should fail on 256, retry with 128 and succeed
    result = engine.process(img=img, infer_fn=mock_infer_fn, scale=2, tile_size=256, auto_oom_retry=True)
    assert result.size == (800, 800)
    assert any(s <= 128 for s in attempt_sizes), "Engine should have downscaled tile size upon OOM"

def test_100_mp_cap_rejection():
    engine = TileEngine(max_output_mp=100)
    # 6000 x 6000 = 36 MP input. At 4x scale -> 24000 x 24000 = 576 MP (> 100 MP)
    img = Image.new("RGB", (6000, 6000), color=(0, 0, 0))

    def dummy_fn(tile: Image.Image) -> Image.Image:
        tw, th = tile.size
        return tile.resize((tw * 4, th * 4))

    with pytest.raises(ValueError, match="exceeds maximum allowed limit of 100 MP"):
        engine.process(img=img, infer_fn=dummy_fn, scale=4)

def test_memory_manager_profile():
    status = memory_manager.get_hardware_status()
    assert "profile" in status
    assert "ram_total_mb" in status
    assert "vram_total_mb" in status
    assert "recommended_tile_size" in status

def test_cancellation_between_tiles():
    engine = TileEngine(default_tile_size=128, overlap=32)
    img = Image.new("RGB", (400, 400), color=(50, 50, 50))

    call_count = 0
    def cancel_after_two_tiles():
        nonlocal call_count
        call_count += 1
        return call_count > 2

    def infer_fn(tile: Image.Image) -> Image.Image:
        tw, th = tile.size
        return tile.resize((tw * 2, th * 2))

    with pytest.raises(RuntimeError, match="Job cancelled by user"):
        engine.process(img=img, infer_fn=infer_fn, scale=2, cancel_check=cancel_after_two_tiles)

