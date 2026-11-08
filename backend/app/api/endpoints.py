import os
import uuid
import asyncio
import json
import io
import zipfile
import tempfile
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse, Response
from PIL import Image

from backend.app.core.config import settings
from backend.app.database import (
    create_image_record, get_image_record,
    create_job, get_job, update_job_status,
    get_all_jobs, delete_job,
    get_queued_jobs, clear_queued_jobs
)
from backend.app.schemas.job import (
    JobCreateRequest, JobResponse, ImageUploadResponse,
    BatchJobCreateRequest, BatchZipRequest, QueueStatusResponse
)
from backend.app.services.job_manager import job_manager
from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
from ai_engine.registry.model_registry import model_registry
from ai_engine.analysis.analyzer import analyzer
from ai_engine.routing.router import router as model_router
from backend.app.services.preset_service import preset_service

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/bmp", "image/tiff"}
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB safety cap

def validate_uuid(val: str) -> str:
    """Strictly validates UUID structure to prevent path traversal and injection attacks."""
    try:
        val_clean = val.strip()
        parsed = uuid.UUID(val_clean)
        return str(parsed)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid resource identifier format.")

@router.get("/health")
def health_check():
    return {"status": "ok", "version": settings.VERSION}

@router.get("/presets")
def list_presets():
    return {"presets": preset_service.list_presets()}

@router.get("/system/capabilities")
def get_capabilities():
    import platform
    import psutil

    total_ram_mb = int(psutil.virtual_memory().total // (1024 * 1024))
    from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter
    temp_adapter = NCNNRealESRGANAdapter()
    devs = temp_adapter.get_vulkan_devices()
    vulkan_name = devs.get(settings.VULKAN_DEVICE_INDEX) or (list(devs.values())[0] if devs else "Vulkan Device")

    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor() or platform.machine(),
        "total_ram_mb": total_ram_mb,
        "gpu": vulkan_name,
        "vulkan_device_index": settings.VULKAN_DEVICE_INDEX,
        "vulkan_device_name": vulkan_name,
        "active_backend": "ncnn-vulkan",
        "max_output_megapixels": settings.MAX_OUTPUT_MEGAPIXELS
    }

@router.get("/models")
def list_models():
    models_data = model_registry.list_models()
    return {
        "models": [
            {
                "id": m["id"],
                "name": m["name"],
                "scale": m["scale"],
                "tier": m.get("tier", 1),
                "code_license": m["code_license"],
                "weight_license": m["weight_license"],
                "license_class": m["license_class"],
                "status": m["license_status"],
                "available": m["weights_available"],
                "smoke_tested": m["smoke_tested"],
                "unsupported_reason": m.get("unsupported_reason")
            }
            for m in models_data
        ]
    }

@router.post("/images/{image_id}/analyze")
def analyze_image_endpoint(image_id: str, mode: str = "upscale", scale: int = 4, requested_model: Optional[str] = None):
    img_record = get_image_record(image_id)
    if not img_record:
        raise HTTPException(status_code=404, detail="Image record not found.")

    storage_path = img_record["storage_path"]
    if not os.path.isfile(storage_path):
        raise HTTPException(status_code=404, detail="Image file missing from storage.")

    analysis = analyzer.analyze(storage_path)
    route_decision = model_router.route(
        analysis=analysis,
        user_mode=mode,
        user_scale=scale,
        requested_model=requested_model
    )

    return {
        "analysis": analysis,
        "recommendation": route_decision
    }

@router.post("/images", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    img_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
        ext = ".png"

    save_filename = f"{img_id}{ext}"
    dest_path = os.path.join(settings.STORAGE_ROOT, "uploads", save_filename)

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds maximum allowed size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
        )

    with open(dest_path, "wb") as f:
        f.write(contents)

    # Validate image via Pillow
    try:
        with Image.open(dest_path) as img:
            w, h = img.size
            fmt = img.format or "UNKNOWN"
            if w * h > settings.MAX_OUTPUT_MEGAPIXELS * 1_000_000:
                raise ValueError("Image dimensions exceed safety cap.")
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    create_image_record(
        img_id=img_id,
        filename=file.filename or save_filename,
        path=dest_path,
        w=w,
        h=h,
        fmt=fmt,
        size=len(contents)
    )

    return ImageUploadResponse(
        image_id=img_id,
        filename=file.filename or save_filename,
        width=w,
        height=h,
        format=fmt,
        size_bytes=len(contents)
    )

@router.post("/images/batch", response_model=List[ImageUploadResponse])
async def upload_images_batch(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        img_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
            ext = ".png"

        save_filename = f"{img_id}{ext}"
        dest_path = os.path.join(settings.STORAGE_ROOT, "uploads", save_filename)
        contents = await file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)

        try:
            with Image.open(dest_path) as img:
                w, h = img.size
                fmt = img.format or "UNKNOWN"
                if w * h > settings.MAX_OUTPUT_MEGAPIXELS * 1_000_000:
                    raise ValueError("Dimensions exceed safety cap.")
        except Exception as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            continue

        create_image_record(
            img_id=img_id,
            filename=file.filename or save_filename,
            path=dest_path,
            w=w,
            h=h,
            fmt=fmt,
            size=len(contents)
        )
        results.append(ImageUploadResponse(
            image_id=img_id,
            filename=file.filename or save_filename,
            width=w,
            height=h,
            format=fmt,
            size_bytes=len(contents)
        ))
    return results

@router.get("/jobs", response_model=List[JobResponse])
def list_recent_jobs(limit: int = Query(default=30, ge=1, le=100)):
    raw_jobs = get_all_jobs(limit=limit)
    res = []
    for j in raw_jobs:
        res.append(JobResponse(
            job_id=j["id"],
            status=j["status"],
            stage=j["stage"],
            progress=j["progress"],
            message=j["message"],
            result_available=j["status"] == "completed" and bool(j["output_path"]),
            error=j["error"],
            scale=j["scale"],
            mode=j["mode"],
            output_format=j.get("output_format") or "png",
            created_at=j["created_at"]
        ))
    return res

@router.post("/jobs", response_model=JobResponse)
def create_upscale_job(req: JobCreateRequest, background_tasks: BackgroundTasks):
    image_record = get_image_record(req.image_id)
    if not image_record:
        raise HTTPException(status_code=404, detail="Image record not found.")

    # Calculate expected output pixels and enforce pixel cap
    base_w = req.crop_region[2] if req.crop_region else image_record["width"]
    base_h = req.crop_region[3] if req.crop_region else image_record["height"]
    expected_w = base_w * req.scale
    expected_h = base_h * req.scale
    expected_mp = (expected_w * expected_h) / 1_000_000.0

    if expected_mp > settings.MAX_OUTPUT_MEGAPIXELS:
        raise HTTPException(
            status_code=400,
            detail=f"Output dimensions ({expected_w}x{expected_h} = {expected_mp:.1f} MP) exceed the {settings.MAX_OUTPUT_MEGAPIXELS} MP limit."
        )

    # Enforce real free-disk check (needed x1.25) and available-RAM preflight
    import shutil
    import psutil
    est_disk_bytes = int(((expected_w * expected_h * 3 * 2.5) / (1024 * 1024)) * 1.25 * 1024 * 1024)
    disk_usage = shutil.disk_usage(settings.STORAGE_ROOT)
    if disk_usage.free < est_disk_bytes:
        raise HTTPException(
            status_code=507,
            detail=f"Insufficient disk space: {disk_usage.free / (1024**2):.1f} MB available, requires {est_disk_bytes / (1024**2):.1f} MB (including 25% safety margin)."
        )

    ram = psutil.virtual_memory()
    if ram.available < 350 * 1024 * 1024:
        raise HTTPException(
            status_code=503,
            detail=f"Insufficient available RAM: {ram.available / (1024**2):.1f} MB available. System requires at least 350 MB available physical RAM."
        )

    job_id = str(uuid.uuid4())
    crop_json = json.dumps(req.crop_region) if req.crop_region else None

    create_job(
        job_id=job_id,
        image_id=req.image_id,
        input_path=image_record["storage_path"],
        mode=req.mode,
        scale=req.scale,
        model=req.model,
        crop_region=crop_json,
        output_format=req.output_format,
        quality=req.quality,
        plan_json=req.plan_json,
        preset=req.preset
    )

    # Spawn worker subprocess in background
    background_tasks.add_task(job_manager.spawn_worker, job_id)

    return JobResponse(
        job_id=job_id,
        status="queued",
        stage="waiting",
        progress=0.0,
        message="Job queued for processing",
        result_available=False,
        scale=req.scale,
        mode=req.mode,
        output_format=req.output_format
    )

@router.post("/jobs/batch", response_model=List[JobResponse])
def create_upscale_jobs_batch(req: BatchJobCreateRequest, background_tasks: BackgroundTasks):
    responses = []
    first_job_id = None
    for item in req.jobs:
        image_record = get_image_record(item.image_id)
        if not image_record:
            continue

        base_w = image_record["width"]
        base_h = image_record["height"]
        expected_w = base_w * item.scale
        expected_h = base_h * item.scale
        expected_mp = (expected_w * expected_h) / 1_000_000.0
        if expected_mp > settings.MAX_OUTPUT_MEGAPIXELS:
            continue

        job_id = str(uuid.uuid4())
        if not first_job_id:
            first_job_id = job_id

        create_job(
            job_id=job_id,
            image_id=item.image_id,
            input_path=image_record["storage_path"],
            mode=item.mode,
            scale=item.scale,
            model=item.model,
            crop_region=None,
            output_format=item.output_format,
            quality=item.quality,
            plan_json=None,
            preset=item.preset
        )
        responses.append(JobResponse(
            job_id=job_id,
            status="queued",
            stage="waiting",
            progress=0.0,
            message="Batch job queued",
            result_available=False,
            scale=item.scale,
            mode=item.mode,
            output_format=item.output_format
        ))

    if first_job_id:
        background_tasks.add_task(job_manager.spawn_worker, first_job_id)

    return responses

@router.get("/jobs/queue", response_model=QueueStatusResponse)
def get_current_queue():
    return job_manager.get_queue_status()

@router.post("/jobs/queue/clear")
def clear_all_queued_jobs():
    cancelled_count = clear_queued_jobs()
    return {"status": "ok", "cancelled_count": cancelled_count}

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return JobResponse(
        job_id=job["id"],
        status=job["status"],
        stage=job["stage"],
        progress=job["progress"],
        message=job["message"],
        result_available=job["status"] == "completed" and bool(job["output_path"]),
        error=job["error"],
        scale=job["scale"],
        mode=job["mode"],
        output_format=job.get("output_format") or "png",
        created_at=job["created_at"]
    )

@router.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def event_generator():
        while True:
            current_job = get_job(job_id)
            if not current_job:
                break

            data = {
                "job_id": current_job["id"],
                "status": current_job["status"],
                "stage": current_job["stage"],
                "progress": current_job["progress"],
                "message": current_job["message"],
                "result_available": current_job["status"] == "completed" and bool(current_job["output_path"])
            }
            yield f"data: {json.dumps(data)}\n\n"

            if current_job["status"] in ("completed", "failed", "cancelled"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/jobs/{job_id}/cancel")
def cancel_job_endpoint(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    success = job_manager.cancel_job(job_id)
    return {"job_id": job_id, "cancelled": success, "status": "cancelled"}

@router.delete("/jobs/{job_id}")
def delete_job_endpoint(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Stop worker if running
    job_manager.cancel_job(job_id)

    # Delete output and preview files
    if job.get("output_path") and os.path.isfile(job["output_path"]):
        try:
            os.remove(job["output_path"])
        except Exception:
            pass

    preview_path = os.path.join(settings.STORAGE_ROOT, "previews", f"{job_id}_preview.jpg")
    if os.path.isfile(preview_path):
        try:
            os.remove(preview_path)
        except Exception:
            pass

    deleted = delete_job(job_id)
    return {"job_id": job_id, "deleted": deleted}

@router.get("/jobs/{job_id}/preview")
def get_job_preview(job_id: str):
    valid_id = validate_uuid(job_id)
    job = get_job(valid_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    previews_dir = os.path.abspath(os.path.join(settings.STORAGE_ROOT, "previews"))
    preview_path = os.path.abspath(os.path.join(previews_dir, f"{valid_id}_preview.jpg"))
    if not preview_path.startswith(previews_dir) or not os.path.isfile(preview_path):
        raise HTTPException(status_code=404, detail="Preview not available yet.")
    return FileResponse(preview_path, media_type="image/jpeg")

@router.get("/jobs/{job_id}/crop")
def get_job_crop(
    job_id: str,
    x: int = Query(default=0, ge=0),
    y: int = Query(default=0, ge=0),
    width: int = Query(default=256, ge=16, le=2048),
    height: int = Query(default=256, ge=16, le=2048)
):
    """100% full-resolution cropped inspection endpoint without browser memory overflow."""
    valid_id = validate_uuid(job_id)
    job = get_job(valid_id)
    if not job or job["status"] != "completed" or not job["output_path"]:
        raise HTTPException(status_code=404, detail="Output result not available.")

    output_path = os.path.abspath(job["output_path"])
    storage_root = os.path.abspath(settings.STORAGE_ROOT)
    if not output_path.startswith(storage_root) or not os.path.isfile(output_path):
        raise HTTPException(status_code=404, detail="Result file missing from storage.")

    try:
        with Image.open(output_path) as full_img:
            img_w, img_h = full_img.size
            x0 = max(0, min(x, img_w - 1))
            y0 = max(0, min(y, img_h - 1))
            x1 = max(x0 + 1, min(x0 + width, img_w))
            y1 = max(y0 + 1, min(y0 + height, img_h))

            cropped = full_img.crop((x0, y0, x1, y1))
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            buf.seek(0)
            return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate crop: {str(e)}")

@router.get("/jobs/{job_id}/download")
def download_job_result(
    job_id: str,
    format: Optional[str] = Query(default=None),
    quality: Optional[int] = Query(default=95, ge=1, le=100)
):
    valid_id = validate_uuid(job_id)
    job = get_job(valid_id)
    if not job or job["status"] != "completed" or not job["output_path"]:
        raise HTTPException(status_code=404, detail="Output result not available.")

    output_path = os.path.abspath(job["output_path"])
    storage_root = os.path.abspath(settings.STORAGE_ROOT)
    if not output_path.startswith(storage_root) or not os.path.isfile(output_path):
        raise HTTPException(status_code=404, detail="Result file missing from storage.")

    # If no format conversion requested, serve file directly
    req_format = (format or "").lower()
    current_ext = os.path.splitext(output_path)[1].replace(".", "").lower()

    if not req_format or req_format == current_ext:
        mime = "image/png" if current_ext == "png" else ("image/webp" if current_ext == "webp" else "image/jpeg")
        return FileResponse(
            output_path,
            media_type=mime,
            filename=f"image_upscale_{valid_id}.{current_ext}"
        )

    # Perform on-the-fly format conversion
    try:
        with Image.open(output_path) as img:
            buf = io.BytesIO()
            if req_format in ("jpg", "jpeg"):
                converted = img.convert("RGB") if img.mode in ("RGBA", "P") else img
                converted.save(buf, format="JPEG", quality=quality)
                mime = "image/jpeg"
                ext = "jpg"
            elif req_format == "webp":
                img.save(buf, format="WEBP", quality=quality)
                mime = "image/webp"
                ext = "webp"
            else:
                img.save(buf, format="PNG")
                mime = "image/png"
                ext = "png"

            buf.seek(0)
            return Response(
                content=buf.getvalue(),
                media_type=mime,
                headers={"Content-Disposition": f'attachment; filename="image_upscale_{valid_id}.{ext}"'}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Format conversion failed: {str(e)}")

@router.post("/jobs/batch/download-zip")
def download_batch_zip(req: BatchZipRequest, background_tasks: BackgroundTasks):
    if not req.job_ids:
        raise HTTPException(status_code=400, detail="No job IDs specified.")

    # Write ZIP to temporary disk file to prevent RAM exhaustion on large batches
    temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    temp_zip_path = temp_zip.name
    temp_zip.close()

    added_count = 0
    try:
        with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for jid in req.job_ids:
                try:
                    valid_jid = validate_uuid(jid)
                except HTTPException:
                    continue
                job = get_job(valid_jid)
                if not job or job.get("status") != "completed" or not job.get("output_path"):
                    continue
                out_path = os.path.abspath(job["output_path"])
                storage_root = os.path.abspath(settings.STORAGE_ROOT)
                temp_root = os.path.abspath(tempfile.gettempdir())
                if not (out_path.startswith(storage_root) or out_path.startswith(temp_root)) or not os.path.isfile(out_path):
                    continue

                filename = os.path.basename(out_path)
                zf.write(out_path, arcname=filename)
                added_count += 1

                manifest_path = f"{out_path}.manifest.json"
                if os.path.isfile(manifest_path):
                    zf.write(manifest_path, arcname=f"{filename}.manifest.json")

        if added_count == 0:
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
            raise HTTPException(status_code=404, detail="No completed image files found to package.")

        def cleanup_temp_zip():
            if os.path.exists(temp_zip_path):
                try:
                    os.remove(temp_zip_path)
                except Exception:
                    pass

        background_tasks.add_task(cleanup_temp_zip)
        return FileResponse(
            temp_zip_path,
            media_type="application/zip",
            filename="upscale_batch_export.zip"
        )
    except Exception as e:
        if os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except Exception:
                pass
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to generate batch zip: {str(e)}")
