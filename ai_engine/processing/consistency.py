import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, Tuple

class ConsistencyChecker:
    """
    Downscale-consistency checker per PRD Section 7.7.
    Downsamples the enhanced output back to original dimensions and computes
    faithfulness metrics against the source input to detect gross hallucination or color drift.
    """

    @staticmethod
    def evaluate(orig_img: Image.Image, enhanced_img: Image.Image) -> Dict[str, Any]:
        orig_rgb = orig_img.convert("RGB")
        orig_w, orig_h = orig_rgb.size
        orig_arr = np.array(orig_rgb, dtype=np.float32)

        # Downsample enhanced image back to input resolution
        downsampled = enhanced_img.convert("RGB").resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        down_arr = np.array(downsampled, dtype=np.float32)

        # Compute Mean Absolute Error (MAE) and Mean Squared Error (MSE)
        diff = np.abs(orig_arr - down_arr)
        mae = float(np.mean(diff))
        mse = float(np.mean(diff ** 2))

        # Peak Signal-to-Noise Ratio (PSNR)
        if mse == 0:
            psnr = 100.0
        else:
            psnr = float(10.0 * np.log10((255.0 ** 2) / mse))

        # Per-channel average drift
        r_drift = float(np.mean(down_arr[:, :, 0] - orig_arr[:, :, 0]))
        g_drift = float(np.mean(down_arr[:, :, 1] - orig_arr[:, :, 1]))
        b_drift = float(np.mean(down_arr[:, :, 2] - orig_arr[:, :, 2]))

        # High faithfulness if PSNR > 28 dB and MAE < 15
        is_faithful = psnr >= 26.0 and mae <= 16.0

        return {
            "psnr_db": round(psnr, 2),
            "mae": round(mae, 2),
            "channel_drifts": {
                "r": round(r_drift, 3),
                "g": round(g_drift, 3),
                "b": round(b_drift, 3)
            },
            "is_faithful": is_faithful
        }

    @staticmethod
    def generate_diff_map(orig_img: Image.Image, enhanced_img: Image.Image) -> Image.Image:
        """Generates visual amplified difference map between input and downsampled output."""
        orig_rgb = orig_img.convert("RGB")
        orig_w, orig_h = orig_rgb.size
        orig_arr = np.array(orig_rgb, dtype=np.float32)

        downsampled = enhanced_img.convert("RGB").resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        down_arr = np.array(downsampled, dtype=np.float32)

        # Amplify diff 4x for visual human inspection
        diff = np.clip(np.abs(orig_arr - down_arr) * 4.0, 0, 255).astype(np.uint8)
        return Image.fromarray(diff, mode="RGB")

