# Architecture — AETHER UPSCALE

## 1. Overview
Modular local-first monolith for AI super-resolution, restoration, and traditional enhancement on constrained hardware (RTX 2050 4GB VRAM, 8GB RAM).

## 2. Subsystems
- **Frontend:** React + TypeScript + Vite + Tailwind CSS.
- **Backend API:** FastAPI running on `127.0.0.1` + SQLite job database.
- **Worker Subprocess:** Spawned isolated inference process owning GPU operations.
- **AI Engine:**
  - Analyzer (Laplacian blur, Immerkaer/MAD noise, JPEG Q-table analysis, YuNet face detection)
  - Router (rules engine mapping image degradation and user intent to smoke-tested models)
  - Tile Engine (feathered Hann/Gaussian blending, coordinate scaling, streaming disk output)
  - Model Registry & Adapters (NCNN Vulkan & Torch+Spandrel)

