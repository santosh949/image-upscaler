import os
import sys
import time
import json
import numpy as np
from PIL import Image
import cv2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.processing.consistency import ConsistencyChecker

def run_tuning():
    print("=== Running Phase 4 Model Tuning & Comparison ===")
    adapter = NCNNRealESRGANAdapter()
    gpu_id = adapter.get_nvidia_device_id()
    devs = adapter.get_vulkan_devices()
    print(f"Device: {devs.get(gpu_id)} (ID: {gpu_id})")

    out_dir = os.path.join(REPO_ROOT, "storage", "tuning_benchmarks")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Manga benchmark test
    manga_path = os.path.join(REPO_ROOT, "storage", "uploads", "e089f67f-b36a-4c5b-9c58-5bdb60f4a15f.webp")
    if not os.path.isfile(manga_path):
        manga_path = os.path.join(REPO_ROOT, "storage", "uploads", "5897927f-f571-45f8-b369-8aa7c255b586.webp")

    img_manga = Image.open(manga_path).convert("RGB")
    m_w, m_h = img_manga.size
    print(f"Manga image: {manga_path} ({m_w}x{m_h})")

    temp_in = os.path.join(out_dir, "manga_in.png")
    img_manga.save(temp_in)

    # Test 1A: realesrgan-x4plus-anime
    out_x4plus_anime = os.path.join(out_dir, "manga_x4plus_anime.png")
    t0 = time.perf_counter()
    res_x4plus = adapter.enhance(temp_in, out_x4plus_anime, scale=4, gpu_id=gpu_id, model_name="realesrgan-x4plus-anime")
    rt_x4plus = time.perf_counter() - t0
    img_out_x4plus = Image.open(out_x4plus_anime)

    # Test 1B: realesr-animevideov3-x4
    out_v3_anime = os.path.join(out_dir, "manga_animevideov3.png")
    t0 = time.perf_counter()
    res_v3 = adapter.enhance(temp_in, out_v3_anime, scale=4, gpu_id=gpu_id, model_name="realesr-animevideov3-x4")
    rt_v3 = time.perf_counter() - t0
    img_out_v3 = Image.open(out_v3_anime)

    # Calculate metrics on manga outputs
    # Line sharpness (Laplacian variance) & moiré / noise
    gray_x4plus = cv2.cvtColor(np.array(img_out_x4plus), cv2.COLOR_RGB2GRAY)
    gray_v3 = cv2.cvtColor(np.array(img_out_v3), cv2.COLOR_RGB2GRAY)

    lap_x4plus = cv2.Laplacian(gray_x4plus, cv2.CV_64F).var()
    lap_v3 = cv2.Laplacian(gray_v3, cv2.CV_64F).var()

    std_x4plus = np.std(gray_x4plus)
    std_v3 = np.std(gray_v3)

    # Consistency with original
    c_x4plus = ConsistencyChecker.evaluate(img_manga, img_out_x4plus)
    c_v3 = ConsistencyChecker.evaluate(img_manga, img_out_v3)

    print("\n--- Manga Model Comparison Results ---")
    print(f"realesrgan-x4plus-anime:  Runtime: {rt_x4plus:.3f}s | LapVar (Line Sharpness): {lap_x4plus:.1f} | PSNR: {c_x4plus['psnr_db']} dB | MAE: {c_x4plus['mae']}")
    print(f"realesr-animevideov3-x4: Runtime: {rt_v3:.3f}s | LapVar (Line Sharpness): {lap_v3:.1f} | PSNR: {c_v3['psnr_db']} dB | MAE: {c_v3['mae']}")

    # Save summary
    results = {
        "manga_input": {"path": manga_path, "size": [m_w, m_h]},
        "realesrgan-x4plus-anime": {
            "runtime_s": round(rt_x4plus, 3),
            "laplacian_var": round(lap_x4plus, 1),
            "noise_std": round(float(std_x4plus), 2),
            "psnr_db": c_x4plus['psnr_db'],
            "mae": c_x4plus['mae']
        },
        "realesr-animevideov3-x4": {
            "runtime_s": round(rt_v3, 3),
            "laplacian_var": round(lap_v3, 1),
            "noise_std": round(float(std_v3), 2),
            "psnr_db": c_v3['psnr_db'],
            "mae": c_v3['mae']
        }
    }

    with open(os.path.join(out_dir, "manga_tuning_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    if os.path.exists(temp_in):
        os.remove(temp_in)

    print(f"Tuning results written to {out_dir}/manga_tuning_results.json")

if __name__ == "__main__":
    run_tuning()
