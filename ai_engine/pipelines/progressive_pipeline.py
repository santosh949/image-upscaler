import os
import time
import shutil
import tempfile
from typing import Dict, Any, Optional, Callable, List
from PIL import Image

from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.processing.tile_engine import TileEngine, JobPausedException
from ai_engine.processing.tile_store import tile_store, TileStore
from ai_engine.processing.alpha_handler import AlphaHandler
from ai_engine.processing.restoration import RestorationEngine
from ai_engine.processing.consistency import ConsistencyChecker
from ai_engine.processing.metadata_embedder import MetadataEmbedder

class ProgressivePipeline:
    """
    Progressive Resolution Pipeline:
    - Multi-stage execution using ResolutionPlanner plans.
    - Flagship feature: 4K -> 8K via Per-Tile Scale Adaptation with cosine-feathered blending.
    - Tile-level persistence and checkpointing via TileStore.
    - Zero intermediate 16K buffer materialized in physical memory.
    """

    def __init__(self):
        self.adapter = NCNNRealESRGANAdapter()
        self.tile_engine = TileEngine(default_tile_size=256, overlap=32, max_output_mp=100)
        self.tile_store = tile_store

    def run(
        self,
        input_path: str,
        output_path: str,
        plan: Dict[str, Any],
        job_id: str,
        gpu_id: int = 0,
        tile_size: int = 256,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        pause_check: Optional[Callable[[], bool]] = None,
        format_name: str = "PNG",
        quality: int = 95
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        raw_img = Image.open(input_path)
        current_img, alpha_channel, has_alpha = AlphaHandler.prepare_rgb_and_alpha(raw_img)

        stages = plan.get("stages", [])
        if not stages:
            raise ValueError("Plan contains no execution stages")

        total_stages = len(stages)
        stages_executed = []

        for s_idx, stage in enumerate(stages):
            if cancel_check and cancel_check():
                raise RuntimeError("Job cancelled by user")
            if pause_check and pause_check():
                raise JobPausedException("Job paused by user")

            stage_num = stage.get("stage_index", s_idx + 1)
            stage_id = f"{job_id}_stage_{stage_num}"
            op = stage.get("operation", "upscale")
            model_name = stage.get("model_name", "realesrgan-x4plus")
            from_res = stage.get("from_res", (current_img.width, current_img.height))
            to_res = stage.get("to_res", (current_img.width, current_img.height))
            model_scale = stage.get("model_scale", 4)
            target_scale = stage.get("target_scale", float(to_res[0]) / float(from_res[0]))

            if op == "classical_resample" or model_name == "lanczos":
                if progress_cb:
                    progress_cb(1, 1, f"Stage {stage_num}/{total_stages}: Traditional Lanczos resample to {to_res[0]}x{to_res[1]}")
                current_img = current_img.resize((to_res[0], to_res[1]), Image.Resampling.LANCZOS)
                stages_executed.append(stage_id)
                continue

            tile_grid = self.tile_engine.generate_tile_grid(current_img.width, current_img.height, tile_size, overlap=32)
            self.tile_store.init_stage(
                stage_id=stage_id,
                job_id=job_id,
                stage_index=stage_num,
                operation=op,
                model=model_name,
                from_size=from_res,
                to_size=to_res,
                tile_grid=tile_grid
            )

            msg_prefix = f"Stage {stage_num}/{total_stages} ({model_name})"
            if progress_cb:
                progress_cb(0, len(tile_grid), f"{msg_prefix}: Starting inference")

            # Determine optimal NCNN scale (native 2x supported directly)
            ncnn_scale = 2 if target_scale == 2.0 else model_scale

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
                        scale=ncnn_scale,
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
                temp_dir = tempfile.mkdtemp(prefix="prog_batch_")
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
                        scale=ncnn_scale,
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

            try:
                stage_out = self.tile_engine.process(
                    img=current_img,
                    infer_fn=ncnn_infer_tile,
                    batch_infer_fn=ncnn_batch_infer_tiles,
                    scale=ncnn_scale,
                    target_scale=target_scale,
                    tile_size=tile_size,
                    overlap=32,
                    progress_cb=lambda done, tot: progress_cb(done, tot, f"{msg_prefix}: tile {done}/{tot}") if progress_cb else None,
                    cancel_check=cancel_check,
                    pause_check=pause_check,
                    tile_store=self.tile_store,
                    stage_id=stage_id
                )
                self.tile_store.update_stage_status(stage_id, "completed")
                self.tile_store.cleanup_stage(stage_id)
                current_img = stage_out
                stages_executed.append(stage_id)

            except JobPausedException:
                self.tile_store.update_stage_status(stage_id, "paused")
                raise
            except Exception as e:
                self.tile_store.update_stage_status(stage_id, "failed")
                raise e

        # Re-composite alpha channel if present
        if has_alpha:
            current_img = AlphaHandler.restore_alpha(
                rgb_img=current_img,
                alpha_channel=alpha_channel,
                target_w=plan["target_width"],
                target_h=plan["target_height"]
            )

        # Verify target dimensions
        if current_img.size != (plan["target_width"], plan["target_height"]):
            current_img = current_img.resize((plan["target_width"], plan["target_height"]), Image.Resampling.LANCZOS)

        # Traditional low-weight Lanczos texture blend per V3 Addendum §5
        blend_weight = float(plan.get("texture_blend_weight", 0.0))
        if blend_weight > 0.0 and plan.get("plan_type") not in ("plan_c", "C"):
            lanczos_ref = raw_img.convert("RGB").resize((plan["target_width"], plan["target_height"]), Image.Resampling.LANCZOS)
            if has_alpha:
                rgb_blended = Image.blend(current_img.convert("RGB"), lanczos_ref, blend_weight)
                current_img = AlphaHandler.restore_alpha(rgb_blended, alpha_channel, plan["target_width"], plan["target_height"])
            else:
                current_img = Image.blend(current_img.convert("RGB"), lanczos_ref, blend_weight)
            stages_executed.append(f"traditional-texture-blend-{int(blend_weight*100)}pct")

        # Manga line & paper refinement if configured by preset
        if plan.get("manga_clean_ink", False):
            from ai_engine.processing.manga_enhancer import MangaEnhancer
            current_img = MangaEnhancer.enhance_manga_lines(current_img, clean_paper=True, deep_black=True)
            stages_executed.append("manga-ink-and-paper-refinement")

        # 4-Pillar Manga/Anime Outline Master Engine
        if plan.get("outline_engine", False):
            from ai_engine.processing.manga_outline_engine import MangaOutlineEngine
            current_img = MangaOutlineEngine.process(
                current_img,
                strength=float(plan.get("outline_strength", 1.0)),
                clean_paper=bool(plan.get("clean_paper", True)),
                deep_ink=bool(plan.get("deep_ink", True)),
                protect_screentones=bool(plan.get("protect_screentones", True)),
                neutralize_chromatic=bool(plan.get("neutralize_chromatic", True))
            )
            stages_executed.append("manga-outline-master-engine")

        # Embed metadata provenance and save atomically with sidecar manifest
        runtime = time.perf_counter() - start_time
        meta_dict = {
            "application": "AETHER UPSCALE 2.0",
            "pipeline": "progressive",
            "plan_type": plan.get("plan_type", "plan_b"),
            "target_resolution": f"{plan['target_width']}x{plan['target_height']}",
            "stages_executed": str(len(stages_executed)),
            "runtime_s": str(round(runtime, 2))
        }
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        MetadataEmbedder.save_with_metadata(
            img=current_img,
            output_path=output_path,
            format_name=format_name,
            metadata=meta_dict,
            quality=quality
        )

        return {
            "status": "completed",
            "output_path": output_path,
            "width": plan["target_width"],
            "height": plan["target_height"],
            "megapixels": round((plan["target_width"] * plan["target_height"]) / 1_000_000.0, 2),
            "runtime_s": round(runtime, 2),
            "stages": stages_executed,
            "stages_executed": stages_executed,
            "stages_count": len(stages_executed)
        }

progressive_pipeline = ProgressivePipeline()

