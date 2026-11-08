# AETHER UPSCALE 2.0

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![Vulkan](https://img.shields.io/badge/Vulkan-1.4-red.svg)](https://www.vulkan.org)
[![Tests Passing](https://img.shields.io/badge/tests-68%2F68%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Local-first, privacy-respecting AI super-resolution & image restoration studio.**  
*Engineered to run 8K UHD scaling and precision manga inking on budget 4GB VRAM laptops without memory exhaustion.*

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Manga Engine](#-manga--anime-outline-mastery) • [Benchmarks](#-hardware-benchmarks) • [License](#-license)

</div>

---

## 💡 Why AETHER UPSCALE?

Most AI upscalers are simple API wrappers or heavy Python applications that crash entry-level GPUs with out-of-memory errors when processing large images, while smudging fine manga screentones and pencil line art into blurry mud.

**AETHER UPSCALE** is built from the ground up as a **systems-engineered desktop application**:
* **Zero Cloud Dependencies:** 100% local inference using portable C++ NCNN Vulkan shaders. Zero telemetry, zero paid API tokens.
* **8K on a 4GB GPU:** Progressive Per-Tile Scale Adaptation scales 4K images to **8K UHD (7680×4320)** without ever loading massive 16K intermediates into system RAM.
* **Custom Manga & Anime Outline Engine:** Built-in computer vision algorithms providing sub-pixel edge steepening, zero-halo mathematical bounding, and local-variance screentone dot protection.
* **Sequential Batch Queue:** Drag and drop 10+ images at once; an automated queue dispatcher processes them one-by-one to safeguard your GPU, and exports everything in a single ZIP file.
* **Non-Destructive Version Graph:** Git-like DAG tracking parent/child versions, branching, decision history, and interactive split-slider comparisons.

---

## 🚀 Key Features

* **Progressive 4K $\rightarrow$ 8K Engine:** 
  Seamlessly scales large inputs through micro-tile streaming with 2D Hann feathered cosine blending. Eliminates edge seams and prevents RAM thrashing.
* **4-Pillar Manga/Anime Outline Master Engine:**
  * **Sub-Pixel Edge Normal Steepening:** Non-linear sigmoid remap steepens stroke boundaries by >12%.
  * **Zero-Halo Mathematical Bounding:** Pixel luminance is strictly bounded inside $[local\_min, local\_max]$, mathematically eliminating white halo spikes.
  * **Screentone Frequency Protection:** Distinguishes fine halftone shading dots from solid strokes, shielding them from smudging.
  * **Paper Purification & Deep Ink:** Background scanner haze and mosquito artifacts ($L > 232$) smoothly snap to pure `#FFFFFF`, while stroke cores ($L < 32$) snap to deep `#000000` ink.
* **Resolution Planner & Hallucination Controls:**
  * **Plan A:** Fast direct neural single-pass.
  * **Plan B:** Progressive staged super-resolution.
  * **Plan C:** Pure anti-aliased Lanczos resample (0% hallucinated detail for archival/forensic fidelity).
* **Batch Upload & Automated Queue:**
  * Multi-file drag & drop support.
  * Strict single-worker sequential GPU dispatching.
  * Real-time per-item progress, pause/resume checkpoints, and one-click ZIP package download.
* **Professional Interactive Studio UI:**
  * Draggable Before/After split comparison slider.
  * Side-by-side synchronized zoom (100% to 300%).
  * Real-time image degradation analysis (Laplacian blur, noise variance, JPEG quality estimation).
  * 1-second crop inspection mode (`/crop`).
  * Cryptographic provenance sidecar manifests (`.manifest.json`).

---

## 🏗 Architecture

```text
       Frontend (React 19 + TypeScript + Vite + Tailwind CSS v4)
                                │ HTTP / SSE
                                ▼
       FastAPI Backend Server (Port 8000)
         ├── Job & Queue Dispatcher (Thread-safe single GPU worker queue)
         ├── Version Graph DAG Repository (SQLite)
         └── Resolution Planner (Real RAM/VRAM/Disk Preflight Estimator)
                                │ Subprocess Isolation
                                ▼
       Inference Engine (NVIDIA RTX / Vulkan Device 0)
         ├── Degradation Analyzer (Blur, Immerkaer Noise, JPEG Q-tables)
         ├── Neural Router (Plain-language task recommendation)
         ├── Tiled NCNN Engine (Hann feathered cosine overlap blending)
         │     ├── RealESRGAN x4plus (Photographic)
         │     └── RealESRGAN x4plus-anime (Anime / Manga)
         ├── 4-Pillar Manga Outline Engine (Zero-halo edge normal steepening)
         ├── Alpha Bleed Channel Preserver (Inpainting + Lanczos alpha)
         └── Provenance Sidecar Embedder (.manifest.json lineage tracking)
```

---

## ⚡ Quick Start

### Prerequisites
* Windows 10/11, Linux, or macOS.
* Dedicated or integrated GPU supporting **Vulkan** (tested on NVIDIA GeForce RTX 2050 Mobile 4GB VRAM).
* Python 3.11+
* Node.js 18+ & npm

### 1. Clone Repository
```bash
git clone https://github.com/your-username/aether-upscale.git
cd aether-upscale
```

### 2. Set Up Python Backend
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Automated Model & Binary Setup
Run the automated downloader to install official Real-ESRGAN NCNN Vulkan binaries and weights:
```bash
python scripts/setup_environment.py
```

### 4. Build Frontend
```bash
npm --prefix frontend install
npm --prefix frontend run build
```

### 5. Start Aether Studio
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🧪 Hardware Benchmarks

Measured on **Profile A Constrained Hardware** (Intel Core i5, 8 GB RAM, NVIDIA GeForce RTX 2050 4 GB VRAM, Windows 11):

| Operation | Input Size | Output Size | Output Megapixels | Runtime | Peak Memory | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Direct 4× Photo** | 512 × 512 | 2048 × 2048 | 4.19 MP | **3.82 s** | < 1.2 GB VRAM | Verified |
| **Manga Inking Master** | 140 × 65 | 560 × 260 | 0.15 MP | **5.72 s** | < 800 MB VRAM | Verified |
| **Progressive 4K $\rightarrow$ 8K** | 3840 × 2160 | 7680 × 4320 | **33.18 MP** | **134.97 s** | < 1.8 GB VRAM | Verified |
| **Crop Inspection (Preview)** | 256 × 256 | 1024 × 1024 | 1.05 MP | **0.95 s** | < 600 MB VRAM | Verified |

---

## 🔬 Automated Testing

AETHER UPSCALE includes **68 automated tests** covering tiling boundaries, memory caps, edge normal steepening, batch queue ordering, and metadata provenance:

```bash
pytest tests/
```
Output:
```text
======================= 68 passed in 72.17s =======================
```

---

## 📜 License

* **Application Code:** [MIT License](LICENSE)
* **Underlying Neural Models:** Powered by Tencent ARC / Real-ESRGAN open-source checkpoints (BSD 3-Clause, non-commercial / research terms).

---

<div align="center">
Built with precision for creators, archivists, and manga enthusiasts.
</div>
