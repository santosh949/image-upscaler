import shutil
import psutil
from typing import Dict, Any, Optional, Tuple

class ResourceEstimator:
    """
    Computes preflight resource estimates per Part C3, C4, and F5a:
    - Output megapixels & dimensions
    - Peak RAM estimate (distinguishing in-memory vs disk-streaming)
    - Peak VRAM estimate based on model & tile size
    - Temporary and final disk requirements (with 1.25x safety margin)
    - Estimated runtime based on measured baseline telemetry
    """

    MAX_INMEMORY_MP = 25.0   # Default conservative in-RAM limit (Part C3)
    MAX_OUTPUT_MP = 100.0    # Hard output limit on Profile A (Part C3)

    # Measured benchmarks on RTX 2050 (from benchmarks/BENCHMARK_RESULTS.md)
    # Output MP/s throughput
    THROUGHPUT_MAP = {
        "realesrgan-x4plus": 0.16,         # ~0.16 MP/s
        "realesrgan-x4plus-anime": 0.32,   # ~0.32 MP/s
        "realesr-animevideov3-x4": 0.39,   # ~0.39 MP/s
        "classical": 0.12                  # ~0.12 MP/s
    }

    @classmethod
    def estimate(
        cls,
        source_w: int,
        source_h: int,
        target_w: int,
        target_h: int,
        model_name: str = "realesrgan-x4plus",
        tile_size: int = 256,
        is_transparent: bool = False
    ) -> Dict[str, Any]:
        channels = 4 if is_transparent else 3
        out_mp = (target_w * target_h) / 1_000_000.0

        # Reference raw memory calculation (Part C4)
        raw_rgb8_mb = (target_w * target_h * channels) / (1024 * 1024)
        raw_float32_mb = (target_w * target_h * channels * 4) / (1024 * 1024)

        # Peak VRAM estimate (model weights + tile buffers)
        # NCNN models on 256 tile size require ~1.2 to 1.8 GB VRAM
        tile_vram_mb = 1200 if "anime" in model_name else 1600
        if tile_size > 256:
            tile_vram_mb += (tile_size - 256) * 2

        # Disk space calculation: tile store + intermediate + output + preview
        # intermediate ~ raw_rgb8 * 1.2, output ~ raw_rgb8 * 0.8
        est_disk_bytes = int((raw_rgb8_mb * 2.5) * (1024 * 1024))
        required_disk_with_margin = int(est_disk_bytes * 1.25)

        # Query system free memory & disk
        ram = psutil.virtual_memory()
        free_ram_mb = ram.available / (1024 * 1024)

        # Runtime estimation
        throughput = cls.THROUGHPUT_MAP.get(model_name, 0.15)
        est_seconds = round(out_mp / max(0.01, throughput), 1)

        # Safety checks
        can_fit_in_memory = out_mp <= cls.MAX_INMEMORY_MP
        exceeds_output_cap = out_mp > cls.MAX_OUTPUT_MP

        warnings = []
        if exceeds_output_cap:
            warnings.append(f"Target size ({out_mp:.1f} MP) exceeds configured limit of {cls.MAX_OUTPUT_MP} MP.")
        if not can_fit_in_memory:
            warnings.append(f"Target exceeds {cls.MAX_INMEMORY_MP} MP in-memory cap; streaming/tiled disk processing will be enforced.")
        if raw_float32_mb > free_ram_mb * 0.8:
            warnings.append("High physical RAM pressure estimated; system swap may occur without disk-streaming.")

        return {
            "source_dimensions": [source_w, source_h],
            "target_dimensions": [target_w, target_h],
            "output_megapixels": round(out_mp, 2),
            "peak_ram_mb": round(raw_float32_mb, 1),
            "peak_vram_mb": tile_vram_mb,
            "required_disk_mb": round(required_disk_with_margin / (1024 * 1024), 1),
            "estimated_runtime_seconds": est_seconds,
            "estimated_throughput_mp_s": throughput,
            "requires_disk_streaming": not can_fit_in_memory,
            "exceeds_output_cap": exceeds_output_cap,
            "warnings": warnings
        }

resource_estimator = ResourceEstimator()

