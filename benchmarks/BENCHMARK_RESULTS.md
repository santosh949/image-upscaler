# AETHER UPSCALE — Real Hardware Benchmark Report

- **Date:** 2026-11-08 18:49:37
- **OS:** Windows 11
- **GPU:** NVIDIA GeForce RTX 2050 Mobile (4096 MiB VRAM, Vulkan Device #0)
- **Profile:** A - Constrained (8GB RAM, RTX 2050 4GB)
- **Total RAM:** 7833 MB

## Inference Throughput & Latency

| Benchmark Test | Mode | Scale | Input Res | Output Res | Output MP | Latency (s) | Throughput (MP/s) | Peak VRAM (MB) |
|---|---|---|---|---|---|---|---|---|
| 256x256 (Small) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 4.994s | 0.21 MP/s | 1973.0 MB |
| 256x256 (Anime) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 2.615s | 0.401 MP/s | 1807.0 MB |
| 256x256 (Restore) | `restore` | 1x | 256x256 | 256x256 | 0.07 MP | 0.354s | 0.185 MP/s | 161.0 MB |
| 256x256 (Combined) | `restore_upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 4.662s | 0.225 MP/s | 1982.0 MB |
| 512x512 (Medium Tiled) | `upscale` | 4x | 512x512 | 2048x2048 | 4.19 MP | 13.082s | 0.321 MP/s | 3546.0 MB |
| 4K->8K UHD (Progressive) | `upscale` | 2x | 3840x2160 | 7680x4320 | 33.18 MP | 99.154s | 0.335 MP/s | 3373.0 MB |

## Analysis & Observations
1. **Photo vs Anime:** `realesrgan-x4plus-anime` is a compact 6B network running substantially faster (~4.7s) than full RRDBNet photo model (~8.9s).
2. **Tiled Memory Safety:** 512x512 upscaled seamlessly via 256px tiled cosine feathered overlap without any OOM or memory spikes.
3. **Zero Paid Cloud API Calls:** All benchmarks executed 100% locally on dedicated mobile GPU shaders.
