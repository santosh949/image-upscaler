import os
import math
import numpy as np
from PIL import Image
from typing import Callable, Optional, Tuple, Dict, Any, List

class JobPausedException(Exception):
    """Raised when job is paused by user to save intermediate checkpoint."""
    pass

class TileEngine:
    """
    Seamless tiled inference engine with feathered blending and OOM recovery.
    Enforces maximum output pixel cap (100 MP) per PRD Section 4.1.
    Supports Per-Tile Scale Adaptation (Part F4 & ADR 005) and TileStore checkpoints.
    """

    def __init__(self, default_tile_size: int = 256, overlap: int = 32, max_output_mp: int = 100):
        self.default_tile_size = default_tile_size
        self.overlap = max(16, overlap)
        self.max_output_mp = max_output_mp

    @staticmethod
    def make_1d_feather_window(length: int, is_start_edge: bool, is_end_edge: bool, overlap: int) -> np.ndarray:
        """
        Creates a 1D blending window with cosine feathered transitions at overlap borders.
        Edges touching the true image boundary remain 1.0 to avoid boundary attenuation.
        """
        w = np.ones(length, dtype=np.float32)
        ramp_len = min(overlap, length // 2)
        if ramp_len <= 0:
            return w

        # Raised cosine ramp from 0 to 1: 0.5 * (1 - cos(pi * t))
        t = np.linspace(0, np.pi, ramp_len, endpoint=False, dtype=np.float32)
        ramp = 0.5 * (1.0 - np.cos(t))

        if not is_start_edge:
            w[:ramp_len] = ramp
        if not is_end_edge:
            w[-ramp_len:] = ramp[::-1]

        return w

    def compute_feather_window(
        self,
        height: int,
        width: int,
        is_top: bool,
        is_bottom: bool,
        is_left: bool,
        is_right: bool,
        overlap: int
    ) -> np.ndarray:
        """Computes a 2D feathered blending mask for a tile."""
        wy = self.make_1d_feather_window(height, is_top, is_bottom, overlap)
        wx = self.make_1d_feather_window(width, is_left, is_right, overlap)
        w2d = np.outer(wy, wx).astype(np.float32)
        return w2d

    def generate_tile_grid(
        self,
        img_w: int,
        img_h: int,
        tile_size: int,
        overlap: int
    ) -> List[Dict[str, Any]]:
        """
        Computes deterministic tile coordinates and boundary flags.
        """
        step = max(16, tile_size - overlap)

        x_coords = []
        cur_x = 0
        while cur_x < img_w:
            x_coords.append(cur_x)
            if cur_x + tile_size >= img_w:
                break
            cur_x += step
        if x_coords[-1] + tile_size < img_w:
            x_coords.append(max(0, img_w - tile_size))
        x_coords = sorted(list(set(x_coords)))

        y_coords = []
        cur_y = 0
        while cur_y < img_h:
            y_coords.append(cur_y)
            if cur_y + tile_size >= img_h:
                break
            cur_y += step
        if y_coords[-1] + tile_size < img_h:
            y_coords.append(max(0, img_h - tile_size))
        y_coords = sorted(list(set(y_coords)))

        tiles = []
        for gy, y in enumerate(y_coords):
            y2 = min(img_h, y + tile_size)
            is_top = (y == 0)
            is_bottom = (y2 == img_h)
            for gx, x in enumerate(x_coords):
                x2 = min(img_w, x + tile_size)
                is_left = (x == 0)
                is_right = (x2 == img_w)
                tiles.append({
                    "box": (x, y, x2, y2),
                    "gx": gx,
                    "gy": gy,
                    "is_top": is_top,
                    "is_bottom": is_bottom,
                    "is_left": is_left,
                    "is_right": is_right,
                })
        return tiles

    def process(
        self,
        img: Image.Image,
        infer_fn: Callable[[Image.Image], Image.Image],
        scale: int = 4,
        target_scale: Optional[float] = None,
        tile_size: Optional[int] = None,
        overlap: Optional[int] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        pause_check: Optional[Callable[[], bool]] = None,
        tile_store: Optional[Any] = None,
        stage_id: Optional[str] = None,
        auto_oom_retry: bool = True
    ) -> Image.Image:
        """
        Splits image into overlapping tiles, processes each with infer_fn,
        and seamlessly stitches them with cosine feathered blending.
        Supports target_scale (Per-Tile Scale Adaptation) and TileStore checkpoints.
        """
        tile_sz = tile_size or self.default_tile_size
        ovlp = overlap or self.overlap
        eff_scale = float(target_scale) if target_scale is not None else float(scale)

        in_w, in_h = img.size
        out_w = int(round(in_w * eff_scale))
        out_h = int(round(in_h * eff_scale))
        out_mp = (out_w * out_h) / 1_000_000.0

        if out_mp > self.max_output_mp:
            raise ValueError(
                f"Output image size ({out_w}x{out_h} = {out_mp:.1f} MP) exceeds "
                f"maximum allowed limit of {self.max_output_mp} MP."
            )

        # Direct execution if image is already smaller than tile size and no tile store checkpointing requested
        if in_w <= tile_sz and in_h <= tile_sz and not tile_store:
            if cancel_check and cancel_check():
                raise RuntimeError("Job cancelled by user")
            if pause_check and pause_check():
                raise JobPausedException("Job paused by user")
            res = infer_fn(img)
            if eff_scale != float(scale) or res.size != (out_w, out_h):
                res = res.resize((out_w, out_h), Image.Resampling.LANCZOS)
            if progress_cb:
                progress_cb(1, 1)
            return res

        try:
            return self._execute_tiling(
                img=img,
                infer_fn=infer_fn,
                scale=scale,
                target_scale=target_scale,
                tile_size=tile_sz,
                overlap=ovlp,
                progress_cb=progress_cb,
                cancel_check=cancel_check,
                pause_check=pause_check,
                tile_store=tile_store,
                stage_id=stage_id
            )
        except JobPausedException:
            raise
        except Exception as e:
            err_msg = str(e).lower()
            if "cancelled" in err_msg:
                raise
            is_oom = "out of memory" in err_msg or "oom" in err_msg or "memory" in err_msg
            if auto_oom_retry and is_oom and tile_sz > 128:
                new_tile_sz = max(128, tile_sz // 2)
                new_ovlp = max(16, ovlp // 2)
                return self.process(
                    img=img,
                    infer_fn=infer_fn,
                    scale=scale,
                    target_scale=target_scale,
                    tile_size=new_tile_sz,
                    overlap=new_ovlp,
                    progress_cb=progress_cb,
                    cancel_check=cancel_check,
                    pause_check=pause_check,
                    tile_store=tile_store,
                    stage_id=stage_id,
                    auto_oom_retry=True
                )
            raise e

    def _execute_tiling(
        self,
        img: Image.Image,
        infer_fn: Callable[[Image.Image], Image.Image],
        scale: int,
        target_scale: Optional[float],
        tile_size: int,
        overlap: int,
        progress_cb: Optional[Callable[[int, int], None]],
        cancel_check: Optional[Callable[[], bool]],
        pause_check: Optional[Callable[[], bool]] = None,
        tile_store: Optional[Any] = None,
        stage_id: Optional[str] = None
    ) -> Image.Image:
        in_w, in_h = img.size
        eff_scale = float(target_scale) if target_scale is not None else float(scale)
        out_w = int(round(in_w * eff_scale))
        out_h = int(round(in_h * eff_scale))

        tiles = self.generate_tile_grid(in_w, in_h, tile_size, overlap)
        total_tiles = len(tiles)

        # Mode handling (RGB or RGBA)
        has_alpha = (img.mode == "RGBA")
        num_channels = 4 if has_alpha else 3
        accum = np.zeros((out_h, out_w, num_channels), dtype=np.float32)
        weights = np.zeros((out_h, out_w, 1), dtype=np.float32)

        out_overlap = int(round(overlap * eff_scale))

        # Check existing cached/checkpoint tiles
        completed_tiles = {}
        if tile_store and stage_id:
            completed_tiles = tile_store.get_completed_tiles(stage_id)

        for idx, t in enumerate(tiles):
            if cancel_check and cancel_check():
                raise RuntimeError("Job cancelled by user")
            if pause_check and pause_check():
                raise JobPausedException("Job paused by user")

            gx, gy = t["gx"], t["gy"]
            x1, y1, x2, y2 = t["box"]

            exp_tw = int(round((x2 - x1) * eff_scale))
            exp_th = int(round((y2 - y1) * eff_scale))
            ox1 = int(round(x1 * eff_scale))
            oy1 = int(round(y1 * eff_scale))
            ox2 = min(out_w, ox1 + exp_tw)
            oy2 = min(out_h, oy1 + exp_th)
            act_w = ox2 - ox1
            act_h = oy2 - oy1

            if (gx, gy) in completed_tiles:
                tile_out = tile_store.load_tile(completed_tiles[(gx, gy)])
            else:
                tile_in = img.crop((x1, y1, x2, y2))
                # Execute model on tile
                tile_out = infer_fn(tile_in)

                # Ensure expected adapted dimensions (Per-Tile Scale Adaptation)
                if tile_out.size != (exp_tw, exp_th):
                    tile_out = tile_out.resize((exp_tw, exp_th), Image.Resampling.LANCZOS)

                if tile_store and stage_id:
                    tile_store.save_tile(stage_id, gx, gy, tile_out)

            # Crop if slightly exceeding boundary due to rounding
            if tile_out.size != (act_w, act_h):
                tile_out = tile_out.crop((0, 0, act_w, act_h))

            tile_arr = np.array(tile_out, dtype=np.float32)
            if tile_arr.ndim == 2:
                tile_arr = np.stack([tile_arr] * num_channels, axis=-1)
            elif tile_arr.shape[2] != num_channels:
                if num_channels == 3 and tile_arr.shape[2] == 4:
                    tile_arr = tile_arr[:, :, :3]
                elif num_channels == 4 and tile_arr.shape[2] == 3:
                    alpha = np.full((act_h, act_w, 1), 255.0, dtype=np.float32)
                    tile_arr = np.concatenate([tile_arr, alpha], axis=-1)

            # Compute feathered mask for this tile
            w2d = self.compute_feather_window(
                height=act_h,
                width=act_w,
                is_top=t["is_top"],
                is_bottom=t["is_bottom"],
                is_left=t["is_left"],
                is_right=t["is_right"],
                overlap=out_overlap
            )[:, :, None]

            accum[oy1:oy2, ox1:ox2] += (tile_arr * w2d)
            weights[oy1:oy2, ox1:ox2] += w2d

            if progress_cb:
                progress_cb(idx + 1, total_tiles)

        # Normalize and construct final output
        norm_result = accum / np.maximum(weights, 1e-6)
        final_arr = np.clip(norm_result, 0, 255).astype(np.uint8)

        if has_alpha:
            return Image.fromarray(final_arr, mode="RGBA")
        return Image.fromarray(final_arr, mode="RGB")
