# Contributing to AETHER UPSCALE

Thank you for your interest in contributing to **AETHER UPSCALE**!

## Development Guidelines

1. **Local-First & Safety Guarantees:**
   - Any new models or pipelines must be tested against memory safety caps.
   - Profile A laptop constraints (4 GB VRAM / 8 GB RAM) are strictly enforced. Never load full uncompressed 8K/16K buffers directly into system RAM.
   - All super-resolution operations must support tiled streaming with 2D Hann feathered cosine blending.

2. **Code Standards:**
   - Python code must conform to PEP 8 standards and run cleanly on Python 3.11+.
   - TypeScript frontend code in `frontend/` must compile with `tsc -b && vite build` with zero errors or warnings.
   - Every new feature or pipeline fix must include automated test coverage under `tests/`.

3. **Running Tests:**
   Before opening a Pull Request, verify that the automated test suite passes:
   ```bash
   python -m pytest tests/
   ```

4. **Pull Request Process:**
   - Fork the repository and create your branch from `main`.
   - Ensure all 68 automated unit and integration tests pass.
   - Provide visual before/after evidence or benchmark metrics if modifying inference algorithms.
   - Submit PR with clear summary of architectural changes.
