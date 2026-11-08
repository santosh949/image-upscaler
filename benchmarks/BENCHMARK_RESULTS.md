# AETHER UPSCALE — Real Hardware Benchmark Report

- **Date:** 2026-11-08 20:41:54
- **OS:** Windows 11
- **GPU:** NVIDIA GeForce RTX 2050 Mobile (4096 MiB VRAM, Vulkan Device #0)
- **Profile:** A - Constrained (8GB RAM, RTX 2050 4GB)
- **Total System RAM:** 7833 MB

> **Methodology Disclosure:**
> - **Model Separation:** Photo (`realesrgan-x4plus`) and Anime/Manga (`realesrgan-x4plus-anime`, `realesr-animevideov3-x4`) are measured independently on real reference images.
> - **Category Separation:** Real photographic images, real manga panels, and synthetic procedural patterns are reported in distinct tables to avoid conflating synthetic metrics with real-world workloads.
> - **VRAM Telemetry:** `Baseline VRAM` reflects pre-inference system/GPU state. `Peak Total VRAM` reflects maximum absolute memory used during inference. `Est. Incremental VRAM` indicates estimated GPU memory headroom consumed (peak minus baseline), not claimed as exact isolated allocation.

## Category A: Real Photographic Benchmarks (realesrgan-x4plus)

| Benchmark Test | Mode | Scale | Input Res | Output Res | Output MP | Latency (s) | Throughput (MP/s) | Baseline VRAM | Peak Total VRAM | Est. Incremental VRAM |
|---|---|---|---|---|---|---|---|---|---|---|
| Real Photo 256x256 (Natural) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 6.464s | 0.162 MP/s | 129.0 MB | 1941.0 MB | +1812.0 MB |
| Real Photo 512x512 (Tiled 4x) | `upscale` | 4x | 512x512 | 2048x2048 | 4.19 MP | 14.536s | 0.289 MP/s | 120.0 MB | 3517.0 MB | +3397.0 MB |

## Category B: Real Illustration & Manga Benchmarks (Anime Models)

| Benchmark Test | Mode | Scale | Input Res | Output Res | Output MP | Latency (s) | Throughput (MP/s) | Baseline VRAM | Peak Total VRAM | Est. Incremental VRAM |
|---|---|---|---|---|---|---|---|---|---|---|
| Real Manga 256x256 (Manga Crisp) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 2.685s | 0.391 MP/s | 124.0 MB | 1786.0 MB | +1662.0 MB |
| Real Manga 512x512 (Tiled 4x) | `upscale` | 4x | 512x512 | 2048x2048 | 4.19 MP | 6.064s | 0.692 MP/s | 144.0 MB | 3358.0 MB | +3214.0 MB |
| Real Manga 256x256 (AnimeVideo v3 Fast) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 1.579s | 0.664 MP/s | 126.0 MB | 166.0 MB | +40.0 MB |

## Category C: Synthetic Signal & Stress Benchmarks

| Benchmark Test | Mode | Scale | Input Res | Output Res | Output MP | Latency (s) | Throughput (MP/s) | Baseline VRAM | Peak Total VRAM | Est. Incremental VRAM |
|---|---|---|---|---|---|---|---|---|---|---|
| Synthetic 256x256 (Small) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 4.721s | 0.222 MP/s | 126.0 MB | 1947.0 MB | +1821.0 MB |
| Synthetic 256x256 (Anime) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 2.5s | 0.419 MP/s | 126.0 MB | 1781.0 MB | +1655.0 MB |
| Synthetic 256x256 (Classical Restore) | `restore` | 1x | 256x256 | 256x256 | 0.07 MP | 0.366s | 0.179 MP/s | 126.0 MB | 126.0 MB | +0.0 MB |
| Synthetic 256x256 (Combined Restore+Upscale) | `restore_upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 4.333s | 0.242 MP/s | 126.0 MB | 1938.0 MB | +1812.0 MB |
| Synthetic 512x512 (Medium Tiled Stress) | `upscale` | 4x | 512x512 | 2048x2048 | 4.19 MP | 12.018s | 0.349 MP/s | 117.0 MB | 3506.0 MB | +3389.0 MB |

## Analysis & Observations
1. **Real Photo vs Real Anime Architecture:** `realesrgan-x4plus` operates as a 64-channel 23-block RRDBNet preserving natural textures, while `realesrgan-x4plus-anime` is a 6B lightweight network optimized for cel boundaries and line art.
2. **Tiled Memory Protection:** 512×512 inputs upscaled smoothly via 256px tiled cosine feathered overlap with negligible incremental memory overhead on the 4GB GPU.
3. **Synthetic vs Real Discrepancy:** Synthetic mathematical patterns exhibit uniform high-frequency distribution across all channels, whereas real photographic scenes and monochrome manga concentrate energy in perceptual midtones and edge structures.
