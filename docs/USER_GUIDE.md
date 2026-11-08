# AETHER UPSCALE — User Guide

Welcome to **AETHER UPSCALE**, a professional local-first AI image restoration, enhancement, and super-resolution studio designed for Windows 11.

---

## 1. Starting the Application

Open a PowerShell terminal in the project directory:
```powershell
.venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8000
```
Open **`http://127.0.0.1:8000`** in your web browser.

---

## 2. Using the Studio

### Step 1: Upload Your Image
- Drag and drop any image (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`) onto the dropzone or click to browse.
- The studio automatically runs the **Degradation Analyzer** in the background:
  - **Blur Level:** Measures image sharpness using normalized Laplacian variance.
  - **Noise Level:** Estimates high-frequency sensor noise via Immerkaer MAD variance.
  - **JPEG Compression:** Detects 8x8 DCT grid blockiness and quantization.
  - **Content Classifier:** Identifies whether the image is photographic or anime/illustration.

### Step 2: Choose Processing Mode & Model
- **Processing Mode:**
  - **Restore:** Cleans up noise, deblocks JPEG compression artifacts, and applies subtle unsharp masking at 1x resolution.
  - **Upscale:** Applies 4x neural super-resolution to recover fine details.
  - **Restore+SR (Combined):** Two-stage enhancement: removes artifacts at low resolution before neural upscaling to avoid amplifying JPEG/noise defects.
- **Neural Architecture:**
  - **Auto (Router Recommended):** Automatically selects the best model based on degradation signals.
  - **Real-ESRGAN x4plus:** Optimized for natural photography, portraits, and real-world scenes.
  - **Real-ESRGAN x4plus Anime:** Optimized for 2D art, manga, line drawings, and digital illustrations.
  - *(Tier 3 Diffusion models are clearly marked as disabled on 4GB VRAM to protect system stability).*

### Step 3: Fast Region Preview vs Full Enhance
- **Fast 256px Preview:** Click **"Fast Crop-Preview"** to crop and upscale the center 256px region in ~1 second. This lets you inspect quality before running full image enhancement.
- **Enhance Full Image:** Click **"Enhance Image"** to process the entire image with seamless tiled inference.

### Step 4: Comparing Results
- **Slider Mode:** Drag the interactive Before/After split handle across the canvas.
- **Side-by-Side:** View input and output side-by-side with synchronized zoom (100% to 300%).
- **100% Inspection:** Click anywhere to inspect full-resolution crops via `/crop` without browser memory overload.

### Step 5: Exporting & History
- Select your desired output format (**PNG**, **JPEG**, or **WebP**) and compression quality slider.
- Click **"Download Output"** to save the result with embedded provenance metadata (model, scale, stages, and consistency score).
- Open the **Job History** drawer from the top right to access and download previously processed images.
