import os
import subprocess
import psutil
from typing import Dict, Any, Tuple
from PIL import Image

class MemoryManager:
    """Monitors hardware memory, VRAM, and enforces image size and pixel caps."""

    def __init__(self, max_output_mp: int = 100):
        self.max_output_mp = max_output_mp

    def get_hardware_status(self) -> Dict[str, Any]:
        """Returns physical RAM and NVIDIA GPU VRAM metrics."""
        ram = psutil.virtual_memory()
        vram_total_mb = 4096
        vram_free_mb = 3500

        # Query nvidia-smi if available
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total,memory.free,memory.used", "--format=csv,nounits,noheader"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split("\n")[0].split(",")
                if len(parts) >= 2:
                    vram_total_mb = int(parts[0].strip())
                    vram_free_mb = int(parts[1].strip())
        except Exception:
            pass

        # Hardware Profile determination (PRD Section 4.1)
        if ram.total / (1024**3) <= 10.0 or vram_total_mb <= 4500:
            profile = "A - Constrained (8GB RAM, RTX 2050 4GB)"
            recommended_tile = 256
        else:
            profile = "B - Moderate / High-End"
            recommended_tile = 512

        return {
            "profile": profile,
            "ram_total_mb": round(ram.total / (1024 * 1024)),
            "ram_available_mb": round(ram.available / (1024 * 1024)),
            "vram_total_mb": vram_total_mb,
            "vram_free_mb": vram_free_mb,
            "recommended_tile_size": recommended_tile
        }

    def validate_image_scale(self, input_path: str, scale: int) -> Tuple[int, int, float]:
        """
        Validates input image dimensions and scale against safety caps.
        Raises ValueError if bounds or decompression limits are breached.
        """
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Protect against decompression bomb exploits
        Image.MAX_IMAGE_PIXELS = 150_000_000

        with Image.open(input_path) as img:
            in_w, in_h = img.size

        out_w = in_w * scale
        out_h = in_h * scale
        out_mp = (out_w * out_h) / 1_000_000.0

        if out_mp > self.max_output_mp:
            raise ValueError(
                f"Output dimensions ({out_w}x{out_h} = {out_mp:.1f} MP) exceed the "
                f"{self.max_output_mp} MP limit configured for this hardware profile."
            )

        return (out_w, out_h, out_mp)

    def estimate_job_ram_mb(self, width: int, height: int, scale: int) -> float:
        """Estimates peak memory footprint in megabytes for tiled assembly."""
        out_pixels = (width * scale) * (height * scale)
        # 3 channels, uint8 output + float accumulator
        return round((out_pixels * 3 * 5) / (1024 * 1024), 1)

memory_manager = MemoryManager()

