import os
import sys
import json
from PIL import Image
from backend.app.core.config import settings
from backend.app.database import get_job, update_job_status
from backend.app.services.job_manager import job_manager
from ai_engine.pipelines.pipeline import pipeline
from ai_engine.processing.tile_engine import JobPausedException

def process_job(job_id: str) -> None:
    job = get_job(job_id)
    if not job:
        print(f"Worker Error: Job {job_id} not found.")
        sys.exit(1)

    input_path = job["input_path"]
    mode = (job.get("mode") or "upscale").lower()
    scale = job.get("scale") or 4
    if mode == "restore":
        if scale > 1:
            mode = "restore_upscale"
        else:
            scale = 1
    crop_region_json = job.get("crop_region")
    output_format = (job.get("output_format") or "png").lower()
    quality = job.get("quality") or 95
    plan_json = job.get("plan_json")

    final_filename = f"{job_id}_x{scale}.{output_format}"
    final_output_path = os.path.join(settings.STORAGE_ROOT, "outputs", final_filename)
    preview_path = os.path.join(settings.STORAGE_ROOT, "previews", f"{job_id}_preview.jpg")
    temp_crop_in = None

    update_job_status(
        job_id,
        status="processing",
        stage="loading",
        progress=0.1,
        message="Initializing enhancement pipeline..."
    )

    try:
        inference_input = input_path

        # Handle fast crop-preview mode if specified
        if crop_region_json:
            try:
                cx, cy, cw, ch = json.loads(crop_region_json)
                with Image.open(input_path) as full_in:
                    img_w, img_h = full_in.size
                    x0 = max(0, min(cx, img_w - 1))
                    y0 = max(0, min(cy, img_h - 1))
                    x1 = max(x0 + 1, min(x0 + cw, img_w))
                    y1 = max(y0 + 1, min(y0 + ch, img_h))

                    cropped_in = full_in.crop((x0, y0, x1, y1))
                    temp_crop_in = os.path.join(settings.STORAGE_ROOT, "temp", f"{job_id}_cropped_input.png")
                    os.makedirs(os.path.dirname(temp_crop_in), exist_ok=True)
                    cropped_in.save(temp_crop_in, format="PNG")
                    inference_input = temp_crop_in
            except Exception as e:
                print(f"Warning: Failed to parse crop region, using full image: {e}")

        def worker_progress_callback(cur_step: int, total_steps: int, msg: str):
            ratio = cur_step / max(1, total_steps)
            mapped_prog = 0.2 + (ratio * 0.65)
            update_job_status(
                job_id,
                status="processing",
                stage="executing",
                progress=round(mapped_prog, 2),
                message=msg
            )

        model_name = job.get("model") or "realesrgan-x4plus"
        preset_name = job.get("preset") or "natural"

        if plan_json:
            plan = json.loads(plan_json)
            if "preset" not in plan or not plan.get("preset"):
                plan["preset"] = preset_name
            if preset_name:
                from backend.app.services.preset_service import preset_service
                p_cfg = preset_service.get_preset(preset_name)
                for k in ["outline_engine", "outline_strength", "clean_paper", "deep_ink", "protect_screentones", "neutralize_chromatic", "manga_clean_ink"]:
                    if k in p_cfg:
                        plan[k] = p_cfg[k]
            for stage in plan.get("stages", []):
                if stage.get("operation") != "classical_resample" and model_name:
                    stage["model_name"] = model_name
            from ai_engine.pipelines.progressive_pipeline import progressive_pipeline
            res = progressive_pipeline.run(
                input_path=inference_input,
                output_path=final_output_path,
                plan=plan,
                job_id=job_id,
                gpu_id=settings.VULKAN_DEVICE_INDEX,
                tile_size=256,
                progress_cb=worker_progress_callback,
                cancel_check=lambda: job_manager.is_cancelled(job_id),
                pause_check=lambda: job_manager.is_paused(job_id),
                format_name=output_format.upper(),
                quality=quality
            )
        else:
            # Extract degradation overrides from plan_json if present
            degrad_overrides = {}
            if plan_json:
                try:
                    p_info = json.loads(plan_json)
                    for k in ["pre_denoise", "post_sharpen", "deblock_jpeg", "denoise_strength", "sharpen_amount"]:
                        if k in p_info:
                            degrad_overrides[k] = p_info[k]
                except Exception:
                    pass

            # Execute standard pipeline
            res = pipeline.run(
                input_path=inference_input,
                output_path=final_output_path,
                mode=mode,
                model_name=model_name,
                scale=scale,
                gpu_id=settings.VULKAN_DEVICE_INDEX,
                tile_size=256,
                progress_cb=worker_progress_callback,
                cancel_check=lambda: job_manager.is_cancelled(job_id),
                format_name=output_format,
                quality=quality,
                preset=preset_name,
                overrides=degrad_overrides
            )

        update_job_status(
            job_id,
            status="processing",
            stage="saving",
            progress=0.9,
            message="Generating lightweight preview..."
        )

        # Generate lightweight preview JPEG
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        with Image.open(final_output_path) as out_img:
            preview_img = out_img.copy()
            preview_img.thumbnail((1280, 1280))
            if preview_img.mode in ("RGBA", "P"):
                # Fill white background for preview JPEG
                bg = Image.new("RGB", preview_img.size, (255, 255, 255))
                if preview_img.mode == "RGBA":
                    bg.paste(preview_img, mask=preview_img.split()[3])
                else:
                    bg.paste(preview_img)
                preview_img = bg
            preview_img.save(preview_path, format="JPEG", quality=85)

        if temp_crop_in and os.path.exists(temp_crop_in):
            try:
                os.remove(temp_crop_in)
            except Exception:
                pass

        runtime = res.get("runtime_s") or res.get("elapsed_seconds") or 0.0
        completion_msg = f"Completed in {runtime}s"
        if res.get("consistency"):
            completion_msg += f" (PSNR: {res['consistency']['psnr_db']} dB)"

        # Register output in Version Graph
        try:
            from backend.app.services.version_service import version_service
            if plan_json:
                p_dict = json.loads(plan_json)
                proj_id = p_dict.get("project_id", f"proj_{job['image_id']}")
                parent_ver_id = p_dict.get("source_version_id", f"v_orig_{job['image_id']}")
            else:
                proj_id = f"proj_{job['image_id']}"
                parent_ver_id = f"v_orig_{job['image_id']}"

            params = {
                "preset": preset_name,
                "output_format": output_format,
                "quality": quality,
                "device": settings.VULKAN_DEVICE_NAME,
                "tile_size": 256,
                "overlap": 32,
                "stages": res.get("stages_executed", [mode])
            }

            version_service.register_derived_version(
                project_id=proj_id,
                parent_version_id=parent_ver_id,
                output_image_path=final_output_path,
                operation=mode,
                mode=mode,
                model_id=model_name,
                scale=scale,
                runtime_s=runtime,
                parameters=params,
                quality_eval=res.get("consistency")
            )
        except Exception as ve:
            print(f"Warning: Failed to register version in graph: {ve}")

        update_job_status(
            job_id,
            status="completed",
            stage="done",
            progress=1.0,
            output_path=final_output_path,
            message=completion_msg
        )
        print(f"Worker SUCCESS: Job {job_id} complete. Output: {final_output_path}")

    except JobPausedException:
        print(f"Worker PAUSED: Job {job_id} paused cleanly at checkpoint.")
        update_job_status(
            job_id,
            status="paused",
            stage="paused",
            message="Job paused at tile checkpoint"
        )
        sys.exit(0)

    except Exception as e:
        error_msg = str(e)
        print(f"Worker FAILED: {error_msg}")
        update_job_status(
            job_id,
            status="failed",
            stage="failed",
            progress=0.0,
            error=error_msg,
            message="Processing failed"
        )
        for p in (final_output_path, temp_crop_in):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.app.workers.job_worker <job_id>")
        sys.exit(1)
    process_job(sys.argv[1])
