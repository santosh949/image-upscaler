import os
import sys
import subprocess
import pytest
from PIL import Image

def get_ncnn_paths():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = "realesrgan-ncnn-vulkan.exe" if sys.platform.startswith("win") else "realesrgan-ncnn-vulkan"
    exe_path = os.path.join(root, "tools", "realesrgan-ncnn-vulkan", bin_name)
    models_dir = os.path.join(root, "tools", "realesrgan-ncnn-vulkan", "models")
    return exe_path, models_dir

def test_ncnn_executable_exists(requires_ncnn):
    exe_path, _ = get_ncnn_paths()
    assert os.path.isfile(exe_path), f"Executable missing at {exe_path}"

def test_model_weights_and_param_exist(requires_ncnn):
    _, models_dir = get_ncnn_paths()
    bin_path = os.path.join(models_dir, "realesrgan-x4plus.bin")
    param_path = os.path.join(models_dir, "realesrgan-x4plus.param")
    assert os.path.isfile(bin_path), f"Binary weights missing at {bin_path}"
    assert os.path.isfile(param_path), f"Param file missing at {param_path}"

def test_real_inference_output(requires_ncnn):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe_path, _ = get_ncnn_paths()
    in_path = os.path.join(root, "tests", "fixtures", "test_input.png")
    out_path = os.path.join(root, "storage", "outputs", "test_output_4x.png")
    
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
    
    if os.path.isfile(out_path):
        try:
            os.remove(out_path)
        except OSError:
            pass

