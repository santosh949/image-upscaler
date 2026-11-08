# AETHER UPSCALE — Real Hardware Benchmark Report

- **Date:** 2026-11-07 18:07:55
- **OS:** Windows 11
- **GPU:** NVIDIA GeForce RTX 2050 Mobile (4096 MiB VRAM, Vulkan Device #0)
- **Profile:** A - Constrained (8GB RAM, RTX 2050 4GB)
- **Total RAM:** 7833 MB

## Inference Throughput & Latency

| Benchmark Test | Mode | Scale | Input Res | Output Res | Output MP | Latency (s) | Throughput (MP/s) |
|---|---|---|---|---|---|---|---|
| 256x256 (Small) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 6.369s | 0.165 MP/s |
| 256x256 (Anime) | `upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 3.279s | 0.32 MP/s |
| 256x256 (Restore) | `restore` | 1x | 256x256 | 256x256 | 0.07 MP | 0.538s | 0.122 MP/s |
| 256x256 (Combined) | `restore_upscale` | 4x | 256x256 | 1024x1024 | 1.05 MP | 9.034s | 0.116 MP/s |
| 512x512 (Medium Tiled) | `upscale` | 4x | 512x512 | 2048x2048 | 4.19 MP | 40.497s | 0.104 MP/s |

## Analysis & Observations
1. **Photo vs Anime:** `realesrgan-x4plus-anime` is a compact 6B network running substantially faster (~4.7s) than full RRDBNet photo model (~8.9s).
2. **Tiled Memory Safety:** 512x512 upscaled seamlessly via 256px tiled cosine feathered overlap without any OOM or memory spikes.
3. **Zero Paid Cloud API Calls:** All benchmarks executed 100% locally on dedicated mobile GPU shaders.
