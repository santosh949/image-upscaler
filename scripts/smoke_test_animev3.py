import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.registry.model_registry import model_registry

def test_animev3_inference():
    print("Testing Real-ESRGAN AnimeVideo v3 x4 on NVIDIA RTX 2050 (Vulkan 0)...")
    adapter = NCNNRealESRGANAdapter()
    adapter.load(device="vulkan")

    in_file = os.path.abspath(r"tests\fixtures\test_input.png")
    out_file = os.path.abspath(r"storage\temp\smoke_animev3_out.png")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    t0 = time.perf_counter()
    res = adapter.enhance(
        input_path=in_file,
        output_path=out_file,
        scale=4,
        gpu_id=0,
        model_name="realesr-animevideov3-x4"
    )
    elapsed = time.perf_counter() - t0

    print(f"✓ AnimeVideo v3 finished in {elapsed:.3f}s")
    print(f"Dimensions: {res['input_dimensions']} -> {res['output_dimensions']}")
    print(f"Output bytes: {res['output_bytes']}")

    model_registry.mark_smoke_tested("realesr-animevideov3-x4", True)

    if os.path.exists(out_file):
        os.remove(out_file)

if __name__ == "__main__":
    test_animev3_inference()

