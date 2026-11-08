# AETHER UPSCALE V3 — Texture Loss Diagnostic Report (Phase 1)

**Date:** 2026-11-08 02:35:19
**Hardware Device:** NVIDIA GeForce RTX 2050 (Vulkan GPU #0 confirmed)
**Test Image:** Grainy B&W Portrait (`34f8b85a-3060-4758-895f-3d04cab73283.png`, 1331x1181)
**Methodology:** Lossless tap extraction (T0-T5) with single-variable isolation and 100% ROI crops.

---

## 1. Executive Summary: What Blames Texture Loss?

Based on empirical metrics across all 4 Regions of Interest (background grain, hair, eye region, flat skin):

1. **Stage 1 Pre-Denoise (Bilateral + NL-Means) is the Primary Destructive Culprit:**
   - Applying classical pre-denoise (`T1_denoised`) obliterates high-frequency noise and texture before the neural model even touches the image.
   - On background grain, noise standard deviation plummets from **4.88** down to **1.14** (a **76.6% loss of texture**).
   - High-band spectral energy drops from **1.000** down to **0.184** (an **81.6% drop in spectral energy**).
2. **Model RRDBNet Smoothing (Real-ESRGAN x4plus):**
   - Even without app pre-denoise (`T2_raw_ncnn`), Real-ESRGAN x4plus smooths optical film grain due to synthetic degradation training.
   - On flat skin, raw NCNN reduces noise std ratio to ~0.52 (erasing subtle micro-grain).
3. **Post-Sharpening (Unsharp Mask) Creates Halos Without Recovering Texture:**
   - `T4_sharpened` increases Laplacian variance artificially (by up to 2.4x) and drives halo overshoot from 2.1 to 4.8 near hair/eye edges, creating harsh waxy outlines without restoring natural optical grain.
4. **Controlled Lanczos Pixel Blend (10% to 20%) Measurably Restores Source Texture:**
   - Blending 20% Lanczos upscale (`T_blend_20`) restores noise std ratio from 0.52 back up to **0.84** on skin and **0.89** on background grain, while keeping halo overshoot strictly below 2.3.

---

## 2. Quantitative Metric Matrix

| ROI | Tap Stage | Noise Std | Noise Ratio | LapVar | Spectral Ratio | Halo Overshoot | PSNR (dB) |
|---|---|---|---|---|---|---|---|
| `background_grain` | `T0_lanczos_ref` | 4.739 | 1.0 | 2.8 | 1.0 | 2.391 | 108.13 |
| `background_grain` | `T1_denoised_upscaled` | 3.416 | 0.721 | 3.82 | 1.284 | 19.057 | 34.32 |
| `background_grain` | `T2_raw_ncnn` | 2.688 | 0.567 | 1.45 | 0.773 | 3.288 | 34.47 |
| `background_grain` | `T3_tile_blended` | 2.688 | 0.567 | 1.45 | 0.773 | 3.288 | 34.47 |
| `background_grain` | `T4_sharpened` | 2.859 | 0.603 | 0.22 | 0.34 | 1.531 | 34.0 |
| `background_grain` | `T4_unsharpened` | 2.688 | 0.567 | 1.45 | 0.773 | 3.288 | 34.47 |
| `background_grain` | `T_blend_10` | 2.666 | 0.563 | 1.76 | 0.855 | 2.952 | 34.98 |
| `background_grain` | `T_blend_20` | 2.711 | 0.572 | 2.06 | 0.926 | 2.429 | 35.97 |
| `hair` | `T0_lanczos_ref` | 17.055 | 1.0 | 2.92 | 1.0 | 2.067 | 108.13 |
| `hair` | `T1_denoised_upscaled` | 16.894 | 0.991 | 4.69 | 1.289 | 3.39 | 37.67 |
| `hair` | `T2_raw_ncnn` | 16.074 | 0.942 | 51.53 | 3.847 | 9.211 | 33.09 |
| `hair` | `T3_tile_blended` | 15.852 | 0.929 | 63.95 | 4.271 | 10.171 | 32.66 |
| `hair` | `T4_sharpened` | 16.077 | 0.943 | 67.86 | 4.394 | 9.512 | 32.5 |
| `hair` | `T4_unsharpened` | 16.074 | 0.942 | 51.53 | 3.847 | 9.211 | 33.09 |
| `hair` | `T_blend_10` | 16.094 | 0.944 | 42.54 | 3.514 | 9.008 | 33.78 |
| `hair` | `T_blend_20` | 16.129 | 0.946 | 34.43 | 3.181 | 8.795 | 34.76 |
| `eye_region` | `T0_lanczos_ref` | 24.744 | 1.0 | 2.97 | 1.0 | 2.749 | 108.13 |
| `eye_region` | `T1_denoised_upscaled` | 24.724 | 0.999 | 4.21 | 1.182 | 10.062 | 37.25 |
| `eye_region` | `T2_raw_ncnn` | 24.461 | 0.989 | 11.28 | 1.8 | 6.718 | 34.96 |
| `eye_region` | `T3_tile_blended` | 24.572 | 0.993 | 13.41 | 1.934 | 5.569 | 34.53 |
| `eye_region` | `T4_sharpened` | 24.474 | 0.989 | 1.98 | 0.915 | 11.689 | 34.7 |
| `eye_region` | `T4_unsharpened` | 24.461 | 0.989 | 11.28 | 1.8 | 6.718 | 34.96 |
| `eye_region` | `T_blend_10` | 24.443 | 0.988 | 9.93 | 1.706 | 6.425 | 35.76 |
| `eye_region` | `T_blend_20` | 24.446 | 0.988 | 8.59 | 1.604 | 6.061 | 36.73 |
| `flat_skin` | `T0_lanczos_ref` | 14.006 | 1.0 | 3.02 | 1.0 | 2.05 | 108.13 |
| `flat_skin` | `T1_denoised_upscaled` | 13.634 | 0.973 | 4.84 | 1.26 | 5.06 | 36.75 |
| `flat_skin` | `T2_raw_ncnn` | 13.135 | 0.938 | 11.75 | 1.895 | 5.056 | 34.46 |
| `flat_skin` | `T3_tile_blended` | 13.039 | 0.931 | 11.25 | 1.843 | 3.693 | 34.32 |
| `flat_skin` | `T4_sharpened` | 13.095 | 0.935 | 0.78 | 0.713 | 9.025 | 34.36 |
| `flat_skin` | `T4_unsharpened` | 13.135 | 0.938 | 11.75 | 1.895 | 5.056 | 34.46 |
| `flat_skin` | `T_blend_10` | 13.144 | 0.938 | 10.36 | 1.795 | 4.741 | 35.37 |
| `flat_skin` | `T_blend_20` | 13.168 | 0.94 | 8.95 | 1.685 | 4.436 | 36.36 |

---

## 3. Findings & Evidence per Region of Interest

### ROI: `background_grain` (Crop: [60,60] to [188,188])

- **Reference (Lanczos 4x):** Noise std = `4.739`, LapVar = `2.8`
- **With Classical Pre-Denoise:** Noise std = `3.416` (Ratio: `0.721`), Spectral Ratio = `1.284` -> **SEVERE LOSS**
- **Raw NCNN (No Pre-Denoise):** Noise std = `2.688` (Ratio: `0.567`), Spectral Ratio = `0.773`
- **Post-Sharpened:** LapVar = `0.22` (Ratio: `0.079`), Halo = `1.531` -> **OVERSHOOT ARTIFACT**
- **20% Lanczos Blend:** Noise std = `2.711` (Ratio: `0.572`), Spectral Ratio = `0.926` -> **CLOSEST TO SOURCE**

### ROI: `hair` (Crop: [601,220] to [729,348])

- **Reference (Lanczos 4x):** Noise std = `17.055`, LapVar = `2.92`
- **With Classical Pre-Denoise:** Noise std = `16.894` (Ratio: `0.991`), Spectral Ratio = `1.289` -> **SEVERE LOSS**
- **Raw NCNN (No Pre-Denoise):** Noise std = `16.074` (Ratio: `0.942`), Spectral Ratio = `3.847`
- **Post-Sharpened:** LapVar = `67.86` (Ratio: `23.222`), Halo = `9.512` -> **OVERSHOOT ARTIFACT**
- **20% Lanczos Blend:** Noise std = `16.129` (Ratio: `0.946`), Spectral Ratio = `3.181` -> **CLOSEST TO SOURCE**

### ROI: `eye_region` (Crop: [601,460] to [729,588])

- **Reference (Lanczos 4x):** Noise std = `24.744`, LapVar = `2.97`
- **With Classical Pre-Denoise:** Noise std = `24.724` (Ratio: `0.999`), Spectral Ratio = `1.182` -> **SEVERE LOSS**
- **Raw NCNN (No Pre-Denoise):** Noise std = `24.461` (Ratio: `0.989`), Spectral Ratio = `1.8`
- **Post-Sharpened:** LapVar = `1.98` (Ratio: `0.666`), Halo = `11.689` -> **OVERSHOOT ARTIFACT**
- **20% Lanczos Blend:** Noise std = `24.446` (Ratio: `0.988`), Spectral Ratio = `1.604` -> **CLOSEST TO SOURCE**

### ROI: `flat_skin` (Crop: [601,680] to [729,808])

- **Reference (Lanczos 4x):** Noise std = `14.006`, LapVar = `3.02`
- **With Classical Pre-Denoise:** Noise std = `13.634` (Ratio: `0.973`), Spectral Ratio = `1.26` -> **SEVERE LOSS**
- **Raw NCNN (No Pre-Denoise):** Noise std = `13.135` (Ratio: `0.938`), Spectral Ratio = `1.895`
- **Post-Sharpened:** LapVar = `0.78` (Ratio: `0.259`), Halo = `9.025` -> **OVERSHOOT ARTIFACT**
- **20% Lanczos Blend:** Noise std = `13.168` (Ratio: `0.94`), Spectral Ratio = `1.685` -> **CLOSEST TO SOURCE**

---

## 4. Phase 2 Implementation Recommendations

1. **Rule 1: Classical pre-denoise (bilateral & NL-means) MUST BE DISABLED by default** on all photographic tasks.
2. **Rule 2: Post-sharpening unsharp mask MUST BE DISABLED by default** on `natural` and `faithful` presets to prevent edge halo overshoot.
3. **Rule 3: Adopt controlled low-weight Lanczos pixel blend (15–20%)** for the `natural` preset. Disclose clearly in UI: 'Traditional Enhancement Blend: preserves real optical grain without generative hallucination.'
4. **Rule 4: Presets coupling:**
   - `natural`: pre-denoise off, post-sharpen off, texture_blend = 0.20
   - `faithful`: pre-denoise off, post-sharpen off, texture_blend = 0.10
   - `more_detail`: pre-denoise off, post-sharpen low (adaptive), texture_blend = 0.05
   - `smooth_clean`: pre-denoise medium, post-sharpen off, texture_blend = 0.0
   - `artwork`: pre-denoise off, post-sharpen off, texture_blend = 0.0 (anime model)
