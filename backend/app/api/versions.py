import os
import io
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from PIL import Image

from backend.app.database import get_version, update_version_decision, delete_version_with_rules
from backend.app.services.version_service import version_service

router = APIRouter()

class DecisionRequest(BaseModel):
    decision: str  # 'accepted', 'rejected'

class CompareRequest(BaseModel):
    compare_with_version_id: str

@router.get("/versions/{version_id}")
def get_version_endpoint(version_id: str):
    v = get_version(version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    sanitized = dict(v)
    sanitized.pop("storage_ref", None)
    return {"version": sanitized}

@router.post("/versions/{version_id}/decision")
def set_version_decision_endpoint(version_id: str, req: DecisionRequest):
    if req.decision not in ("accepted", "rejected", "pending"):
        raise HTTPException(status_code=400, detail="Invalid decision value. Must be 'accepted' or 'rejected'.")
    v = get_version(version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")

    success = update_version_decision(version_id, req.decision)
    return {"version_id": version_id, "decision": req.decision, "success": success}

@router.post("/versions/{version_id}/compare")
def compare_versions_endpoint(version_id: str, req: CompareRequest):
    try:
        comparison = version_service.compare_versions(version_id, req.compare_with_version_id)
        return comparison
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/versions/{version_id}/preview")
def get_version_preview_endpoint(version_id: str):
    v = get_version(version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    path = v["storage_ref"]
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing from storage")

    try:
        with Image.open(path) as img:
            prev = img.copy()
            prev.thumbnail((1280, 1280))
            if prev.mode in ("RGBA", "P"):
                prev = prev.convert("RGB")
            buf = io.BytesIO()
            prev.save(buf, format="JPEG", quality=85)
            buf.seek(0)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")

@router.get("/versions/{version_id}/crop")
def get_version_crop_endpoint(
    version_id: str,
    x: int = Query(default=0, ge=0),
    y: int = Query(default=0, ge=0),
    width: int = Query(default=256, ge=16, le=2048),
    height: int = Query(default=256, ge=16, le=2048)
):
    v = get_version(version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    path = v["storage_ref"]
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing from storage")

    try:
        with Image.open(path) as full_img:
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
        raise HTTPException(status_code=500, detail=f"Crop failed: {str(e)}")

@router.get("/versions/{version_id}/download")
def download_version_endpoint(
    version_id: str,
    format: Optional[str] = Query(default=None),
    quality: Optional[int] = Query(default=95, ge=1, le=100)
):
    v = get_version(version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    path = v["storage_ref"]
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing from storage")

    req_format = (format or "").lower()
    current_ext = os.path.splitext(path)[1].replace(".", "").lower()

    if not req_format or req_format == current_ext:
        mime = "image/png" if current_ext == "png" else ("image/webp" if current_ext == "webp" else "image/jpeg")
        return FileResponse(path, media_type=mime, filename=f"aether_{version_id}.{current_ext}")

    try:
        with Image.open(path) as img:
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
                headers={"Content-Disposition": f'attachment; filename="aether_{version_id}.{ext}"'}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download conversion failed: {str(e)}")

@router.delete("/versions/{version_id}")
def delete_version_endpoint(version_id: str, force_subtree: bool = Query(default=False)):
    res = delete_version_with_rules(version_id, force_subtree=force_subtree)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
