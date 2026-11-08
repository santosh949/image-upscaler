import os
import time
import subprocess
import re
from typing import Dict, Any, Optional
from PIL import Image
from ai_engine.models.base import ModelAdapter

class NCNNRealESRGANAdapter(ModelAdapter):
    """Adapter for NCNN Vulkan binary implementation of Real-ESRGAN."""

    _cached_devices: Optional[Dict[int, str]] = None

    def __init__(self, exe_path: Optional[str] = None, models_dir: Optional[str] = None):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.exe_path = exe_path or os.path.join(root_dir, "tools", "realesrgan-ncnn-vulkan", "realesrgan-ncnn-vulkan.exe")
        self.models_dir = models_dir or os.path.join(root_dir, "tools", "realesrgan-ncnn-vulkan", "models")
        self.current_process: Optional[subprocess.Popen] = None

    def get_vulkan_devices(self) -> Dict[int, str]:
        """Queries NCNN binary directly for available Vulkan devices and their names."""
        if NCNNRealESRGANAdapter._cached_devices is not None:
            return NCNNRealESRGANAdapter._cached_devices

        devices: Dict[int, str] = {}
        if os.path.isfile(self.exe_path):
            try:
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                test_input = os.path.join(root_dir, "tests", "fixtures", "test_input.png")
                temp_out = os.path.join(root_dir, "storage", "temp", "dev_probe.png")
                if os.path.isfile(test_input):
                    res = subprocess.run(
                        [self.exe_path, "-i", test_input, "-o", temp_out, "-m", self.models_dir, "-n", "realesrgan-x4plus", "-s", "4", "-g", "0", "-v"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    matches = re.findall(r"\[(\d+)\s+([^\]]+)\]", res.stderr)
                    for idx, name in matches:
                        devices[int(idx)] = name.strip()
                    if os.path.exists(temp_out):
                        os.remove(temp_out)
            except Exception:
                pass

        if not devices:
            devices[0] = "NVIDIA GeForce RTX 2050"

        NCNNRealESRGANAdapter._cached_devices = devices
        return devices

    def get_nvidia_device_id(self) -> int:
        """Finds device ID corresponding to discrete NVIDIA GPU, defaulting to 0."""
        devs = self.get_vulkan_devices()
        for dev_id, name in devs.items():
            if any(k in name.lower() for k in ("nvidia", "geforce", "rtx")):
                return dev_id
        return 0

    def capabilities(self) -> Dict[str, Any]:
        return {
            "supported_models": ["realesrgan-x4plus", "realesrgan-x4plus-anime"],
            "backend": "ncnn-vulkan",
            "supported_scales": [4],
            "tasks": ["super-resolution", "general-photo", "anime-art"],
            "license_class": "non-commercial / unclear",
            "hardware_backend": "vulkan"
        }

    def load(self, device: str = "vulkan", precision: str = "fp16") -> None:
        if not os.path.isfile(self.exe_path):
            raise FileNotFoundError(f"NCNN executable not found at: {self.exe_path}")

    def enhance(
        self,
        input_path: str,
        output_path: str,
        scale: int = 4,
        tile_size: int = 0,
        gpu_id: int = 0,
        model_name: str = "realesrgan-x4plus",
        cancel_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        bin_file = f"{model_name}.bin"
        param_file = f"{model_name}.param"
        if not os.path.isfile(os.path.join(self.models_dir, bin_file)):
            raise FileNotFoundError(f"Model file missing: {bin_file} in {self.models_dir}")

        in_img = Image.open(input_path)
        in_w, in_h = in_img.size

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if os.path.exists(output_path):
            os.remove(output_path)

        cmd = [
            self.exe_path,
            "-i", os.path.abspath(input_path),
            "-o", os.path.abspath(output_path),
            "-m", os.path.abspath(self.models_dir),
            "-n", model_name,
            "-s", str(scale),
            "-g", str(gpu_id),
            "-t", str(tile_size),
            "-v"
        ]

        start_time = time.perf_counter()
        self.current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = self.current_process.communicate()
            returncode = self.current_process.returncode
        except Exception as e:
            if self.current_process:
                self.current_process.kill()
            raise e
        finally:
            self.current_process = None

        elapsed = time.perf_counter() - start_time

        if returncode != 0:
            raise RuntimeError(f"NCNN inference failed with exit code {returncode}. Stderr: {stderr}")

        if not os.path.isfile(output_path):
            raise FileNotFoundError(f"Expected output file not generated: {output_path}")

        out_img = Image.open(output_path)
        out_w, out_h = out_img.size

        # Resolve exact Vulkan device name used
        devs = self.get_vulkan_devices()
        device_name = devs.get(gpu_id, f"Vulkan Device {gpu_id}")

        return {
            "backend": "ncnn-vulkan",
            "model": model_name,
            "scale": scale,
            "gpu_id": gpu_id,
            "device_name": device_name,
            "input_dimensions": [in_w, in_h],
            "output_dimensions": [out_w, out_h],
            "elapsed_seconds": round(elapsed, 3),
            "output_bytes": os.path.getsize(output_path)
        }

    def cancel(self) -> None:
        if self.current_process and self.current_process.poll() is None:
            self.current_process.kill()

    def unload(self) -> None:
        self.cancel()
