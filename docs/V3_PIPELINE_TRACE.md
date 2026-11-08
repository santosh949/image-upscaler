# AETHER UPSCALE V3 — End-to-End Pipeline Trace

> **Trace Date:** 2026-11-08  
> **Source Baseline:** Codebase audit of active frontend, backend, engine, and NCNN Vulkan binary.  
> **Hardware Target:** Profile A — Constrained (Intel Core i5, NVIDIA GeForce RTX 2050 4 GB VRAM, Windows 11)

---

## 1. End-to-End Execution Flowchart

```
+---------------------------------------------------------------------------------------------------+
| 1. User Interface (React 19 / TypeScript)                                                         |
|    - User selects Task Card (e.g. "Improve a Photo", "Restore an Old Photo", "Anime & Cartoons")  |
|    - Selects Target Resolution (2x, 4x, 4K UHD, 8K UHD, or Custom)                                |
|    - Optional: Selects Quality Preset or opens Expert Mode (Model override, PNG/JPEG/WebP)       |
|    - Clicks "Start Enhancement" -> triggers startJob() in App.tsx (Line 264)                     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  POST /api/v1/jobs (JSON payload)
+---------------------------------------------------------------------------------------------------+
| 2. Backend API Ingestion (FastAPI / Pydantic v2)                                                  |
|    - endpoints.py::create_upscale_job (Line 154)                                                  |
|    - Fetches image record from storage/aether.db                                                  |
|    - Preflight checks: Dimensions * Scale <= 100 Megapixels cap (Line 167)                        |
|    - Preflight checks: Free disk space >= estimated_disk * 1.25                                   |
|    - Preflight checks: Available system RAM check                                                 |
|    - Generates UUID job_id, writes job record to SQLite                                           |
|    - Schedules background worker via FastAPI BackgroundTasks                                      |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  job_manager.spawn_worker(job_id)
+---------------------------------------------------------------------------------------------------+
| 3. Process Isolation & Worker Launch                                                              |
|    - job_manager.py::spawn_worker (Line 28)                                                       |
|    - Spawns subprocess: python -m backend.app.workers.job_worker <job_id>                         |
|    - Tracks PID for cancellation (.cancel) and pause (.pause) signals                             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  backend/app/workers/job_worker.py::process_job()
+---------------------------------------------------------------------------------------------------+
| 4. Job Dispatcher & Routing                                                                       |
|    - job_worker.py (Lines 16-30): Reads job configuration from database                           |
|    - Auto-promotes mode="restore" with scale > 1 to "restore_upscale"                             |
|    - If plan_json present -> calls progressive_pipeline.run()                                     |
|    - Else -> calls pipeline.run()                                                                 |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 5. Pre-Processing & Transparency Preparation                                                     |
|    - pipeline.py / progressive_pipeline.py (Line 51)                                              |
|    - AlphaHandler.prepare_rgb_and_alpha():                                                        |
|      * Separates RGBA into RGB and Alpha channels                                                 |
|      * Dilates RGB color 4px outward into transparent zones (prevents dark edge bleeding)         |
|    - If mode == "restore_upscale":                                                                |
|      * Stage 1: RestorationEngine.restore() runs OpenCV Bilateral filter + FastNlMeans            |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 6. Tiled Inference Engine (TileEngine)                                                            |
|    - tile_engine.py (Line 115): generate_tile_grid() partitions canvas into macro-tiles           |
|    - Computes step = max(16, tile_size - overlap) with boundary flags (top, bottom, left, right)  |
|    - For each tile:                                                                               |
|      * Crops tile from input image                                                                |
|      * Calls ncnn_infer_tile() -> NCNNRealESRGANAdapter.enhance()                                 |
|      * Spawns: realesrgan-ncnn-vulkan.exe -i temp_in -o temp_out -n <model> -s 4 -g 0 -t <tile>   |
|      * Vulkan Device 0 (NVIDIA GeForce RTX 2050) executes SPIR-V shader passes                     |
|      * If target_scale != model_scale (e.g. 4K->8K target_scale 2.0 with 4x model):               |
|        Immediately downscales tile output via Lanczos to target scale (Per-Tile Scale Adaptation) |
|      * Computes 2D Hann feathered cosine window mask: W(x,y) = sin^2(pi*x/L) * sin^2(pi*y/L)      |
|      * Accumulates weighted tile: accum += tile * W; weights += W                                 |
|      * Checks cancel_check() and pause_check() between tiles                                      |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 7. Normalization & Post-Processing                                                                |
|    - Normalizes blended canvas: final_arr = accum / np.maximum(weights, 1e-6)                     |
|    - If mode == "restore_upscale":                                                                |
|      * Stage 3: Conservative unsharp mask (amount=0.35, radius=1.0)                               |
|    - If has_alpha: AlphaHandler.restore_alpha() recombines scaled alpha channel                   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 8. Export, Manifest & Provenance                                                                  |
|    - metadata_embedder.py::save_with_metadata() saves final image to storage/outputs/             |
|    - Embeds audit metadata (Software, Model, Scale, Stages, Hardware, License, Timestamp)         |
|    - Generates 1280x1280 JPEG preview to storage/previews/                                        |
|    - Writes manifest record to storage/manifests/{job_id}.json                                    |
|    - Registers derived version in SQLite version graph (Invariant E2)                             |
|    - Marks job status="completed" in database -> SSE stream updates UI                           |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. File & Line Trace Index

| Stage | Module | Primary Function | Relevant Lines |
|---|---|---|---|
| **UI Action** | `frontend/src/App.tsx` | `startJob()` | Lines 264–309 |
| **API Ingestion** | `backend/app/api/endpoints.py` | `create_upscale_job()` | Lines 154–201 |
| **Preflight Planning** | `backend/app/services/resolution_planner.py` | `generate_plan()` | Lines 182–240 |
| **Job Process Isolation** | `backend/app/services/job_manager.py` | `spawn_worker()` | Lines 28–36 |
| **Worker Execution** | `backend/app/workers/job_worker.py` | `process_job()` | Lines 11–130 |
| **Alpha Pre-processing** | `ai_engine/processing/alpha_handler.py` | `prepare_rgb_and_alpha()` | Lines 15–45 |
| **Artifact Cleaning** | `ai_engine/processing/restoration.py` | `restore()` | Lines 52–77 |
| **Tile Coordinates** | `ai_engine/processing/tile_engine.py` | `generate_tile_grid()` | Lines 61–113 |
| **NCNN Process Launch** | `ai_engine/models/ncnn_adapter.py` | `enhance()` | Lines 56–85 |
| **Cosine Feathering** | `ai_engine/processing/tile_engine.py` | `compute_feather_window()` | Lines 50–60 |
| **Per-Tile Scale Adaptation** | `ai_engine/processing/tile_engine.py` | `_execute_tiling()` | Lines 260–270 |
| **Provenance Embedding** | `ai_engine/processing/metadata_embedder.py` | `save_with_metadata()` | Lines 30–65 |
| **Version Registration** | `backend/app/services/version_service.py` | `register_derived_version()` | Lines 65–115 |

