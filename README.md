# AI Image Upscaler

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![Vulkan](https://img.shields.io/badge/Vulkan-1.4-red.svg)](https://www.vulkan.org)
[![Tests Passing](https://img.shields.io/badge/tests-83%2F83%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A free, local AI super-resolution studio designed to scale images up to 8K UHD on consumer hardware.**  
Runs offline via Vulkan shaders with specialized processing for manga, anime, and realistic photography.

[Quick Start](#-quick-start) • [Key Differences](#-how-it-differs-from-standard-upscalers) • [Core Features](#-core-features) • [System Limits](#-hardware-requirements--limits) • [Benchmarks](#-benchmarks) • [Architecture](#-architecture)

</div>

---

## ⚖️ How It Differs from Standard Upscalers

| Aspect | Standard AI Upscalers | This Studio |
| :--- | :--- | :--- |
| **Pricing & Privacy** | Paid subscriptions, monthly credit limits, or cloud fees. | **100% Free & Unlimited**. Fully offline; no image data ever leaves your computer. |
| **Hardware Fit** | Heavy scripts or cloud dependencies that crash entry-level GPUs on large images. | **Hardware Adaptive**. Preflight safety checks evaluate RAM/VRAM to run 8K scaling safely on budget 4GB laptops. |
| **Manga & Line Art** | Smudges halftone screentone dots and creates distracting white halos around black lines. | **Dedicated Manga Engine**: Bounded luminance clamp on line transitions, sub-pixel edge steepening, morphological screentone dot protection, and paper whitening. |
| **Anime & Manga** | Over-smooths flat color zones and smudges line work. | **Stock Real-ESRGAN Anime + Custom CV Outline Engine**: Clean line borders with sub-pixel edge steepening, morphological screentone dot protection, and zero-halo bounding. |
| **Realistic Photos** | Blurs fine skin/fabric textures into waxy synthetic artifacts. | **Degradation-Aware Analysis**: Laplacian blur and noise variance estimation preserve natural high-frequency textures. |
| **Archival / Forensic** | Forces AI hallucination on everything, inventing fake details on text/documents. | **Controllable Hallucination (Plan C)**: Pure anti-aliased Lanczos resample with 0% AI hallucination for authentic fidelity. |
| **Batch Processing** | Either missing or tries to run concurrently, causing out-of-memory GPU crashes. | **Sequential GPU Queue**: Safely processes multiple images one-by-one, exporting all results in a single ZIP. |

---

## 🚀 Core Features

### 1. Progressive 8K Scaling Engine
* **Micro-Tile Streaming:** Slices large inputs into manageable tiles with 2D Hann-feathered cosine blending.
* **Zero Seam Artifacts:** Eliminates visible tile gridlines and prevents high-RAM exhaustion during high-megapixel upscaling.

### 2. 4-Pillar Manga & Line Art Engine
* **Sub-Pixel Edge Steepening:** Non-linear sigmoid remap sharpens line boundaries without thickening strokes.
* **Zero-Halo Clamping:** Pixel luminance is strictly bounded to eliminate ringing spikes along high-contrast edges.
* **Screentone Frequency Protection:** Distinguishes fine halftone dot patterns from line strokes to prevent smudging.
* **Paper Purification & Deep Ink:** Background scanner haze ($L > 232$) snaps cleanly to pure white (`#FFFFFF`), while line cores ($L < 32$) snap to deep black (`#000000`).

### 3. Sequential Batch Queue
* Drag-and-drop multi-file uploads.
* Thread-safe single-worker dispatcher processes items sequentially to protect GPU VRAM.
* Real-time progress tracking, pause/resume controls, and one-click ZIP package download.

### 4. Interactive Studio UI
* Draggable Before/After split comparison slider.
* Synchronized side-by-side zoom (100% to 300%).
* Real-time image degradation analysis (Laplacian blur score, noise variance, JPEG quality estimate).
* Non-destructive version graph tracking parent/child versions and processing parameters.

---

## 🖥️ Hardware Requirements & Limits

### System Requirements

| Component | Minimum (Budget / Laptop) | Recommended (Desktop / Workstation) |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11 (64-bit); Multiplatform binaries packaged (Linux x86_64, macOS via MoltenVK) | Windows 11 (64-bit) (Hardware Verified) |
| **Processor (CPU)** | Intel Core i3 (8th Gen+) / AMD Ryzen 3 (1000+), 4 cores | Intel Core i5/i7 (11th Gen+) / AMD Ryzen 5/7, 6+ cores |
| **System Memory (RAM)** | **8 GB DDR4** ($\ge$ 4 GB free available memory) | **16 GB DDR4/DDR5** or higher |
| **Graphics (GPU)** | **Vulkan 1.1+ Compatible**: GTX 960 / RTX 2050 Mobile / RX 550 / Intel Iris Xe | **NVIDIA RTX 3060 / 4050 / 4060+** (6 GB – 8 GB+ VRAM) |
| **Video Memory (VRAM)** | **2 GB – 4 GB VRAM** (micro-tiling handles memory caps) | **6 GB – 8 GB+ VRAM** |
| **Disk Space** | 2 GB free SSD space for dependencies and model checkpoints | NVMe SSD |

### Maximum Resolution Limits

| Mode | Max Resolution | Megapixels | Memory Strategy & Hardware |
| :--- | :--- | :--- | :--- |
| **Standard 2× / 4×** | 4K UHD ($3840 \times 2160$) | **8.29 MP** | Direct neural pass or single-pass 512px tiling (4 GB VRAM) |
| **Progressive 8K Engine** | **8K UHD ($7680 \times 4320$)** | **33.18 MP** | Hann-feathered micro-tile streaming (tested on **4 GB VRAM / 8 GB RAM**) |
| **Architectural Hard Limit** | **Up to $8192 \times 8192$** | **67.11 MP** | Multi-pass staged tile stitching (6 GB+ VRAM / 16 GB RAM) |
| **Batch Queue Capacity** | **Unlimited sequential queue** (20+ images/batch) | Single-worker sequential dispatch prevents VRAM accumulation |

> 🛡️ **Safety Preflight System**: Before execution, the backend estimates exact RAM, VRAM, and disk space required for your input. If an operation exceeds safe physical limits, it automatically switches to staged micro-tiling or alerts you before running, preventing system freezes.

---

## ⚡ Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/santosh949/image-upscaler.git
cd image-upscaler
```

### 2. Set Up Python Environment
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Download Models & Native Binaries
Run the setup script to automatically download official Real-ESRGAN NCNN Vulkan binaries and weights:
```bash
python scripts/setup_environment.py
```

### 4. Build Frontend
```bash
npm --prefix frontend install
npm --prefix frontend run build
```

### 5. Launch Application
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🧪 Benchmarks

Measured on **Profile A Constrained Hardware** (Intel Core i5, 8 GB RAM, NVIDIA GeForce RTX 2050 Mobile 4 GB VRAM, Windows 11, Vulkan Device #0).  
Full methodology and raw logs: [`benchmarks/BENCHMARK_RESULTS.md`](benchmarks/BENCHMARK_RESULTS.md).

> **VRAM Telemetry Disclosure:** `Baseline VRAM` reflects pre-inference system state. `Peak Total VRAM` reflects maximum absolute GPU memory during inference. `Est. Incremental VRAM` indicates estimated memory headroom consumed (peak minus baseline), not claimed as exact isolated allocation.

### Category A: Real Photographic Benchmarks (`realesrgan-x4plus`)
| Test Case | Mode | Scale | Input | Output | Megapixels | Latency | Baseline VRAM | Peak Total VRAM | Est. Incremental |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Real Photo 256×256** | `upscale` | 4× | 256 × 256 | 1024 × 1024 | 1.05 MP | **6.46 s** | 129 MB | 1941 MB | +1812 MB |
| **Real Photo 512×512 (Tiled)** | `upscale` | 4× | 512 × 512 | 2048 × 2048 | 4.19 MP | **14.54 s** | 120 MB | 3517 MB | +3397 MB |

### Category B: Real Illustration & Manga Benchmarks (Anime Models)
| Test Case | Model | Scale | Input | Output | Megapixels | Latency | Baseline VRAM | Peak Total VRAM | Est. Incremental |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Real Manga (Manga Crisp)** | `realesrgan-x4plus-anime` | 4× | 256 × 256 | 1024 × 1024 | 1.05 MP | **2.69 s** | 124 MB | 1786 MB | +1662 MB |
| **Real Manga 512×512 (Tiled)** | `realesrgan-x4plus-anime` | 4× | 512 × 512 | 2048 × 2048 | 4.19 MP | **6.06 s** | 144 MB | 3358 MB | +3214 MB |
| **Real Manga (AnimeVideo v3)** | `realesr-animevideov3-x4` | 4× | 256 × 256 | 1024 × 1024 | 1.05 MP | **1.58 s** | 126 MB | 166 MB | +40 MB |

### Category C: Synthetic Signal & Stress Benchmarks
| Test Case | Mode | Scale | Input | Output | Megapixels | Latency | Baseline VRAM | Peak Total VRAM | Est. Incremental |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Synthetic 256×256** | `upscale` | 4× | 256 × 256 | 1024 × 1024 | 1.05 MP | **4.72 s** | 126 MB | 1947 MB | +1821 MB |
| **Classical Restore** | `restore` | 1× | 256 × 256 | 256 × 256 | 0.07 MP | **0.37 s** | 126 MB | 126 MB | +0 MB |
| **Combined Restore + 4×** | `restore_upscale` | 4× | 256 × 256 | 1024 × 1024 | 1.05 MP | **4.33 s** | 126 MB | 1938 MB | +1812 MB |
| **Synthetic 512×512 Tiled** | `upscale` | 4× | 512 × 512 | 2048 × 2048 | 4.19 MP | **12.02 s** | 117 MB | 3506 MB | +3389 MB |

---

## 🏗 Architecture

```text
       Frontend (React 19 + TypeScript + Vite + Tailwind CSS v4)
                                │ HTTP / Server-Sent Events (SSE)
                                ▼
       FastAPI Backend Server (Port 8000)
         ├── Job & Queue Dispatcher (Thread-safe single GPU worker)
         ├── Version Graph DAG Repository (SQLite)
         └── Preflight Resolution Planner (RAM/VRAM Safety Estimator)
                                │ Subprocess Isolation
                                ▼
       Inference Engine (NCNN Vulkan Device 0)
         ├── Degradation Analyzer (Laplacian blur, noise variance, JPEG quality)
         ├── Neural Router (Content-type auto-detection)
         ├── Tiled NCNN Engine (Folder-batching & 2D Hann-feathered cosine blending)
         │     ├── RealESRGAN x4plus (Photographic)
         │     └── RealESRGAN x4plus-anime (Anime / Manga)
         ├── 4-Pillar Manga Outline Engine (Zero-halo bounding & screentone protection)
         ├── Alpha Bleed Channel Preserver (Inpainting + Lanczos alpha)
         └── Provenance Sidecar Embedder (.manifest.json lineage records)
```

---

## 🔬 Testing

Includes **83 automated tests** covering tiling boundaries, memory limits, edge normal steepening, batch queue ordering, execution control (cancellation, pause, checkpoint recovery), security validation, and metadata provenance:

```bash
pytest tests/
```
```text
======================= 83 passed =======================
```

---

## 📜 License & Model Provenance

* **Application Code:** [MIT License](LICENSE)
* **Model Checkpoints:** Stock Real-ESRGAN weights (`realesrgan-x4plus`, `realesrgan-x4plus-anime`) created by Xinntao / Tencent ARC. Neural network architecture is BSD 3-Clause; pre-trained weights are governed by DIV2K/Flickr2K non-commercial research terms.
