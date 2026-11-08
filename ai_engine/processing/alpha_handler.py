import numpy as np
import cv2
from PIL import Image
from typing import Tuple

class AlphaHandler:
    """
    Handles transparent PNG alpha channels per PRD Section 7.5:
    - Bleeds RGB outward under transparent pixels before upscaling to prevent dark/white halo fringes.
    - Upscales alpha channel separately using high-fidelity Lanczos resampling.
    - Recombines RGB and alpha without loss or flattening.
    """

    @staticmethod
    def has_transparency(img: Image.Image) -> bool:
        if img.mode != "RGBA":
            return False
        alpha = np.array(img.split()[3])
        return bool(np.any(alpha < 255))

    @classmethod
    def prepare_rgb_and_alpha(cls, img: Image.Image) -> Tuple[Image.Image, Image.Image, bool]:
        """
        Splits image into bled RGB and raw Alpha channel.
        If no alpha exists, returns (RGB, None, False).
        """
        if not cls.has_transparency(img):
            return img.convert("RGB"), None, False

        rgba = img.convert("RGBA")
        r, g, b, a = rgba.split()
        alpha_arr = np.array(a, dtype=np.uint8)
        rgb_arr = np.array(Image.merge("RGB", (r, g, b)), dtype=np.uint8)

        # Inpainting mask: 255 where transparent (to be filled), 0 where opaque
        inpaint_mask = (alpha_arr == 0).astype(np.uint8) * 255

        # If image is completely transparent, return as is
        if np.all(inpaint_mask == 255):
            return Image.fromarray(rgb_arr, mode="RGB"), a, True

        # Fast color bleeding outward into zero-alpha pixels
        # cv2.inpaint expects BGR format
        bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        bled_bgr = cv2.inpaint(bgr, inpaint_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        bled_rgb = cv2.cvtColor(bled_bgr, cv2.COLOR_BGR2RGB)

        return Image.fromarray(bled_rgb, mode="RGB"), a, True

    @classmethod
    def recombine(cls, rgb_img: Image.Image, alpha_img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Upscales alpha channel with Lanczos resampling and recombines with RGB.
        """
        target_w, target_h = target_size
        rgb = rgb_img.convert("RGB")
        if rgb.size != (target_w, target_h):
            rgb = rgb.resize((target_w, target_h), Image.Resampling.LANCZOS)

        alpha_upscaled = alpha_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        r, g, b = rgb.split()
        return Image.merge("RGBA", (r, g, b, alpha_upscaled))

    @classmethod
    def restore_alpha(cls, rgb_img: Image.Image, alpha_channel: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Restores alpha channel scaled to target dimensions."""
        return cls.recombine(rgb_img, alpha_channel, (target_w, target_h))

