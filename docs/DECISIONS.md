# Architectural Decisions Record — AETHER UPSCALE

## ADR 001: Python 3.11 Runtime Selection
- **Context:** System default is Python 3.14.0. PyTorch and Torchvision pre-built CUDA binary wheels are not currently released for Python 3.14 on Windows.
- **Decision:** Use Python 3.11 managed via `uv` for `.venv`.
- **Status:** Accepted.

## ADR 002: Dual Inference Backends (NCNN-Vulkan + PyTorch Spandrel)
- **Context:** Constrained 4GB VRAM laptop with hybrid Intel/NVIDIA graphics.
- **Decision:** Support NCNN Vulkan binary backend as portable zero-dependency engine, and PyTorch + Spandrel for advanced features (weight interpolation, custom models).
- **Status:** Accepted.


## ADR 003: Version Graph Data Model & Immutable Artifacts (AETHER 2.0)
- **Context:** `FINAL_SPEC.md` requires outputs to become reusable sources for multi-stage pipelines without browser re-uploads, while guaranteeing prior versions are never modified or corrupted.
- **Decision:** Implement a Project -> Version directed acyclic graph in SQLite. Versions once marked `ready` are set immutable and read-only.
- **Status:** Accepted.

## ADR 004: Tiling Ownership — Python TileEngine with Lossless Tile Store
- **Context:** Phase 0 audit evaluated whether tiling should be owned solely by NCNN binary (`-t`) or orchestrated in Python.
- **Decision:** Python `TileEngine` orchestrates macro-tiles, computes 2D Hann/raised-cosine overlap masks, and manages a tile store on disk. This enables tile-by-tile checkpointing, pause/resume at tile boundaries, and cancellation without corrupting partial outputs.
- **Status:** Accepted.

## ADR 005: Resolution Strategy for 4K -> 8K (The 16K Intermediate Problem)
- **Context:** Applying a 4x super-resolution model to 3840x2160 yields 15360x8640 (132.7 MP), which exceeds 100 MP RAM limits and causes memory thrashing.
- **Decision:** Use **Per-Tile Scale Adaptation** (Plan F4 #2): run the 4x model per tile with halo, immediately downscale each tile by 0.5x with anti-aliasing (Lanczos/area) to match the exact 8K target, and blend into the 8K accumulator. Fall back to disk-backed intermediate if seam suppression requires it.
- **Status:** Accepted.
