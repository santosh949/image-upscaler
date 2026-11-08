import os
import time
import uuid
import stat
from typing import Dict, Any, Optional, List
from PIL import Image

from backend.app.core.config import settings
from backend.app.database import (
    create_project, get_project, list_projects,
    create_version, get_version, get_versions_by_project,
    get_child_versions, update_version_decision, delete_version_with_rules
)
from backend.app.services.storage_service import storage_service
from ai_engine.processing.consistency import ConsistencyChecker

class VersionService:
    """
    Business logic for the Version Graph (Part E).
    Enforces immutable versioning, parent provenance chains,
    authoritative JSON manifests, and acceptance/rejection semantics.
    """

    @staticmethod
    def create_project_from_image(image_id: str, filename: str, image_path: str, w: int, h: int, fmt: str) -> Dict[str, Any]:
        proj_id = f"proj_{image_id}"
        orig_ver_id = f"ver_{uuid.uuid4().hex[:12]}"
        now = time.time()
        mp = round((w * h) / 1_000_000.0, 2)

        # Compute SHA256 of source
        sha256 = storage_service.compute_sha256(image_path)

        create_project(proj_id, filename, image_id)

        version_data = {
            "id": orig_ver_id,
            "parent_version_id": None,
            "project_id": proj_id,
            "storage_ref": image_path,
            "width": w,
            "height": h,
            "megapixels": mp,
            "pixel_format": fmt,
            "bit_depth": 8,
            "has_alpha": 0,
            "color_profile": "sRGB",
            "operation": "original",
            "state": "ready",
            "decision": "accepted",
            "sha256": sha256,
            "created_at": now
        }
        create_version(version_data)

        # Write authoritative manifest
        manifest_data = {
            "version_id": orig_ver_id,
            "project_id": proj_id,
            "operation": "original",
            "source_hash": None,
            "output_hash": sha256,
            "parent_chain": [],
            "dimensions": [w, h],
            "created_at": now
        }
        storage_service.write_manifest(orig_ver_id, manifest_data)

        return {"project_id": proj_id, "root_version_id": orig_ver_id}

    @staticmethod
    def register_derived_version(
        project_id: str,
        parent_version_id: str,
        output_image_path: str,
        operation: str,
        mode: str,
        model_id: str,
        scale: int,
        runtime_s: float,
        parameters: Optional[Dict[str, Any]] = None,
        quality_eval: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registers an enhanced output as an immutable child version in the project DAG.
        Enforces Invariant E2.1 (read-only), E2.2 (never overwrite parent), E4 (manifest).
        """
        parent = get_version(parent_version_id)
        if not parent:
            raise ValueError(f"Parent version {parent_version_id} does not exist.")

        with Image.open(output_image_path) as img:
            w, h = img.size
            has_alpha = (img.mode == "RGBA")
            pixel_fmt = img.mode

        ver_id = f"ver_{uuid.uuid4().hex[:12]}"
        now = time.time()
        mp = round((w * h) / 1_000_000.0, 2)
        sha256 = storage_service.compute_sha256(output_image_path)

        # Invariant E2.1: Mark file read-only once ready
        try:
            os.chmod(output_image_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
        except Exception:
            pass

        version_data = {
            "id": ver_id,
            "parent_version_id": parent_version_id,
            "project_id": project_id,
            "storage_ref": output_image_path,
            "width": w,
            "height": h,
            "megapixels": mp,
            "pixel_format": pixel_fmt,
            "bit_depth": 8,
            "has_alpha": 1 if has_alpha else 0,
            "color_profile": "sRGB",
            "operation": operation,
            "mode": mode,
            "model_id": model_id,
            "parameters": parameters or {},
            "tile_size": (parameters or {}).get("tile_size", 256),
            "overlap": (parameters or {}).get("overlap", 32),
            "backend": "ncnn-vulkan",
            "device": "NVIDIA GeForce RTX 2050 (Vulkan #0)",
            "runtime_s": runtime_s,
            "sha256": sha256,
            "quality_eval": quality_eval or {},
            "state": "ready",
            "decision": "accepted",
            "created_at": now
        }
        create_version(version_data)

        # Build parent chain for authoritative manifest
        parent_chain = [parent_version_id]
        cur_p = parent
        while cur_p.get("parent_version_id"):
            parent_chain.append(cur_p["parent_version_id"])
            cur_p = get_version(cur_p["parent_version_id"]) or {}

        manifest_data = {
            "version_id": ver_id,
            "project_id": project_id,
            "operation": operation,
            "mode": mode,
            "model_id": model_id,
            "source_hash": parent.get("sha256"),
            "output_hash": sha256,
            "parent_chain": parent_chain,
            "dimensions": [w, h],
            "scale": scale,
            "parameters": parameters or {},
            "runtime_seconds": runtime_s,
            "consistency": quality_eval,
            "created_at": now
        }
        storage_service.write_manifest(ver_id, manifest_data)

        return version_data

    @staticmethod
    def compare_versions(version_a_id: str, version_b_id: str) -> Dict[str, Any]:
        """Calculates PSNR, MAE, color drift, and dimension ratio between two versions."""
        va = get_version(version_a_id)
        vb = get_version(version_b_id)
        if not va or not vb:
            raise ValueError("One or both versions not found.")

        path_a = va["storage_ref"]
        path_b = vb["storage_ref"]
        if not os.path.isfile(path_a) or not os.path.isfile(path_b):
            raise FileNotFoundError("Storage files missing for comparison.")

        with Image.open(path_a) as img_a, Image.open(path_b) as img_b:
            eval_metrics = ConsistencyChecker.evaluate(img_a, img_b)

        return {
            "version_a": {"id": va["id"], "dimensions": [va["width"], va["height"]], "operation": va["operation"]},
            "version_b": {"id": vb["id"], "dimensions": [vb["width"], vb["height"]], "operation": vb["operation"]},
            "metrics": eval_metrics
        }

version_service = VersionService()

