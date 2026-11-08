# Known Limitations & Hardware Architecture Constraints — AETHER UPSCALE

## 1. Hardware Profile A Target & VRAM Bounds
- **GPU:** NVIDIA GeForce RTX 2050 Mobile (GA107 / Ampere architecture)
- **Dedicated VRAM:** 4096 MiB (4.0 GB) GDDR6, 64-bit bus width.
- **Typical Desktop Footprint:** OS and DWM consume ~400–600 MiB VRAM at idle, leaving ~3.5 GB for tensor allocation.
- **Physical RAM:** 8.0 GB DDR4/LPDDR4.
- **Constraint Impact:** Tiled processing with conservative tile dimensions (256×256 with 32px overlap) is required to guarantee zero out-of-memory crashes during large image inference passes.
- **Output Pixel Cap:** Enforced at **100 Megapixels** (e.g., 10,000 × 10,000 pixels) to prevent system memory exhaustion during tiled canvas assembly and PNG serialization.

## 2. Phase 7 Generative Research Evaluation (Tier 3 Models)
Evaluated Tier 3 Diffusion and Generative super-resolution architectures against Profile A:
- **DiffBIR (Diffusion Blind Image Restoration):**
  - Backbone: Stable Diffusion v1.5 / v2.1 + ControlNet.
  - Model Weight Footprint: > 4.5 GB on disk, > 6.8 GB peak VRAM in FP16 during multi-step denoising.
  - Verdict on Profile A: **UNAVAILABLE / EXCLUDED**. Causes immediate CUDA OOM or severe CUDA unified memory swapping into system RAM, increasing runtime by 50–100× and thrashing Windows desktop stability.
  - License: Apache-2.0 code; training data non-commercial / research only.
- **SUPIR (Scaling-Up Photo-Realistic Diffusion SR):**
  - Backbone: SDXL (2.6B parameter UNet) + Text-conditioned guidance.
  - Model Weight Footprint: > 12 GB, requires 16 GB+ VRAM.
  - Verdict on Profile A: **UNAVAILABLE / EXCLUDED**. Completely exceeds physical address space of 4GB VRAM.
- **Generative Hallucination Warning:**
  - Diffusion-based upscaling invents novel high-frequency textures that do not exist in the source image.
  - For faithful restoration, forensics, or portrait preservation, AETHER UPSCALE strictly defaults to deterministic regression / GAN-based super-resolution (Real-ESRGAN RRDBNet) with downscale-consistency verification.

## 3. Dual-GPU Vulkan Indexing
- Laptops with Intel UHD / Iris Xe integrated graphics and NVIDIA discrete GPUs present multiple Vulkan physical devices.
- Vulkan Device Index 0 maps to `NVIDIA GeForce RTX 2050` (Vulkan API 1.4.325, Driver 592.82).
- Vulkan Device Index 1 maps to `Intel(R) UHD Graphics`.
- To avoid slow fallback to integrated graphics, AETHER UPSCALE hard-codes or explicitly routes inference to Vulkan device index 0 (`-g 0`).

## 4. Native PyTorch Acceleration on Windows
- Windows 11 lacks official native wheels for PyTorch `torch.compile` with Triton.
- High-performance inference is delivered natively via the NCNN Vulkan binary engine compiled with MSVC and direct SPIR-V shaders, achieving 100% GPU utilization without Python runtime overhead.
