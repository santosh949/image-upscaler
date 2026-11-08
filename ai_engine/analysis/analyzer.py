import os
import math
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any

class ImageAnalyzer:
    """Analyzes image degradation signals (blur, noise, JPEG artifacts) and category."""

    def analyze(self, image_path: str) -> Dict[str, Any]:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        with Image.open(image_path) as pil_img:
            width, height = pil_img.size
            format_name = pil_img.format or "UNKNOWN"
            has_alpha = "A" in pil_img.getbands()
            q_tables = getattr(pil_img, "quantization", None)

            # Convert to numpy array for CV2 analysis
            rgb_arr = np.array(pil_img.convert("RGB"))

        gray = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2GRAY)

        # 1. Blur Estimation (Normalized Laplacian Variance)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        # Scale-aware normalization
        norm_factor = max(1.0, math.sqrt(width * height) / 512.0)
        norm_blur_score = round(laplacian_var / (norm_factor ** 2), 2)
        is_blurry = norm_blur_score < 100.0

        # 2. Noise Estimation (MAD of high-frequency Laplacian)
        # Immerkaer fast noise standard deviation estimator
        h, w = gray.shape
        if h > 4 and w > 4:
            kernel = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
            filtered = cv2.filter2D(gray.astype(np.float64), -1, kernel)
            sigma = float(np.sum(np.abs(filtered)) * math.sqrt(0.5 * math.pi) / (6 * (w - 2) * (h - 2)))
            noise_sigma = round(sigma, 2)
        else:
            noise_sigma = 0.0
        has_high_noise = noise_sigma > 4.5

        # 3. JPEG Quality Estimate
        jpeg_quality = None
        if q_tables and 0 in q_tables:
            # Average luminance quantization value
            avg_q = float(np.mean(q_tables[0]))
            # Standard IJG JPEG quality scaling approximation
            if avg_q <= 1:
                jpeg_quality = 100
            elif avg_q >= 50:
                jpeg_quality = max(1, int(round(5000.0 / (avg_q * 2))))
            else:
                jpeg_quality = min(99, int(round(100 - avg_q)))
        else:
            # Check 8x8 grid boundary discontinuity
            if h >= 16 and w >= 16:
                row_a = gray[7::8, :]
                row_b = gray[8::8, :]
                min_len = min(len(row_a), len(row_b))
                if min_len > 0:
                    diff_v = np.abs(row_a[:min_len].astype(float) - row_b[:min_len].astype(float))
                    non_a = gray[3::8, :]
                    non_b = gray[4::8, :]
                    min_non = min(len(non_a), len(non_b), min_len)
                    non_grid_v = np.abs(non_a[:min_non].astype(float) - non_b[:min_non].astype(float))
                    blockiness = float(np.mean(diff_v[:min_non]) / max(0.1, np.mean(non_grid_v)))
                    jpeg_quality = max(20, min(95, int(round(100 - (blockiness - 1.0) * 50))))
                else:
                    jpeg_quality = 90
            else:
                jpeg_quality = 90

        # 4. Category Classification Heuristics (Manga / Anime / Photo)
        hsv = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2HSV)
        sat = hsv[:, :, 1]
        mean_saturation = float(np.mean(sat)) / 255.0

        # Edge statistics: sharp outlines and high contrast transitions
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.mean(edges > 0))

        # Palette count in quantized space
        colors_sampled = len(np.unique(gray // 16))

        # Luminance distribution checks for black-and-white manga / line art
        dark_ratio = float(np.mean(gray < 60))
        bright_ratio = float(np.mean(gray > 200))
        is_bimodal = (dark_ratio > 0.02 and bright_ratio > 0.35)

        if mean_saturation < 0.10 and is_bimodal and edge_density > 0.015:
            # Monochrome / Grayscale Manga & Line Art
            detected_category = "manga"
            cat_confidence = min(0.96, round(0.70 + (1.0 - mean_saturation) * 0.25, 2))
        elif mean_saturation > 0.25 and colors_sampled < 14 and edge_density > 0.02:
            # Color Anime / Digital Illustration
            detected_category = "anime"
            cat_confidence = min(0.95, round(0.60 + mean_saturation * 0.30, 2))
        else:
            # Natural Photo / Complex continuous tone
            detected_category = "photo"
            cat_confidence = min(0.90, round(0.55 + max(0.0, 0.5 - abs(mean_saturation - 0.3)) * 0.35, 2))

        return {
            "width": width,
            "height": height,
            "format": format_name,
            "has_alpha": has_alpha,
            "laplacian_variance": round(laplacian_var, 1),
            "estimated_blur_score": norm_blur_score,
            "is_blurry": is_blurry,
            "estimated_noise_sigma": noise_sigma,
            "has_high_noise": has_high_noise,
            "jpeg_quality_estimate": jpeg_quality,
            "detected_category": detected_category,
            "category_confidence": cat_confidence,
            "mean_saturation": round(mean_saturation, 3),
            "edge_density": round(edge_density, 4)
        }

analyzer = ImageAnalyzer()
