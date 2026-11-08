# AETHER UPSCALE 2.0 --- FINAL SPECIFICATION (Single Source of Truth)

> **Revised edition:** Includes the user-friendly frontend redesign and
> Maximum Resolution Explorer requirements. This revised file supersedes
> the previously shared FINAL SPEC.

**Date:** 7 November 2026 **Applies to:** The existing, already-built
AETHER UPSCALE application (upgrade, NOT a rebuild) **Supersedes:**
AETHER UPSCALE PRD v1.0, PRD v2.0 (greenfield), the "Upgrade PRD &
Master Prompt" draft, and the earlier Claude FINAL SPEC shared before
the frontend-usability revision. Where they conflict, THIS revised file
wins. **Reference hardware:** Windows 11, NVIDIA RTX 2050 Mobile (4 GB
VRAM, verify at runtime), 8 GB RAM, 512 GB SSD **Budget:**
Free/open-source only. No paid API, cloud GPU, subscription or API key
--- ever. **IDE/agent:** Google Antigravity. Model: whatever the owner
selected (owner-stated: Gemini 3.8 Flash High). Do not spend time
changing it.

Tags: **\[VERIFIED\]** = confirmed against an official source during
review. **\[VERIFY\]** = unconfirmed; the agent must check before
relying on it. **\[OWNER-CLAIM\]** = stated in the product dossier; not
independently audited.

------------------------------------------------------------------------

# PART A --- HOW THE AGENT MUST WORK

## A1. Authority and precedence

1.  The owner's latest instruction.
2.  This file.
3.  `AGENTS.md` / `GEMINI.md` / `SKILLS.md` in the repo (must not
    contradict this file; if they do, stop and report).
4.  Everything else (older PRDs, dossier, comments). If anything here
    conflicts with reality in the repo, report the conflict in
    `docs/V2_AUDIT.md`; do not silently pick one.

## A2. Status of the existing product (what is and is not known)

The product dossier \[OWNER-CLAIM\] says the app already has: FastAPI +
React 19/TypeScript/Vite; NCNN Vulkan inference; Real-ESRGAN general,
anime and anime-video variants; isolated inference worker; SQLite job
tracking; SSE progress; blur/noise/JPEG analyzer and model routing;
tiled inference with overlap blending and OOM tile fallback;
before/after editor, crop inspector, synchronized viewer; PNG/JPEG/WebP
export; restore / upscale / restore+upscale modes; alpha handling;
downscale-consistency check; PNG metadata; 38 passing tests; 100 MP
safety cap.

**The reviewer has NOT seen the dossier or the source code.** None of
the above is verified. The agent must treat every claim as unverified
until Phase 0 proves it (A5).

## A3. Non-negotiable rules

1.  Do NOT rebuild from scratch. Do NOT replace NCNN Vulkan without
    measured evidence of material benefit. Do NOT remove working
    features. Do NOT break existing API routes without a compatibility
    plan.
2.  Never mock inference, progress, GPU use, metrics, benchmarks or
    image quality. Progress is `null` when it cannot be measured.
3.  A model is "available" only when its weights exist, their hash
    matches the manifest, and a smoke test passed on this machine.
4.  No paid services, API keys, telemetry or cloud dependency. Images
    never leave the machine. Never upload to any third party.
5.  Windows 11 + PowerShell only. Do not assume Bash, WSL, Conda,
    Docker, Redis or admin rights. No Kubernetes/microservices.
6.  Never run destructive commands (delete, overwrite, reset) without
    explicit owner approval. Never overwrite unknown files. Never delete
    the owner's images.
7.  Download only the model needed for the current milestone, from the
    official source, and verify SHA-256. Never download all checkpoints
    at once.
8.  Do not train models. Inference, integration and small experiments
    only.
9.  Check licenses for code, checkpoint, training data and dependencies
    SEPARATELY. A permissive code license does not cover weights. Record
    in `docs/MODEL_LICENSES.md` before any download.
10. Never overwrite an original or an accepted version. Never use JPEG
    (or any lossy format) between processing stages.
11. Never silently change aspect ratio, distort, downscale the source,
    flatten transparency, or swap a user-selected model.
12. Never promise "infinite" or "unlimited" upscaling. There is no
    universal stopping point; the system enforces bounded, user-set
    limits.
13. Never claim a feature works unless it was run and tested. Never
    leave fake buttons or placeholder features.
14. Do not add dependencies or abstractions without a measured need. Pin
    versions after a working install.
15. Keep the app runnable at the end of every milestone. Never leave it
    broken while starting something else.
16. Subprocess calls use argument arrays, never shell strings built from
    user input.
17. Ollama is optional and is NOT an upscaler. The app must work without
    it. Never run it concurrently with an SR job.
18. If an environment problem (CUDA, dependency conflict) stalls
    progress, stop reinstalling; isolate the component or use the
    existing NCNN backend, document it, continue.

## A4. Skills and Graphify protocol (mandatory)

-   At the start of every session read `SKILLS.md`. If it does not
    exist, create it first: list every installed skill and connected MCP
    server with (name, what it does, when to use it here, when not to).
    Never invent a skill or a link; unknown source = "source: unknown".
-   Before EVERY step write one line:
    `Skill check: using <skill> because <reason>` or
    `Skill check: none apply because <reason>`. If a skill applies, use
    it; do not hand-roll around it.
-   Typical mapping (confirm against SKILLS.md): any error or unexpected
    behavior → systematic-debugging; before claiming done →
    verification-before-completion; long/multi-step work → the single
    planning skill chosen; licenses → model-license-check; model
    readiness → model-smoke-test; end of milestone → phase-handoff;
    library APIs (FastAPI, Vite, Tailwind, PyTorch, Pillow, NCNN
    bindings) → Context7 MCP if connected.
-   Use only ONE workflow/planning system at a time.
-   **Graphify (very important):** the codebase already exists, so build
    the graph in Phase 0 on code folders only (backend, ai_engine,
    frontend/src, scripts, tests --- never docs, weights, storage,
    models, tools, benchmarks output). Read `GRAPH_REPORT.md` at the
    start of every session. BEFORE grepping, reading many files, or
    changing shared code, query the graph ("where is X", "what depends
    on X", "what breaks if I change X"). Rebuild/update after every
    phase and every large refactor. No `--watch`. If graphify is not
    installed, tell the owner the exact install commands
    (`uv tool install graphifyy`, then `graphify antigravity install`)
    and continue without it; do not install silently. Each phase report
    states whether graphify was used and what it showed.

## A5. Verification protocol (every time, no exceptions)

1.  **Claim ledger:** `docs/V2_AUDIT.md` lists every dossier claim with
    status Verified / Refuted / Unverifiable and the evidence (exact
    command + result, or file+line).
2.  Re-run the existing test suite BEFORE any change and save the
    baseline output. Do not assume 38 tests pass.
3.  After every step run the real command/test/inference that proves it;
    record command and result in `docs/V2_IMPLEMENTATION_STATUS.md`.
4.  Before starting a phase, re-run the previous phase's acceptance
    checks. Before finishing, run the full suite.
5.  A failure → systematic root-cause debugging → fix → re-verify. Never
    skip or silently work around.
6.  Verify on the real NVIDIA GPU. Confirm the Vulkan device used is the
    NVIDIA GPU, not an Intel iGPU (see C2).
7.  Benchmarks follow the protocol in section I3; no number is reported
    without it.

## A6. Reporting

At the end of each phase report: files changed; features implemented;
commands run; tests passed/failed (counts); real hardware used; runtime
and memory observations; graphify findings; known limitations; next
exact task. Keep `docs/V2_IMPLEMENTATION_STATUS.md` current so a new
session can resume (files changed, commands, results, open errors, next
task). Stop and ask the owner only for: destructive actions, a genuinely
blocking decision with no safe default, or something only the owner can
do (connect an MCP, install a tool).

------------------------------------------------------------------------

# PART B --- PRODUCT DEFINITION

## B1. Vision

A complete local-first **image restoration, enhancement and
super-resolution studio** with a **Progressive Resolution Studio**:
upload once, restore, upscale to 4K, continue from that internal version
to 8K or a custom target, refine at the same resolution, compare stages,
accept/reject, branch, and export only when desired --- with no
intermediate download/re-upload.

Central philosophy: not a one-click 4× converter. The goal is the best
perceptual result while preserving source structure. A smaller faithful
result can beat a larger artifact-filled one.

## B2. Principles

1.  Faithfulness first; generative detail is opt-in and labelled.
2.  Every stage is reproducible and inspectable (settings, model, hash,
    version).
3.  Preserve the original and every accepted version.
4.  Local-first, private, free.
5.  Honest hardware and quality claims.
6.  Graceful fallback; the app stays useful when advanced models cannot
    run.

## B3. Result classes (label in UI and manifest)

  -----------------------------------------------------------------------
  Class                   Examples                Meaning
  ----------------------- ----------------------- -----------------------
  Restoration             denoise, deblock,       Attempts to recover
                          supported deblur        degraded real content

  Traditional enhancement resample, sharpen,      Classical; no new
                          color, contrast,        detail. Never labelled
                          bilateral/NLM filters   "AI"

  Generative detail       GAN super-resolution,   May invent plausible
                          face restoration,       detail that was not in
                          colorization, diffusion the source
  -----------------------------------------------------------------------

Even Real-ESRGAN (GAN) output is partly generative. "Faithful mode"
means the lowest-hallucination option available, not a guarantee. Never
present generated detail as recovered truth.

## B4. Out of scope

Forensic reconstruction, guaranteed text recovery, historically accurate
detail, video processing, cloud inference, training.

------------------------------------------------------------------------

# PART C --- HARDWARE AND RESOURCE RULES

## C1. Default profile (constrained)

Windows 11, RTX 2050 Mobile (VRAM detected at runtime; commonly 4 GB), 8
GB RAM (expect \~3--4 GB free after Windows and the browser), 512 GB
SSD. One heavy model at a time; lazy load/unload; conservative tiles;
FP16 only where validated; diffusion models disabled by default.
Hardware tiers displayed to the user: **Verified** (tested here),
**Tested elsewhere**, **Expected, untested**, **Unsupported**.

## C2. Windows and laptop realities (must be handled)

1.  **Hybrid GPU:** NCNN selects Vulkan devices by index (`-g`); device
    0 can be an Intel iGPU (real-world logs show this). Enumerate
    devices, select the NVIDIA GPU explicitly, and log which device ran
    each job. Do not assume auto-selection is right.
2.  **Driver reset (TDR):** long Vulkan compute can trigger a driver
    timeout/reset. Treat NCNN failures, device-lost errors,
    all-black/NaN/constant tiles as failures → retry with a smaller
    tile. Add a per-tile sanity check (not uniformly black/constant
    unless the source tile is; plausible luminance vs the source tile).
3.  **Sysmem fallback:** recent NVIDIA drivers may spill VRAM to system
    RAM (huge slowdown instead of OOM). Monitor throughput and VRAM;
    warn on collapse.
4.  **VRAM free is less than total** (Windows and the browser hold
    some). Read free memory before each heavy load.
5.  **Process control:** killing the worker must also kill its child
    NCNN process tree. Use `spawn` multiprocessing; verify no orphan
    processes after cancel.
6.  **File locking:** deleting or renaming files in use fails on
    Windows; use retry with backoff; never rely on delete-while-open.
7.  **Atomic writes:** write to `*.partial`, flush/fsync, hash, then
    `os.replace` into place.
8.  **Sleep/hibernate/power:** jobs must survive restart (resume from
    tile checkpoints). Advise plugged-in/performance power plan; record
    power state in benchmarks.
9.  **Antivirus scanning** can slow tile-file I/O; keep tile files in a
    dedicated directory and document an exclusion suggestion without
    requiring it.
10. **Long paths:** keep storage paths short; never nest deep per-tile
    paths.
11. SQLite: WAL mode, short transactions, `busy_timeout`; single writer
    discipline.

## C3. Resource estimator (required, not a hard cap alone)

Before any job compute and show: output megapixels, peak RAM estimate,
peak VRAM estimate (model+tile based), disk needed (tile store +
intermediates + output + previews), stage count, and a time estimate
labelled as an estimate from past measured runs on this machine (or
"unknown" if none exist). Refuse to start when free disk \< required ×
1.25, or RAM estimate exceeds free RAM.

**Two separate limits** (do not conflate them): - `max_inmemory_mp`:
largest image the code may hold as an in-RAM array. Default conservative
(e.g., 25 MP); anything larger MUST stream/tile via disk. -
`max_output_mp`: largest final output. Default stays the existing 100
MP. Raising it (e.g., to \~140 MP for 16K UHD) requires: owner opt-in
setting, passing large-image tests on this hardware, disk-backed
streaming, and an explicit per-job confirmation. Disk-backed
intermediates (e.g., a 4× pass later downscaled) are allowed beyond the
RAM limit but still count toward disk checks.

## C4. Reference math (use these exact numbers; do not hand-wave)

  Name      Dimensions   Megapixels   RGB8 raw   float32 RGB raw
  --------- ------------ ------------ ---------- -----------------
  1080p     1920×1080    2.07         6.2 MB     24.9 MB
  4K UHD    3840×2160    8.29         24.9 MB    99.5 MB
  8K UHD    7680×4320    33.18        99.5 MB    398 MB
  16K UHD   15360×8640   132.71       398 MB     1.59 GB

(UHD ≠ DCI 4K 4096×2160; do not mix them.) RGBA adds one-third.
Consequences: 1080p→8K is exactly 4×. 4K→8K is exactly 2×. **A 4× model
on a 4K input produces a 16K (132.7 MP) intermediate** --- over the 100
MP cap and \~1.6 GB as float32. Section F handles this. Format limits to
validate before export: WebP max 16383 px per side; JPEG max 65535 px
per side. 16K UHD width (15360) fits WebP but only just; reject
over-limit exports with a clear message.

------------------------------------------------------------------------

# PART D --- ARCHITECTURE

## D1. Principle

Preserve FastAPI + SQLite + isolated worker subprocess. Add services; do
not rewrite. The audit (Phase 0) maps the real file layout; the names
below are targets --- adapt them to what exists.

    Browser (React 19 + TS + Vite)
       | REST + SSE, opaque IDs only, 127.0.0.1
    FastAPI API  ──  SQLite (WAL): projects, versions, jobs, stages, tiles, model_status, settings, schema_version
       | DB-backed queue, ONE heavy job at a time (constrained profile)
    Worker subprocess (spawn; owns the GPU; killable with its child process tree)
       ├ Analyzer (CPU, heuristic, with confidence)
       ├ Router / Resolution Planner
       ├ Pipelines: restore | upscale | refine | progressive
       ├ Tile engine (halo, feathered blend, OOM retry, tile store, checkpoints)
       ├ Backends: NCNN-Vulkan (default) | optional Torch worker (isolated venv) | optional extra adapters
       └ Quality service (metrics, stage comparison, seam checks)
    Storage (local disk only): uploads / versions / tiles / previews+pyramids / temp ; originals read-only

Target modules (create only what is needed, when needed):

    backend/app/api/        projects.py versions.py resolution.py pipelines.py   (existing routes preserved)
    backend/app/services/   project_service version_service resolution_planner progressive_engine resource_estimator quality_service storage_service migration_service
    ai_engine/pipelines/    progressive_pipeline.py refinement_pipeline.py
    ai_engine/quality/      metrics.py stage_comparison.py seam_check.py
    ai_engine/processing/   color_management.py tile_store.py streaming_resample.py

## D2. Backends

-   **NCNN Vulkan (default, preserve).** \[VERIFIED from official
    README/help\] portable exe options include `-s` (2, 3 or 4; default
    4), `-t` tile size (≥32; 0=auto), `-m` model path, `-n` model name
    (shipped: `realesr-animevideov3`, `realesrgan-x4plus`,
    `realesrgan-x4plus-anime`, `realesrnet-x4plus`), `-g` GPU id, `-j`
    thread counts, `-x` TTA, `-f` format. The README states the portable
    exe does not support every Python-script feature (e.g., arbitrary
    `outscale`). The agent must re-read `-h` of the installed build; do
    not assume `-s 2/3` works for every model --- test per model and
    verify exact output dimensions.
-   **Tiling ownership must be determined in the audit:** does the app
    call NCNN once per image with `-t`, or run its own tile loop calling
    NCNN per tile? Checkpoint/pause design (G4) depends on this. NCNN
    invoked per call reloads the model each time; if the app drives
    tiles, measure the overhead and evaluate Python NCNN bindings
    \[VERIFY availability/license\] to keep the model loaded.
-   **Optional Torch worker (isolated venv, JSON-over-stdio),** only if
    benchmarks show material benefit. Reason it exists:
    `RealESRGAN_x2plus` (native 2×) and `realesr-general-x4v3` (with
    WDN-weight denoise interpolation) are available as PyTorch
    checkpoints \[VERIFIED in official inference script: x2plus v0.2.1;
    general-x4v3 + general-wdn-x4v3 v0.2.5.0\] but are NOT in the NCNN
    portable model list. Converting them to NCNN is an alternative;
    evaluate which is simpler. Python script `outscale` resizes after
    inference with LANCZOS4 \[VERIFIED\]. Python path also supports
    alpha, grayscale and 16-bit input \[VERIFIED per README\] --- NCNN
    path should be assumed 8-bit unless proven otherwise. Do not install
    PyTorch into the main API environment unless verified harmless;
    avoid the BasicSR/`torchvision.transforms.functional_tensor` break
    by pinning or by using a loader such as Spandrel \[VERIFY\].
-   **Rule:** one heavy model resident at a time; unload before loading
    another; never run two heavy backends concurrently on the 4 GB GPU.

## D3. Model adapter interface (extend, don't replace)

`load(device, precision)`,
`enhance(in_array_or_path, out, scale, options, progress_cb, cancel_event)`,
`unload()`, `capabilities()` (native scales, tile limits, alpha support,
bit depth, supported tasks). Capabilities drive the UI: hide/disable
unsupported controls with an explanation.

## D4. Model registry states

Installed+smoke-tested · Download available · Tested on this device ·
Expected but untested · Unsupported by hardware · Disabled due to
licensing · Experimental. Per model: id, display name, adapter,
checkpoint path, SHA-256, version, official source URL, code license,
**weight license**, license status (verified/unclear), license class
(permissive / non-commercial / unclear), tasks, scales, measured min
VRAM, tile defaults, availability, enabled-on-this-profile.

## D5. Analyzer

Heuristic signals (Laplacian variance normalised for size, MAD noise
estimate, 8×8 JPEG blockiness, JPEG quantisation tables via Pillow when
JPEG, saturation/edge statistics, face detection if a detector is
available). Output estimates WITH confidence/uncertainty and a user
override. These are not ground truth. Calibrate thresholds on the legal
test set (Part I) and record results; do not tune on a single image.

------------------------------------------------------------------------

# PART E --- DATA MODEL AND STORAGE (the version graph)

## E1. Entities

-   **Project:** id (opaque), name, source_image_id, created_at,
    settings.
-   **Version (immutable):** version_id, parent_version_id (nullable for
    original), project_id, storage_ref (opaque, never a browser path),
    width, height, megapixels, pixel_format, bit_depth, has_alpha,
    color_profile, operation
    (original\|restore\|upscale\|refine\|branch\|import), mode,
    model_id/version/checkpoint_hash, parameters (JSON), tile_size,
    overlap, backend, device, runtime_s, peak_ram, peak_vram, sha256,
    quality_eval (JSON, nullable), state (building\|ready\|corrupt),
    decision (pending\|accepted\|rejected), created_at.
-   **Job:** job_id, project_id, source_version_id, plan (JSON), status,
    current_stage, created/started/finished, error code.
-   **Stage:** stage_id, job_id, index, operation, model, from_size,
    to_size, status, tile_grid, resume_state, output_version_id.
-   **Tile:** stage_id, grid_x, grid_y, status, file_ref, sha256.
-   **schema_version** table + forward-only migrations.

## E2. Invariants (test all of them)

1.  Versions are immutable once `ready`. Files set read-only; verified
    by size always and by SHA-256 on demand and before using a version
    as a source for a long job.
2.  A job never writes into a version it reads from. New output = new
    version.
3.  Write order: stage output to `*.partial` → hash → atomic rename → DB
    transaction marks version `ready`. On startup reconcile: delete
    `*.partial` orphans, mark DB rows without files `corrupt`, never
    delete files that DB references.
4.  A rejected stage leaves the parent version and every other version
    byte-identical.
5.  Accepted versions are never auto-deleted. Rejected versions are
    retained for a configurable period (default 7 days), then eligible
    for cleanup after user-visible notice.
6.  Deleting a version that has children is blocked unless the user
    deletes the whole subtree (explicit confirmation listing sizes). The
    original is protected: deleting it needs a second explicit
    confirmation.
7.  Browser input is opaque IDs and validated settings only; never a
    filesystem path.

## E2a. Migrations (existing jobs must keep working)

Add `schema_version`; write idempotent forward migrations; back up the
SQLite file before migrating (copy, do not move); provide a migration
test that opens an old-format database and verifies old jobs still
list/download; legacy job outputs are wrapped as versions without moving
the files unless needed.

## E3. Storage formats

-   **Never JPEG between stages.** Intermediates are lossless.
-   Small/medium images: lossless PNG is acceptable. **Large images
    (decision rule: above `max_inmemory_mp`, or any 8K+ version): use
    tiled, losslessly compressed storage (e.g., tiled TIFF) so crops and
    streaming reads do not require decoding the whole image.** The audit
    chooses the library (`tifffile`, `pyvips` binary wheel, or
    Pillow-only) by testing on this machine \[VERIFY\]; record in
    `docs/DECISIONS.md`.
-   Pillow's decompression-bomb limit must be set deliberately (not
    disabled blindly) and tested. Never decode a 33--133 MP image fully
    just to serve a preview or crop.
-   Preview pyramids / tiles generated lazily and cached for the viewer
    (G/H); cleanup-able; never required for correctness.
-   Preserve ICC profile (convert to sRGB for processing; embed on
    export), EXIF orientation applied once, alpha kept. Bit depth: if
    NCNN is 8-bit-only, say so in the UI when a 16-bit source is
    processed ("processed at 8-bit"); do not claim 16-bit end-to-end.
-   Disk quotas: per-project size shown; global limit setting; warn
    before starting jobs that would exceed it.

## E4. Provenance

PNG text metadata is convenience only, NOT proof. Authoritative
provenance = a separate manifest (JSON) per version: source hash, output
hash, parent chain, model+checkpoint hash, parameters, versions of
software, timestamps. Optional local signing (e.g., Ed25519 key kept
locally) is allowed; never a cloud service.

------------------------------------------------------------------------

# PART F --- RESOLUTION PLANNER AND PROGRESSIVE ENGINE (flagship)

## F1. Three operations

A. **Direct target scaling** --- one logical operation to an exact size;
engine picks model scale and any final resample. B. **Progressive
multi-stage scaling** --- output of one stage is the next stage's input,
internally. C. **Same-resolution refinement** --- dimensions unchanged
(denoise, deblock, supported deblur, face restoration, color,
conservative sharpening). The UI must distinguish "more pixels" from
"better quality at the same size".

## F2. Planner rules (this resolves the repeated-pass problem)

For a requested target, the planner computes and shows up to three plans
with explicit costs and warnings: 1. **Plan A --- Direct from the best
ancestor (default recommendation).** Walk up the version graph to the
earliest lossless ancestor (usually the original). If the target is
reachable in a single model pass from there, prefer that. Example: 1080p
original → 8K is exactly 4× → ONE pass of a 4× model; this is the
faithful path. Reaching 8K by 1080p→4K→8K is TWO passes of a GAN model
and is not the default. 2. **Plan B --- Continue from the selected
version.** Allowed (the flagship requirement: continue 4K→8K without
re-upload). If the selected version's last model is in the same model
family as the model the planner would use, require
`allow_same_model_repeat=true` plus an explicit UI confirmation showing
the diminishing-returns/hallucination warning. If a different model is
justified by task/compatibility, use it. Record why. 3. **Plan C ---
Classical resample (labelled "Traditional enhancement, no new
detail").** Always available for comparison. Never force another pass
just because more pixels are possible. The user may run A and B as
branches and compare.

## F3. Scale selection per target

Let `f = target_w / source_w` (aspect-ratio must match within 1 px
unless the user chose crop/pad/stretch explicitly; never distort
silently). - If a model with native scale `s` exists with `s ≥ f`: use
it, then resample down by `f/s` with anti-aliasing (area/Lanczos). If
`s` is a better fit (e.g., a native 2× model for f=2), use that and skip
the wasted compute. - If `f > s`: use multiple stages only through Plan
A/B rules above. - `-s 2/3` in NCNN must be tested per model (F3 note in
D2); never assume. - Compute cost scales with the model's OUTPUT pixels;
a 4× model asked for 2× still computes 4× pixels. Show this in the
estimate. Native-2× (`RealESRGAN_x2plus`) halves the linear factor ---
treat this as a hypothesis to BENCHMARK, not a promise.

## F4. The 4K→8K problem and its required solution

Running a 4× model on a 4K image yields 15360×8640. Do NOT materialise
it in RAM and do not rely on the 100 MP cap being lifted. Required
approach, in preference order: 1. Native 2× model (Torch worker or
converted NCNN) if benchmarked as beneficial. 2. **Per-tile scale
adaptation:** run the 4× model per macro-tile (with halo), immediately
downscale each tile output by `f/4` with an anti-aliased filter, then
blend into the final-resolution tile store. Tile geometry must make
final-scale tile boundaries integral (choose tile/halo sizes
accordingly, or compute boundaries by exact rational rounding with a
larger resample margin). Must pass the seam test (I4); if seams appear,
fall back to 3. 3. **Disk-backed 4× intermediate:** write the 4× result
to tiled lossless storage on disk (≈398 MB raw for 16K), then
stream-downscale to the target in blocks. Allowed beyond
`max_inmemory_mp`; counts toward disk preflight. The agent chooses based
on measured quality/time on this machine and records the decision.

## F5. Auto-Continue / Maximum Practical Resolution

Default OFF. When enabled, bounded by: user max width/height,
`max_output_mp`, free disk/RAM/VRAM, estimated time, model-supported
scales, **`max_stages` default 2**, per-stage user acceptance by default
(unattended multi-stage only if the user opts in), quality-regression
warnings, cancellation. It may RECOMMEND stopping (no suitable model,
resource limit, candidate materially worse, next step is mostly
interpolation). It never claims further upscaling is impossible or that
quality cannot improve.

### F5a. Maximum Resolution Explorer

Provide a user-facing **Maximum Resolution Explorer** that estimates
what this particular computer can reasonably attempt for the selected
image. It is a planning aid, not a guarantee and not a claim about the
world's theoretical maximum. - Show the source dimensions and
megapixels, candidate target dimensions and megapixels, selected
model/backend compatibility, estimated peak RAM/VRAM, temporary and
final disk requirements, likely stage count, and measured-time estimate
(or "unknown"). - Offer sensible targets such as 2×, 4×, 4K, 8K, 16K
(only if allowed by current limits), and custom dimensions. Do not imply
that every target is supported by every model. - Distinguish **maximum
technically permitted output** from **recommended practical output**.
The recommended output should account for resource limits, model
capability, estimated processing cost, and likely quality regression. -
Explain in plain language why a target is unavailable or not recommended
(for example: "This image would exceed the current 100-megapixel limit"
or "The selected model does not support this scale"). - Allow the owner
to configure limits, but never silently raise `max_output_mp`, disable
safety checks, or promise unlimited resolution. - Do not present an
estimated time or memory value as measured. Label estimates clearly and
show "unknown" when there is no reliable measurement.

## F6. Stage checkpointing, pause, resume, cancel

-   Each stage works on a **tile store** (lossless per-tile files + DB
    tile rows with hashes). A resumed job skips tiles that exist and
    verify. Assembly into the output version happens only when all tiles
    are verified.
-   **Pause = stop at the next tile boundary, persist state, release the
    GPU** (and kill the NCNN child). Resume = reload and continue. State
    clearly in the UI that pause is not instantaneous.
-   **Cancel:** stop between tiles, kill the process tree, mark the
    stage cancelled, leave prior versions untouched, delete partial tile
    stores only on user confirmation or per retention policy.
-   **Restart/crash:** on startup, running jobs become `interrupted` and
    are resumable.
-   **OOM / TDR / bad tile:** retry the tile with a smaller tile size
    (then retry once after unloading), then fall back per C2/D2; if
    still failing the stage fails cleanly. A failed stage never corrupts
    prior versions.
-   **Disk full:** detected before and during; stop cleanly; keep
    verified tiles.

## F7. Stage acceptance

Each completed stage creates a version in `pending` decision. The user
can compare against the parent, accept, reject, or branch. Quality
evaluation (Part I) is advisory; it can recommend rejecting but never
auto-deletes.

## F8. Request shape (example; extend existing schema compatibly)

``` json
{
  "project_id": "opaque",
  "source_version_id": "opaque",
  "operation": "progressive_upscale",
  "target": {"width": 7680, "height": 4320},
  "aspect_policy": "require_match",
  "plan": "A",
  "mode": "faithful",
  "model_strategy": "auto",
  "allow_same_model_repeat": false,
  "max_megapixels": 50,
  "max_stages": 2,
  "preserve_alpha": true,
  "output_format": "png"
}
```

Validate every field; reject mismatched aspect unless an explicit
crop/pad/stretch policy is chosen.

------------------------------------------------------------------------

# PART G --- MODELS

## G1. Active/known (preserve)

`realesrgan-x4plus` (general photo), `realesrgan-x4plus-anime`
(anime/illustration), `realesr-animevideov3` (fast animation model; not
a general photo model). Official sources:
https://github.com/xinntao/Real-ESRGAN ,
https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan (+ releases).
Official checkpoints: `RealESRGAN_x4plus.pth` (v0.1.0),
`RealESRGAN_x4plus_anime_6B.pth` (v0.2.2.4).

## G2. Cheap next steps (in order)

1.  **`realesrnet-x4plus`** --- already in the NCNN portable model list
    \[VERIFIED\]; PSNR-oriented, smoother, fewer invented textures →
    candidate "Maximum Faithfulness" model. Zero new runtime needed;
    smoke test, benchmark, add to the registry.
2.  **Fidelity slider (honest implementation):** with NCNN-only models,
    implement as a **pixel-space blend of the RealESRNet and RealESRGAN
    outputs** (two sequential passes, so \~2× cost; show it). Weight
    interpolation between the two checkpoints (same architecture) is
    possible only in the Torch worker; do not call the blend
    "interpolation of weights".
3.  Torch worker + `RealESRGAN_x2plus` and `realesr-general-x4v3` (+ WDN
    denoise strength) --- only after benchmarks show benefit and the
    isolation holds.

## G3. Additional candidates (evaluate one at a time; never bulk-download)

-   Waifu2x NCNN Vulkan (https://github.com/nihui/waifu2x-ncnn-vulkan)
    for anime/line art --- \[VERIFY license and model terms\].
-   SwinIR (https://github.com/JingyunLiang/SwinIR), HAT
    (https://github.com/XPixelGroup/HAT), BasicSR
    (https://github.com/XPixelGroup/BasicSR): optional separate
    adapters; select specific lightweight checkpoints; measure on this
    GPU; HAT-L likely too heavy \[VERIFY by measurement\].
-   Face restoration: GFPGAN (https://github.com/TencentARC/GFPGAN) OR
    CodeFormer (https://github.com/sczhou/CodeFormer) --- pick ONE after
    comparing on the same faces; never chain both by default.
    CodeFormer's license is believed non-commercial \[VERIFY\]. Opt-in
    only; feathered paste-back with blend weight; keep the pre-face
    result.
-   Blind restoration candidates (SCUNet, FBCNN, NAFNet, Restormer):
    research only if an official compatible implementation and
    checkpoint exist; \[VERIFY licenses --- some are
    academic/non-commercial\].
-   Damage repair: only a real implementation (manual-mask inpainting,
    e.g., LaMa \[VERIFY\], or classical `cv2.inpaint`). No claim of
    automatic scratch repair without a real detector.

## G4. Generative candidates (research-only, disabled by default)

-   **HYPIR** (https://github.com/XPixelGroup/HYPIR): LoRA on Stable
    Diffusion 2.1, Python 3.10, CUDA PyTorch; its README declares
    **non-commercial use only** \[VERIFIED\]; its README says inference
    runs on a free T4 (16 GB), which is NOT evidence it runs on 4 GB
    \[VERIFIED\]. The SD 2.1 base has its own terms \[VERIFY\].
-   **SUPIR** (https://github.com/Fanghua-Yu/SUPIR): license text
    restricts to non-commercial use \[VERIFIED\]; very heavy; not for
    this profile.
-   **DiffBIR** (https://github.com/XPixelGroup/DiffBIR): code listed
    under Apache-2.0 \[VERIFIED from the org listing\]; weights and the
    SD base are separate \[VERIFY\]; heavy.
-   Rules: opt-in, hallucination warning, never in Faithful mode, save
    the faithful result separately, report "unavailable" with the reason
    if hardware is insufficient, never silently send images anywhere.
    Personal local use of non-commercial models is the owner's choice,
    but the registry must carry `license_class` so any future
    distributable build excludes them.

## G5. Ollama

Optional: captions or preset suggestions only if a vision model is
already installed. Never in the processing path, never concurrent with
SR, `keep_alive: 0`.

## G6. Licensing table (maintain in `docs/MODEL_LICENSES.md`)

Columns: model, code license, weight license, training-data notes,
status (verified/unclear), license class, source URL, SHA-256,
checked-on date. Real-ESRGAN code is believed BSD-3-Clause \[VERIFY\];
weight terms: mark "unclear" until the release page/model card is read.
Keep any model with unclear rights or unmet hardware needs disabled.

------------------------------------------------------------------------

# PART H --- RESTORATION AND ENHANCEMENT TOOLKIT

Independent, previewable, non-destructive, composable operations; each
labelled Classical / Neural / Generative; hide/disable controls the
selected pipeline cannot honour. - **Restoration:** JPEG
deblocking/ringing, color/Gaussian noise reduction, mild deblur only
with a validated model, face restoration (opt-in), transparent-edge
cleanup, optional color-cast correction, damage repair only with a real
method. - **Enhancement:** exposure/gamma, contrast, highlights/shadows,
white balance/tint, saturation/vibrance, local contrast, sharpening with
halo control, optional film grain, dehaze only if implemented and
tested. - **Region-aware:** brush/rectangle/lasso masks, face regions;
masks editable, feathered, stored with project metadata. No large
segmentation model in the low-memory profile without measurement.
Foreground/background selection only if a suitable model is installed. -
**Presets** (starting points, not guarantees): Natural Photo, Maximum
Faithfulness, Detailed Photo, Portrait Recovery, Old Photograph,
Anime/Illustration, Manga, Compressed Web Image, Low-Light, Game
Asset/Texture, Transparent PNG/Icon, Custom. Never auto-route photos to
anime models. - **Alpha:** bleed colors outward under transparent pixels
before upscaling, upscale alpha separately, recombine; never silently
flatten.

------------------------------------------------------------------------

# PART I --- QUALITY, BENCHMARKS, TESTS

## I1. Metrics

PSNR/SSIM only with ground truth; LPIPS/DISTS when a reference setup
exists; optional no-reference (MUSIQ/NIQE via `pyiqa`) correctly
configured; edge/halo analysis; seam analysis; Lab color drift;
dimension checks; runtime; peak RAM/VRAM; disk use. **The
downscale-consistency check is NOT proof of fidelity** (a hallucinated
image can downsample close to the source); label it "consistency with
the source, not authenticity". Never merge unrelated metrics into one
score without calibration; never show a made-up score.

## I2. Test data

A small fixed, legally usable set (self-made or properly licensed):
portraits/faces/hair, text, foliage, architecture, anime line art,
digital art, JPEG artifacts, low-light noise, gradients, transparent
PNG, fine textures, odd dimensions, portrait orientation, extreme
panorama. Build a **synthetic degradation set**
(downscale+blur+noise+JPEG applied to the owner's own high-resolution
images) so full-reference metrics mean something; note that PSNR/SSIM on
bicubic-downsampled inputs do not predict real-world GAN quality. Do not
auto-download large datasets.

## I3. Benchmark protocol (the dossier's timings differed between sections --- standardise)

Record: hardware, driver version, power mode, backend/exe version,
model + checkpoint hash, input file hashes and dimensions, tile
size/overlap, scale path, warm-up policy (discard first run), N≥3 runs
with median and spread, timing boundaries (model load / inference /
blending / encode reported separately), peak VRAM/RAM, disk use,
retries, valid metrics. Test sizes: 256², 512², 1080p, 1440p, 4K, and
feasible 8K (8K is a test target, not a speed promise). 16K only after
the C3 conditions.

## I4. Required tests (add; keep existing)

Rerun and save baseline of existing tests first. New tests: 1080p→4K
exact dims; 4K→8K exact 7680×4320; 1080p→8K single-pass plan chosen as
default; custom target & aspect-ratio validation (mismatch rejected
without policy); progressive stage chaining; **no browser
download/re-upload between stages** (the API never returns an
intermediate to the client and the next stage reads by version ID);
version persistence/branching; every invariant in E2; migration of an
old DB; resume after process restart; pause/resume at tile boundary;
cancel kills the child process tree; OOM retry (mock the exception);
bad-tile (black/NaN) retry; disk-full; `max_output_mp` and
`max_inmemory_mp` enforcement; output integrity (hash); **no JPEG
intermediate**; rejected stage leaves parent unchanged;
same-model-repeat requires confirmation; manifest/hash correctness;
alpha/ICC/EXIF behavior; odd sizes/portrait; format dimension limits
(WebP 16383, JPEG 65535); path-traversal and malformed-input tests. Seam
tests: real-image seam metric across tile boundaries, with synthetic
grid images AND real photos, at 100% zoom review of faces, eyes, hair,
text, diagonals, fine lines, foliage, architecture, gradients,
transparent edges. Keep the existing Hann/raised-cosine blend if it
passes regression. Regression: baseline outputs for the fixed set;
compare dimensions and visual difference after every change; a metric
gain alone never proves better perceptual quality.

------------------------------------------------------------------------

# PART J --- API

Preserve every existing route. Add (names may be adapted to the
codebase's conventions; document the final contract): \| Method \|
Endpoint \| Purpose \| \|---\|---\|---\| \| POST \| `/api/v1/projects`
\| Create project from an uploaded source \| \| GET \|
`/api/v1/projects/{id}` \| Project + versions summary \| \| GET \|
`/api/v1/projects/{id}/versions` \| Version graph \| \| POST \|
`/api/v1/projects/{id}/plan` \| Return plans A/B/C with estimates (no
processing) \| \| POST \| `/api/v1/projects/{id}/versions/{vid}/upscale`
\| Continue from an internal version \| \| POST \|
`/api/v1/projects/{id}/versions/{vid}/restore` \| Restore selected
version \| \| POST \| `/api/v1/projects/{id}/versions/{vid}/refine` \|
Same-resolution refinement \| \| POST \|
`/api/v1/projects/{id}/versions/{vid}/branch` \| Create a branch \| \|
POST \| `/api/v1/versions/{vid}/decision` \| accept / reject \| \| GET
\| `/api/v1/jobs/{id}/stages` \| Stage progress \| \| GET \|
`/api/v1/jobs/{id}/events` \| SSE \| \| POST \|
`/api/v1/jobs/{id}/pause` · `/resume` · `/cancel` \| Controls (pause at
tile boundary) \| \| POST \| `/api/v1/versions/{vid}/compare` \| Compare
two versions (metrics + seam/color) \| \| GET \|
`/api/v1/versions/{vid}/preview` · `/tile/{z}/{x}/{y}` · `/crop` \|
Viewer data (derivatives, never the full original) \| \| GET \|
`/api/v1/versions/{vid}/download` \| Export (format-limit validated) \|
\| DELETE \| `/api/v1/versions/{vid}` · `/projects/{id}` \|
Subtree/project deletion per E2 \|

Requirements: validate every field; reject filesystem paths; opaque IDs;
structured error codes; no stack traces to the client; do not log image
content or sensitive paths; no local paths in responses; request
timeouts; job status `progress: null` when unmeasurable.

------------------------------------------------------------------------

# PART K --- FRONTEND AND USER EXPERIENCE

## K1. Overall design direction

Keep the existing dark studio visual identity and working components.
This is a usability redesign and extension, not a visual rebuild for its
own sake.

The interface must work for two audiences: - **Everyday users:** people
who want a better image but do not know AI model names, algorithms, GPU
backends, or image-processing terminology. - **Advanced users:** people
who want to inspect or manually control models and technical parameters.

Default to the everyday-user experience. Keep advanced controls
available, but do not make technical knowledge a requirement for
ordinary tasks.

Suggested layout: left = projects/sources/history/versions; center =
canvas, comparison, zoom; right = simple task and quality controls,
Resolution Studio; header = project, processing/device status, and
export. Adapt to the actual existing frontend rather than replacing
working components unnecessarily.

## K2. Simple main workflow

The primary workflow should be understandable without a tutorial:

**Choose Image → Choose What You Want to Do → Choose Output Size →
Preview/Enhance → Compare → Export**

The first screen should make the next action obvious. Use short
descriptions under controls. Avoid presenting a wall of model names,
abbreviations, sliders, or unexplained settings.

## K3. User-facing task categories

Use clear task names such as: - **Improve a Photo** --- general
photographic clarity and detail enhancement. - **Restore an Old Photo**
--- supported fading, noise, compression and damage-repair workflows. -
**Enhance a Face** --- optional face-focused restoration. - **Anime &
Cartoons** --- anime and cartoon artwork. - **Illustrations & Line Art**
--- drawings, manga and clean outlines. - **Repair a Compressed Image**
--- supported JPEG blockiness and ringing reduction. - **Transparent
Images & Icons** --- preserve and improve transparent artwork.

Only show a category as available when a real compatible pipeline is
installed, smoke-tested and enabled. If a category is not supported on
the current machine, either hide it or show it as unavailable with a
clear reason. Never use a decorative card or button that does nothing.

## K4. Plain-language quality presets

Offer a small set of understandable starting points: - **Natural** ---
aims to keep the image looking realistic and avoid excessive
processing. - **Faithful** --- chooses the least-generative suitable
option available; it is not a guarantee that every output detail is
authentic. - **More Detail** --- favours stronger detail enhancement and
may create plausible details that were not present in the source. -
**Smooth & Clean** --- prioritises supported noise and compression
cleanup. - **Portrait** --- uses supported face-aware processing, with a
clear warning that facial details may be reconstructed. - **Artwork**
--- favours suitable illustration/anime processing and preserves
line-art appearance where possible. - **Old Photo** --- combines only
the restoration operations actually supported by the installed
pipeline. - **Custom** --- exposes user-selected operations and
settings.

Presets are starting points, not promises. Their actual model and
operation choices must be determined by verified model capabilities and
recorded in the job manifest.

## K5. Friendly model names and technical transparency

Do not use raw checkpoint or repository names as the primary choices in
the everyday interface.

Each model registry entry must support: - `technical_id` / actual
checkpoint name (internal identifier; never change it to a friendly
alias). - `friendly_name` (plain-language display name). -
`short_description` (what it is good for). - `tasks` and `capabilities`
(verified). - `limitations` (plain-language). - `availability` and
device compatibility. - code/weight license status.

Examples of possible friendly labels: - A tested general photo model may
be shown as **Detailed Photo**. - A tested conservative model may be
shown as **Natural & Faithful**. - A tested anime model may be shown as
**Anime & Cartoon**. - A tested face-restoration model may be shown as
**Face Restoration**.

These are examples, NOT hard-coded mappings. The agent must verify each
model's real behaviour and supported tasks before assigning a label. Do
not imply that a model is faithful, natural, portrait-capable or
suitable for a task without testing.

The everyday interface should show the friendly name and explanation.
The actual model/checkpoint name belongs under an expandable **Technical
Details** section or Advanced Mode. Never remove technical transparency.

## K6. Resolution controls and Resolution Studio

Make output size understandable: - Simple choices: **2×**, **4×**,
**4K**, **8K**, **16K (only when permitted)**, and **Custom size**. -
Show current dimensions and requested output dimensions in pixels. -
Explain that 4K→8K is a 2× linear increase. - Show output megapixels and
clear warnings when a target exceeds a configured limit. - Show the
recommended plan and allow the user to inspect alternative plans
A/B/C. - Use plain-language labels alongside internal terminology. For
example, "Continue from this version" rather than only "Plan B". - Show
estimates for memory, storage, stage count and processing time, clearly
labelling estimates versus measured values. - Include the Maximum
Resolution Explorer from F5a. - Do not show 16K or larger as selectable
when the current configuration or resource checks prohibit it.

## K7. Advanced Settings and Expert Mode

Keep technical controls inside a collapsed **Advanced Settings** area or
an explicit **Expert Mode**. Ordinary users should not need to open it.

Where supported, advanced controls may include: - Actual
model/checkpoint selection. - Model version and checkpoint status. -
Enhancement or denoising strength. - Face-restoration strength. - Tile
size and overlap. - Processing backend and GPU selection. - Precision
settings. - Model-specific parameters.

Every control must have a short explanation, a safe default, and
capability-based validation. Hide or disable unsupported controls with a
reason. Do not expose settings that the selected backend ignores.

## K8. Technical Details panel

For users who want to know what happened, provide an expandable panel
showing: - Actual model and checkpoint name. - Model/checkpoint version
and hash status. - Processing method and result class: Classical, Neural
or Generative. - Backend and actual GPU used. - Input and output
dimensions. - Processing stages and parameters. - Runtime and measured
resource use, when available. - Warnings and known limitations.

The UI must not hide whether a result uses generated detail. Display the
appropriate hallucination warning for generative processing.

## K9. Existing studio capabilities to preserve and improve

-   **Resolution Studio:** current/target dimensions, presets (1.5×, 2×,
    3×, 4×, 4K, 8K, 16K only if allowed, custom), aspect handling, plans
    A/B/C with estimates and warnings, stage timeline, model per stage,
    megapixels/disk/RAM estimates, fidelity mode,
    start/pause/resume/cancel, accept/reject, branch.
-   **Version timeline/graph:** Original → Restored → Upscaled → Refined
    → Alternate model; compare any two; continue from any.
-   **Model comparison lab:** run the same image/crop through two
    installed models sequentially (never simultaneously on 4 GB);
    compare detail, noise, edges, faces, runtime, memory. Present
    friendly names first; technical model names remain inspectable.
-   **Batch:** queue, per-image presets, shared target, individual
    progress, pause/cancel, error isolation, export folder, no automatic
    overwrite.
-   **Large images:** never load 8K+ originals into browser canvases.
    Serve derivatives/pyramid tiles; `/crop` for 100% inspection. Test
    on the real browser with 8K versions.
-   **Comparison:** before/after slider, side-by-side view, zoom and
    crop inspection, compare any saved versions.
-   **Genuine processing states:** Uploading, Validating, Analyzing,
    Waiting for model, Loading model, Processing, Blending tiles,
    Validating output, Paused, Completed, Failed, Cancelled,
    Interrupted. No fake percentages.
-   Label every control/result with its result class (B3). Show the
    hallucination warning where generative classes are used.

## K10. Usability, accessibility and contextual help

-   Use plain language and concise tooltips for unfamiliar terms.
-   Explain technical terms only when needed; do not fill the default
    interface with explanations of internal implementation.
-   Use consistent names for the same operation throughout the
    application.
-   Keep primary actions visually clear and avoid duplicate controls.
-   Provide confirmation before costly, destructive or potentially
    quality-reducing operations.
-   Make error messages actionable: explain what happened and what the
    user can try next.
-   Keep layouts usable at common desktop and laptop sizes; ensure
    controls remain usable on smaller screens.
-   Preserve keyboard navigation, visible focus, readable contrast and
    accessible labels.
-   Do not display internal file paths, stack traces, or raw backend
    errors.

## K11. Frontend acceptance criteria

1.  A first-time user can upload a supported image, choose a task,
    select a target size, process, compare and export without needing to
    understand model names or abbreviations.
2.  The everyday interface uses friendly names and short descriptions;
    actual model names remain available in Technical Details or Expert
    Mode.
3.  Every visible task, preset, model and control maps to a real, tested
    backend capability.
4.  The interface never promises a capability that is unavailable on the
    current hardware or with the installed checkpoints.
5.  The 4K→8K internal continuation workflow is operable from the UI
    without downloading/re-uploading intermediate images.
6.  The Maximum Resolution Explorer clearly distinguishes recommended
    output from the maximum technically permitted output.
7.  Advanced users can still inspect model names, versions, settings,
    backend and GPU details.
8.  Existing working studio features and API compatibility are
    preserved.

------------------------------------------------------------------------

# PART L --- SECURITY AND PRIVACY

Bind to `127.0.0.1` only; CORS only for the configured frontend origin;
validate extension AND decoded signature; file-size and pixel limits;
opaque server IDs; sanitise filenames; path-traversal protection;
outputs confined to the storage root; subprocess argument arrays; one
heavy job at a time (queue the rest); no secrets in source control; no
telemetry; delete controls for jobs/projects/versions; configurable temp
cleanup; weights and user images git-ignored. Tests for malformed inputs
and path traversal. Licensing and privacy review are part of Phase 8.

------------------------------------------------------------------------

# PART M --- ROADMAP (phases, in order; each ends with verification + report)

**Phase 0 --- Audit and baseline.** Inspect the repo; map the real
layout; build the graphify graph; run the existing tests and save the
baseline; verify Python/Node/NCNN/Vulkan devices/GPU/VRAM; verify
installed checkpoints and hashes; read the actual benchmark data;
determine tiling ownership (D2); produce the claim ledger and licensing
check. Outputs: `docs/V2_AUDIT.md`, `docs/V2_IMPLEMENTATION_STATUS.md`,
`docs/DECISIONS.md`, `docs/KNOWN_LIMITATIONS.md`, `SKILLS.md`,
`docs/MODEL_LICENSES.md`, prioritised task list. Exit: verified baseline
and plan.

**Phase 1 --- Version graph.** Schema + migrations (E2a), storage
service, atomic write protocol, hashes, manifests, wrap legacy jobs as
versions, deletion rules. Exit: every output is a reusable source; all
E2 invariants tested; old jobs still work.

**Phase 2 --- Progressive engine.** Resource estimator, planner (plans
A/B/C), tile store + checkpoints, pause/resume/cancel, per-tile scale
adaptation or disk-backed intermediate (F4), branching, stage
accept/reject, same-model-repeat policy. **First flagship test:** take
an existing processed 4K version, request 8K UHD, process internally
with no browser round-trip, verify exactly 7680×4320, original and 4K
versions byte-identical afterwards. Also run the 1080p→8K single-pass
path and compare.

**Phase 3 --- Resolution Studio UI and usability redesign.** Implement
the beginner-friendly workflow, task categories, quality presets,
friendly model names, Technical Details/Expert Mode, Maximum Resolution
Explorer, planner UI, estimates, timeline, stage progress, comparison,
accept/reject/branch, and large-image viewer (pyramids/crop). Preserve
the dark studio identity and existing working components. Exit: an
ordinary user can complete the main workflow without understanding model
names, while advanced users can still inspect and control technical
settings.

**Phase 4 --- Model expansion.** realesrnet-x4plus first; fidelity
blend; benchmark-driven decision on the Torch worker (x2plus,
general-x4v3); one face model; optional Waifu2x/SwinIR/HAT evaluation.
Exit: multiple real, smoke-tested model choices; router picks only
those.

**Phase 5 --- Restoration and enhancement.** Distinct, labelled,
previewable operations; presets; region masks where feasible. Exit:
restore, enhance, upscale work alone and combined.

**Phase 6 --- Quality and benchmarks.** Metrics, protocol I3 results,
seam/color/halo analysis, regression set, performance report. Exit:
model choices can be evaluated objectively and visually.

**Phase 7 --- Batch/project workflows.** Queue, resume, history, export
management, cleanup/retention. Exit: reliable multi-image workflows.

**Phase 8 --- Hardening and release.** Security (Part L), privacy,
licensing sign-off, long-run stability (soak test of repeated jobs and
restarts), fresh-install verification, documentation (README with exact
Windows commands, USER_GUIDE, ARCHITECTURE, TEST_PLAN). Exit: stable,
documented local-first product.

------------------------------------------------------------------------

# PART N --- DEFINITION OF DONE

1.  A processed 4K version continues to 8K from the UI with no
    download/re-upload; the backend uses the selected internal version;
    output dimensions are exact; the previous version is unchanged.
2.  Every stage has a version record with manifest and hashes; users can
    compare, accept, reject, branch.
3.  OOM, TDR, disk-full and cancellation never corrupt prior versions;
    pause/resume/restart-resume work.
4.  The planner prefers the minimum-pass faithful path, requires
    confirmation for same-model repeats, and never promises unlimited
    upscaling.
5.  Large images use memory-aware tiled/streamed processing; limits are
    enforced and reported.
6.  Multiple real model families run where compatible; availability,
    license class and hardware limits are shown honestly.
7.  Restore, enhance and upscale are independent and composable;
    classical vs neural vs generative are labelled.
8.  Benchmarks follow the protocol; no fake numbers; large-image and
    seam tests pass.
9.  Security and privacy rules hold; tests (old + new) pass; baseline vs
    final test counts reported.
10. Docs are accurate: `V2_AUDIT.md`, `V2_IMPLEMENTATION_STATUS.md`,
    `DECISIONS.md`, `KNOWN_LIMITATIONS.md`, `MODEL_LICENSES.md`,
    `SKILLS.md`, README.
11. The everyday frontend uses understandable task names and presets;
    technical model names and parameters are available only in Technical
    Details/Expert Mode by default; every visible option maps to a real
    tested capability.
12. Maximum Resolution Explorer distinguishes recommended practical
    output from the configured technical maximum and never presents
    estimates as measured facts.

------------------------------------------------------------------------

# PART O --- START PROMPT FOR ANTIGRAVITY (paste after placing this file in the repo root as `FINAL_SPEC.md`)

``` text
Read FINAL_SPEC.md completely. It is the single source of truth. AETHER UPSCALE is ALREADY BUILT: this is an upgrade, not a rebuild. Inspect the real repository and any existing product dossier before editing. Treat every claim about the existing product as unverified until you prove it.

Do in this order, without waiting for approval unless a rule in FINAL_SPEC.md A6 says to stop:
1. Read SKILLS.md (create it per section A4 if missing). Before every step write "Skill check: ...". Prefer skills over manual work.
2. Phase 0 per section M: audit, build the graphify graph on code folders only, run and save baseline tests, verify hardware/Vulkan device/checkpoints/hashes, determine tiling ownership, write docs/V2_AUDIT.md with a claim ledger (Verified/Refuted/Unverifiable + evidence), docs/V2_IMPLEMENTATION_STATUS.md, docs/DECISIONS.md, docs/KNOWN_LIMITATIONS.md, docs/MODEL_LICENSES.md.
3. Then continue through Phases 1 to 8 in order. Query the graphify graph before grepping or changing shared code; rebuild it after each phase.
4. Verify every step with a real run (A5). Re-check the previous phase before starting the next. Never mock inference, progress or metrics. Never use JPEG between stages. Never overwrite originals or accepted versions.
5. First flagship milestone (Phase 2): an existing processed 4K version -> 8K UHD internally with no browser download/re-upload, exact 7680x4320, parent versions unchanged. Do not materialise the 16K intermediate in RAM; follow F4.
6. Frontend requirement (Phase 3): redesign the user-facing controls for ordinary users. Use understandable task names and quality presets, hide raw model names and technical parameters by default, retain them in Technical Details/Expert Mode, and implement the Maximum Resolution Explorer. Follow Part K; do not invent friendly-name mappings without verifying each model's capabilities.
7. At the end of each phase give the report defined in A6, then continue to the next phase. If quota/context runs out, update docs/V2_IMPLEMENTATION_STATUS.md so a fresh session can resume.

Rules that always apply: free/local only; Windows 11 PowerShell; no destructive commands without approval; official sources and license checks (code AND weights) before any model download; one heavy model at a time; select the NVIDIA GPU explicitly; keep the app runnable at every milestone.
```
