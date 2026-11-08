import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, Optional

class RestorationEngine:
    """
    Classical and adaptive low-resolution image restoration filter suite.
    Applies edge-preserving artifact suppression, adaptive denoising,
    and conservative detail recovery without hallucination.
    """

    @staticmethod
    def deblock_jpeg(img_arr: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        Suppresses 8x8 DCT grid artifacts while preserving real high-contrast edges
        using edge-preserving bilateral filtering.
        """
        d = int(5 * max(0.5, strength))
        sigma_color = 25.0 * strength
        sigma_space = 25.0 * strength
        return cv2.bilateralFilter(img_arr, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)

    @staticmethod
    def denoise_adaptive(img_arr: np.ndarray, noise_score: float = 5.0) -> np.ndarray:
        """
        Applies adaptive denoising scaled by the estimated noise level from the degradation analyzer.
        """
        h = max(2.0, min(12.0, noise_score * 0.4))
        # fastNlMeansDenoisingColored on BGR
        bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
        denoised_bgr = cv2.fastNlMeansDenoisingColored(
            bgr,
            None,
            h=h,
            hColor=h,
            templateWindowSize=7,
            searchWindowSize=15
        )
        return cv2.cvtColor(denoised_bgr, cv2.COLOR_BGR2RGB)

    @staticmethod
    def mild_unsharp_mask(img_arr: np.ndarray, amount: float = 0.5, radius: float = 1.0) -> np.ndarray:
        """
        Conservative unsharp mask that enhances local micro-contrast without haloing or clipping.
        """
        blurred = cv2.GaussianBlur(img_arr, (0, 0), radius)
        sharpened = float(1.0 + amount) * img_arr - float(amount) * blurred
        return np.clip(sharpened, 0, 255).astype(np.uint8)

    @classmethod
    def restore(
        cls,
        img: Image.Image,
        noise_score: float = 0.0,
        has_jpeg_artifacts: bool = False,
        apply_sharpen: bool = False,
        sharpen_amount: float = 0.30
    ) -> Image.Image:
        """
        Full restoration pipeline on RGB image.
        Adaptive to degradation signals: skips denoising when noise_score <= 0
        to preserve natural human skin texture, pores, and fine hair strands.
        """
        rgb = img.convert("RGB")
        arr = np.array(rgb, dtype=np.uint8)

        # 1. Deblock if JPEG compression was detected
        if has_jpeg_artifacts:
            arr = cls.deblock_jpeg(arr, strength=0.8)

        # 2. Adaptive denoise ONLY when noise is detected (> 1.0)
        if noise_score > 1.0:
            arr = cls.denoise_adaptive(arr, noise_score=noise_score)

        # 3. Restrained unsharp mask
        if apply_sharpen:
            arr = cls.mild_unsharp_mask(arr, amount=sharpen_amount, radius=0.8)

        return Image.fromarray(arr, mode="RGB")

