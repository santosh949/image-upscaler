import numpy as np
from PIL import Image

class MangaEnhancer:
    """
    Specialized post-processing filter for manga, inking, and black-and-white comic art.
    - Eliminates JPEG compression ringing on paper backgrounds.
    - Deepens ink lines without crushing fine screentone dots in midtones.
    - Suppresses chromatic aberration / color fringing on black borders.
    """

    @classmethod
    def enhance_manga_lines(cls, img: Image.Image, clean_paper: bool = True, deep_black: bool = True) -> Image.Image:
        arr = np.array(img, dtype=np.float32)
        has_alpha = (arr.shape[2] == 4) if arr.ndim == 3 else False
        rgb = arr[:, :, :3] if has_alpha else arr

        # Check if predominantly monochrome (B&W manga)
        if rgb.ndim == 3:
            channel_diff = np.max(np.abs(rgb[:, :, 0] - rgb[:, :, 1])) + np.max(np.abs(rgb[:, :, 1] - rgb[:, :, 2]))
            is_monochrome = (channel_diff < 15.0) or (np.std(rgb[:, :, 0] - rgb[:, :, 1]) < 3.0)
        else:
            is_monochrome = True

        if is_monochrome and rgb.ndim == 3:
            # Desaturate subtle JPEG compression color fringes along high-contrast ink edges
            gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
            # Replace RGB with gray for pure monochrome cleanliness
            rgb[:, :, 0] = gray
            rgb[:, :, 1] = gray
            rgb[:, :, 2] = gray

        # Paper whitening: pixels very close to white (>238) smoothly mapped to 255
        if clean_paper:
            white_mask = (rgb > 235.0)
            white_factor = np.clip((rgb - 235.0) / 20.0, 0.0, 1.0)
            # Smooth ramp to 255
            rgb = np.where(white_mask, rgb + (255.0 - rgb) * white_factor, rgb)

        # Deep black reinforcement: pixels very close to black (<30) smoothly snapped to 0
        if deep_black:
            black_mask = (rgb < 35.0)
            black_factor = np.clip((35.0 - rgb) / 35.0, 0.0, 1.0)
            rgb = np.where(black_mask, rgb * (1.0 - black_factor), rgb)

        rgb = np.clip(rgb, 0.0, 255.0).astype(np.uint8)

        if has_alpha:
            out_arr = np.dstack([rgb, arr[:, :, 3].astype(np.uint8)])
            return Image.fromarray(out_arr, mode="RGBA")
        return Image.fromarray(rgb, mode="RGB")

