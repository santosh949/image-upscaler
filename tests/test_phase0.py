import os
import subprocess
from PIL import Image

def test_ncnn_executable_exists():
    exe_path = os.path.abspath(r"tools\realesrgan-ncnn-vulkan\realesrgan-ncnn-vulkan.exe")
    assert os.path.isfile(exe_path), f"Executable missing at {exe_path}"

def test_model_weights_and_param_exist():
    bin_path = os.path.abspath(r"tools\realesrgan-ncnn-vulkan\models\realesrgan-x4plus.bin")
    param_path = os.path.abspath(r"tools\realesrgan-ncnn-vulkan\models\realesrgan-x4plus.param")
    assert os.path.isfile(bin_path), f"Binary weights missing at {bin_path}"
    assert os.path.isfile(param_path), f"Param file missing at {param_path}"

def test_real_inference_output():
    exe_path = os.path.abspath(r"tools\realesrgan-ncnn-vulkan\realesrgan-ncnn-vulkan.exe")
    in_path = os.path.abspath(r"tests\fixtures\test_input.png")
    out_path = os.path.abspath(r"storage\outputs\test_output_4x.png")
    
    assert os.path.isfile(in_path), "Input fixture missing"
    
    if not os.path.isfile(out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        res = subprocess.run([
            exe_path,
            "-i", in_path,
            "-o", out_path,
            "-n", "realesrgan-x4plus"
        ], capture_output=True, text=True)
        assert res.returncode == 0, f"Inference execution failed: {res.stderr}"

    assert os.path.isfile(out_path), "Output upscaled image missing"
    
    in_img = Image.open(in_path)
    out_img = Image.open(out_path)
    
    assert out_img.size == (in_img.size[0] * 4, in_img.size[1] * 4)
    assert os.path.getsize(out_path) > 10_000, "Output file is suspiciously small / mock"
    
    # Clean up test output so storage remains clean
    if os.path.isfile(out_path):
        try:
            os.remove(out_path)
        except OSError:
            pass

