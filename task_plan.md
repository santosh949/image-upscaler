# Task Plan — AETHER UPSCALE

## Milestones

### Phase 0 — Environment + Real Inference (COMPLETED)
- [x] Hardware & environment discovery (RTX 2050 4GB VRAM, Vulkan device 0)
- [x] Create SKILLS.md and update AGENTS.md
- [x] Create documentation stubs
- [x] Create Python 3.11 `.venv` via `uv` and install core dependencies
- [x] Obtain official Real-ESRGAN NCNN Vulkan portable Windows release
- [x] Verify and record `realesrgan-x4plus` SHA256 hashes
- [x] Create test fixture (`tests/fixtures/test_input.png`)
- [x] Write `scripts/test_upscale.py` and run real 4x upscale on RTX 2050
- [x] Verify acceptance criteria via `pytest tests/test_phase0.py`

### Phase 1 — Minimal Backend (COMPLETED)
- [x] Implement AI engine base model interface and NCNN adapter (`ai_engine/models/base.py`, `ai_engine/models/ncnn_adapter.py`)
- [x] Implement SQLite job table and DB repository (`backend/app/database.py`)
- [x] Implement worker subprocess for inference execution and job cancellation (`backend/app/workers/job_worker.py`)
- [x] Implement FastAPI app with versioned endpoints (`backend/app/main.py`, `backend/app/api/endpoints.py`)
- [x] Implement upload, job creation, SSE events, and download
- [x] Acceptance verification: automated tests in `tests/test_phase1_api.py` (all passed)

### Phase 2 — Web MVP (COMPLETED)
- [x] Initialize React + TypeScript + Vite in `frontend/`
- [x] Configure Tailwind CSS v4 and custom SVG icons
- [x] Build UI layout: Header, Capabilities indicator, Dropzone, Mode & Scale controls
- [x] Integrate API services (Upload, Job creation, SSE status stream, Download)
- [x] Add basic preview comparison & cancellation button
- [x] Build & test production bundle (`npm run build`)
- [x] Serve frontend directly from FastAPI app at `/`
- [x] Acceptance verification: automated tests in `tests/test_phase2_web.py` (11/11 passed)
- [x] Update graphify knowledge graph (489 nodes, 627 edges)

### Phase 3 — Professional Editor (COMPLETED)
- [x] Implement draggable Before/After split comparison slider with handle
- [x] Implement side-by-side synchronized comparison view
- [x] Implement zoom controls (100% to 300%)
- [x] Implement `/crop` 100% inspection endpoint (`tests/test_phase3_editor.py`)
- [x] Implement fast Crop-Preview job mode (256px region in ~1s)
- [x] Implement export format options (PNG, JPEG, WebP) with quality compression
- [x] Implement Job History drawer (`GET /jobs`, `DELETE /jobs/{id}`)
- [x] Rebuild frontend production bundle
- [x] Automated test suite: 15/15 tests passed
- [x] Graphify knowledge graph updated (514 nodes, 697 edges)

### Phase 4 — Models, Analyzer, Router (COMPLETED)
- [x] Model registry with code & weight licenses (`ai_engine/registry/model_registry.py`)
- [x] Added `realesrgan-x4plus-anime` model support and ran GPU smoke test (passed in 4.78s)
- [x] Real degradation analyzer (`ai_engine/analysis/analyzer.py` - blur, noise, JPEG Q-tables, category)
- [x] Degradation-aware router (`ai_engine/routing/router.py`) with plain-language explanations
- [x] Added `/api/v1/images/{id}/analyze` endpoint
- [x] Frontend Model Selector & real-time Degradation Signals Card
- [x] Automated test suite: 19/19 tests passed
- [x] Graphify knowledge graph updated (560 nodes, 773 edges)

### Phase 5 — Tiling and Hardware Optimization (COMPLETED)
- [x] Implement standalone tile engine with Hann/Gaussian feathered blending (`ai_engine/processing/tile_engine.py`)
- [x] Enforce output pixel cap (100 MP)
- [x] Hardware memory manager (`ai_engine/memory/memory_manager.py`)
- [x] Automatic OOM retry logic with tile subdivision
- [x] Seam suppression verification test (`tests/test_phase5_tiling.py`)
- [x] Knowledge graph updated (604 nodes, 850 edges)

### Phase 6 — Restore + Upscale and Advanced Controls (COMPLETED)
- [x] Low-res pre-pass & CV2 artifact reduction filters (`ai_engine/processing/restoration.py`)
- [x] Full `restore_and_upscale` pipeline (`ai_engine/pipelines/pipeline.py`)
- [x] Alpha channel bleed & separate alpha upscaling per PRD 7.5 (`ai_engine/processing/alpha_handler.py`)
- [x] Provenance metadata embedding in output PNG text chunks (`ai_engine/processing/metadata_embedder.py`)
- [x] Difference / downscale consistency check (`ai_engine/processing/consistency.py`)
- [x] Acceptance verification: automated tests in `tests/test_phase6_pipeline.py` (all passed)
- [x] Knowledge graph updated (660 nodes, 983 edges)

### Phase 7 — Generative Research & Hardware Constraints Documentation (COMPLETED)
- [x] Review compute, memory, and license limits for Tier 3 generative models on 4GB VRAM
- [x] Document strict rationale and refusal for SDXL/SUPIR on Profile A in `docs/KNOWN_LIMITATIONS.md`
- [x] Implement clear UI/API status explaining unavailability on Profile A (`ai_engine/registry/model_registry.py`, `frontend/src/App.tsx`)
- [x] Verify non-generative faithful mode safety guarantees (`tests/test_phase7_generative_constraints.py`)
- [x] Knowledge graph updated (670 nodes, 995 edges)

### Phase 8 — Tests, Security, Benchmarks, Release (COMPLETED)
- [x] Automated benchmark suite on GPU (`benchmarks/benchmark_suite.py` & `benchmarks/BENCHMARK_RESULTS.md`)
- [x] Comprehensive security & sanitization tests (`tests/test_phase8_security.py`)
- [x] Documentation updates (`README.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/USER_GUIDE.md`)
- [x] Full automated test suite passing (38/38 tests)
- [x] Definition of Done verified across all PRD Section 18 criteria
- [x] Knowledge graph updated (670 nodes, 995 edges, 49 communities)

### Phase 9 (V3 Addendum) — Quality & Architecture Refinement (COMPLETED)
- [x] **Phase 0:** Baseline freeze; Vulkan device 0 confirmed as `NVIDIA GeForce RTX 2050` by name via Vulkan API; real physical disk-free (`shutil.disk_usage`) and available RAM preflights; Plan C (pure Lanczos resample) wired in UI, API, and engine; sidecar JSON manifests (`*.manifest.json`) emitted for all formats; pipeline trace documented in `docs/V3_PIPELINE_TRACE.md`.
- [x] **Phase 1:** Lossless diagnostic tap test (T0–T5) across 4 ROIs on grainy portrait; identified classical pre-denoise as root cause of texture erasure; documented in `docs/V3_TEXTURE_LOSS_REPORT.md`.
- [x] **Phase 2:** Human-photo texture preservation: classical pre-denoise skipped; post-sharpen disabled; 20% Lanczos optical blend retains microscopic source grain without halo overshoot (< 2.4).
- [x] **Phase 3:** Single unified `backend/app/core/presets.yaml` configuration coupled to backend worker and version manifests; `GET /presets` API endpoint.
- [x] **Phase 4:** Manga/illustration tuning: `realesrgan-x4plus-anime` verified as primary manga model (Laplacian variance 11,961 vs 662 for animevideov3).
- [x] **Phase 5:** Quality benchmarks, 4K→8K regression, automated test suite expanded to 59/59 passed, clean frontend build, and `docs/V3_QUALITY_REPORT.md`.

### Phase 10 — Batch Upload, Sequential Queue & ZIP Export (COMPLETED)
- [x] **Step 1:** Queue Dispatcher in `JobManager` (sequential single-worker execution on GPU, auto-advances next `queued` job)
- [x] **Step 2:** Batch REST Endpoints (`/images/batch`, `/jobs/batch`, `/jobs/queue`, `/jobs/batch/download-zip`, `/jobs/queue/clear`)
- [x] **Step 3:** Frontend API Client (`uploadImagesBatch`, `createJobsBatch`, `fetchQueueStatus`, `downloadBatchZip`)
- [x] **Step 4:** Frontend UI Studio (`multiple` file dropzone, Batch Queue Modal/Tray, per-item live progress, ZIP download, click-to-compare)
- [x] **Step 5:** Automated verification suite (`tests/test_phase10_batch_queue.py`) — 4/4 passed
- [x] **Step 6:** Build frontend bundle, restart server, end-to-end verification (68/68 passed)
