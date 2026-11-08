import os
import sys
sys.path.insert(0, os.path.abspath("."))
import cv2
import numpy as np
from PIL import Image
from ai_engine.pipelines.pipeline import pipeline

input_path = "storage/uploads/9446774f-615d-43f0-917a-436a317ba0ff.webp"
v2_path = "storage/outputs/2bc02f7f-ef49-46d0-91c8-5c717851c7ce_x4.png"
out_master_path = "storage/outputs/gon_manga_master_x4.png"

print(f"Testing Manga Master outline enhancement...")
print(f"Input: {input_path}")
img = Image.open(input_path)
print(f"Input dimensions: {img.size}")

# 1. Run pipeline with manga_crisp preset
res = pipeline.run(
    input_path=input_path,
    output_path=out_master_path,
    mode="upscale",
    model_name="realesrgan-x4plus-anime",
    scale=4,
    preset="manga_crisp"
)
print("Pipeline result:", res)

# 2. Analyze image metrics
master_img = cv2.imread(out_master_path, cv2.IMREAD_GRAYSCALE)
sobel_x = cv2.Sobel(master_img, cv2.CV_32F, 1, 0, ksize=3)
sobel_y = cv2.Sobel(master_img, cv2.CV_32F, 0, 1, ksize=3)
grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)

print("\n--- METRICS EVALUATION ---")
print(f"Dimensions: {master_img.shape[1]}x{master_img.shape[0]}")
print(f"Stages: {res.get('stages')}")
print(f"Max Edge Gradient (Steepness): {np.max(grad_mag):.2f}")
print(f"95th percentile Edge Gradient: {np.percentile(grad_mag, 95):.2f}")
print(f"White background pixels (>250): {np.sum(master_img >= 250) / master_img.size * 100:.2f}%")
print(f"Black ink pixels (<15): {np.sum(master_img <= 15) / master_img.size * 100:.2f}%")

if os.path.exists(v2_path):
    v2_img = cv2.imread(v2_path, cv2.IMREAD_GRAYSCALE)
    v2_sobel_x = cv2.Sobel(v2_img, cv2.CV_32F, 1, 0, ksize=3)
    v2_sobel_y = cv2.Sobel(v2_img, cv2.CV_32F, 0, 1, ksize=3)
    v2_grad = np.sqrt(v2_sobel_x**2 + v2_sobel_y**2)
    print(f"\n--- COMPARISON WITH V2 BASELINE ---")
    print(f"V2 Max Gradient: {np.max(v2_grad):.2f} vs Master: {np.max(grad_mag):.2f}")
    print(f"V2 95th percentile Gradient: {np.percentile(v2_grad, 95):.2f} vs Master: {np.percentile(grad_mag, 95):.2f}")
    print(f"Edge steepness improvement: +{((np.percentile(grad_mag, 95) / np.percentile(v2_grad, 95)) - 1.0)*100:.2f}%")
