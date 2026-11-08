import os
import sys
import time
import subprocess
from PIL import Image

def run_test_upscale(input_path: str, output_path: str, gpu_id: int = 0) -> bool:
    exe_path = os.path.abspath(r"tools\realesrgan-ncnn-vulkan\realesrgan-ncnn-vulkan.exe")
    models_dir = os.path.abspath(r"tools\realesrgan-ncnn-vulkan\models")
    
    if not os.path.isfile(exe_path):
        print(f"ERROR: Executable not found at {exe_path}")
        return False

    if not os.path.isfile(input_path):
        print(f"ERROR: Input image not found at {input_path}")
        return False

    input_img = Image.open(input_path)
    in_w, in_h = input_img.size
    print(f"Input image: {input_path} ({in_w}x{in_h})")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if os.path.exists(output_path):
        os.remove(output_path)

    cmd = [
        exe_path,
        "-i", os.path.abspath(input_path),
        "-o", os.path.abspath(output_path),
        "-m", models_dir,
        "-n", "realesrgan-x4plus",
        "-s", "4",
        "-g", str(gpu_id),
        "-v"
    ]

    print(f"Executing command: {' '.join(cmd)}")
    start_time = time.perf_counter()
    res = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - start_time

    if res.returncode != 0:
        print(f"ERROR: Process exited with code {res.returncode}")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        return False

    if not os.path.isfile(output_path):
        print(f"ERROR: Output file was not generated: {output_path}")
        return False

    out_img = Image.open(output_path)
    out_w, out_h = out_img.size
    file_size_kb = os.path.getsize(output_path) / 1024

    print(f"Inference SUCCESS!")
    print(f"Backend: NCNN Vulkan (realesrgan-ncnn-vulkan)")
    print(f"Model: realesrgan-x4plus (Scale: 4x)")
    print(f"Target GPU Device: Vulkan Device {gpu_id} (NVIDIA GeForce RTX 2050)")
    print(f"Input dimensions: {in_w}x{in_h}")
    print(f"Output dimensions: {out_w}x{out_h} (Expected: {in_w*4}x{in_h*4})")
    print(f"Output file size: {file_size_kb:.2f} KB")
    print(f"Inference wall-clock time: {elapsed:.3f} s")

    # Assert dimension correctness
    assert out_w == in_w * 4, f"Width mismatch: {out_w} != {in_w * 4}"
    assert out_h == in_h * 4, f"Height mismatch: {out_h} != {in_h * 4}"
    return True

if __name__ == "__main__":
    in_file = r"tests\fixtures\test_input.png"
    out_file = r"storage\outputs\test_output_4x.png"
    success = run_test_upscale(in_file, out_file, gpu_id=0)
    sys.exit(0 if success else 1)

