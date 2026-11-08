import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.registry.model_registry import model_registry

def smoke_test_anime():
    adapter = NCNNRealESRGANAdapter()
    input_path = os.path.abspath(r"tests\fixtures\test_input.png")
    output_path = os.path.abspath(r"storage\outputs\smoke_anime_x4.png")

    print(f"Running Real-ESRGAN Anime smoke test on GPU 0...")
    res = adapter.enhance(
        input_path=input_path,
        output_path=output_path,
        scale=4,
        gpu_id=0,
        model_name="realesrgan-x4plus-anime"
    )

    print("Smoke test result:", res)
    assert res["model"] == "realesrgan-x4plus-anime"
    assert res["output_dimensions"] == [1024, 1024]
    assert os.path.isfile(output_path)
    assert os.path.getsize(output_path) > 100_000

    model_registry.mark_smoke_tested("realesrgan-x4plus-anime", True)
    print("realesrgan-x4plus-anime SMOKE TEST PASSED!")
    return True

if __name__ == "__main__":
    success = smoke_test_anime()
    sys.exit(0 if success else 1)
