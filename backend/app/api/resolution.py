import os
import uuid
import json
import shutil
import psutil
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.database import get_version, get_versions_by_project, create_job, get_job
from backend.app.services.resolution_planner import resolution_planner
from backend.app.services.job_manager import job_manager

router = APIRouter(tags=["resolution"])

def check_system_resources(target_w: int, target_h: int):
    # Free disk preflight (required * 1.25 safety margin)
    est_disk_bytes = int(((target_w * target_h * 3 * 2.5) / (1024 * 1024)) * 1.25 * 1024 * 1024)
    usage = shutil.disk_usage(settings.STORAGE_ROOT)
    if usage.free < est_disk_bytes:
        raise HTTPException(
            status_code=507,
            detail=f"Insufficient disk space: {usage.free / (1024**2):.1f} MB available, requires {est_disk_bytes / (1024**2):.1f} MB (including 25% safety margin)."
        )

    # Available RAM preflight
    ram = psutil.virtual_memory()
    if ram.available < 350 * 1024 * 1024:
        raise HTTPException(
            status_code=503,
            detail=f"Insufficient available RAM: {ram.available / (1024**2):.1f} MB available. System requires at least 350 MB available physical RAM."
        )

class PlanRequest(BaseModel):
    target_width: int = Field(..., gt=0)
    target_height: int = Field(..., gt=0)
    source_version_id: Optional[str] = None
    preset: Optional[str] = None
    model: Optional[str] = None
    plan_choice: Optional[str] = None

class UpscaleVersionRequest(BaseModel):
    target_width: Optional[int] = Field(None, gt=0)
    target_height: Optional[int] = Field(None, gt=0)
    scale: Optional[int] = Field(None, ge=1, le=16)
    preset: Optional[str] = None
    model: Optional[str] = None
    output_format: str = "png"
    quality: int = Field(95, ge=1, le=100)
    plan_choice: Optional[str] = None

@router.post("/projects/{project_id}/plan")
def get_resolution_plan(project_id: str, req: PlanRequest):
    """
    Computes optimal upscale strategy (Plan A vs Plan B vs Plan C) with resource preflight
    and quality warnings (Part F1-F4).
    """
    source_ver_id = req.source_version_id
    if not source_ver_id:
        versions = get_versions_by_project(project_id)
        if not versions:
            raise HTTPException(status_code=404, detail="No versions found for project.")
        # Default to root original version
        orig = next((v for v in versions if v.get("parent_version_id") is None), versions[0])
        source_ver_id = orig["id"]

    source_ver = get_version(source_ver_id)
    if not source_ver:
        raise HTTPException(status_code=404, detail=f"Source version '{source_ver_id}' not found.")

    try:
        plan = resolution_planner.generate_plan(
            project_id=project_id,
            source_version_id=source_ver_id,
            target_width=req.target_width,
            target_height=req.target_height,
            preset=req.preset,
            preferred_model=req.model,
            plan_choice=req.plan_choice
        )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/projects/{project_id}/versions/{version_id}/upscale")
def upscale_from_version(
    project_id: str,
    version_id: str,
    req: UpscaleVersionRequest,
    background_tasks: BackgroundTasks
):
    """
    Spawns progressive upscale job directly from an existing version's on-disk image
    without requiring a browser upload round-trip (Part F4 & Invariant E2).
    """
    version = get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found.")

    if not os.path.isfile(version["storage_ref"]):
        raise HTTPException(status_code=410, detail="Version image file is missing from storage.")

    # Determine target dimensions
    target_w = req.target_width
    target_h = req.target_height

    if not target_w or not target_h:
        if req.scale:
            target_w = version["width"] * req.scale
            target_h = version["height"] * req.scale
        else:
            # Default 2x
            target_w = version["width"] * 2
            target_h = version["height"] * 2

    # Enforce preflight resource safety checks (disk + available RAM)
    check_system_resources(target_w, target_h)

    # Generate multi-stage or direct plan
    try:
        plan = resolution_planner.generate_plan(
            project_id=project_id,
            source_version_id=version_id,
            target_width=target_w,
            target_height=target_h,
            preset=req.preset,
            preferred_model=req.model,
            plan_choice=req.plan_choice
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job_id = str(uuid.uuid4())
    effective_scale = max(1, int(round(float(target_w) / float(version["width"]))))
    chosen_model = req.model or plan["stages"][0].get("model_name", "realesrgan-x4plus")

    create_job(
        job_id=job_id,
        image_id=version.get("project_id", project_id),
        input_path=version["storage_ref"],
        mode="progressive_upscale",
        scale=effective_scale,
        model=chosen_model,
        output_format=req.output_format.lower(),
        quality=req.quality,
        plan_json=json.dumps(plan)
    )

    background_tasks.add_task(job_manager.spawn_worker, job_id)

    return {
        "job_id": job_id,
        "project_id": project_id,
        "source_version_id": version_id,
        "target_resolution": f"{target_w}x{target_h}",
        "status": "queued",
        "plan": plan
    }

@router.post("/jobs/{job_id}/pause")
def pause_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    paused = job_manager.pause_job(job_id)
    return {"job_id": job_id, "paused": paused, "status": "paused" if paused else job["status"]}

@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    resumed = job_manager.resume_job(job_id)
    return {"job_id": job_id, "resumed": resumed, "status": "processing" if resumed else job["status"]}

@router.get("/jobs/{job_id}/stages")
def get_job_stages(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    stages = job_manager.get_stages(job_id)
    return {
        "job_id": job_id,
        "status": job["status"],
        "stages": stages
    }

