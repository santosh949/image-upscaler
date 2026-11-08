# AETHER UPSCALE V3 — FINAL ADDENDUM (Quality Refinement, corrected)

**Date:** 8 November 2026
**Precedence:** This file > `V3 spec` (aether_upscale_3_0_spec.md) > `FINAL_SPEC.md` (V2) > older docs. Where this file is silent, the V3 spec and FINAL_SPEC.md apply unchanged. All rules in FINAL_SPEC.md Part A (skills check, graphify, verification, no mocks, no destructive commands, local-only) remain in force.
**Goal:** better human-photo output (texture, grain, skin, hair, eyes) from the existing app, models and hardware. No new product areas.

Tags: [OWNER-CLAIM] = stated in the V2 audit; unverified by the reviewer. [VERIFY] = agent must confirm.

---

## 1. Corrections to the V3 spec (the agent must apply these)

1. **Audit arithmetic is inconsistent.** The V2 table has 38 rows (31 verified, 5 partial, 2 "implemented but not fully verified"), but the text says 40 requirements / 33 verified / 82.5%. Recount from the table; do not quote 82.5% until reconciled. Test count (53), runtime (134.97 s) and hashes are [OWNER-CLAIM] — re-run them in Phase 0 and record the real output.
2. **Vulkan "Device 0" is NOT proof of the NVIDIA GPU.** The stated CPU (Intel Core i5-11400H class) has an Intel iGPU, which commonly appears as a Vulkan device. Log the NCNN device list and the device name used for every job. If device 0 is Intel, the 134.97 s figure was measured on the wrong GPU or the claim is wrong; either way fix: select the NVIDIA device index explicitly (`-g`), verify by name, and re-run the 4K→8K benchmark.
3. **"Peak RAM < 500 MB" is a claim to measure,** and the audit says only ~0.7–1.5 GB RAM was available during sessions. Add a preflight on *available* RAM (not total) and measure peak working set of API + worker + NCNN child during the 8K job. Report numbers, not the claim.
4. **Texture control cannot be a single slider.** With the installed NCNN checkpoints (x4plus, x4plus-anime, animevideov3 x2/x3/x4) the model itself exposes no denoise/texture control. Real-ESRGAN was trained on synthetic degradations that include noise, so x4plus likely smooths grain by itself [VERIFY with the tap test, section 3]. The Preserve Texture setting can therefore only control the app's own classical pre/post steps, plus model/path choices. Where the model smooths grain regardless, the UI must say so (V3 §12.1 already requires disclosure).
5. **Acceptance criterion 1 ("does not erase grain") is only testable as two parts:** (a) the app's own steps do not erase grain by default (provable), (b) model-level smoothing is measured and disclosed (not claimed fixed).
6. **`realesr-animevideov3` is an anime-VIDEO model.** Using it for manga/line art is a hypothesis; test it against `realesrgan-x4plus-anime` on the manga benchmark and pick on evidence (watch screen-tone moiré, line thinning).
7. **Close known V2 gaps in Phase 0 of V3** (cheap, previously required by FINAL_SPEC C3): real free-disk check via `shutil.disk_usage` before every job (needed ×1.25); available-RAM preflight; Plan C wired in the UI as a labelled "Traditional resample"; provenance in the version manifest for all formats (PNG tEXt is not proof, and JPEG/WebP need a manifest/XMP or sidecar). Do not skip these because the V3 focus is quality.
8. **The two diagnostic images (grainy B&W portrait, blurred manga) are AI-generated.** Fine for visual diagnosis; they are NOT ground truth. For measurable evaluation build a synthetic set (section 4) from properly licensed or self-made high-resolution photographs.

---

## 2. Phase 0 (V3) — baseline and wrong-GPU check
1. Re-run tests and save the output; reconcile test counts; record the real device name NCNN uses; freeze V2 code/checkpoints (tag or copy; do not move files).
2. Build/refresh the graphify graph (code folders only). Query it to trace: frontend preset → API → job → worker → preprocess → NCNN → post-process → export. Document the actual trace in `docs/V3_PIPELINE_TRACE.md` with file+line evidence.
3. Fix the wrong-GPU risk, disk/RAM preflights (item 7 above).
4. Save benchmark inputs with SHA-256 and the V2 outputs and effective settings as the baseline.
Exit: reproducible baseline; correct GPU confirmed by name.

## 3. Phase 1 — Locate where texture is lost (tap test, one variable at a time)
Capture and keep (hidden/diagnostic artifacts, lossless): (T0) input; (T1) input after any app pre-processing; (T2) raw NCNN output before any blend/resample; (T3) after per-tile resample/blend; (T4) after post-processing (sharpen/filters); (T5) exported file. Compare T0 (Lanczos-upscaled to the same size) vs T2 vs T4 on the grainy portrait at 100% crops of: flat skin, hair, eye region, background grain.
Controlled experiments (change ONE thing per run, same source/scale/tile): classical pre-denoise on/off; post-sharpen off/on; model x4plus vs the other installed models; tile size/overlap; direct vs staged scaling.
Decision rule: attribute texture loss to the stage where the measured texture metrics (section 4) drop most. Record it. Fix only what the data blames.
Exit: `docs/V3_TEXTURE_LOSS_REPORT.md` naming the stage(s) responsible with evidence.

## 4. Measurement (replaces "looks better")
Use, per benchmark image and per crop (fixed ROI list stored with the image):
- **Flat-patch noise/grain std** in hand-marked flat regions (skin, background) of output vs the reference (ground truth if available, else Lanczos-upscaled input — label which).
- **High-band spectral energy ratio** (radially averaged power spectrum, output vs reference at the same size).
- **Laplacian-variance ratio** (watch for over-sharpening), **halo/overshoot metric** near strong edges, **tile-seam metric**, **Lab colour drift**.
- **With ground truth only:** PSNR/SSIM, LPIPS/DISTS. Build the synthetic set: take clean high-res photos, degrade (downscale ×2/×4 + mild blur + noise/grain + JPEG), upscale with the pipeline, compare to the originals. PSNR/SSIM never decide perceptual quality alone.
- **Human check:** blinded A/B at 100% crops (eyes, hair, skin, clothing, shadows), owner or a second person; record which output was preferred and any regression flagged (waxy skin, merged strands, halos, lost lashes, repetition, flattened shadows, seams, tonal shifts).
A change counts as an improvement only if texture metrics move toward the reference, AND the blinded check is not worse, AND no metric in the regression list degrades materially. Report metric values and ROI, not a single combined score.

## 5. Phase 2 — Fix texture loss (smallest change that the data supports)
Candidate levers, in order of preference; adopt only what Phase 1 data supports:
1. Disable app-level denoise/NLM/bilateral and fixed unsharp by default for the human-photo path; keep them as opt-in steps (Balanced / Reduce Noise).
2. Make post-sharpening adaptive or off, with a halo check; never use it to hide smoothing.
3. Evaluate a **labelled, low-weight pixel blend** of the model output with a Lanczos upscale of the input (restores some source texture; it is "Traditional enhancement", not recovered detail). Keep only if it passes section 4 without halos/ghosting; record the weight per preset.
4. Evaluate **`realesrnet-x4plus`** (shipped in the NCNN portable set per FINAL_SPEC; currently NOT installed here) — it is PSNR-oriented and smoother, so test it, do not assume it preserves grain.
5. Only if 1–4 fail the grain criterion: evaluate `realesr-general-x4v3` with its denoise-strength interpolation (strength 0 keeps noise) via an isolated Torch worker or NCNN conversion [VERIFY]. This is the only documented model-level texture control in the Real-ESRGAN family; adopting it requires the license/hash/smoke-test steps in FINAL_SPEC and a measured benefit on THIS hardware. Do not add it speculatively.
Never: add synthetic grain, auto-run face-generative restoration, or repeat the same model over its own output.
Exit: grainy portrait retains measurably more texture (metrics + blind check) without new artifacts; Texture Preservation setting changes real behaviour and the UI states what it can and cannot do per model.

## 6. Phase 3 — Presets made real (one documented config)
Create one config file (e.g., `presets.yaml`) loaded by the backend; the frontend only sends the preset id. Each preset resolves to: task/model, scale, pre-denoise (none/low/medium), post-sharpen (off/low), texture blend weight, tile/overlap, and "warnings shown". Validate against the selected model's capabilities and reject/disclose unsupported settings. Write resolved parameters into the job and version manifest and show them in Technical Details. Starting hypotheses to calibrate with data (not final values):
| Preset | Pre-denoise | Post-sharpen | Texture blend | Notes |
|---|---|---|---|---|
| Natural | none | off/very low | per Phase 2 | default for human photos |
| Faithful | none | off | per Phase 2 | minimum changes, consider RealESRNet if it wins tests |
| More Detail | none | low (halo-checked) | low | disclose increased invented-texture risk |
| Smooth & Clean | low–medium | off | none | warn: grain/fine texture may be lost |
| Artwork | none (no photographic denoise) | off | n/a | anime/line-art path |
| Custom | only controls the model supports | | | |
Tests: each preset yields a different resolved config; unsupported control is rejected or disclosed; config persists in the version record; regenerating from the same record reproduces the output (same hash if deterministic, else metrics within tolerance).

## 7. Phase 4 — Tune existing model paths on their own categories
Evaluate installed models only: x4plus on human photos; x4plus-anime on anime/illustration; animevideov3 variants vs x4plus-anime on manga/line art. One variable at a time; same source/scale/tile. Pick defaults by section 4 + blind check + runtime on the confirmed NVIDIA device. Add a model only for an evidenced gap that the existing models cannot close.

## 8. Phase 5 — Regression and release
Run the full benchmark (human set from V3 §15 + manga/line art + existing 4K→8K test). Confirm: 4K→8K still exact 7680×4320 with parent SHA-256 unchanged; version graph, exports, alpha handling, cancel/resume unaffected; all 53+ tests plus new quality-regression tests pass. Write `docs/V3_QUALITY_REPORT.md` separating measured results from subjective observations, with per-image before/after crops, settings, dimensions, runtime and RAM/VRAM measured.

## 9. UI honesty rules (V3 additions)
- Texture setting copy states what it controls ("affects the app's cleanup steps; the AI model may still soften grain").
- Smooth & Clean shows the grain-loss warning.
- No text implies recovered detail; AI-generated detail is labelled per FINAL_SPEC B3.
- Technical Details shows the effective resolved settings and the exact device name used.

## 10. Acceptance (measurable)
1. Default human-photo path: app-level steps do not remove grain (verified by T1 vs T0 metrics); model-level softening measured and disclosed.
2. Texture Preservation changes real behaviour and is covered by tests.
3. Presets resolve to distinct, documented, persisted configs (section 6 tests).
4. Raw model output (T2) and final output (T4) are comparable in the diagnostic view.
5. Benchmark shows texture metrics closer to reference than the V2 baseline on grainy/skin crops, with no material regression in halos, seams, colour, hair/eyelash detail (blind check recorded).
6. Artwork path applies no photographic denoise by default.
7. 4K→8K regression passes; parent hashes unchanged; all tests pass; counts reported (baseline vs final).
8. Device name, runtime, peak RAM/VRAM and dimensions are measured and reported.

---

## 11. START PROMPT FOR ANTIGRAVITY (paste after placing V3_FINAL_ADDENDUM.md and the V3 spec in the repo root)

```text
Read V3_FINAL_ADDENDUM.md, then the V3 spec it references, then FINAL_SPEC.md. Precedence: addendum > V3 spec > FINAL_SPEC. AETHER UPSCALE is already built; this is a quality refinement, not a rebuild. All FINAL_SPEC Part A rules still apply (SKILLS.md and a "Skill check:" line before every step, graphify queried before grepping and rebuilt after each phase, real verification of every step, no mocks, no destructive commands, local-only).

Work in this order and do not skip ahead:
Phase 0: re-run tests and save output; reconcile the V2 audit counts; print the NCNN Vulkan device list and the device actually used; if it is not the NVIDIA GPU, fix it and re-run the 4K->8K benchmark; add real disk-free and available-RAM preflights; wire Plan C; freeze the V2 baseline; write docs/V3_PIPELINE_TRACE.md from the real code.
Phase 1: texture-loss tap test (T0-T5), one variable at a time, on the grainy portrait; write docs/V3_TEXTURE_LOSS_REPORT.md naming where texture is lost, with metrics and crops.
Phase 2: fix only what the data blames, preferring the smallest change; no synthetic grain, no auto face-generative, no repeated same-model passes.
Phase 3: one presets config; presets must change real backend parameters and be persisted in the job/version manifest.
Phase 4: tune the installed models on their own image categories with controlled experiments.
Phase 5: full benchmark vs baseline, regression checks, docs/V3_QUALITY_REPORT.md.

Report after each phase: files changed, behaviour changed, images/settings used, dimensions, measured runtime/RAM/VRAM, improvements, regressions, tests, limitations. Claim no quality improvement without before/after metrics and 100% crop evidence. Continue to the next phase after each report unless a stop rule applies.
```
