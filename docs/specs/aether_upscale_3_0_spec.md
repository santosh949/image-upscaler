# AETHER UPSCALE 3.0 --- Quality Refinement Specification & Product Baseline

> **Document Type:** V3 refinement specification based on the V2 product
> baseline **Status:** V2 baseline documented; V3 quality refinements
> are requirements, not claims of completion\
> **Baseline Audit Date:** 2026-11-08\
> **Automated Test Suite:** 53 Passed, 0 Failed (`pytest tests/`)\
> **Frontend Build:** Clean (`tsc -b && vite build`)\
> **Host Hardware:** Profile A --- Constrained (Intel Core i5, 7.65 GB
> RAM, NVIDIA GeForce RTX 2050 4 GB VRAM, Windows 11)\
> **Engine:** Vulkan 1.4 API + Real-ESRGAN NCNN Binary
> (`realesrgan-ncnn-vulkan.exe`)

------------------------------------------------------------------------

## 1. Executive Implementation Status

AETHER UPSCALE 2.0 has been audited against
`AETHER_UPSCALE_2.0_FINAL_SPEC_REVISED.md`.

-   **Audited Requirements:** 40 core requirements across 6 categories.
-   **Implemented & Verified:** 33 requirements (**82.5%**).
-   **Partially Implemented / Limitations Documented:** 7 requirements
    (**17.5%**).
-   **Core Flagship Capability:** Progressive 4K $\rightarrow$ 8K UHD
    (7680×4320) Per-Tile Scale Adaptation is **implemented and
    empirically verified** on physical hardware (RTX 2050 runtime:
    **134.97 s**).
-   **Release Readiness:** **Production-viable for local
    super-resolution, version tracking, and 4K $\rightarrow$ 8K
    workflows**. Minor gaps in preset hyperparameter coupling and
    multi-tier resolution explorer are itemized in
    [V2_REMAINING_WORK.md](file:///c:/Users/Santhosh/OneDrive/Documents/Desktop/aether%20upscalar/docs/V2_REMAINING_WORK.md).

------------------------------------------------------------------------

## 2. Feature-by-Feature Verification Matrix

    +---------------------------------------------------------------------------------------------------------+
    |                                    FEATURE VERIFICATION AUDIT MATRIX                                    |
    +------------------------------------+--------------------------------+-----------------------------------+
    | Feature Area                       | Status                         | Evidence / Verification           |
    +------------------------------------+--------------------------------+-----------------------------------+
    | 1. Friendly Task Cards             | IMPLEMENTED AND VERIFIED       | `App.tsx`: 6 non-technical cards  |
    | 2. Hidden Technical Models         | IMPLEMENTED AND VERIFIED       | Collapsed in Expert Mode (auto)   |
    | 3. Advanced / Expert Mode          | IMPLEMENTED AND VERIFIED       | `expertModeOpen` accordion toggle |
    | 4. Technical Details Panel         | IMPLEMENTED AND VERIFIED       | Displays backend, tiling, cap     |
    | 5. Quality Presets Coupling        | PARTIALLY IMPLEMENTED          | Presets set UI; backend uses task |
    | 6. Functional Task Controls        | IMPLEMENTED AND VERIFIED       | All cards map to real pipelines   |
    | 7. Progressive 4K Source Ingestion | IMPLEMENTED AND VERIFIED       | Local disk read, zero re-upload   |
    | 8. 4K -> 8K Scale Adaptation       | IMPLEMENTED AND VERIFIED       | Real NCNN 7680x4320 in 134.97s    |
    | 9. Parent Version Immutability     | IMPLEMENTED AND VERIFIED       | Invariant E2: SHA-256 byte-match  |
    | 10. Separate Version Graph Nodes   | IMPLEMENTED AND VERIFIED       | Version tree persisted in SQLite  |
    | 11. TileStore Checkpoint / Resume  | IMPLEMENTED AND VERIFIED       | Disk tiles persist across pause   |
    | 12. Pause, Resume, Cancel Jobs     | IMPLEMENTED AND VERIFIED       | Control flags tested in API       |
    | 13. Zero 16K Buffer in RAM         | IMPLEMENTED AND VERIFIED       | Accumulator fits in <500MB RAM    |
    | 14. Version Decision Lifecycle     | IMPLEMENTED AND VERIFIED       | Accept / Reject / Branch verified |
    | 15. Standard Targets (2x,4x,4K,8K) | IMPLEMENTED AND VERIFIED       | Responsive resolution buttons     |
    | 16. 16K Safety Cap Enforcement     | PARTIALLY IMPLEMENTED          | >100 MP rejected; no 16K button   |
    | 17. Custom Dimensions & Aspect Lock| IMPLEMENTED AND VERIFIED       | Inputs work; >5% aspect blocked   |
    | 18. Maximum Resolution Explorer    | PARTIALLY IMPLEMENTED          | Preflight shown; no multi-table   |
    | 19. RAM / VRAM / Disk Estimator    | IMPLEMENTED AND VERIFIED       | Algorithmic preflight calculator  |
    | 20. Model Compatibility Checks     | IMPLEMENTED AND VERIFIED       | Repeated model warnings emitted   |
    | 21. Plan A / B / C Generation      | IMPLEMENTED BUT NOT FULLY VER. | Plans A & B run; Plan C unwired   |
    | 22. Installed Checkpoints          | IMPLEMENTED AND VERIFIED       | 3 active models present on disk   |
    | 23. Friendly Display Names         | IMPLEMENTED AND VERIFIED       | Model registry display mapping    |
    | 24. Available vs Experimental Tiers| IMPLEMENTED AND VERIFIED       | Tier 1 enabled; Tier 3 disabled   |
    | 25. Model Comparison Studio        | PARTIALLY IMPLEMENTED          | Version slider; no 1-click batch  |
    | 26. Sequential Job Execution       | IMPLEMENTED AND VERIFIED       | Single GPU worker process queue   |
    | 27. Image Processing Categories    | IMPLEMENTED AND VERIFIED       | Photo, anime, line art, alpha     |
    | 28. Aspect Ratio Preservation      | IMPLEMENTED AND VERIFIED       | Exact dimensions preserved        |
    | 29. PNG, JPEG, WebP Export         | IMPLEMENTED AND VERIFIED       | Multi-format export with quality  |
    | 30. Alpha Bleed / Transparency     | IMPLEMENTED AND VERIFIED       | Color dilation eliminates halos   |
    | 31. Cosine-Bell Tile Seams         | IMPLEMENTED AND VERIFIED       | 2D Hann window; zero seam jumps   |
    | 32. Provenance Metadata Embedding  | IMPLEMENTED BUT NOT FULLY VER. | PNG tEXt chunks only; no JPEG XMP |
    | 33. NVIDIA GPU Detection           | IMPLEMENTED AND VERIFIED       | nvidia-smi queries RTX 2050 4GB   |
    | 34. Vulkan Device 0 Selection      | IMPLEMENTED AND VERIFIED       | Device index 0 passed to NCNN     |
    | 35. Dynamic Tile Halving (OOM)     | IMPLEMENTED AND VERIFIED       | Auto-retry with tile_size // 2    |
    | 36. Physical Disk Capacity Check   | PARTIALLY IMPLEMENTED          | Estimated, but not pre-checked OS |
    | 37. Job Cancellation Mid-Flight    | IMPLEMENTED AND VERIFIED       | Inter-tile check halts subprocess |
    | 38. Large Image Stability          | IMPLEMENTED AND VERIFIED       | 33.18 MP (8K) processed cleanly   |
    +------------------------------------+--------------------------------+-----------------------------------+

------------------------------------------------------------------------

## 3. Frontend & Usability Architecture

### 3.1 Task Categories vs. Model Abstraction

Everyday users interact with task cards rather than machine learning
terminology: \* **Improve a Photo:** Directs to `realesrgan-x4plus` (4×
super-resolution). \* **Restore an Old Photo:** Directs to
`restore_upscale` (artifact suppression + super-resolution). \* **Anime
& Cartoons:** Directs to `realesrgan-x4plus-anime` (preserves clean line
fills). \* **Illustrations & Line Art:** Directs to
`realesr-animevideov3-x4` (fast ink and manga scaling). \* **Repair
Compressed Image:** Directs to `restore_upscale` (removes 8×8 JPEG
ringing + neural pass). \* **Transparent Art & Icons:** Directs to Alpha
Bleed pipeline (dilates color under transparency).

### 3.2 Technical Transparency (Expert Mode)

-   Click **"Technical Details & Expert Mode"** at the bottom of the
    studio to reveal:
    -   Checkpoint override selector (manual selection of NCNN models).
    -   Active compute backend (`ncnn-vulkan Device #0`).
    -   Tile size & overlap feather parameters
        (`256px tile, 32px cosine feather`).
    -   System safety cap (`100 Megapixels max`).
    -   Export format selector (PNG, JPEG, WebP) with a compression
        quality slider (20%--100%).

### 3.3 Quality Presets & Limitations

-   **UI Presets:** `Natural` (2×), `Faithful` (4×), `More Detail` (4×),
    `Smooth & Clean` (2×), `Artwork` (4×), `Custom`.
-   **Current Limitation:** Presets provide plain-language guidance in
    the UI and are passed to the API. However, in the current backend
    engine, pipeline hyperparameters (such as denoising thresholds and
    unsharp mask strength) are driven primarily by the selected Task
    Card rather than custom tuning per preset.

------------------------------------------------------------------------

## 4. Flagship Progressive 4K $\rightarrow$ 8K Engine

### 4.1 The Architectural Challenge

Attempting to run a 4× model on a 4K image (3840×2160) produces a 16K
image (15360×8640 = 132.7 Megapixels). In raw float32 memory, a 16K
image requires **over 1.6 GB** of continuous RAM, which causes severe
memory thrashing or out-of-memory crashes on 8 GB RAM laptops.

### 4.2 The Solution: Per-Tile Scale Adaptation (ADR 005)

AETHER UPSCALE 2.0 solves this via **Per-Tile Scale Adaptation**: 1. The
4K input is partitioned into macro-tiles (e.g. 512×512 with 32px
overlap). 2. The 4× neural model scales the tile to 2048×2048. 3. The
tile is **immediately downscaled by $0.5\times$** using anti-aliased
Lanczos filtering to 1024×1024 ($2.0\times$ net scale). 4. The adapted
tile is blended directly into the 8K accumulator using a 2D Hann cosine
feather window. 5. **Zero 16K buffer is ever materialized in physical
RAM.** Peak RAM remains strictly under 500 MB.

### 4.3 Empirical Verification Results

A real 4K image was processed through native NCNN Vulkan on the host RTX
2050:

    ============================================================
    FLAGSHIP 4K -> 8K EMPIRICAL BENCHMARK
    ============================================================
    Input Resolution:          3840 x 2160 (4K UHD, 8.29 MP)
    Output Resolution:         7680 x 4320 (8K UHD, 33.18 MP)
    Effective Scale:           2.0x
    Model:                     realesrgan-x4plus (NCNN Vulkan)
    Hardware:                  NVIDIA GeForce RTX 2050 (4GB VRAM)
    Execution Time:            134.97 seconds (2.25 minutes)
    Parent 4K SHA-256 Before:  38f2b3899f1c79e6027a42b109e99a81...
    Parent 4K SHA-256 After:   38f2b3899f1c79e6027a42b109e99a81... (Byte-identical)
    Tile Seam Defects:         0 visible seams (Hann-window cosine blend)
    ============================================================

------------------------------------------------------------------------

## 5. Model Registry & Checkpoint Truth

### 5.1 Physical Checkpoints on Disk

Verified files in `tools/realesrgan-ncnn-vulkan/models/`: \*
`realesrgan-x4plus.bin` (33.4 MB) & `.param` (116 KB) --- General photo.
\* `realesrgan-x4plus-anime.bin` (8.9 MB) & `.param` (30 KB) --- Anime /
illustrations. \* `realesr-animevideov3-x4.bin` (1.2 MB) & `.param` (3
KB) --- Fast line art. \* `realesr-animevideov3-x3.bin` / `.param` \*
`realesr-animevideov3-x2.bin` / `.param`

### 5.2 Disabled / Missing Models

-   **`realesrnet-x4plus`:** The `.bin` and `.param` checkpoint files
    are **not installed** in the local models directory. In
    `model_registry.py`, it is correctly marked with
    `weights_available: False`.
-   **`diffbir` & `supir` (Tier 3 Generative Diffusion):** These models
    require 8 GB to 16 GB VRAM. They are intentionally disabled
    (`weights_available: False`) to prevent memory crashes on 4 GB VRAM
    Profile A machines.

------------------------------------------------------------------------

## 6. Image Processing & Physics Boundaries

### 6.1 Super-Resolution vs. Motion Blur

-   **Super-Resolution:** Inverts spatial decimation
    ($y = (x \downarrow s) + n$). Reconstructs missing high-frequency
    details along existing sharp edges.
-   **Severe Motion Blur:** Governed by point-spread-function
    convolution ($y = x * k + n$). Spatial frequencies in the direction
    of motion are destroyed (zeroed out).
-   **The Reality:** Single-image super-resolution models **cannot
    invert severe motion blur**. AETHER UPSCALE sharpens recoverable
    edge gradients, but cannot hallucinate destroyed facial features
    without generative facial priors (e.g. CodeFormer/GFPGAN).

### 6.2 Alpha Transparency Handling

-   Transparent PNGs/WebPs undergo alpha separation.
-   Colors under transparent pixels are dilated outward by 4 pixels
    before scaling.
-   Prevents dark fringing/halos when transparent icons are composited
    onto light backgrounds.

------------------------------------------------------------------------

## 7. Hardware Profile & Reliability

### 7.1 Host Profile A Verification

-   **Operating System:** Windows 11 Home (Build 26100)
-   **CPU:** Intel Core i5-11400H / equivalent (6 cores, 12 threads)
-   **System RAM:** 7.65 GB Total (Available: \~0.7 GB -- 1.5 GB during
    active sessions)
-   **GPU:** NVIDIA GeForce RTX 2050 (4096 MiB Dedicated VRAM, Driver
    592.82, CUDA 13.1)
-   **Vulkan Index:** Device 0

### 7.2 Safety Measures

-   **100 Megapixel Safety Cap:** Prevents decompression bombs and
    unbounded canvas allocations.
-   **OOM Tile Halving:** If Vulkan returns an out-of-memory error,
    `TileEngine` automatically halves the tile size
    (`new_tile_sz = max(128, tile_sz // 2)`) and retries.
-   **Sequential Execution:** Jobs run sequentially to prevent
    concurrent GPU VRAM contention.

------------------------------------------------------------------------

## 8. Known Limitations & Remaining Work

The following items are identified for future enhancement in version
2.1: 1. **Quality Preset Backend Coupling:** Presets change UI labels
and scale targets, but do not yet alter denoising thresholds or unsharp
weights in the backend. 2. **Multi-Resolution Explorer UI:** Preflight
RAM/VRAM estimates are shown for the active target; a comparative matrix
across all tiers (4K vs 8K vs 12K) is not yet exposed as a single
interactive view. 3. **Plan C UI Selection:** The Lanczos mathematical
resample plan is generated by `ResolutionPlanner`, but the UI only
submits Plans A and B. 4. **Metadata Formats:** Detailed provenance text
chunks are embedded only into PNG output files; JPEG and WebP do not
embed EXIF/XMP provenance tags. 5. **Physical Disk Space Pre-Check:**
Disk requirements are estimated, but free OS disk space is not verified
via `shutil.disk_usage()` prior to job execution.

*(Full technical audit details are available in
[V2_FINAL_AUDIT.md](file:///c:/Users/Santhosh/OneDrive/Documents/Desktop/aether%20upscalar/docs/V2_FINAL_AUDIT.md).)*

------------------------------------------------------------------------

## 9. Reproducible Test Commands

To verify the test suite and build status:

``` powershell
# Run full automated test suite (53 tests)
.venv\Scripts\python.exe -m pytest tests/

# Build frontend production bundle
npm --prefix frontend run build

# Start server locally
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

------------------------------------------------------------------------

# PART V3 --- QUALITY-FIRST REFINEMENT (PRIMARY DEVELOPMENT FOCUS)

## 10. V3 Product Direction: Improve What Exists, Do Not Expand the Product

AETHER UPSCALE 3.0 is a focused quality refinement of the existing
AETHER UPSCALE 2.0 application.

**The goal is not to add a large collection of new features, models,
modes, or complicated controls. The goal is to make the existing
image-upscaling pipeline produce the best possible output from the
models and hardware already supported.**

The primary quality target is real human photographs: portraits, faces,
skin, hair, eyes, clothing, natural texture, shadows, highlights, and
photographic grain.

The existing application, API, job system, version graph, progressive
resolution engine, export formats, model registry, and frontend should
be preserved. Change them only when a measured quality issue or
correctness issue requires it.

### V3 priorities, in order

1.  Improve real-person photo upscaling quality.
2.  Preserve natural photographic texture, including legitimate film
    grain.
3.  Avoid over-smoothing skin, hair, facial features, clothing, and fine
    details.
4.  Improve detail and edge preservation without creating halos,
    ringing, waxy skin, or artificial sharpness.
5.  Make existing quality presets meaningfully affect the actual
    processing pipeline.
6.  Improve model selection and preprocessing only where controlled
    tests demonstrate a benefit.
7.  Improve output evaluation and regression testing so quality gains
    are measurable and repeatable.
8.  Preserve existing progressive 4K → 8K processing, version safety,
    and constrained-hardware reliability.

Do not prioritize adding unrelated editing tools, generative image
creation, cloud services, new product sections, or a large model
catalogue.

## 11. Human Photograph Quality Standard

Human photographs are the primary benchmark category for V3. AETHER must
not treat every irregular high-frequency pattern as unwanted noise.

The application should preserve the character of the original photograph
while increasing resolution and improving recoverable detail.

### 11.1 Preserve natural photographic texture

Natural photographic texture may include: - Film grain and photographic
grain structure. - Fine skin texture and pores where visible in the
source. - Fine hair strands and flyaway hairs. - Eyebrow, eyelash, and
beard detail. - Fine fabric and clothing texture. - Subtle shadow and
highlight variation. - Natural tonal transitions across skin. - Small
photographic details that are not compression defects.

**Do not automatically classify all grain as damage.** Grain may be an
intentional and important part of the photograph. Removing it can make
faces and other surfaces look waxy, smeared, painted, or synthetic.

### 11.2 Distinguish different kinds of image degradation

The system should distinguish, as far as its existing analysis methods
and processing models permit:

  -----------------------------------------------------------------------
  Image characteristic                Desired treatment
  ----------------------------------- -----------------------------------
  Natural film grain                  Preserve by default; do not erase
                                      automatically

  Sensor noise                        Reduce conservatively when it
                                      visibly harms the image

  JPEG blocking and ringing           Target the compression defects
                                      without broadly smoothing the image

  Genuine fine texture                Preserve

  Fine hair and eyelashes             Preserve boundaries and strands
                                      where present

  Slight blur                         Improve only to the extent
                                      supported by the selected model

  Severe motion blur                  Do not claim that ordinary
                                      super-resolution can recover lost
                                      information

  Low-resolution edges                Reconstruct plausible
                                      high-resolution edges while
                                      avoiding exaggerated halos
  -----------------------------------------------------------------------

These categories can overlap. The analyzer must not pretend it can
identify every grain or noise source perfectly. When uncertain, prefer
conservative processing and let the user choose a stronger cleanup
setting.

### 11.3 Human-detail preservation

During model and pipeline evaluation, inspect: - Eyes, eyelids, iris
boundaries, eyelashes, and eyebrows. - Hair strands, hairline, and
flyaway hairs. - Nose, lips, ears, and facial contours. - Skin texture,
pores, fine lines, and natural tonal variation. - Facial hair and
stubble. - Clothing fibers and fabric patterns. - Fine detail in both
lit and shadowed areas.

The objective is not to make every face smoother or sharper. It is to
produce a natural-looking enlargement that retains the source's identity
and visual character.

### 11.4 No invented-detail claims

A super-resolution model may predict plausible high-frequency details.
It does not prove that those details were present in the original scene.

-   Do not describe generated details as recovered facts.
-   Do not claim that hidden facial information has been recovered.
-   Do not use face-generative restoration as a silent default.
-   If a model or operation is generative, label it accurately and make
    its use explicit.
-   Prioritize source-faithful output for the default human-photo
    workflow.

## 12. Texture Preservation and Conservative Processing

V3 must address the over-smoothing seen in the grainy human portrait
test.

### 12.1 User-facing texture control

Add a simple control to the existing photo workflow. It must be
connected to real backend behaviour; it must not be a decorative slider.

Suggested settings:

-   **Preserve Texture (default):** Avoid optional aggressive denoising
    and preserve source texture as much as the selected model allows.
-   **Balanced:** Apply conservative cleanup only when the selected task
    and image analysis justify it.
-   **Reduce Noise:** Apply stronger noise reduction, with a warning
    that fine texture and grain may be lost.

The exact internal parameters must be calibrated through tests. Do not
assume that a single denoising parameter works consistently across every
model or image.

If a model inherently smooths texture and does not expose a reliable
control, disclose that limitation rather than pretending the setting can
reverse it.

### 12.2 Default behaviour

-   Do not run aggressive bilateral filtering or non-local means
    denoising automatically on every portrait.
-   Do not run an unsharp mask at a fixed strength on every image
    without checking for halos and noise amplification.
-   Do not remove film grain simply because a noise estimator reports
    high-frequency variation.
-   Do not apply the same preprocessing chain to every image category.
-   Do not add artificial grain to disguise excessive smoothing.
-   Do not compensate for lost texture by applying aggressive
    sharpening.
-   Preserve an option to compare the raw model output with any
    post-processed output.

### 12.3 Processing-stage inspection

For quality investigations, retain or expose inspectable outputs for: 1.
Original input. 2. Output immediately after neural inference. 3. Output
after any classical cleanup or post-processing. 4. Final exported image.

This makes it possible to identify whether texture loss comes from the
neural model, preprocessing, post-processing, resizing, or export.

The normal user interface does not need to display every intermediate
stage. These are diagnostic views for the quality audit and, where
useful, an advanced inspection panel.

## 13. Existing Quality Presets Must Become Real

V2 documents several presets, but its audit identifies that presets
primarily affect UI guidance and task selection rather than fully
controlling backend hyperparameters.

V3 must make the existing presets meaningful without creating a large
new preset catalogue.

### 13.1 Required existing presets

  -----------------------------------------------------------------------
  Existing preset                     V3 intended behaviour
  ----------------------------------- -----------------------------------
  Natural                             Conservative processing; retain
                                      natural texture and avoid
                                      exaggerated sharpening

  Faithful                            Minimize optional cleanup and
                                      unnecessary changes; prioritize
                                      source structure

  More Detail                         Allow stronger detail-oriented
                                      model behaviour where supported;
                                      disclose increased risk of invented
                                      texture or artifacts

  Smooth & Clean                      Stronger noise/compression cleanup;
                                      warn that natural grain and fine
                                      texture may be reduced

  Artwork                             Use the already-installed
                                      artwork/anime path and avoid
                                      photographic denoising

  Custom                              Expose only supported controls for
                                      the selected model and task
  -----------------------------------------------------------------------

Do not add more presets simply to make the interface appear more
advanced.

### 13.2 Preset implementation requirements

For every preset: - Define its actual backend settings in one documented
configuration. - Validate settings against the selected model's
capabilities. - Pass the chosen preset and resolved parameters through
the API and job record. - Record the resolved parameters in the version
metadata. - Display the effective settings in Technical Details. - Test
that selecting different presets produces the intended pipeline
changes. - Do not claim a preset is implemented if it only changes a
label or resolution choice.

Where the underlying model does not support a requested control, explain
that limitation and do not silently pretend the setting was applied.

## 14. Controlled Model and Pipeline Tuning

V3 should first improve the use of the currently installed, verified
checkpoints. Do not download or integrate a large number of additional
models as the default response to a quality issue.

### 14.1 Existing model evaluation

Evaluate the installed models against appropriate images: - General
photo model on human portraits and ordinary photographs. - Anime model
on anime and illustrated artwork. - Line-art model on manga and
black-and-white drawings.

A model must be evaluated on the image category it is intended to
process. Do not infer that a model is best for portraits or manga solely
from its filename or repository description.

### 14.2 Controlled experiments

Change one variable at a time: - Model/checkpoint. - Denoising enabled
versus disabled. - Conservative versus stronger cleanup. -
Post-sharpening disabled versus enabled. - Tile size and overlap where
relevant. - Direct processing versus existing multi-stage processing.

Keep the source image, output dimensions, model version, and all other
settings constant during each comparison.

Compare: - Raw model output. - Final pipeline output. - Final exported
output.

Do not select a setting merely because it produces a higher sharpness
score. It must also preserve important source structures and look
natural at normal viewing size and 100% zoom.

### 14.3 No blind repeated enhancement

Do not repeatedly run the same model over its own output by default.
Repeated enhancement may amplify invented details, halos, noise, and
texture distortions.

Continue progressive scaling only when the resolution plan requires it,
and keep each stage separately inspectable and reversible.

## 15. V3 Human-Photo Benchmark and Quality Regression Suite

V3 must establish a repeatable quality benchmark using legally usable
test images, including the two generated test references supplied during
this project:

1.  A high-contrast black-and-white human portrait with visible
    photographic grain.
2.  A softly blurred human manga-style illustration with overlapping
    hair strands and facial line art.

These references are diagnostic examples. The first is a primary
human-photo texture-preservation test. The second is an artwork/line-art
regression test, not a reason to expand the product into generative
restoration.

Add a small, varied human-photo benchmark set covering: - Sharp, clean
portrait. - Low-resolution portrait. - Grainy black-and-white
portrait. - Colour portrait with visible skin texture. - Portrait with
fine hair and flyaway strands. - Portrait with facial hair. - Portrait
with shadows and high-contrast lighting. - Compressed portrait. -
Slightly blurred portrait. - A difficult portrait where hair overlaps
part of the face.

### 15.1 Evaluation method

For every benchmark image: - Preserve the exact source file and its
hash. - Run the same target scale for each comparison. - Record model,
checkpoint, preset, effective settings, backend, tile settings, runtime,
peak RAM/VRAM where measurable, and output dimensions. - Compare at
fit-to-screen, 100% zoom, and selected detail crops. - Inspect eyes,
hair, skin, facial contours, texture, shadows, and highlights. - Record
regressions as well as improvements.

Use PSNR and SSIM only when a genuine aligned ground-truth
high-resolution reference exists. Perceptual or no-reference metrics may
supplement human inspection, but no single score proves that a face is
natural or that texture was preserved.

### 15.2 Required regression checks

Flag: - Waxy or plastic-looking skin. - Smudged facial regions. -
Disappearing pores or natural grain. - Merged hair strands. - Lost
eyelashes or eyebrows. - Over-sharpened edges and halos. - Ringing
around facial contours. - Unnatural texture repetition. - Shadow and
highlight flattening. - Colour or tonal shifts. - Aspect-ratio
changes. - Tile seams and edge discontinuities.

A build must not be described as a quality improvement if it fixes one
defect while silently introducing a major regression elsewhere.

## 16. Existing Artwork and Manga Pipeline: Preserve, Do Not Expand

V3 is not a request to add a new manga product or generative
illustration editor.

The existing Anime & Cartoons and Illustrations & Line Art tasks should
be tuned to preserve their intended source characteristics: - Thin ink
lines. - Hair strands crossing the face. - Eyes, eyelashes, and facial
contours. - Solid black regions and white gaps. - Fine line spacing. -
Original aspect ratio. - Grayscale and black-and-white tonal structure.

Do not apply photographic denoising to artwork by default. Test the
existing installed anime/line-art checkpoints before considering another
model.

If a hair strand obscures part of the face, preserve the visible strand
and face boundary. Do not invent hidden facial information or merge the
strand into the skin.

## 17. Preserve Existing Product Capabilities

V3 is a quality refinement, not a replacement architecture.

Unless a measured defect requires a change, preserve: - Local-only
processing and privacy model. - Existing React/FastAPI architecture. -
NCNN Vulkan inference. - Existing verified model checkpoints. - Existing
task cards and user-friendly terminology. - Existing resolution planner
and progressive 4K → 8K engine. - Existing immutable version graph. -
Existing job queue, cancellation, and resume behaviour. - Existing tiled
processing and OOM recovery. - Existing comparison studio. - Existing
PNG/JPEG/WebP export. - Existing alpha/transparency handling. - Existing
APIs and database compatibility.

Do not remove a working feature to simplify implementation. Do not
change the 4K → 8K algorithm unless a controlled test demonstrates a
correctness, quality, or resource-management improvement.

## 18. V3 Acceptance Criteria

V3 quality work is complete only when the following are demonstrated:

1.  The default human-photo path does not automatically erase natural
    photographic grain.
2.  The Texture Preservation setting changes real backend behaviour
    where the selected model supports it.
3.  Natural and Faithful presets use documented, verified conservative
    settings.
4.  Smooth & Clean clearly warns users about possible loss of grain and
    fine texture.
5.  Raw model output and final post-processed output can be compared
    during quality verification.
6.  Human portraits retain recognizable source structure without waxy
    skin, excessive smoothing, or artificial sharpening.
7.  Fine hair, eyelashes, eyebrows, facial contours, and clothing
    details are inspected in the benchmark suite.
8.  The artwork path does not automatically apply photographic
    denoising.
9.  Existing 4K → 8K processing remains functional and its regression
    test still passes.
10. Parent versions remain byte-identical after progressive processing.
11. All existing tests continue to pass, with new quality regression
    tests added.
12. Runtime, RAM, VRAM, and output dimensions are measured rather than
    invented.
13. The UI never claims that a model recovered details that were not
    present in the source.
14. V3 release notes distinguish measured quality improvements from
    subjective visual observations.

## 19. V3 Development Order

### Phase 1 --- Establish a quality baseline

-   Freeze the current V2 code and model checkpoints.
-   Save benchmark inputs and hashes.
-   Record current outputs and effective settings.
-   Capture current performance and resource measurements.
-   Identify where texture loss occurs in the pipeline.

Exit condition: a reproducible baseline exists.

### Phase 2 --- Fix excessive texture loss

-   Audit automatic denoising and smoothing.
-   Audit fixed sharpening and post-processing.
-   Compare raw model output with final output.
-   Make conservative texture-preserving behaviour the default.
-   Add the functional Texture Preservation choices.

Exit condition: grainy human-photo tests retain more natural texture
without unacceptable noise or artifacts.

### Phase 3 --- Make existing presets real

-   Define and implement backend settings for existing presets.
-   Ensure the selected task and model support those settings.
-   Record resolved settings in job/version metadata.
-   Add tests proving the settings actually affect the pipeline.

Exit condition: presets are functional, transparent, and repeatable.

### Phase 4 --- Tune existing model paths

-   Evaluate installed photo, anime, and line-art models on their
    intended image categories.
-   Run controlled comparisons.
-   Select defaults based on output quality and hardware performance.
-   Avoid adding models unless an evidenced gap cannot be addressed by
    existing models.

Exit condition: each existing task uses a tested, appropriate processing
path.

### Phase 5 --- Quality regression and release

-   Run the complete benchmark set.
-   Compare against the V2 baseline.
-   Confirm no major regression in 4K → 8K, version history, exports,
    alpha handling, or job reliability.
-   Document limitations and measured improvements.

Exit condition: the V3 quality report is reproducible and honest.

## 20. Instructions for the Implementation Agent

Treat this V3 section as the primary development direction.

Before editing code: 1. Inspect the current implementation and the V2
audit. 2. Identify exactly where each quality operation occurs. 3. Trace
the path from frontend preset to API request, worker, preprocessing,
model inference, post-processing, and export. 4. Establish baseline
outputs before changing anything. 5. Propose the smallest set of changes
that can improve measured quality.

Implementation rules: - Do not rebuild the application. - Do not add a
large set of new models. - Do not turn AETHER into a generative photo
editor. - Do not add unrelated features. - Do not assume all grain is
noise. - Do not add artificial grain or aggressive sharpening to hide
smoothing. - Do not claim that hidden details can be recovered. - Do not
change several processing variables at once during experiments. - Do not
claim quality improvements without before/after benchmark evidence. -
Preserve working features and existing APIs unless a justified change is
necessary. - Test on the actual constrained hardware profile when
available. - If a change cannot be tested on the target hardware,
clearly mark it as unverified.

At the end of each phase, report: - Files changed. - Exact processing
behaviour changed. - Benchmark images and settings used. - Before/after
output dimensions. - Runtime and memory measurements. - Visual
improvements. - Visual regressions. - Tests run and results. - Remaining
limitations.

**V3 success is measured by better images, not by a longer feature
list.**

------------------------------------------------------------------------

# PART V3 --- FINAL PRODUCT PRINCIPLE

AETHER UPSCALE should not make every image look smooth, glossy, or
artificially sharp.

For real human photographs, it should preserve the natural qualities
that make a photograph believable: skin texture, hair, grain, fine
detail, tonal variation, and the original person's appearance.

For artwork, it should preserve the artist's lines, shapes, and visual
structure.

The product should use its existing models and processing architecture
more intelligently, expose understandable controls, and provide evidence
that output quality has improved.

**The V3 objective: maximum practical super-resolution quality, with
source fidelity and natural-looking detail as the priority.**
