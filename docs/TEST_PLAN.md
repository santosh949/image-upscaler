# Test Plan — AETHER UPSCALE

## 1. Unit Tests
- Dimension calculations and scaling logic.
- Tile coordinate mapping and boundary conditions.
- Hann/Gaussian feathering and seam suppression.
- Alpha channel preservation and color bleeding.
- Security: Path traversal rejection, MIME sniffing, pixel cap limits.

## 2. Integration Tests
- NCNN Vulkan binary invocation and exit codes.
- PyTorch adapter inference on real fixtures.
- API job lifecycle: upload -> status SSE -> cancellation -> download.

## 3. Visual & Regression Matrix
- Test fixtures: portrait, architecture, anime, JPEG-compressed, transparent PNG.
- No-reference and full-reference metrics (PSNR, SSIM) on synthetic test set.

