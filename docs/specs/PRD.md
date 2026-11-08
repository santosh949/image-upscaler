# AETHER UPSCALE — Product Requirements Document v2.0 (Revised)

**Date:** 7 November 2026
**Status:** Implementation specification (supersedes v1.0)
**Target OS:** Windows 11
**Target hardware:** 8 GB RAM, NVIDIA RTX 2050 laptop GPU (VRAM detected at runtime; commonly 4 GB, verify), 512 GB SSD
**Deployment:** Browser-based web app, local-first, localhost only
**Budget:** Free/open-source only. No paid APIs, no cloud GPU, no API keys.
**Dev environment:** Google Antigravity IDE (model as selected by the owner; do not assume model availability)

Items marked **[verify]** are unconfirmed and must be checked against the official repo/checkpoint page before use. Never claim benchmark results that were not measured on this machine.

---

# 0. AGENT RULES (copy into root `AGENTS.md`)

1. This document is the source of truth. Work one phase at a time; do not attempt the whole project in one pass.
2. Inspect the workspace and machine before changing anything. Never overwrite unknown files. Ask before destructive actions.
3. Do not fake AI output, progress, GPU use, benchmark scores or image quality. Progress is `null` when it cannot be measured.
4. No paid services, API keys, telemetry or cloud dependency. Images never leave the machine.
5. Windows 11 + PowerShell only. Do not assume Bash, WSL, Conda, Docker, Redis or admin rights.
6. Use a Python venv. Keep frontend and backend dependencies isolated. Pin versions after a working install.
7. Download only the model needed for the current milestone. Verify SHA256 from the manifest. Official sources only.
8. Before integrating any model, record code license AND weight license separately in `docs/MODEL_LICENSES.md` (status: verified / unclear). A permissive code license does not imply the weights are permissive.
9. A model is "available" only when its weights exist and a smoke test passes.
10. Run tests after every meaningful change; keep the app runnable at the end of each phase.
11. Maintain `docs/IMPLEMENTATION_STATUS.md` (files changed, commands run, test results, current errors, next task), `docs/DECISIONS.md`, `docs/KNOWN_LIMITATIONS.md`.
12. Do not train models. Inference, integration and small experiments only.
13. Do not rewrite the architecture after implementation starts unless evidence proves it broken; record a decision and continue.
14. If PyTorch/CUDA setup stalls, stop reinstalling. Use the NCNN Vulkan backend, document the limitation, continue behind the common model interface.
15. Never construct shell strings from user input. Use subprocess argument arrays.
16. At the end of each milestone report: what works, what was tested, what failed, next task.

**First response before editing files:** report workspace contents, Windows/Python versions, `nvidia-smi` GPU + VRAM, Node/npm, Git, Ollama (`ollama list`), Vulkan device list if available, and a short plan. Then start Phase 0 without waiting for approval.

---

# 1. PRODUCT VISION AND PRINCIPLES

AETHER UPSCALE is a local-first AI image restoration, enhancement and super-resolution studio. It is not a resize tool and not a wrapper around one model. It combines classical processing, deep-learning SR, specialised restoration, optional face restoration and a transparent router, with tiled inference suited to a constrained laptop.

1. Maximum practical quality on available hardware.
2. Faithfulness is the default; generative changes are opt-in.
3. Every enhancement runs a real pipeline.
4. Useful even if advanced models cannot run; graceful fallback is mandatory.
5. Originals are never modified.
6. Hardware limits and model availability are explained honestly.
7. Every result stores settings, model, version and stage list (reproducible).
8. Privacy-first: no uploads, no telemetry, no training on user images.

## 1.1 Three result classes (must be labelled in UI and metadata)

| Class | Examples | Meaning |
|---|---|---|
| **Restoration** | denoise, JPEG artifact reduction, deblur | Aims to recover degraded real content |
| **Traditional enhancement** | sharpen, color, contrast, resample | Not AI; no new detail |
| **Generative detail** | GAN SR, face restoration, colorization, diffusion | May invent plausible detail that was not in the source |

Even GAN-based SR (Real-ESRGAN) is partly generative. "Faithful" means the *lowest-hallucination option available* (PSNR-oriented model / fidelity slider toward fidelity), not a guarantee. Never claim generated detail is the original detail.

---

# 2. USERS AND USE CASES

Owner: developer/student, Windows 11 laptop, 8 GB RAM, RTX 2050, Python/VS Code/web experience, Ollama installed (optional).

Image categories: photographs, portraits, old/scanned photos, anime/manga, digital art and game assets, landscapes/architecture, screenshots and compressed web images, product images/textures.

Out of scope: perfect restoration of illegible text, forensic reconstruction, historically accurate detail guarantees, video processing.

---

# 3. FUNCTIONAL SCOPE

## 3.1 Modes
1. **Restore** — correct degradation, preserve original look.
2. **Upscale** — SR with selected model.
3. **Restore + Upscale** — analyze, restore at low resolution, then upscale (and optional face pass).
4. **Generative Restore** — optional, off by default, clearly marked, unavailable unless hardware allows.
5. **Manual / Expert** — choose model and individual steps.

## 3.2 Upscaling
- 2× (native `x2plus` model when installed; do not run 4× then downscale), 4×.
- **8× is experimental**: staged two-pass, explicit warning (compounded artifacts/hallucination), subject to the output-pixel cap. Never the default; never claim a native 8× model.
- Custom target width/height with aspect lock: pick the smallest native scale ≥ target, then resample down with anti-aliasing (area/Lanczos). Never stretch or crop to fit.
- Show output dimensions, estimated memory and file size before processing.

## 3.3 Restoration and enhancement
- Denoise (Off/Low/Medium/High where supported; for `realesr-general-x4v3` implemented via WDN weight interpolation).
- JPEG artifact reduction (see 6.4; otherwise conservative classical fallback, labelled traditional).
- Mild blur recovery only where the model supports it.
- Optional face restoration (opt-in, feathered paste-back with blend weight).
- Optional conservative color/contrast/sharpen (traditional, labelled).
- Scratch/damage repair: **manual-mask inpainting only** (LaMa or classical `cv2.inpaint`). Automatic scratch detection is not claimed unless a real model is integrated.
- Colorization, if ever added, is generative and labelled so.
- Alpha-preserving processing (see 7.5).

## 3.4 Presets
Photo, Portrait, Anime/Illustration, Old photo, Screenshot/compressed, Auto-detect (advisory, with confidence, always overridable).

## 3.5 Controls
Scale; Mode; Model (Auto/explicit); **Fidelity 0–100** (real implementation: network-weight interpolation between PSNR-oriented RealESRNet and GAN RealESRGAN x4plus, same RRDBNet architecture; verify output sanity before exposing; pixel-space blend as fallback); Detail creativity (only for generative models that expose it); Face enhancement + blend weight; Denoise; Output format PNG/JPEG/WebP + quality; Output folder; Tile size Auto/128/192/256/384/512 where supported; TTA (8× slower, off by default). Hide or disable (with explanation) any control the selected model does not support.

## 3.6 Comparison, preview, export
- **Crop-preview mode:** process a 256–512 px region in seconds to tune settings before a full run.
- **A/B model compare** on the same crop.
- Draggable before/after slider, side-by-side, original/output/difference toggle, fit/100%, synchronized zoom/pan.
- Show original/output dimensions, processing time, model, stage list.
- Export PNG/JPEG/WebP; preserve alpha where supported; never silently flatten transparency.
- Batch queue with per-image status and cancellation.
- Embed provenance in output metadata (PNG text/XMP): "AI-enhanced; model; settings; generated detail may not be real."

## 3.7 Input handling
JPEG, PNG, WebP, BMP, TIFF; HEIC/AVIF via `pillow-heif` / AVIF plugin when installed; 16-bit and grayscale; CMYK converted to sRGB; EXIF orientation applied; ICC profile preserved or converted to sRGB and embedded. Animated images rejected with a clear message.

---

# 4. HARDWARE-AWARE EXECUTION

## 4.1 Profiles (runtime detection)
- **A — Constrained (expected):** 8 GB RAM, RTX 2050. One neural model at a time, conservative tiles/overlap, FP16 only when validated (FP32 fallback), diffusion disabled, CPU fallback only for small images.
- **B — Moderate / C — High-end:** larger tiles and optional extra models; still one large model at a time unless memory clearly allows.
The UI displays detected hardware and which models are available on it.

## 4.2 Hardware realities the implementation must handle
1. **Effective RAM is ~3–4 GB** after Windows and browser. Budget against that.
2. **Hybrid GPU:** NCNN picks Vulkan devices by index; device 0 may be the Intel iGPU. Enumerate Vulkan devices and select the NVIDIA one explicitly (`-g`). PyTorch must use the CUDA device.
3. **VRAM tracking:** use `torch.cuda.mem_get_info` / `nvidia-ml-py` before loading. Windows/browser use part of VRAM, so usable VRAM is less than total.
4. **Sysmem fallback:** recent NVIDIA drivers can spill into system RAM instead of raising OOM, causing severe slowdowns. Monitor VRAM and warn when throughput collapses; do not rely on OOM exceptions alone.
5. **Thermals/power:** record power mode and clocks in benchmarks; advise plugged-in, performance power plan.
6. `torch.compile` is not supported on Windows without Triton — do not use. Use FP16 autocast and `channels_last`.
7. Multiprocessing uses `spawn` (no fork on Windows). Handle file locking when deleting outputs in use.

## 4.3 Memory rules
- Lazy-load models; unload before loading a large one; cache only small models if memory allows.
- `torch.inference_mode()`; release references before `torch.cuda.empty_cache()`.
- Keep intermediates as uint8/float16 arrays; avoid repeated PNG round-trips between stages.
- **Large outputs:** a 4000×3000 image at 4× is 192 MP (~576 MB uint8, ~2.3 GB float32). Never assemble this naively in memory. Stream output tiles/strips to disk (memmap or striped TIFF, then encode) and enforce a configurable **max output megapixel cap** with a clear error. Handle Pillow's decompression-bomb limit deliberately. Never silently downscale the source.
- Never freeze the UI during inference.

## 4.4 Quality tiers
- **Tier 1 (default, reliable):** Real-ESRGAN family, tiled inference, OpenCV/Pillow post-processing, optional face restoration.
- **Tier 2 (optional, benchmark first):** SwinIR real-world SR (slow, small tiles), FBCNN/SCUNet pre-passes, one face model, LaMa manual inpainting.
- **Tier 3 (research, not default, may be unavailable):** HAT-L/Real-HAT-GAN, DiffBIR, SUPIR, HYPIR, one-step diffusion SR. Do not promise they run on this laptop; do not quote VRAM numbers that were not measured.

---

# 5. MODEL CATALOGUE

Ollama is not an SR engine. It may optionally caption/suggest presets via a vision model, run on CPU or with `keep_alive: 0`, never concurrently with an SR job, never in the critical path.

## 5.1 Core (Tier 1) — official repo https://github.com/xinntao/Real-ESRGAN
| Role | Model | Notes |
|---|---|---|
| General photo SR | `RealESRGAN_x4plus` (RRDBNet) | Baseline. https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth |
| Anime/illustration | `RealESRGAN_x4plus_anime_6B` | https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth |
| Small/fast + denoise control | `realesr-general-x4v3` (+ WDN weights) | Compact network, suited to 4 GB; denoise strength by weight interpolation |
| Native 2× | `RealESRGAN_x2plus` | Avoids 4×→downscale |
| Faithful / low-hallucination | `RealESRNet_x4plus` | PSNR-oriented, smoother |

Code license BSD-3-Clause (fairly confident, **[verify]**). Weight terms: mark **unclear** until release notes/model card are read.

## 5.2 Backends
- **NCNN Vulkan (first backend, fallback forever):** https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases. Inspect `-h` before relying on flags. Typical flags: `-i -o -n -s -t -g -f`. Portable build ships `realesrgan-x4plus`, `realesrgan-x4plus-anime`, `realesrnet-x4plus`, `realesr-animevideov3`. NCNN stitching differs from the Python tile engine; test seams.
- **Torch + Spandrel (primary Python backend):** Spandrel (chaiNNer-org/spandrel) loads many SR architectures from state dicts via one API without cloning each research repo and avoids BasicSR dependency problems. Check supported architectures for the installed version; per-architecture licenses may differ **[verify]**. Supply the project's own tile engine.
- **Avoid BasicSR/official Real-ESRGAN pip stacks in the main env.** Known problems: `basicsr` imports `torchvision.transforms.functional_tensor` (removed in newer torchvision), NumPy 2 incompatibilities. If a legacy repo is required, isolate it (5.5).
- Optional: ONNX Runtime + DirectML for compact models.
- Community models: OpenModelDB lists per-model licenses; audit each before adding. Newer efficient SR models may exist beyond what this document knows — check there.

## 5.3 Restoration (Tier 2, all **[verify license + checkpoint]**)
- **FBCNN** — blind JPEG artifact reduction with adjustable quality factor; run before SR on heavily compressed images.
- **SCUNet** — blind denoising.
- **NAFNet** — motion deblur only; not general defocus restoration.
- **LaMa** — user-masked inpainting for damage/scratches.
- **SwinIR** (https://github.com/JingyunLiang/SwinIR) — real-world SR checkpoint; slow, small tiles; select a specific checkpoint and verify source/license.

## 5.4 Face restoration (optional, opt-in)
- **GFPGAN v1.4** (https://github.com/TencentARC/GFPGAN) — code Apache-2.0 **[verify]**; depends on `facexlib`/`basicsr`; run isolated.
- **CodeFormer** (https://github.com/sczhou/CodeFormer) — I believe non-commercial S-Lab license **[verify]**; has a real fidelity parameter.
- Benchmark both on a few faces; keep **one**. Do not chain both.
- Face detection: OpenCV YuNet (`cv2.FaceDetectorYN`) **[verify weight license]**. Avoid face-analysis stacks with non-commercial weights unless reviewed.
- Always feathered-mask paste-back with user blend weight; faces may change identity details; keep the pre-face result for comparison.

## 5.5 Dependency isolation
One main env (torch + spandrel + core). Legacy repos (GFPGAN etc.) run in separate venvs behind a JSON-over-stdio worker protocol. Never mix competing model environments into one fragile env.

## 5.6 Unsuitable for default / likely unsuitable for 4 GB
SUPIR (SDXL-based; license believed non-commercial **[verify]**), DiffBIR (SD-based), HYPIR (unverified), HAT-L/Real-HAT-GAN (slow), full diffusion pipelines. Treat as research; report "unavailable" with the reason if hardware is insufficient. One-step diffusion SR (OSEDiff-class) is cheaper but still loads an SD-size backbone; feasibility test only, no promise.

## 5.7 Licensing policy
- Registry stores per model: code license, **weight license**, source URL, hash, status (verified/unclear), `license_class` (permissive / non-commercial / unclear).
- Personal local use is not blocked by non-commercial licenses. Only the "distributable build" is gated by `license_class`.
- UI shows license status per model.

---

# 6. ANALYSIS AND ROUTING

## 6.1 Analyzer (estimates, not ground truth; include confidence)
- JPEG: read quantization tables via Pillow for an actual quality estimate; blockiness via 8×8 grid periodicity.
- Noise: robust estimator (MAD / Immerkaer).
- Blur: Laplacian variance normalized for resolution.
- Faces: YuNet detection.
- Category: heuristics (palette size, edge statistics, saturation), plus optional zero-shot CLIP on CPU. Always overridable.
- Output example: `{width, height, format, has_alpha, estimated_blur, estimated_noise, jpeg_quality_estimate, face_count, image_category, confidence}`.
The analyzer must work without Ollama.

## 6.2 Router
Inputs: image type, dimensions, degradation estimates, mode, scale, installed + smoke-tested models, free VRAM/RAM, license class, estimated time. Output includes a plain-language explanation (e.g., "Selected RealESRGAN x4plus: general photo, installed, fits available VRAM").
Rules:
- Anime + upscale → anime model. Photo + upscale → x4plus (or general-x4v3 if VRAM tight / denoise wanted).
- Heavy JPEG artifacts → FBCNN pre-pass if installed, else conservative classical step (labelled).
- Faithful mode → never generative; prefer RealESRNet / fidelity slider toward fidelity.
- Face enhancement only if installed, opted-in and a face is detected.
- Auto mode chooses only from smoke-tested models.
- Never run every model in sequence; never silently swap a selected generative operation for another model.

---

# 7. PIPELINES

Order principle: artifact removal/denoise at **low resolution** (cheaper, avoids amplifying blocks) → SR → face pass → conservative post. Avoid duplicate denoising (e.g., skip extra denoise when general-x4v3 handles it).

## 7.1 Restore
Decode, apply orientation/ICC → analyze → pick restoration model → tiled run → alpha handled separately → conservative post (opt-in) → validate → save + metadata.

## 7.2 Upscale
Validate scale/dimensions/pixel cap → analyze → route → estimate memory/disk → SR → resample to exact size if needed → validate dimensions/seams → save.

## 7.3 Restore + Upscale
Analyze → low-res restoration → SR → optional face pass → optional color/contrast → consistency check → save. Each stage recorded in metadata.

## 7.4 Generative (optional, off by default)
Explicit selection; hallucination warning; never in Faithful mode; save the non-generative result as an alternate output; record model/settings; if it cannot fit, report why without crashing.

## 7.5 Alpha
Bleed colors outward under transparent pixels **before** upscaling to avoid dark/white halos; upscale alpha separately (Lanczos/bicubic) and recombine. Never silently flatten.

## 7.6 Post-processing
Restrained only: mild sharpen, color, contrast, denoise. No aggressive sharpening by default, no fake detail overlays, avoid clipping. Keep the untouched neural output for comparison.

## 7.7 Faithfulness aids
- **Downscale-consistency check:** downsample output to input size and compare with input (catches color shifts and gross hallucination). Optional iterative back-projection correction of low frequencies, labelled traditional.
- Difference view in the UI.

---

# 8. TILED INFERENCE

- Configurable tile size; halo/overlap ≥ the model's receptive-field needs; reflect padding at edges.
- Correct coordinate mapping for scale; Hann/Gaussian feathered blending in overlaps; deterministic placement.
- Progress by completed tiles; cancellation between tiles; release tensors promptly.
- On CUDA OOM: retry with smaller tile; then unload other models and retry once; then CPU only if size/time acceptable; then NCNN if installed; otherwise explain.
- Model-specific tile defaults, benchmarked, not hardcoded universals.
- Stream output to disk (4.3).
- Unit test for seams and coordinate mapping.
- Test images: 512×512, 1920×1080, 4000×3000 (subject to pixel cap), portrait, odd dimensions, transparent PNG, very wide panorama.

---

# 9. ARCHITECTURE

Modular monolith; no microservices/Kubernetes/cloud.

```
React/Vite/TS (preview derivatives, SSE, crop viewer)
        | REST + SSE (127.0.0.1 only)
FastAPI API -- SQLite (jobs, settings, model status)
        | DB-backed job queue (1 concurrent job on Profile A)
Worker subprocess (spawn, killable, owns the GPU)
  - Analyzer (CPU)
  - Router
  - Pipeline: [pre-pass] -> SR -> [face] -> [post]
  - Tile engine (halo, feathered blend, OOM retry, streaming output)
  - Backends: Torch+Spandrel | NCNN-Vulkan (explicit GPU index)
              | isolated-venv legacy workers
  - QA: consistency check, optional metrics
Storage: uploads / outputs / previews / temp on disk; originals untouched
```

- **No RQ/Redis/Celery** (RQ does not work on Windows; Redis is not officially supported on Windows). Use a SQLite job table + worker subprocess.
- Inference never runs inside the FastAPI request process. Cancel by terminating the worker/NCNN process; ensure cleanup of partial outputs.
- Progress via Server-Sent Events (simpler than WebSockets) or polling.
- Persist job state; after a crash/power loss mark running jobs failed cleanly. Check free disk before starting; configurable quota cleanup.
- CLI with parity to the API (batch and testing).
- A `doctor` command checks GPU, VRAM, Vulkan devices, weights (SHA256 vs manifest), backends and smoke tests.

## 9.1 Model interface
Adapters implement `load(device, precision)`, `enhance(...)`, `unload()`, `capabilities()`. Prefer in-memory arrays between stages; path-based entry points are fine for NCNN. Supports progress callback and cancel.

## 9.2 Model registry fields
id, display name, adapter, checkpoint path, version/hash, source URL, code license, weight license, license status, license_class, tasks, image types, scales, min VRAM estimate (measured), CPU support, precision support, availability status (weights present + smoke test passed), experimental flag, enabled on current hardware profile.

## 9.3 Weight management
Manifest with source URL, SHA256, size. Downloader script verifies hashes. Weights and user images are git-ignored.

---

# 10. BACKEND API

Versioned endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Health |
| GET | `/api/v1/system/capabilities` | Hardware, Vulkan devices, runtime |
| GET | `/api/v1/models` | Registry + license status |
| POST | `/api/v1/images` | Upload |
| POST | `/api/v1/images/{id}/analyze` | Analyze |
| POST | `/api/v1/jobs` | Create job (full or crop-preview) |
| GET | `/api/v1/jobs/{id}` | Status |
| GET | `/api/v1/jobs/{id}/events` | SSE progress |
| POST | `/api/v1/jobs/{id}/cancel` | Cancel |
| GET | `/api/v1/jobs/{id}/preview` | Preview derivative |
| GET | `/api/v1/jobs/{id}/crop` | Cropped region at 100% (x,y,w,h) |
| GET | `/api/v1/jobs/{id}/download` | Result |
| DELETE | `/api/v1/jobs/{id}` | Delete job + files |

Job request fields: `image_id, mode, scale, target_size?, image_type, model, face_enhancement, face_blend, fidelity, detail_creativity, denoise, output_format, quality, tile_size, tta, crop_region?`.
Job status: `{job_id, status, stage, progress|null, message, result_available, warnings[]}`.

Requirements: validate every field; no filesystem paths from the browser; validate MIME and actual decoded format; file-size and pixel limits; opaque server-side IDs; sanitized filenames; outputs confined to the storage root; structured error codes; no stack traces to the frontend; no image content or sensitive paths in logs; request timeouts.

---

# 11. FRONTEND

Stack: React + TypeScript + Vite + Tailwind (follow the current official Tailwind install docs; do not assume older config).

Direction: clean, dark, professional; large central canvas; compact settings panel; accessible keyboard focus; no animations that slow the editor.

Pages: Workspace (upload, recent jobs, formats/limits, hardware summary), Editor, History (thumbnails, metadata, reopen/download/delete), Settings (output folder, limits, defaults, GPU/CPU preference, model availability + license status, cleanup, privacy).

Genuine states: Uploading, Validating, Analyzing, Waiting for model, Loading model, Processing, Blending tiles, Validating output, Completed, Failed, Cancelled.

Viewer: stacked `<img>` with CSS clip for the slider; transform-based pan/zoom on **preview derivatives**; 100% inspection via the backend `/crop` endpoint. Never load full-resolution outputs into multiple canvases. Display the result-class label (Restoration / Traditional / Generative) and the generated-detail warning.

---

# 12. QUALITY ASSURANCE

## 12.1 Metrics
PSNR, SSIM (reference required), LPIPS/DISTS (reference), NIQE/MUSIQ etc. via `pyiqa` (no-reference, optional), runtime, peak VRAM/RAM, dimensions, file size. Never show made-up scores. No-reference metrics do not prove faithfulness; a sharp result can contain hallucinated detail.

## 12.2 Test data
Self-made **synthetic degradation set**: downscale, blur, noise, JPEG applied to your own high-resolution images, so full-reference metrics mean something. PSNR/SSIM on bicubic-downsampled images do not predict real-world GAN quality. Use only legally usable images. Do not auto-download large datasets (DIV2K, Set5/Set14, Urban100, RealSR, DRealSR, Manga109 — verify access/terms).

## 12.3 Visual matrix
Faces, hair, text/signs, foliage, architecture, fabric, anime line art, gradients, JPEG artifacts, low-light noise, transparent PNG, old scans. Compare same inputs/settings after every model change; keep baseline outputs. A metric gain is not proof of better perceptual quality.

---

# 13. ERROR HANDLING

Explicit handling: CUDA unavailable, CUDA OOM, missing weights, corrupted checkpoint, unsupported image, decompression bomb/extreme dimensions, output over pixel cap, disk full, alpha issues, inference failure, wrong Vulkan device, cancellation, invalid settings, backend unavailable. Fallback order per section 8. Never silently change a selected generative operation into a different model.

---

# 14. SECURITY AND PRIVACY

- Bind to `127.0.0.1`; CORS only for the configured frontend origin.
- Validate extensions and decoded signatures; upload/pixel limits; random internal IDs; sanitize filenames; prevent path traversal; subprocess argument arrays only.
- One concurrent job on Profile A; queue the rest; safe cancellation and cleanup.
- Store job metadata in SQLite; never image binaries. Do not expose local paths in API responses.
- No telemetry; delete controls; configurable temp cleanup.
- Tests for malformed inputs and path traversal.

---

# 15. PROJECT STRUCTURE

```text
AETHER-UPSCALE/
├── AGENTS.md
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── requirements.txt
├── frontend/            (Vite React TS: app, components, pages, services, hooks, store, types)
├── backend/app/         (main.py, api, core, schemas, services, database, workers)
├── ai_engine/           (analysis, routing, registry, models/{base,realesrgan,spandrel_adapter,swinir,face,inpaint,generative}, pipelines, processing, memory, quality)
├── tools/realesrgan-ncnn-vulkan/
├── weights/             (README.md + manifest; weights git-ignored)
├── storage/             (uploads, outputs, previews, temp)
├── tests/               (unit, integration, api, fixtures)
├── benchmarks/
├── scripts/             (doctor, download_weights, test_upscale)
└── docs/                (ARCHITECTURE, MODEL_LICENSES, IMPLEMENTATION_STATUS, DECISIONS, KNOWN_LIMITATIONS, TEST_PLAN, USER_GUIDE)
```
No `docker-compose.yml` and no root `package.json`.

---

# 16. PHASES AND ACCEPTANCE

Each phase is tested before the next. Give the agent one phase per prompt.

**Phase 0 — Environment + real inference**
Tasks: inspect OS/Python/Node/Git/GPU/Vulkan/Ollama; create project, `AGENTS.md`, docs stubs; create venv; verify PyTorch/CUDA if feasible; obtain official NCNN build; fetch only `realesrgan-x4plus`; write `scripts/test_upscale.py`; run one real image; record exact commands and versions.
Acceptance: real image → real upscaled output; dimensions verified; runtime and backend reported; NVIDIA device confirmed (not iGPU); no mock output; README has exact commands.

**Phase 1 — Minimal backend**
FastAPI health, upload, NCNN adapter behind the model interface, DB-backed job table + worker subprocess, status, download, safe storage.
Acceptance: upload → inference → download via API; structured errors; original unchanged; model availability reported accurately; cancel kills the worker cleanly.

**Phase 2 — Web MVP**
Vite app, dropzone, mode/scale, start/cancel, real status (SSE), preview, download.
Acceptance: full flow in browser; no faked progress.

**Phase 3 — Professional editor**
Slider, side-by-side, zoom/pan, preview derivatives, `/crop` 100% view, history, export formats, settings, crop-preview mode.
Acceptance: large images do not crash the browser; comparison aligned; export dimensions/format correct.

**Phase 4 — Models, analyzer, router**
Torch + Spandrel backend; add anime, general-x4v3, x2plus, RealESRNet; registry with license fields; analyzer with real signals; router with explanations; manual override; fidelity slider via weight interpolation; A/B compare.
Acceptance: ≥2 real model paths (photo + anime); router picks only smoke-tested models; interpolation output sane.

**Phase 5 — Tiling and hardware optimization**
Tile engine with feathering, OOM retry, streaming output, memory manager, pixel cap, VRAM/sysmem monitoring, CPU/NCNN fallback.
Acceptance: 1080p reliable; larger image works via streaming where under the cap; no visible seams in test set; OOM handled without corrupting output.

**Phase 6 — Restore + Upscale and advanced controls**
Low-res pre-pass (FBCNN/SCUNet if verified), combined pipeline, one face model (isolated), alpha handling, ICC/EXIF/16-bit/HEIC, conservative post, consistency check, provenance metadata, LaMa manual inpainting (optional).
Acceptance: restore-only, upscale-only, combined all work and are distinct; stages recorded; unsupported controls hidden/explained.

**Phase 7 — Generative research (optional)**
Review licenses/compute; try only if a compatible runtime fits; optional plugin; hallucination warning; faithful output saved separately.
Acceptance: no effect on normal startup; clear "unavailable" on insufficient hardware; no factual-reconstruction claims.

**Phase 8 — Tests, security, benchmarks, release**
Automated tests, benchmark suite on the synthetic set, file validation, privacy review, docs, clean setup.
Acceptance: fresh setup works; tests pass; no secrets/weights committed; limitations documented; one documented run command per service.

---

# 17. TEST PLAN (minimum)

**Unit:** metadata, format validation, output dimension math, registry, router, tile mapping, overlap blending/seam test, alpha bleed + recombine, storage ID/path safety, pixel-cap enforcement, weight interpolation.
**Integration:** adapter smoke test, upload → job → download, cancellation (worker kill), OOM fallback (mock the exception), missing-model behavior, wrong-GPU detection.
**Visual:** face, anime, landscape, JPEG-compressed, transparent PNG, odd dimensions, portrait, large image.
**Regression:** small fixed legally usable set with baseline outputs; compare dimensions and visual differences after changes.

---

# 18. DEFINITION OF DONE

Frontend and backend run; real inference works; photo and anime workflows work if models are installed; restore/upscale/combined are distinct and real; before/after works; downloads correct; large images use safe tiled/streamed processing within the cap; hardware detection (including correct GPU selection) works; no fake progress or results; model availability, license status and limitations are transparent; result classes labelled; originals preserved; validation and privacy implemented; tests pass; README has exact Windows setup/run steps; `IMPLEMENTATION_STATUS.md` is accurate.

---

# 19. COPY-PASTE START PROMPT FOR ANTIGRAVITY (Phase 0 only)

```text
Read PRD.md (v2.0) completely, especially sections 0, 4, 5 and 16. It is the source of truth for AETHER UPSCALE.

Do ONLY Phase 0 now.

Rules:
- Inspect the workspace and machine before editing. Never overwrite unknown files or run destructive commands.
- Windows 11 + PowerShell. No paid services, API keys, cloud, Docker, Redis or WSL.
- Real inference only. No mock outputs, no fake progress.
- Download only the official Real-ESRGAN NCNN Vulkan build and the realesrgan-x4plus model. Verify hashes where available.

Steps:
1. Report: workspace contents; Windows/Python versions; nvidia-smi GPU and VRAM; Node/npm; Git; Ollama and `ollama list`; Vulkan devices.
2. Create AGENTS.md (from PRD section 0), the folder structure (section 15, without docker-compose or root package.json), and docs/IMPLEMENTATION_STATUS.md, DECISIONS.md, KNOWN_LIMITATIONS.md.
3. Create .venv; verify PyTorch/CUDA only if it works quickly (use the exact command from the official PyTorch selector). If it blocks, stop and use NCNN.
4. Get the official NCNN Vulkan build; inspect `-h`; make sure the NVIDIA GPU (not the Intel iGPU) is selected via -g.
5. Write scripts/test_upscale.py and run one real image through realesrgan-x4plus at 4x.
6. Verify output exists, dimensions are exactly 4x, record runtime, backend and GPU used.
7. Write exact commands and results to README.md and docs/IMPLEMENTATION_STATUS.md.

At the end state what works, what was tested, what failed, and the next task. Do not start Phase 1 until I confirm.
```

---

# 20. OFFICIAL REFERENCES

- Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN
- Real-ESRGAN NCNN Vulkan: https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan
- Spandrel: https://github.com/chaiNNer-org/spandrel
- OpenModelDB: https://openmodeldb.info/
- SwinIR: https://github.com/JingyunLiang/SwinIR
- HAT: https://github.com/XPixelGroup/HAT
- GFPGAN: https://github.com/TencentARC/GFPGAN
- CodeFormer: https://github.com/sczhou/CodeFormer
- DiffBIR: https://github.com/XPixelGroup/DiffBIR
- SUPIR: https://github.com/Fanghua-Yu/SUPIR
- HYPIR: https://github.com/XPixelGroup/HYPIR
- BasicSR: https://github.com/XPixelGroup/BasicSR
- PyTorch install selector: https://pytorch.org/get-started/locally/
- FastAPI: https://fastapi.tiangolo.com/
- Vite: https://vite.dev/
- Tailwind: https://tailwindcss.com/docs/installation
- Ollama: https://ollama.com/
- Antigravity docs: https://www.antigravity.google/docs

**Final instruction:** The first proof of success is not a dashboard. It is a real image processed by a real model on the NVIDIA GPU, with verified dimensions and no fake processing.
