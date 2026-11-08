import os
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.database import get_project, list_projects, get_versions_by_project

router = APIRouter()

def _sanitize_version(v: dict) -> dict:
    sanitized = dict(v)
    sanitized.pop("storage_ref", None)
    return sanitized

@router.get("/projects")
def list_projects_endpoint(limit: int = Query(default=30, ge=1, le=100)):
    projs = list_projects(limit=limit)
    res = []
    for p in projs:
        versions = get_versions_by_project(p["id"])
        res.append({
            "id": p["id"],
            "name": p["name"],
            "source_image_id": p["source_image_id"],
            "version_count": len(versions),
            "created_at": p["created_at"]
        })
    return {"projects": res}

@router.get("/projects/{project_id}")
def get_project_endpoint(project_id: str):
    p = get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    versions = [_sanitize_version(v) for v in get_versions_by_project(project_id)]
    return {
        "project": dict(p),
        "versions": versions
    }

@router.get("/projects/{project_id}/versions")
def get_project_versions_endpoint(project_id: str):
    p = get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    versions = [_sanitize_version(v) for v in get_versions_by_project(project_id)]
    return {"project_id": project_id, "versions": versions}
