# Findings — AETHER UPSCALE

## Hardware & Environment (Measured)
- **OS:** Windows 11 Home/Pro (Build 10.0.26200)
- **CPU / System Python:** Python 3.14.0 (Warning: PyTorch wheels unavailable on 3.14; Python 3.11 available via `uv` at `C:\Users\Santhosh\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe`)
- **Node / npm:** Node v24.14.0, npm 11.9.0
- **Git:** 2.54.0.windows.1
- **GPU:** NVIDIA GeForce RTX 2050 (4096 MiB total VRAM, ~280 MiB active during idle)
- **Vulkan Devices:**
  - `GPU0`: NVIDIA GeForce RTX 2050 (Discrete, driver 592.82.0.0, API 1.4.325)
  - `GPU1`: Intel(R) UHD Graphics (Integrated, driver 101.4502, API 1.3.250)
- **Critical Vulkan Note:** NVIDIA GPU is index `0` in Vulkan enumeration on this machine (`-g 0`). We must pass `-g 0` explicitly to NCNN binaries to avoid accidentally using Intel iGPU.
- **Ollama:** Version 0.40.14 installed on machine; server currently not running in background.

