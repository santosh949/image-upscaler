import os
import time
import shutil
import tempfile
from typing import Dict, Any, Optional, Callable, List
from PIL import Image

from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.processing.tile_engine import TileEngine
from ai_engine.processing.alpha_handler import AlphaHandler
from ai_engine.processing.restoration import RestorationEngine
from ai_engine.processing.consistency import ConsistencyChecker
from ai_engine.processing.metadata_embedder import MetadataEmbedder
from ai_engine.registry.model_registry import model_registry

class EnhancementPipeline:
    """
    Unified multi-stage enhancement pipeline supporting:
    - 'restore': Low-resolution classical & adaptive restoration at 1x
    - 'upscale': Direct neural super-resolution with tile management
    - 'restore_upscale': Multi-stage pipeline (restoration pre-pass -> neural SR -> post-processing)
    Handles transparent PNG alpha bleeding, downscale consistency checking, and provenance embedding.
    """

    def __init__(self):
        self.adapter = NCNNRealESRGANAdapter()
        self.tile_engine = TileEngine(default_tile_size=256, overlap=32, max_output_mp=100)

    def run(
        self,
        input_path: str,
        output_path: str,
        mode: str = "upscale",
        model_name: str = "realesrgan-x4plus",
        scale: int = 4,
        gpu_id: int = 0,
        tile_size: int = 256,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        format_name: str = "PNG",
        quality: int = 95,
        preset: Optional[str] = "natural"
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        from backend.app.services.preset_service import preset_service
        preset_cfg = preset_service.resolve(preset)
        pre_denoise = preset_cfg.get("pre_denoise", "none")
        post_sharpen = preset_cfg.get("post_sharpen", "off")
        blend_weight = float(preset_cfg.get("texture_blend_weight", 0.0))

        raw_img = Image.open(input_path)
        in_w, in_h = raw_img.size
        target_w = in_w * scale
        target_h = in_h * scale
        stages_executed: List[str] = []

        # Step 1: Alpha inspection and bleeding
        rgb_img, alpha_channel, has_alpha = AlphaHandler.prepare_rgb_and_alpha(raw_img)
        if has_alpha:
            stages_executed.append("alpha-bleed-separation")

        if cancel_check and cancel_check():
            raise RuntimeError("Job cancelled by user")

        # Step 2: Branch based on mode
        final_rgb: Image.Image
        actual_scale = scale

        if mode == "restore" and scale > 1:
            mode = "restore_upscale"

        if mode == "restore":
            actual_scale = 1
            if progress_cb:
                progress_cb(1, 2, "Running artifact suppression & restoration")
            stages_executed.append("classical-restoration-prepass")
            final_rgb = RestorationEngine.restore(
                rgb_img,
                noise_score=6.0,
                has_jpeg_artifacts=True,
                apply_sharpen=True
            )
            if progress_cb:
                progress_cb(2, 2, "Restoration complete")

        elif mode in ("upscale", "restore_upscale", "restore+upscale"):
            is_restore_mode = mode in ("restore_upscale", "restore+upscale")
            # Pre-pass denoise if mode is restore_upscale or configured by preset (e.g. smooth_clean)
            if is_restore_mode or pre_denoise == "medium":
                if progress_cb:
                    progress_cb(1, 4, "Stage 1: Artifact & noise suppression")
                cleaned_rgb = RestorationEngine.restore(
                    rgb_img,
                    noise_score=5.0,
                    has_jpeg_artifacts=True,
                    apply_sharpen=False
                )
                stages_executed.append("classical-restoration-prepass")
            elif pre_denoise == "low":
                if progress_cb:
                    progress_cb(1, 4, "Stage 1: Mild deblocking prepass")
                cleaned_rgb = RestorationEngine.restore(
                    rgb_img,
                    noise_score=2.0,
                    has_jpeg_artifacts=True,
                    apply_sharpen=False
                )
                stages_executed.append("mild-deblock-prepass")
            else:
                # Default for human photos: App-level pre-denoising DISABLED to preserve natural grain
                cleaned_rgb = rgb_img

            if cancel_check and cancel_check():
                raise RuntimeError("Job cancelled by user")

            stages_executed.append("neural-sr-upscale")
            if progress_cb:
                progress_cb(2, 4, f"Neural super-resolution ({model_name})")

            def ncnn_infer_tile(tile: Image.Image) -> Image.Image:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t_in, \
                     tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t_out:
                    temp_in_path = t_in.name
                    temp_out_path = t_out.name
                try:
                    tile.save(temp_in_path, format="PNG")
                    self.adapter.enhance(
                        input_path=temp_in_path,
                        output_path=temp_out_path,
                        scale=actual_scale,
                        tile_size=tile_size,
                        gpu_id=gpu_id,
                        model_name=model_name
                    )
                    return Image.open(temp_out_path).copy()
                finally:
                    if os.path.exists(temp_in_path):
                        os.remove(temp_in_path)
                    if os.path.exists(temp_out_path):
                        os.remove(temp_out_path)

            def ncnn_batch_infer_tiles(tile_list: List[Image.Image]) -> List[Image.Image]:
                if not tile_list:
                    return []
                temp_ins = []
                temp_outs = []
                temp_dir = tempfile.mkdtemp(prefix="pipeline_batch_")
                try:
                    for i, t in enumerate(tile_list):
                        p_in = os.path.join(temp_dir, f"in_{i:05d}.png")
                        p_out = os.path.join(temp_dir, f"out_{i:05d}.png")
                        t.save(p_in, format="PNG")
                        temp_ins.append(p_in)
                        temp_outs.append(p_out)

                    self.adapter.enhance_batch(
                        input_paths=temp_ins,
                        output_paths=temp_outs,
                        scale=actual_scale,
                        tile_size=tile_size,
                        gpu_id=gpu_id,
                        model_name=model_name
                    )

                    results = []
                    for p_out in temp_outs:
                        with Image.open(p_out) as im:
                            results.append(im.copy())
                    return results
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

            upscaled = self.tile_engine.process(
                img=cleaned_rgb,
                infer_fn=ncnn_infer_tile,
                batch_infer_fn=ncnn_batch_infer_tiles,
                scale=actual_scale,
                tile_size=tile_size,
                overlap=32,
                cancel_check=cancel_check
            )

            # Post-sharpen if in restore_upscale mode or configured by preset (e.g. more_detail)
            if is_restore_mode or post_sharpen == "low":
                if progress_cb:
                    progress_cb(3, 4, "Post-sharpening refinement")
                final_rgb = RestorationEngine.restore(
                    upscaled,
                    noise_score=1.0,
                    has_jpeg_artifacts=False,
                    apply_sharpen=True
                )
                stages_executed.append("conservative-post-polish")
            else:
                final_rgb = upscaled

            # Traditional low-weight Lanczos pixel blend (restores source grain without hallucination)
            if not is_restore_mode and blend_weight > 0.0:
                lanczos_ref = rgb_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                final_rgb = Image.blend(final_rgb, lanczos_ref, blend_weight)
                stages_executed.append(f"traditional-texture-blend-{int(blend_weight*100)}pct")

            # Manga & Inking line/paper refinement
            if preset_cfg.get("manga_clean_ink", False):
                from ai_engine.processing.manga_enhancer import MangaEnhancer
                final_rgb = MangaEnhancer.enhance_manga_lines(final_rgb, clean_paper=True, deep_black=True)
                stages_executed.append("manga-ink-and-paper-refinement")

            # 4-Pillar Manga/Anime Outline Master Engine
            if preset_cfg.get("outline_engine", False):
                from ai_engine.processing.manga_outline_engine import MangaOutlineEngine
                final_rgb = MangaOutlineEngine.process(
                    final_rgb,
                    strength=float(preset_cfg.get("outline_strength", 1.0)),
                    clean_paper=bool(preset_cfg.get("clean_paper", True)),
                    deep_ink=bool(preset_cfg.get("deep_ink", True)),
                    protect_screentones=bool(preset_cfg.get("protect_screentones", True)),
                    neutralize_chromatic=bool(preset_cfg.get("neutralize_chromatic", True))
                )
                stages_executed.append("manga-outline-master-engine")

        else:
            raise ValueError(f"Unknown pipeline mode: {mode}")

        target_w = in_w * actual_scale
        target_h = in_h * actual_scale

        # Step 3: Recombine alpha if present
        if has_alpha and alpha_channel is not None:
            final_output = AlphaHandler.recombine(
                rgb_img=final_rgb,
                alpha_img=alpha_channel,
                target_size=(target_w, target_h)
            )
            stages_executed.append("alpha-lanczos-recombine")
        else:
            final_output = final_rgb.convert("RGB")

        # Step 4: Consistency check
        consistency_report = None
        if actual_scale > 1:
            consistency_report = ConsistencyChecker.evaluate(raw_img, final_output)
            stages_executed.append("downscale-consistency-audit")

        # Step 5: Embed metadata and save
        stages_executed.append("provenance-metadata-embed")
        meta = MetadataEmbedder.build_provenance_dict(
            mode=mode,
            model_name=model_name if mode != "restore" else "classical-restoration",
            scale=actual_scale,
            stages=stages_executed,
            consistency=consistency_report
        )

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        MetadataEmbedder.save_with_metadata(
            img=final_output,
            output_path=output_path,
            format_name=format_name,
            metadata=meta,
            quality=quality
        )

        elapsed = time.perf_counter() - start_time
        out_w, out_h = final_output.size

        return {
            "mode": mode,
            "model": model_name,
            "scale": actual_scale,
            "stages": stages_executed,
            "stages_executed": stages_executed,
            "input_dimensions": [in_w, in_h],
            "output_dimensions": [out_w, out_h],
            "elapsed_seconds": round(elapsed, 3),
            "output_bytes": os.path.getsize(output_path),
            "consistency": consistency_report,
            "has_alpha": has_alpha
        }

pipeline = EnhancementPipeline()

