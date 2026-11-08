import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional, Tuple

class MangaOutlineEngine:
    """
    Precision Edge Steepening, Inking, and Paper Purification Engine for Manga & Anime.
    
    Pillars:
    1. Sub-pixel non-linear edge normal steepening (transforms soft 2-3px gradient ramps into crisp 1px ink lines).
    2. Zero-halo bounded profile mapping (guarantees zero ringing or white halo spikes).
    3. Screentone & halftone frequency protection (prevents shading dots from turning into gray mud).
    4. Paper purification (eliminates scanner haze / JPEG mosquito noise from white background).
    5. Deep black ink reinforcement (snaps core strokes to rich black).
    6. Chromatic aberration neutralization (eliminates color fringing along black borders).
    """

    @classmethod
    def process(
        cls,
        img: Image.Image,
        strength: float = 1.0,
        clean_paper: bool = True,
        deep_ink: bool = True,
        protect_screentones: bool = True,
        neutralize_chromatic: bool = True
    ) -> Image.Image:
        """
        Enhances character outlines and clean inking.
        strength: 0.0 (off) to 1.5 (maximum razor sharpness)
        """
        if strength <= 0.0:
            return img

        arr = np.array(img)
        has_alpha = (arr.ndim == 3 and arr.shape[2] == 4)
        if has_alpha:
            alpha = arr[:, :, 3]
            rgb = arr[:, :, :3].astype(np.float32)
        elif arr.ndim == 3:
            rgb = arr.astype(np.float32)
            alpha = None
        else:
            # 2D grayscale
            rgb = np.repeat(arr[:, :, np.newaxis], 3, axis=2).astype(np.float32)
            alpha = None

        # Calculate luminance (Rec. 601)
        lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]

        # 1. Detect if predominantly monochrome (B&W Manga)
        diff_rg = np.abs(rgb[:, :, 0] - rgb[:, :, 1])
        diff_gb = np.abs(rgb[:, :, 1] - rgb[:, :, 2])
        is_monochrome = (np.mean(diff_rg) + np.mean(diff_gb)) < 10.0

        if is_monochrome and neutralize_chromatic:
            # Desaturate subtle JPEG chromatic fringes on high-contrast edges
            rgb[:, :, 0] = lum
            rgb[:, :, 1] = lum
            rgb[:, :, 2] = lum

        # 2. Screentone Frequency Protection Mask
        # Screentones feature high localized variance with low macro-scale gradient
        screentone_mask = np.zeros_like(lum, dtype=np.float32)
        if protect_screentones:
            # Local variance in 3x3 window: Var = E[X^2] - (E[X])^2
            mean_l = cv2.blur(lum, (3, 3))
            mean_sq = cv2.blur(lum ** 2, (3, 3))
            local_std = np.sqrt(np.maximum(0.0, mean_sq - (mean_l ** 2)))

            # Macro gradient (smoothed)
            smooth_l = cv2.GaussianBlur(lum, (5, 5), 1.0)
            sobel_x = cv2.Sobel(smooth_l, cv2.CV_32F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(smooth_l, cv2.CV_32F, 0, 1, ksize=3)
            macro_grad = np.sqrt(sobel_x ** 2 + sobel_y ** 2)

            # Midtones with high local texture variance but low macro edge strength are screentones
            screentone_candidate = (
                (local_std > 8.0) &
                (macro_grad < 25.0) &
                (lum >= 50.0) &
                (lum <= 220.0)
            )
            # Dilate slightly to form a protective envelope
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            screentone_mask = cv2.dilate(screentone_candidate.astype(np.float32), kernel)

        # 3. Non-Linear Edge Normal Steepening (Zero-Halo Bounded Remap)
        # Compute localized min and max in an isotropic 5x5 window
        struct_elem = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        local_min = cv2.erode(lum, struct_elem)
        local_max = cv2.dilate(lum, struct_elem)
        local_range = local_max - local_min

        # Focus edge steepening strictly where true edges exist (range > 20)
        edge_weight = np.clip((local_range - 20.0) / 40.0, 0.0, 1.0)
        # Suppress edge steepening on protected screentones
        edge_weight = edge_weight * (1.0 - screentone_mask)

        # Non-linear sigmoid remap: transforms soft 2-3px gradient into crisp 1px ink boundary
        # Bounded between local_min and local_max -> guarantees ZERO overshoot halos
        norm_l = np.clip((lum - local_min) / np.maximum(local_range, 1e-5), 0.0, 1.0)
        k = 8.0 * strength
        steepened_norm = 1.0 / (1.0 + np.exp(-k * (norm_l - 0.5)))
        steepened_norm = (steepened_norm - (1.0 / (1.0 + np.exp(0.5 * k)))) / (
            (1.0 / (1.0 + np.exp(-0.5 * k))) - (1.0 / (1.0 + np.exp(0.5 * k)))
        )
        steepened_norm = np.clip(steepened_norm, 0.0, 1.0)
        steepened_l = local_min + local_range * steepened_norm

        # Blend steepened luminance according to edge weight
        blend_factor = float(np.clip(strength, 0.0, 1.0))
        enhanced_lum = lum * (1.0 - edge_weight * blend_factor) + steepened_l * (edge_weight * blend_factor)

        # 4. Paper Purification & Deep Black Reinforcement
        if clean_paper:
            # Whites > 232 pushed cleanly to 255 (eliminates dirty scanner haze & JPEG mosquito artifacts)
            white_thresh = 232.0
            white_mask = enhanced_lum > white_thresh
            white_ramp = np.clip((enhanced_lum - white_thresh) / (248.0 - white_thresh), 0.0, 1.0)
            enhanced_lum = np.where(white_mask, enhanced_lum + (255.0 - enhanced_lum) * white_ramp, enhanced_lum)

        if deep_ink:
            # Darks < 32 snapped cleanly to pure deep black (#000000)
            black_thresh = 32.0
            black_mask = enhanced_lum < black_thresh
            black_ramp = np.clip((black_thresh - enhanced_lum) / (black_thresh - 8.0), 0.0, 1.0)
            enhanced_lum = np.where(black_mask, enhanced_lum * (1.0 - black_ramp), enhanced_lum)

        # Re-apply enhanced luminance to RGB channels
        enhanced_lum = np.clip(enhanced_lum, 0.0, 255.0)
        lum_ratio = (enhanced_lum + 1e-4) / (lum + 1e-4)
        if is_monochrome:
            out_rgb = np.repeat(enhanced_lum[:, :, np.newaxis], 3, axis=2)
        else:
            out_rgb = np.clip(rgb * lum_ratio[:, :, np.newaxis], 0.0, 255.0)

        out_arr = out_rgb.astype(np.uint8)
        if has_alpha and alpha is not None:
            out_arr = np.dstack([out_arr, alpha.astype(np.uint8)])
            return Image.fromarray(out_arr, mode="RGBA")
        return Image.fromarray(out_arr, mode="RGB")
