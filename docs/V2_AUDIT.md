# AETHER UPSCALE 2.0 — Comprehensive Audit & Claim Ledger

> **Date:** November 7, 2026  
> **Auditor:** Antigravity Autonomous Pair Programmer  
> **Reference Document:** `FINAL_SPEC.md` / `AETHER_UPSCALE_2.0_FINAL_SPEC_REVISED.md`  
> **Audited Environment:** Windows 11 (Build 26200), NVIDIA GeForce RTX 2050 Mobile (4GB VRAM), 8GB System RAM  

---

## 1. Hardware & System Verification

| Parameter | Specification Claim | Real Audited Value | Command & Verification Proof |
|---|---|---|---|
| **OS** | Windows 11 64-bit | Windows 11 Build 26200 | `[System.Environment]::OSVersion` |
| **GPU Vendor & Model** | Discrete NVIDIA GPU | NVIDIA GeForce RTX 2050 Mobile | `nvidia-smi` -> Driver 592.82 |
| **Dedicated VRAM** | 4096 MiB | 4096 MiB total, ~3680 MiB free | `nvidia-smi --query-gpu=memory.total,memory.free` |
| **Vulkan Devices** | Explicit GPU index needed | Device 0: RTX 2050 (Discrete)<br>Device 1: Intel UHD (iGPU) | `vulkaninfo --summary` |
| **Python Environment** | Python 3.11 (`.venv`) | Python 3.11.15 via `uv` | `.venv\Scripts\python.exe --version` |
| **Node.js & npm** | Node >= 20, npm >= 10 | Node v24.14.0, npm 11.9.0 | `node -v`, `npm -v` |
| **Vulkan Binary** | Portable MSVC NCNN | `tools\realesrgan-ncnn-vulkan\` (v0.2.5.0) | `realesrgan-ncnn-vulkan.exe -h` |

---

## 2. Dossier Claim Ledger (Section A2 Verification)

Every claim made about the existing product has been inspected and tested against live code and execution:

| # | Product Claim | Audit Status | Real Evidence & Verification Details |
|---|---|---|---|
| 1 | **FastAPI + React 19/TS/Vite** | **VERIFIED** | FastAPI `0.135.1` mounted at `backend/app/main.py`. Frontend `package.json` specifies React `19.2.4`, TypeScript `5.9.3`, Vite `8.3.6`. Production bundle in `frontend/dist`. |
| 2 | **NCNN Vulkan Inference** | **VERIFIED** | Real execution of `tools/realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan.exe` on GPU index `0`. Tested in `tests/test_phase0.py`. |
| 3 | **Model Variants Shipped** | **VERIFIED** | `realesrgan-x4plus.bin` (33.4MB), `realesrgan-x4plus-anime.bin` (8.9MB), and `realesr-animevideov3-x4.bin` (1.2MB) exist in models directory and smoke test passes on GPU 0. |
| 4 | **Isolated Inference Worker** | **VERIFIED** | `backend/app/workers/job_worker.py` executed as separate OS process via `subprocess.Popen` in `job_manager.py`. Enables process-tree kill. |
| 5 | **SQLite Job Tracking** | **VERIFIED** | `backend/app/database.py` manages `images` and `jobs` tables with WAL mode, parameterized queries, and startup crash recovery. |
| 6 | **SSE Progress Streaming** | **VERIFIED** | `GET /api/v1/jobs/{job_id}/events` serves real-time Server-Sent Events with progress updates (0.0 to 1.0) and stage descriptions. |
| 7 | **Degradation Analyzer & Router** | **VERIFIED** | `ai_engine/analysis/analyzer.py` calculates normalized Laplacian variance, Immerkaer MAD noise, and JPEG 8x8 DCT grid blockiness. `router.py` emits recommendation with plain-language explanation. Tested in `tests/test_phase4_models_router.py`. |
| 8 | **Tiled Inference with Feathered Overlap** | **VERIFIED** | `ai_engine/processing/tile_engine.py` implements 2D Hann / raised-cosine feathered blending. Seam test in `tests/test_phase5_tiling.py` confirms MAE < 1.0 reconstruction. |
| 9 | **Automatic OOM Tile Fallback** | **VERIFIED** | `tile_engine.py` automatically catches memory/OOM exceptions and recursively retries by halving tile size (512 -> 256 -> 128). Verified in `tests/test_phase5_tiling.py`. |
| 10 | **Before/After Split Slider & Zoom** | **VERIFIED** | `frontend/src/App.tsx` has interactive draggable split slider, side-by-side synchronized view, and zoom controls (100% to 300%). |
| 11 | **100% Crop Inspection** | **VERIFIED** | `GET /api/v1/jobs/{job_id}/crop` extracts and serves arbitrary sub-regions without browser canvas memory overflow. Tested in `tests/test_phase3_editor.py`. |
| 12 | **Fast 1s Crop-Preview** | **VERIFIED** | `job_worker.py` supports `crop_region` mode, processing center 256px region in ~1s. Tested in `tests/test_phase3_editor.py`. |
| 13 | **Multi-Format Export (PNG, JPEG, WebP)** | **VERIFIED** | `GET /api/v1/jobs/{job_id}/download?format=...&quality=...` performs on-the-fly format encoding with quality sliders. |
| 14 | **Restore, Upscale, Combined Modes** | **VERIFIED** | `ai_engine/pipelines/pipeline.py` implements distinct 1x restoration (bilateral deblock + NLM denoise), 4x SR, and combined two-stage pipeline. Tested in `tests/test_phase6_pipeline.py` (MAE > 0.05 between modes). |
| 15 | **Alpha Channel Handling** | **VERIFIED** | `ai_engine/processing/alpha_handler.py` bleeds RGB outward into zero-alpha areas via Telea inpainting and upscales alpha separately with Lanczos. |
| 16 | **Downscale-Consistency Check** | **VERIFIED** | `ai_engine/processing/consistency.py` calculates PSNR, MAE, per-channel drift, and visual difference map. |
| 17 | **Provenance Metadata** | **VERIFIED** | `ai_engine/processing/metadata_embedder.py` injects PNG `tEXt` chunks recording model, scale, stages, timestamps, and consistency metrics. |
| 18 | **Baseline Test Suite Passing** | **VERIFIED** | Pytest run on 2026-11-07 confirmed **38 passed, 0 failed** in 43.81s. |
| 19 | **100 Megapixel Cap Enforcement** | **VERIFIED** | `ai_engine/memory/memory_manager.py` and `tile_engine.py` reject jobs where output dimensions exceed 100 MP. Tested in `tests/test_phase5_tiling.py`. |

---

## 3. Tiling Ownership & Architectural Finding (Section D2)

- **Finding:** Tiling is currently driven at the Python level by `TileEngine` (`ai_engine/processing/tile_engine.py`).
- **Mechanism:** Python partitions the image into overlapping macro-tiles, invokes `realesrgan-ncnn-vulkan.exe` on each tile, and recombines the tiles into an in-memory/on-disk accumulator using a 2D Hann feathered cosine window.
- **Architectural Value:** This design is ideal for **Phase 2 (Progressive Engine)** because it allows:
  1. Per-tile checkpointing to disk (`tile_store.py`).
  2. Pause/resume at exact tile boundaries.
  3. Per-tile downscale adaptation for the 4K -> 8K flagship problem (Section F4).
  4. Preventing 16K (132.7 MP) intermediate allocation in physical RAM.

---

## 4. Code & Weight License Verification (Section G6)

| Model Name | Binary / Checkpoint File | Official Source | Code License | Weight License | Status | SHA256 Hash |
|---|---|---|---|---|---|---|
| `realesrgan-x4plus` | `realesrgan-x4plus.bin` | Xinntao Real-ESRGAN v0.2.5.0 | BSD-3-Clause | Non-Commercial / Unclear (DIV2K, Flickr2K) | Verified | `713EE713B0353AFAA27976F0563A64A5043BD70B9BD8936C2E26E25EBCDBCDDF` |
| `realesrgan-x4plus-anime` | `realesrgan-x4plus-anime.bin` | Xinntao Real-ESRGAN v0.2.5.0 | BSD-3-Clause | Non-Commercial / Unclear | Verified | `FE01C269CFD10CDEF8E018AB66EBE750CF79C7AF4D1F9C16C737E1295229BACC` |
| `realesr-animevideov3-x4` | `realesr-animevideov3-x4.bin` | Xinntao Real-ESRGAN v0.2.5.0 | BSD-3-Clause | Non-Commercial / Unclear | Verified | `548A36F9C3F4AB8DA56CD3B13BADF23968BEE207B396DAD14D04B830E5F2AB2D` |
| `realesrnet-x4plus` | Pending Phase 4 | Official Release | BSD-3-Clause | Non-Commercial / Unclear | Pending download | To be fetched in Phase 4 |
| `diffbir` | N/A | Open-source repo | Apache-2.0 | Research-only | Disabled (4GB Profile A) | Excluded per Section G4 |
| `supir` | N/A | Open-source repo | Apache-2.0 | Research-only | Disabled (4GB Profile A) | Excluded per Section G4 |

---

## 5. Upgrade Gaps to Address in AETHER UPSCALE 2.0

While the baseline product operates cleanly (38/38 tests passing), `FINAL_SPEC.md` requires the following strategic advancements:
1. **Version Graph & Storage Service (Phase 1):** Migrate flat jobs database to full Project -> Version graph with immutable ready versions, parent tracking, and forward-only schema migration (Section E1/E2).
2. **Progressive Engine & 4K->8K Internal Workflow (Phase 2):** Implement internal version continuation without re-upload, per-tile downscaling for 4K->8K, tile store checkpoints, and pause/resume at tile boundaries (Section F).
3. **Resolution Studio UI & Usability Redesign (Phase 3):** Redesign user workflow for non-technical users with clear task categories, quality presets, friendly model names, Maximum Resolution Explorer, and Technical Details panel (Section K).
4. **Model Expansion (Phase 4):** Integrate `realesrnet-x4plus` as the high-faithfulness option, honest pixel-space fidelity slider blend, and evaluate native 2x models.
5. **Quality, Seam & Benchmark Hardening (Phases 5–8):** Comprehensive metrics suite (PSNR, SSIM, color delta), long-run stability soak tests, and final release packaging.

