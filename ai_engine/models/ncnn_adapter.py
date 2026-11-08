import os
import sys
import time
import shutil
import tempfile
import subprocess
import re
from typing import Dict, Any, Optional, List, Callable
from PIL import Image
from ai_engine.models.base import ModelAdapter

class NCNNRealESRGANAdapter(ModelAdapter):
    """Adapter for NCNN Vulkan binary implementation of Real-ESRGAN."""

    _cached_devices: Optional[Dict[int, str]] = None

    def __init__(self, exe_path: Optional[str] = None, models_dir: Optional[str] = None):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        bin_name = "realesrgan-ncnn-vulkan.exe" if sys.platform.startswith("win") else "realesrgan-ncnn-vulkan"
        self.exe_path = exe_path or os.path.join(root_dir, "tools", "realesrgan-ncnn-vulkan", bin_name)
        self.models_dir = models_dir or os.path.join(root_dir, "tools", "realesrgan-ncnn-vulkan", "models")
        self.current_process: Optional[subprocess.Popen] = None

    def get_vulkan_devices(self) -> Dict[int, str]:
        """Queries Vulkan devices dynamically via vulkaninfo or NCNN probe."""
        if NCNNRealESRGANAdapter._cached_devices is not None:
            return NCNNRealESRGANAdapter._cached_devices

        devices: Dict[int, str] = {}
        cf = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        # 1. Fast sub-50ms query via standard vulkaninfo
        try:
            v_out = subprocess.check_output(
                ["vulkaninfo", "--summary"],
                text=True,
                stderr=subprocess.DEVNULL,
                creationflags=cf,
                timeout=3
            )
            current_gpu_idx = None
            for line in v_out.splitlines():
                gpu_match = re.search(r"GPU(\d+):", line)
                if gpu_match:
                    current_gpu_idx = int(gpu_match.group(1))
                elif current_gpu_idx is not None and "deviceName" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        devices[current_gpu_idx] = parts[1].strip()
                        current_gpu_idx = None
        except Exception:
            pass

        # 2. Fallback to lightweight NCNN probe on 4x4 dummy image
        if not devices and os.path.isfile(self.exe_path):
            try:
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                tiny_probe = os.path.join(root_dir, "storage", "temp", "tiny_probe.png")
                tiny_out = os.path.join(root_dir, "storage", "temp", "tiny_probe_out.png")
                os.makedirs(os.path.dirname(tiny_probe), exist_ok=True)
                Image.new("RGB", (4, 4), (0, 0, 0)).save(tiny_probe, "PNG")

                res = subprocess.run(
                    [self.exe_path, "-i", tiny_probe, "-o", tiny_out, "-m", self.models_dir, "-s", "2", "-t", "32", "-v"],
                    capture_output=True,
                    text=True,
                    creationflags=cf,
                    timeout=3
                )
                matches = re.findall(r"\[(\d+)\s+([^\]]+)\]", res.stderr)
                for idx, name in matches:
                    devices[int(idx)] = name.strip()

                for p in (tiny_probe, tiny_out):
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
            except Exception:
                pass

        if not devices:
            devices[0] = "Vulkan Compatible Device"

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
        cancel_token: Optional[Any] = None,
        cancel_check: Optional[Callable[[], bool]] = None
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
            while True:
                ret = self.current_process.poll()
                if ret is not None:
                    break
                if cancel_check and cancel_check():
                    self.cancel()
                    raise RuntimeError("Inference cancelled by user")
                time.sleep(0.05)
            stdout, stderr = self.current_process.communicate()
            returncode = self.current_process.returncode
        except Exception as e:
            self.cancel()
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

    def enhance_batch(
        self,
        input_paths: List[str],
        output_paths: List[str],
        scale: int = 4,
        tile_size: int = 0,
        gpu_id: int = 0,
        model_name: str = "realesrgan-x4plus",
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> List[str]:
        """
        Executes NCNN inference across multiple image tiles in a single process.
        Avoids reloading neural network weights per tile.
        Actively monitors cancel_check every 50ms and kills subprocess on request.
        """
        if not input_paths:
            return []

        bin_file = f"{model_name}.bin"
        if not os.path.isfile(os.path.join(self.models_dir, bin_file)):
            raise FileNotFoundError(f"Model file missing: {bin_file} in {self.models_dir}")

        with tempfile.TemporaryDirectory(prefix="ncnn_batch_in_") as batch_in_dir, \
             tempfile.TemporaryDirectory(prefix="ncnn_batch_out_") as batch_out_dir:

            name_map = {}
            for idx, in_p in enumerate(input_paths):
                ext = os.path.splitext(in_p)[1] or ".png"
                tile_fname = f"tile_{idx:05d}{ext}"
                dest_in = os.path.join(batch_in_dir, tile_fname)
                shutil.copyfile(in_p, dest_in)
                name_map[f"tile_{idx:05d}"] = output_paths[idx]

            cmd = [
                self.exe_path,
                "-i", os.path.abspath(batch_in_dir),
                "-o", os.path.abspath(batch_out_dir),
                "-m", os.path.abspath(self.models_dir),
                "-n", model_name,
                "-s", str(scale),
                "-g", str(gpu_id),
                "-t", str(tile_size),
                "-v"
            ]

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                while True:
                    ret = self.current_process.poll()
                    if ret is not None:
                        break
                    if cancel_check and cancel_check():
                        self.cancel()
                        raise RuntimeError("Inference cancelled by user")
                    time.sleep(0.05)
                stdout, stderr = self.current_process.communicate()
                returncode = self.current_process.returncode
            except Exception as e:
                self.cancel()
                raise e
            finally:
                self.current_process = None

            if returncode != 0:
                raise RuntimeError(f"Batch NCNN inference failed with exit code {returncode}. Stderr: {stderr}")

            for stem, final_out_path in name_map.items():
                out_candidate = os.path.join(batch_out_dir, f"{stem}.png")
                if not os.path.isfile(out_candidate):
                    ext = os.path.splitext(final_out_path)[1]
                    out_candidate = os.path.join(batch_out_dir, f"{stem}{ext}")

                if os.path.isfile(out_candidate):
                    os.makedirs(os.path.dirname(os.path.abspath(final_out_path)), exist_ok=True)
                    shutil.move(out_candidate, final_out_path)
                else:
                    raise FileNotFoundError(f"Batch inference failed to produce tile for {final_out_path}")

        return output_paths

    def cancel(self) -> None:
        proc = self.current_process
        if proc and proc.poll() is None:
            try:
                proc.kill()
                proc.wait(timeout=2.0)
            except Exception:
                pass
            finally:
                self.current_process = None

    def unload(self) -> None:
        self.cancel()
