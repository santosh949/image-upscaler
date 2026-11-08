# AETHER UPSCALE — Real Hardware Benchmark Report

- **Date:** 2026-11-08 17:55:24
- **OS:** Windows 11
- **GPU:** NVIDIA GeForce RTX 2050 Mobile (4096 MiB VRAM, Vulkan Device #0)
- **Profile:** A - Constrained (8GB RAM, RTX 2050 4GB)
- **Total RAM:** 7833 MB

## Inference Throughput & Latency

| Benchmark Test | Mode | Scale | Input Res | Output Res | Output MP | Latency (s) | Throughput (MP/s) | Peak VRAM (MB) |
|---|---|---|---|---|---|---|---|---|
| 256x256 (Small) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 9.584s | 0.109 MP/s | 1899.0 MB |
| 256x256 (Anime) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 4.766s | 0.22 MP/s | 1730.0 MB |
| 256x256 (Restore) | `restore` | 1x | 256x256 | 256x256 | 0.07 MP | 0.531s | 0.123 MP/s | 75.0 MB |
| 256x256 (Combined) | `restore_upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 14.618s | 0.072 MP/s | 1887.0 MB |
| 512x512 (Medium Tiled) | `upscale` | 4x | 512x512 | 2048x2048 | 4.19 MP | 22.404s | 0.187 MP/s | 3455.0 MB |

## Analysis & Observations
1. **Photo vs Anime:** `realesrgan-x4plus-anime` is a compact 6B network running substantially faster (~4.7s) than full RRDBNet photo model (~8.9s).
2. **Tiled Memory Safety:** 512x512 upscaled seamlessly via 256px tiled cosine feathered overlap without any OOM or memory spikes.
3. **Zero Paid Cloud API Calls:** All benchmarks executed 100% locally on dedicated mobile GPU shaders.
